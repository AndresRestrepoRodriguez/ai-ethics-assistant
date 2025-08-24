import logging

from fastapi import APIRouter

from ai_ethics_assistant.version import __version__

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/liveness", tags=["ops"])
def liveness_check():
    """
    Check if the server is running.
    """
    return f"OK: {__version__}"
