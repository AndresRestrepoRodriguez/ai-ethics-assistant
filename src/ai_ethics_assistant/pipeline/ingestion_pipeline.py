import hashlib
import logging
from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_DNS

from ai_ethics_assistant.configuration import Config
from ai_ethics_assistant.pipeline.embedder import HuggingFaceEmbedder, TextChunker
from ai_ethics_assistant.pipeline.pdf_processor import DoclingPDFProcessor
from ai_ethics_assistant.services.s3_service import S3Service
from ai_ethics_assistant.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class IngestionPipelineError(Exception):
    pass


class IngestionPipeline:
    """Orchestrates PDF ingestion pipeline: S3 → PDF Processing → Chunking → Embedding → Vector Storage"""

    def __init__(
        self,
        s3_service: S3Service,
        vector_store_service: VectorStoreService,
        embedder: HuggingFaceEmbedder,
        config: Config,
    ):
        self.s3_service = s3_service
        self.vector_store_service = vector_store_service
        self.embedder = embedder
        self.config = config

        # Initialize processing components
        self.pdf_processor = DoclingPDFProcessor()
        self.text_chunker = TextChunker(
            chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
        )

        logger.info("Initialized ingestion pipeline")

    async def ingest_all_pdfs(self) -> dict:
        """Process all PDFs in S3 bucket"""
        try:
            logger.info("Starting ingestion of all PDFs")

            # List all PDFs in bucket
            pdf_keys = await self.s3_service.list_pdfs()

            if not pdf_keys:
                logger.info("No PDF files found in bucket")
                return {"processed": 0, "failed": 0, "files": []}

            logger.info(f"Found {len(pdf_keys)} PDF files to process")

            results = {"processed": 0, "failed": 0, "files": []}

            # Process each PDF individually
            for pdf_key in pdf_keys:
                try:
                    result = await self.ingest_single_pdf(pdf_key)
                    results["processed"] += 1
                    results["files"].append(
                        {
                            "file": pdf_key,
                            "status": "success",
                            "chunks": result["chunks"],
                        }
                    )
                    logger.info(f"Successfully processed {pdf_key}")
                except Exception as e:
                    results["failed"] += 1
                    results["files"].append(
                        {"file": pdf_key, "status": "failed", "error": str(e)}
                    )
                    logger.error(f"Failed to process {pdf_key}: {e}")

            logger.info(
                f"Ingestion complete: {results['processed']} succeeded, {results['failed']} failed"
            )
            return results

        except Exception as e:
            raise IngestionPipelineError(f"Failed to ingest PDFs: {e}")

    async def ingest_single_pdf(self, pdf_key: str) -> dict:
        """Process a single PDF file with deduplication"""
        try:
            logger.info(f"Processing PDF: {pdf_key}")

            # Generate consistent document ID from filename
            document_id = self._generate_document_id(pdf_key)

            # Step 1: Delete existing chunks for this document (deduplication)
            await self._delete_existing_chunks(document_id)

            # Step 2: Download PDF from S3
            pdf_content = await self.s3_service.download_pdf(pdf_key)
            file_size = len(pdf_content)

            # Step 3: Process PDF to extract text
            text = await self.pdf_processor.process_pdf(pdf_content, pdf_key)

            # Step 4: Chunk text into optimal sizes
            filename = pdf_key.split("/")[-1]  # Extract filename from S3 key
            metadata = {
                "filename": filename,
                "document_id": document_id,
                "file_size": file_size,
                "processed_date": datetime.now(timezone.utc).isoformat(),
            }

            chunks = self.text_chunker.chunk_text(text, metadata)

            if not chunks:
                logger.warning(f"No chunks created for {pdf_key}")
                return {"chunks": 0}

            # Step 5: Generate embeddings for all chunks
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = await self.embedder.embed_batch(chunk_texts)

            # Step 6: Prepare data for vector store
            embeddings_data = []
            for chunk, embedding in zip(chunks, embeddings):
                # Update chunk metadata with actual chunk info
                payload = chunk["metadata"].copy()
                payload["text"] = chunk["text"]
                payload["chunk_id"] = chunk["chunk_id"]

                # Generate deterministic UUID from document_id and chunk_id
                point_id = str(uuid5(NAMESPACE_DNS, f"{document_id}_chunk_{chunk['chunk_id']}"))
                
                embeddings_data.append(
                    {
                        "id": point_id,
                        "vector": embedding,
                        "payload": payload,
                    }
                )

            # Step 7: Store embeddings in vector database
            await self.vector_store_service.store_embeddings(embeddings_data)

            logger.info(
                f"Successfully processed {pdf_key}: {len(chunks)} chunks stored"
            )
            return {"chunks": len(chunks)}

        except Exception as e:
            raise IngestionPipelineError(f"Failed to process {pdf_key}: {e}")

    def _generate_document_id(self, pdf_key: str) -> str:
        """Generate consistent document ID hash from S3 key"""
        # Remove S3 prefix to get the clean filename
        cleaned_name = pdf_key.replace(self.config.s3.pdf_prefix, "")
        # Generate SHA-256 hash for consistent, collision-resistant ID
        return hashlib.sha256(cleaned_name.encode()).hexdigest()[:16]

    async def _delete_existing_chunks(self, document_id: str) -> None:
        """Delete existing chunks for a document (deduplication)"""
        try:
            # Use the proper delete_by_filter method
            deleted_count = await self.vector_store_service.delete_by_filter(
                {"document_id": document_id}
            )

            if deleted_count > 0:
                logger.info(
                    f"Deleted {deleted_count} existing chunks for document {document_id}"
                )

        except Exception as e:
            # Don't fail the entire ingestion if deletion fails
            logger.warning(f"Failed to delete existing chunks for {document_id}: {e}")
