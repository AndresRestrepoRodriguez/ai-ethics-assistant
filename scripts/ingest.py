#!/usr/bin/env python3
"""
Ingestion script for AI Ethics Assistant
Processes all PDFs from S3 bucket and stores embeddings in Qdrant

Usage:
    uv run python scripts/ingest.py

Configuration:
    Uses environment variables from .env file
    See .env.example for required variables
"""

import asyncio
import logging
import sys

from ai_ethics_assistant.configuration import Config
from ai_ethics_assistant.pipeline.embedder import HuggingFaceEmbedder
from ai_ethics_assistant.pipeline.ingestion_pipeline import IngestionPipeline
from ai_ethics_assistant.services.s3_service import S3Service
from ai_ethics_assistant.services.vector_store_service import VectorStoreService


async def main():
    """Main ingestion function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(__name__)

    try:
        # Load configuration from environment variables
        logger.info("Loading configuration...")
        config = Config()

        # Initialize all services
        logger.info("Initializing services...")

        # S3 Service
        s3_service = S3Service(config.s3)
        if not await s3_service.test_connection():
            raise RuntimeError(
                "Failed to connect to S3 - check credentials and bucket configuration"
            )

        # Vector Store Service (Qdrant)
        vector_store_service = VectorStoreService(config.vector_db)
        if not await vector_store_service.test_connection():
            raise RuntimeError(
                "Failed to connect to Qdrant - ensure service is running"
            )

        # Ensure collection exists
        await vector_store_service.ensure_collection()

        # Embedder
        embedder = HuggingFaceEmbedder(config.embedding.model_name)

        # Create ingestion pipeline
        pipeline = IngestionPipeline(
            s3_service=s3_service,
            vector_store_service=vector_store_service,
            embedder=embedder,
            config=config,
        )

        # Run ingestion
        logger.info("Starting PDF ingestion pipeline...")
        results = await pipeline.ingest_all_pdfs()

        # Report results
        logger.info("Ingestion Summary:")
        logger.info(f"   Successfully processed: {results['processed']} PDFs")
        logger.info(f"   Failed to process: {results['failed']} PDFs")

        if results["files"]:
            logger.info("File Details:")
            for file_info in results["files"]:
                if file_info["status"] == "success":
                    logger.info(
                        f"   SUCCESS: {file_info['file']} - {file_info['chunks']} chunks"
                    )
                else:
                    logger.error(
                        f"   FAILED: {file_info['file']} - {file_info['error']}"
                    )

        if results["failed"] == 0:
            logger.info("All PDFs processed successfully!")
            return 0
        else:
            logger.warning(f"{results['failed']} PDFs failed to process")
            return 1

    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
