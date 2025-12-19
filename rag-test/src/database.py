import shutil
from pathlib import Path
from typing import List

from embeddings import get_embeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma


class VectorStoreManager:
    """Manager for Chroma vector store operations"""

    def __init__(self, persist_directory: str | None = None):
        """Initialize vector store"""
        base_dir = Path(__file__).resolve().parent.parent
        if persist_directory is None:
            self.persist_directory = base_dir / "chroma_db"
        else:
            self.persist_directory = Path(persist_directory)

        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.embedding_function = get_embeddings()
        self.vectorstore = Chroma(
            persist_directory=str(self.persist_directory),
            embedding_function=self.embedding_function,
        )

    def process_pdf(
        self, file_name: str, chunk_size: int, chunk_overlap: int
    ) -> List[Document]:
        """
        Process PDF files and return chunks with metadata.
        """
        # Create PDF reader object
        loader = PyPDFLoader(file_name)
        docs = loader.load()
        print(f"Pages loaded from {file_name}: {len(docs)}.")
        # Divide text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_documents(docs)
        # Print the number of chunks created from the documents
        print(f"Current number of chunks: {len(chunks)}.")

        return chunks

    def add_pdf(
        self, file_path: str, chunk_size: int = 1000, chunk_overlap: int = 100
    ) -> bool:
        """
        Add a PDF to the vector store.
        """
        try:
            # Process the PDF
            chunks = self.process_pdf(file_path, chunk_size, chunk_overlap)

            # Add to vector store
            self.vectorstore.add_documents(chunks)
            self.vectorstore.persist()

            print(f"Successfully added {len(chunks)} chunks from {file_path}")
            return True

        except Exception as e:
            print(f"Error adding PDF: {str(e)}")
            return False

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """
        Search for similar documents.
        """
        return self.vectorstore.similarity_search(query, k=k)

    def clear(self) -> None:
        """
        Clear all documents from the vector store by deleting all entries
        from the underlying Chroma collection.
        """
        try:
            collection = self.vectorstore._collection

            data = collection.get(include=[])
            ids = data.get("ids", [])

            if not ids:
                print("Vector store is already empty.")
                return

            collection.delete(ids=ids)
            print(f"Vector store cleared ({len(ids)} documents deleted).")

        except Exception as e:
            print(f"Error clearing vector store: {e}")
            raise e


# Global instance
_vector_store_manager = None


def get_vector_store():
    global _vector_store_manager
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager()
    return _vector_store_manager
