from dataclasses import dataclass

from fastapi import Request

from ai_ethics_assistant.configuration import Config


@dataclass
class Dependencies:
    config: Config
    # Future services will be added here in later stages
    # rag_service: RAGService
    # vector_store_client: QdrantClient
    # llm_service: LLMService


def get_config(request: Request) -> Config:
    """Get configuration from application state."""
    state: Dependencies = request.app.state.dependencies
    return state.config
