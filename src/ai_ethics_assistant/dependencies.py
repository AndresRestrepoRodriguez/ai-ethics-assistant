from dataclasses import dataclass

from fastapi import Request

from ai_ethics_assistant.configuration import Config
from ai_ethics_assistant.services.s3_service import S3Service
from ai_ethics_assistant.services.vector_store_service import VectorStoreService


@dataclass
class Dependencies:
    config: Config
    s3_service: S3Service
    vector_store_service: VectorStoreService
    # Future services will be added here in later stages
    # rag_service: RAGService
    # llm_service: LLMService


def get_config(request: Request) -> Config:
    """Get configuration from application state."""
    state: Dependencies = request.app.state.dependencies
    return state.config


def get_s3_service(request: Request) -> S3Service:
    """Get S3 service from application state."""
    state: Dependencies = request.app.state.dependencies
    return state.s3_service


def get_vector_store_service(request: Request) -> VectorStoreService:
    """Get vector store service from application state."""
    state: Dependencies = request.app.state.dependencies
    return state.vector_store_service
