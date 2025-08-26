import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from ai_ethics_assistant.configuration import Config
from ai_ethics_assistant.dependencies import get_config
from ai_ethics_assistant.version import __version__

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/liveness", tags=["ops"])
def liveness_check():
    """
    Check if the server is running.
    """
    return f"OK: {__version__}"


@router.get("/health", tags=["ops"])
async def health_check(config: Annotated[Config, Depends(get_config)]):
    #TODO: Add proper readiness/health checks
    """
    Check if the API is healthy and running.
    """
    return {
        "status": "healthy", 
        "message": f"AI Ethics Assistant API is running (dev_mode: {config.dev_mode})"
    }
