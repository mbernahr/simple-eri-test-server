from config import EMBEDDING_MODEL_NAME
from langchain_community.embeddings import HuggingFaceEmbeddings


def get_embeddings():
    """Get the embedding function"""
    embedding_model = EMBEDDING_MODEL_NAME
    return HuggingFaceEmbeddings(
        model_name=embedding_model, model_kwargs={"device": "cpu"}
    )
