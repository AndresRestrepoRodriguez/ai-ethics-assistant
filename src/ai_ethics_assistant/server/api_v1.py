import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from ai_ethics_assistant.configuration import Config
from ai_ethics_assistant.dependencies import get_config
from ai_ethics_assistant.server.models import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def api_health_check(
    config: Annotated[Config, Depends(get_config)],
) -> HealthResponse:
    """
    Check if the API is healthy.
    """
    return HealthResponse(
        status="healthy",
        message=f"AI Ethics Assistant API is running (dev_mode: {config.dev_mode})",
    )


# Placeholder endpoint for future Q&A functionality
@router.get("/status", tags=["status"])
async def get_status(config: Annotated[Config, Depends(get_config)]):
    """
    Get system status (placeholder for Stage 4).
    """
    return {
        "status": "ready",
        "services": {
            "api": "running",
            "vector_db": f"configured for {config.vector_db.host}:{config.vector_db.port}",
            "llm": f"configured for {config.llm.model_name}",
        },
        "dev_mode": config.dev_mode,
    }
