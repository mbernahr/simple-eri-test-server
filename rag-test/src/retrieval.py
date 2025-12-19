from typing import List
from database import get_vector_store
from models import Context, RetrievalRequest
from config import ContentType

class RetrievalManager:
    """Manages retrieval from vector store"""
    
    def __init__(self):
        self.vector_store = get_vector_store()

    def process_retrieval_request(self, request: RetrievalRequest) -> List[Context]:
        """
        Process a retrieval request.
        """
        # Get similar documents
        docs = self.vector_store.similarity_search(
            request.latestUserPrompt,
            k=request.maxMatches if request.maxMatches > 0 else 3
        )
        
        # Convert to Context objects
        contexts = []
        for doc in docs:
            context = Context(
                name=doc.metadata.get("source", "Unknown"),
                category="Research Paper",
                path=doc.metadata.get("source"),
                type=ContentType.TEXT,
                matchedContent=doc.page_content,
                surroundingContent=[],
                links=[]
            )
            contexts.append(context)
            
        return contexts
    
# Global instance
_retrieval_manager = None

def get_retrieval_manager():
    global _retrieval_manager
    if _retrieval_manager is None:
        _retrieval_manager = RetrievalManager()
    return _retrieval_manager