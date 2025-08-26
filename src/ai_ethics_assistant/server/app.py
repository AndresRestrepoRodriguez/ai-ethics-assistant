import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_ethics_assistant.configuration import Config
from ai_ethics_assistant.dependencies import Dependencies
from ai_ethics_assistant.pipeline.embedder import HuggingFaceEmbedder
from ai_ethics_assistant.server.api_v1 import router as api_v1_endpoints
from ai_ethics_assistant.server.internal import router as internal_endpoints
from ai_ethics_assistant.services.llm_service import LLMService
from ai_ethics_assistant.services.rag_service import RAGService
from ai_ethics_assistant.services.s3_service import S3Service
from ai_ethics_assistant.services.vector_store_service import VectorStoreService
from ai_ethics_assistant.version import __version__

logger = logging.getLogger(__name__)


def build_app(cfg: Config, **kwargs) -> FastAPI:
    # configure logging
    log_format: str = "%(asctime)s %(levelname)s %(module)s %(name)s %(message)s"
    logging.basicConfig(encoding="UTF-8", level=cfg.log_level, format=log_format)

    logger.warning(f"Server version: {__version__}")
    logger.warning(f"Starting server with configuration: {cfg}")

    readiness_lock = asyncio.Lock()

    @asynccontextmanager
    async def setup(app: FastAPI):
        async with readiness_lock:
            logger.warning("Setting up application")

            # Initialize services
            s3_service = S3Service(cfg.s3)
            vector_store_service = VectorStoreService(cfg.vector_db)
            embedder = HuggingFaceEmbedder(cfg.embedding.model_name)

            # Test S3 connection during startup (fail fast)
            if not await s3_service.test_connection():
                raise RuntimeError("Failed to connect to S3 service")

            # Test Qdrant connection during startup (fail fast)
            if not await vector_store_service.test_connection():
                raise RuntimeError("Failed to connect to Qdrant service")

            # Ensure collection exists
            await vector_store_service.ensure_collection()

            # Initialize RAG services
            try:
                llm_service = LLMService(cfg.llm)
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                logger.error(
                    "Please ensure LLM__API_KEY is set in environment variables"
                )
                raise RuntimeError(f"LLM service initialization failed: {e}")

            rag_service = RAGService(llm_service, embedder, vector_store_service)

            # Test LLM connection during startup (fail fast)
            if not await llm_service.test_connection():
                logger.warning(
                    "LLM connection test failed - service may not work properly"
                )

            # Initialize dependencies
            app.state.dependencies = Dependencies(
                config=cfg,
                s3_service=s3_service,
                vector_store_service=vector_store_service,
                embedder=embedder,
                llm_service=llm_service,
                rag_service=rag_service,
            )
            app.state.readiness_lock = readiness_lock

        try:
            # Do not move the `yield` statement. we must yield
            # outside of the lock, to ensure we release it
            # and unblock the readiness check.
            yield
        finally:
            # Cleanup on shutdown
            logger.warning("Application cleanup complete")

    app = FastAPI(
        lifespan=setup,
        debug=cfg.dev_mode,
        root_path=cfg.root_path,
        title="AI Ethics Assistant API",
        description="RAG-based Q&A system for AI policy and ethics documents",
        version=__version__,
    )

    if cfg.cors_origins is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cfg.cors_origins.split(","),
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )

    # Dependencies are now injected via FastAPI Depends() pattern in routes

    # Include routers
    app.include_router(internal_endpoints, prefix="/internal")
    app.include_router(api_v1_endpoints)

    return app
