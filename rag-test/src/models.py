from typing import Dict, List, Optional

from config import AuthField, AuthMethod, ContentType, ProviderType, Role
from pydantic import BaseModel, Field


class AuthFieldMapping(BaseModel):
    authField: AuthField
    fieldName: Optional[str] = None


class AuthScheme(BaseModel):
    authMethod: AuthMethod
    authFieldMappings: Optional[List[AuthFieldMapping]] = None


class AuthResponse(BaseModel):
    success: bool = Field(description="True, when the authentication was successful.")
    token: Optional[str] = Field(
        None, description="The token to use for further requests."
    )
    message: Optional[str] = Field(
        None,
        description="When the authentication was not successful, this contains the reason.",
    )


class DataSourceInfo(BaseModel):
    name: Optional[str] = Field(None, description="The name of the data source")
    description: Optional[str] = Field(
        None, description="A short description of the data source"
    )


class EmbeddingInfo(BaseModel):
    embeddingType: Optional[str] = Field(
        None, description="What kind of embedding is used"
    )
    embeddingName: Optional[str] = Field(None, description="Name the embedding used")
    description: Optional[str] = Field(
        None, description="A short description of the embedding"
    )
    usedWhen: Optional[str] = Field(
        None, description="Describe when the embedding is used"
    )
    link: Optional[str] = Field(
        None, description="A link to the embedding's documentation"
    )


class RetrievalInfo(BaseModel):
    id: Optional[str] = Field(
        None, description="A unique identifier for the retrieval process"
    )
    name: Optional[str] = Field(None, description="The name of the retrieval process")
    description: Optional[str] = Field(
        None, description="A short description of the retrieval process"
    )
    link: Optional[str] = Field(
        None, description="A link to the retrieval process's documentation"
    )
    parametersDescription: Optional[Dict[str, str]] = Field(
        None, description="A dictionary that describes the parameters"
    )
    embeddings: Optional[List[EmbeddingInfo]] = Field(
        None, description="A list of embeddings used"
    )


class ContentBlock(BaseModel):
    content: Optional[str] = Field(None, description="The content of the block")
    role: Role
    type: ContentType


class ChatThread(BaseModel):
    contentBlocks: Optional[List[ContentBlock]] = Field(
        None, description="The content blocks in this chat thread"
    )


class RetrievalRequest(BaseModel):
    latestUserPrompt: Optional[str] = Field(None, description="The latest user prompt")
    latestUserPromptType: ContentType
    thread: ChatThread
    retrievalProcessId: Optional[str] = Field(
        None, description="The ID of the retrieval process to use"
    )
    parameters: Optional[Dict[str, str]] = Field(
        None, description="Parameters for the retrieval process"
    )
    maxMatches: int = Field(description="Maximum number of matches to return")


class Context(BaseModel):
    name: Optional[str] = Field(None, description="The name of the source")
    category: Optional[str] = Field(None, description="Category of the contents")
    path: Optional[str] = Field(None, description="The path to the content")
    type: ContentType
    matchedContent: Optional[str] = Field(
        None, description="The content that matched the user prompt"
    )
    surroundingContent: Optional[List[str]] = Field(
        None, description="The surrounding content"
    )
    links: Optional[List[str]] = Field(None, description="Links to related content")


class SecurityRequirements(BaseModel):
    allowedProviderType: ProviderType


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class TokenRequest(BaseModel):
    token: str = Field(..., description="The static token for authentication")
