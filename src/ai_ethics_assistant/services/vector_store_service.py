import logging
from datetime import datetime
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ai_ethics_assistant.configuration import VectorDBConfig

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    pass


class VectorStoreService:
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.client = QdrantClient(
            host=config.host,
            port=config.port,
        )
        # Vector dimension for all-MiniLM-L6-v2
        self.vector_size = 384

    async def ensure_collection(self) -> bool:
        """Create collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.config.collection_name not in collection_names:
                # Create collection with cosine similarity
                self.client.create_collection(
                    collection_name=self.config.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created collection '{self.config.collection_name}'")
            else:
                logger.info(
                    f"Collection '{self.config.collection_name}' already exists"
                )

            return True

        except Exception as e:
            raise VectorStoreError(f"Failed to ensure collection: {e}")

    async def store_embeddings(self, embeddings: list[dict]) -> bool:
        """Store document embeddings with metadata

        Args:
            embeddings: List of dicts with format:
                {
                    "id": str (optional, will generate if not provided),
                    "vector": list[float],
                    "payload": {
                        "text": str,
                        "filename": str,
                        "chunk_id": int,
                        ...other metadata
                    }
                }
        """
        try:
            points = []
            for embedding in embeddings:
                point_id = embedding.get("id", str(uuid4()))

                # Add timestamp if not present
                payload = embedding["payload"].copy()
                if "created_at" not in payload:
                    payload["created_at"] = datetime.now().isoformat()

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding["vector"],
                        payload=payload,
                    )
                )

            # Upload points to collection
            self.client.upsert(
                collection_name=self.config.collection_name,
                points=points,
            )

            logger.info(f"Stored {len(points)} embeddings in collection")
            return True

        except Exception as e:
            raise VectorStoreError(f"Failed to store embeddings: {e}")

    async def search_similar(
        self, query_embedding: list[float], limit: int = 5
    ) -> list[dict]:
        """Search for similar documents using vector similarity

        Args:
            query_embedding: Query vector
            limit: Maximum number of results

        Returns:
            List of similar documents with scores and metadata
        """
        try:
            results = self.client.search(
                collection_name=self.config.collection_name,
                query_vector=query_embedding,
                limit=limit,
            )

            # Format results
            documents = []
            for result in results:
                documents.append(
                    {
                        "id": result.id,
                        "score": result.score,
                        "payload": result.payload,
                    }
                )

            logger.info(f"Found {len(documents)} similar documents")
            return documents

        except Exception as e:
            raise VectorStoreError(f"Failed to search documents: {e}")

    async def test_connection(self) -> bool:
        """Test Qdrant connection"""
        try:
            # Try to get collections as a connection test
            self.client.get_collections()
            logger.info(
                f"Successfully connected to Qdrant at {self.config.host}:{self.config.port}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            return False
