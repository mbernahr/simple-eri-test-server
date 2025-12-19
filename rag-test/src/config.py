from enum import Enum

# Server Configuration
HOST = "0.0.0.0"
PORT = 40304
API_TITLE = "RAG Test"
API_VERSION = "v1"

# Security Configuration
SECRET_KEY = (
    "your-secret-key-here"  # Should be loaded from environment variable in production
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

# Authentication Configuration
VALID_STATIC_TOKENS = {}

# Static User/Pass-Pairs for USERNAME_PASSWORD
VALID_USER_CREDENTIALS = {}


# ChromaDB Configuration
# CHROMA_HOST = "localhost"
# CHROMA_PORT = 8000
COLLECTION_NAME = "document_chunks"

# Embedding Configuration
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # Dimension of the embedding vectors

# Retrieval Configuration
MAX_RESULTS = 3  # Default maximum number of results to return
SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score to consider a match

# API Information
DATA_SOURCE_INFO = {
    "name": "RAG Test",
    "description": "A test implementation of the ERI API using ChromaDB for vector storage and retrieval.",
}

EMBEDDING_INFO = {
    "embeddingType": "Transformer embedding",
    "embeddingName": "all-MiniLM-L6-v2",
    "description": "Using the 'all-MiniLM-L6-v2' model from the Sentence Transformers library.",
    "usedWhen": "anytime",
    "link": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
}

RETRIEVAL_INFO = {
    "id": "test-retrieval-1",
    "name": "Test Retrieval",
    "description": "Using a similarity-based search with the top 3 similar results",
    "link": None,
    "parametersDescription": {
        "similarity_threshold": "Float between 0.0 and 1.0, default: 0.7",
        "max_results": "Integer > 0, default: 3",
    },
    "embeddings": [
        {
            "embeddingType": "Transformer embedding",
            "embeddingName": "all-MiniLM-L6-v2",
            "description": "Using the 'all-MiniLM-L6-v2' model from the Sentence Transformers library.",
            "usedWhen": "anytime",
            "link": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
        }
    ],
}


class ContentType(str, Enum):
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    SPEECH = "SPEECH"


class Role(str, Enum):
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"
    SYSTEM = "SYSTEM"
    USER = "USER"
    AI = "AI"
    AGENT = "AGENT"


class AuthMethod(str, Enum):
    NONE = "NONE"
    KERBEROS = "KERBEROS"
    USERNAME_PASSWORD = "USERNAME_PASSWORD"
    TOKEN = "TOKEN"


class AuthField(str, Enum):
    NONE = "NONE"
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"
    TOKEN = "TOKEN"
    KERBEROS_TICKET = "KERBEROS_TICKET"


class ProviderType(str, Enum):
    NONE = "NONE"
    ANY = "ANY"
    SELF_HOSTED = "SELF_HOSTED"


# Security requirements
SECURITY_REQUIREMENTS = {"allowedProviderType": ProviderType.ANY}

# Authentication schemes configuration
AUTH_SCHEMES = [
    {
        "authMethod": AuthMethod.TOKEN,
        "authFieldMappings": [{"authField": AuthField.TOKEN, "fieldName": "token"}],
    },
    {
        "authMethod": AuthMethod.USERNAME_PASSWORD,
        "authFieldMappings": [
            {
                "authField": AuthField.USERNAME,
                "fieldName": "username",
            },
            {
                "authField": AuthField.PASSWORD,
                "fieldName": "password",
            },
        ],
    },
]
