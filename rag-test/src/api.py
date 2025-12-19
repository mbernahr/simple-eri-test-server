import logging
from pathlib import Path
from typing import List, Optional

from auth import authenticate_user, authenticate_user_password, get_current_user
from config import (
    AUTH_SCHEMES,
    DATA_SOURCE_INFO,
    EMBEDDING_INFO,
    RETRIEVAL_INFO,
    SECURITY_REQUIREMENTS,
    VALID_USER_CREDENTIALS,
)
from database import get_vector_store
from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import (
    AuthMethod,
    AuthResponse,
    AuthScheme,
    Context,
    DataSourceInfo,
    EmbeddingInfo,
    RetrievalInfo,
    RetrievalRequest,
    SecurityRequirements,
)
from pydantic import BaseModel
from retrieval import get_retrieval_manager
from security import get_security_manager
from user_store import upsert_user

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# Create API routers
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
data_source_router = APIRouter(tags=["Data Source"])
embedding_router = APIRouter(prefix="/embedding", tags=["Embedding"])
retrieval_router = APIRouter(prefix="/retrieval", tags=["Retrieval"])
security_router = APIRouter(prefix="/security", tags=["Security"])


# Authentication endpoints
@auth_router.get("/methods", response_model=List[AuthScheme])
async def get_auth_methods() -> List[AuthScheme]:
    """Get available authentication methods"""
    return AUTH_SCHEMES


@auth_router.post("", response_model=AuthResponse)
async def authenticate(
    authMethod: AuthMethod = Query(..., alias="authMethod"),
    token_cred: Optional[HTTPAuthorizationCredentials] = Depends(security),
    username: Optional[str] = Header(None, alias="user"),
    password: Optional[str] = Header(None, alias="password"),
) -> AuthResponse:
    """
    Authenticate with the data source.

    Args:
        authMethod: Authentication method to use
        token_request: Token request data

    Returns:
        Authentication response
    """

    # TOKEN-Flow
    if authMethod == AuthMethod.TOKEN:
        if not token_cred or not token_cred.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return authenticate_user(token_cred.credentials)

    # USERNAME_PASSWORD-Flow
    if authMethod == AuthMethod.USERNAME_PASSWORD:
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Header 'username' and 'password' required.",
            )
        return authenticate_user_password(username, password)

    # All other Methods (at the moment)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported authentication method",
    )


# Data Source endpoints
@data_source_router.get("/dataSource", response_model=DataSourceInfo)
async def get_data_source_info(_=Depends(get_current_user)) -> DataSourceInfo:
    """Get information about the data source"""
    return DATA_SOURCE_INFO


# Embedding endpoints
@embedding_router.get("/info", response_model=List[EmbeddingInfo])  # List notwendig?
async def get_embedding_info(_=Depends(get_current_user)) -> List[EmbeddingInfo]:
    """Get information about the embeddings"""
    return [EMBEDDING_INFO]


# Retrieval endpoints
@retrieval_router.get("/info", response_model=List[RetrievalInfo])
async def get_retrieval_info(_=Depends(get_current_user)) -> List[RetrievalInfo]:
    """Get information about the retrieval processes"""
    return [RETRIEVAL_INFO]


@retrieval_router.post("", response_model=List[Context])  # get?
async def retrieve(
    request: RetrievalRequest, _=Depends(get_current_user)
) -> List[Context]:
    """
    Retrieve information from the data source.

    Args:
        request: Retrieval request

    Returns:
        List of context objects
    """

    # Validate request
    if not request.latestUserPrompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User prompt is required"
        )

    # Sanitize input
    security_manager = get_security_manager()
    sanitized_prompt = security_manager.sanitize_input(request.latestUserPrompt)
    request.latestUserPrompt = sanitized_prompt

    # Process retrieval request
    retrieval_manager = get_retrieval_manager()
    try:
        contexts = retrieval_manager.process_retrieval_request(request)
        return contexts
    except Exception as e:
        logger.exception("Retrieval failed")
        raise HTTPException(status_code=500, detail=f"Retrieval process failed: {e}")


# Security endpoints
@security_router.get("/requirements", response_model=SecurityRequirements)
async def get_security_requirements(
    _=Depends(get_current_user),
) -> SecurityRequirements:
    """Get the security requirements"""
    return SECURITY_REQUIREMENTS


# Admin endpoints
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


class UserCreateRequest(BaseModel):
    username: str
    password: str


@admin_router.post("/user")
async def create_user(req: UserCreateRequest):
    """
    Create or update a user in the persistent user store.
    """
    upsert_user(req.username, req.password)
    return {"success": True, "username": req.username}


@admin_router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF, save it under src/Papers, and index it into the vector DB.
    """
    papers_dir = Path(__file__).resolve().parent / "Papers"
    papers_dir.mkdir(parents=True, exist_ok=True)
    dest = papers_dir / file.filename

    contents = await file.read()
    dest.write_bytes(contents)

    vs = get_vector_store()
    ok = vs.add_pdf(str(dest))
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to index PDF.")

    return {"success": True, "filename": file.filename}


@admin_router.post("/clear")
async def clear_vector_store():
    """
    Clear all documents from the Chroma vector DB.
    (PDF-Dateien unter Papers bleiben erhalten.)
    """
    vs = get_vector_store()
    vs.clear()
    return {"success": True}


# Create combined router
api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(data_source_router)
api_router.include_router(embedding_router)
api_router.include_router(retrieval_router)
api_router.include_router(security_router)
api_router.include_router(admin_router)


@api_router.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    return {"status": "healthy"}
