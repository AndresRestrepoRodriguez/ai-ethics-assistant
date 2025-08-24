from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""

    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Health check message")


class QueryRequest(BaseModel):
    """Request model for Q&A queries (placeholder for Stage 4)."""

    query: str = Field(..., min_length=1, description="Question to ask the system")
    max_results: Optional[int] = Field(
        5, ge=1, le=20, description="Maximum number of results to return"
    )


class QueryResponse(BaseModel):
    """Response model for Q&A queries (placeholder for Stage 4)."""

    answer: str = Field(..., description="Generated answer")
    sources: list[str] = Field(
        default_factory=list, description="Source documents referenced"
    )
    query: str = Field(..., description="Original query")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )
