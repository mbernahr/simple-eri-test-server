import logging
import sys

import uvicorn
from api import api_router
from config import API_TITLE, API_VERSION, HOST, PORT
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from security import get_security_manager

# Create Logger
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="External Retrieval Interface (ERI) for RAG implementation",
    docs_url=None,
    redoc_url="/redoc",
)


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    """Expose the OpenAPI schema as JSON."""
    return JSONResponse(content=app.openapi())


def custom_openapi():
    """Generate and cache a custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description="External Retrieval Interface (ERI) for RAG implementation",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Set custom OpenAPI schema
app.openapi = custom_openapi


@app.get("/panda", include_in_schema=False)
async def custom_swagger_ui_html():
    """Serve Swagger UI for manual testing."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


@app.get("/")
async def root():
    """Simple health/info endpoint."""
    return {"message": "ERI API Server is running"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return formatted HTTPExceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers or {},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    # logger.exception(f"Uncaught exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# Add CORS middleware with strict settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # 10 minutes
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API router
app.include_router(api_router)


@app.middleware("http")
async def validate_request_security(request: Request, call_next) -> Response:
    """
    Middleware to validate request security.

    Args:
        request: The incoming request
        call_next: The next middleware or route handler

    Returns:
        Response after security validation
    """
    # Preflight-OPTIONS without token check
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path

    # Skip security validation for authentication endpoints
    if path.startswith("/auth"):
        return await call_next(request)

    if path.startswith("/admin"):
        return await call_next(request)

    # Skip security validation for OpenAPI documentation
    if request.url.path in [
        "/panda",
        "/redoc",
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/health",
        "/",
    ]:
        return await call_next(request)

    # Validate request security
    security_manager = get_security_manager()
    await security_manager.validate_request_security(request)

    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    """
    Middleware to add security headers to all responses.

    Args:
        request: The incoming request
        call_next: The next middleware or route handler

    Returns:
        Response with added security headers
    """
    # Get response from next handler
    response = await call_next(request)

    # Add security headers
    security_manager = get_security_manager()
    security_headers = security_manager.get_security_headers()

    for header_name, header_value in security_headers.items():
        response.headers[header_name] = header_value

    return response


@app.on_event("startup")
async def startup_event() -> None:
    """
    Perform startup and shutdown tasks.
    Initialize necessary components and validate configuration.
    """

    # Initialize security manager
    security_manager = get_security_manager()

    # Validate configuration
    if not security_manager.validate_provider_type(None):
        raise RuntimeError("Invalid provider type configuration")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Perform shutdown tasks.
    Clean up resources and connections.
    """

    # Add cleanup code here if needed


def start() -> None:
    """
    Start the FastAPI application using Uvicorn.
    """

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,  # Disable in production
        workers=1,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
        server_header=False,
    )


if __name__ == "__main__":
    start()
