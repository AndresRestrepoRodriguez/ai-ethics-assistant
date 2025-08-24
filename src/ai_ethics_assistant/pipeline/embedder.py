import logging
from abc import ABC, abstractmethod

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class EmbedderError(Exception):
    pass


class Embedder(ABC):
    """Abstract base class for embedding generators"""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Return embedding vector dimension"""
        pass


class HuggingFaceEmbedder(Embedder):
    """Hugging Face sentence-transformers implementation using LangChain"""

    def __init__(self, model_name: str):
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
            # Get dimension by embedding a test string
            self.dimension = len(self.embeddings.embed_query("test"))
            logger.info(f"Initialized HuggingFace embedder with model '{model_name}'")
            logger.info(f"Embedding dimension: {self.dimension}")
        except Exception as e:
            raise EmbedderError(
                f"Failed to initialize embedder with model '{model_name}': {e}"
            )

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text"""
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            raise EmbedderError(f"Failed to embed text: {e}")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts efficiently"""
        try:
            if not texts:
                return []

            logger.info(f"Embedding batch of {len(texts)} texts")
            embeddings = self.embeddings.embed_documents(texts)
            logger.info(f"Successfully embedded {len(texts)} texts")
            return embeddings

        except Exception as e:
            raise EmbedderError(f"Failed to embed batch: {e}")

    def get_embedding_dimension(self) -> int:
        return self.dimension


class TextChunker:
    """Utility for chunking text into optimal sizes for embedding"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize text chunker

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Character overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # RecursiveCharacterTextSplitter maintains sentence boundaries
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

        logger.info(
            f"Initialized text chunker (size={chunk_size}, overlap={chunk_overlap})"
        )

    def chunk_text(self, text: str, metadata: dict | None = None) -> list[dict]:
        """Split text into chunks with metadata

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunks with format:
                {
                    "text": str,
                    "chunk_id": int,
                    "metadata": dict
                }
        """
        try:
            chunks = self.splitter.split_text(text)

            result = []
            for i, chunk_text in enumerate(chunks):
                chunk_data = {
                    "text": chunk_text,
                    "chunk_id": i,
                    "metadata": metadata or {},
                }
                result.append(chunk_data)

            logger.info(f"Split text into {len(chunks)} chunks")
            return result

        except Exception as e:
            raise EmbedderError(f"Failed to chunk text: {e}")
