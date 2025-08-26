from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""

    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Health check message")


class ChatRequest(BaseModel):
    """Request model for chat/RAG queries."""

    query: str = Field(..., min_length=1, description="Question to ask the system")
    stream: Optional[bool] = Field(
        False, description="Whether to stream the response using Server-Sent Events"
    )
    top_k: Optional[int] = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of documents to retrieve for context",
    )


class ChatResponse(BaseModel):
    """Response model for chat/RAG queries."""

    answer: str = Field(..., description="Generated answer")
    query: str = Field(..., description="Original query")
    reformulated_query: str = Field(..., description="Query after reformulation")
    num_documents: int = Field(..., description="Number of documents used for context")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )


class RAGHealthResponse(BaseModel):
    """Response model for RAG system health check."""

    rag_service: str = Field(..., description="RAG service status")
    llm_service: str = Field(..., description="LLM service status")
    vector_store: str = Field(..., description="Vector store status")
    overall: str = Field(..., description="Overall system health")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
