import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ai_ethics_assistant.dependencies import get_rag_service
from ai_ethics_assistant.server.models import (
    ChatRequest,
    ChatResponse,
)
from ai_ethics_assistant.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")




@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    request: ChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> ChatResponse | StreamingResponse:
    """
    Ask a question to the AI Ethics Assistant using RAG.

    Supports both regular and streaming responses via Server-Sent Events.
    """
    try:
        if request.stream:
            # Return Server-Sent Events streaming response
            async def stream_response():
                # First get the query context for metadata
                context_info = await rag_service.get_context_for_query(
                    request.query, request.top_k or 5
                )

                # Stream the response
                response_generator = await rag_service.ask(
                    user_query=request.query, stream=True, top_k=request.top_k or 5
                )

                # Send initial metadata as SSE
                metadata = {
                    "type": "metadata",
                    "query": request.query,
                    "reformulated_query": context_info.get(
                        "reformulated_query", request.query
                    ),
                    "num_documents": context_info.get("num_documents", 0),
                }
                yield f"data: {json.dumps(metadata)}\n\n"

                # Stream response chunks (check if it's actually a generator)
                if not isinstance(response_generator, str):
                    async for chunk in response_generator:
                        if chunk:
                            chunk_data = {"type": "chunk", "content": chunk}
                            yield f"data: {json.dumps(chunk_data)}\n\n"

                # Send end marker
                yield f"data: {json.dumps({'type': 'end'})}\n\n"

            return StreamingResponse(
                stream_response(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        else:
            # Regular non-streaming response
            # Get context info for response metadata
            context_info = await rag_service.get_context_for_query(
                request.query, request.top_k or 5
            )

            # Generate response
            answer = await rag_service.ask(
                user_query=request.query, stream=False, top_k=request.top_k or 5
            )

            if not isinstance(answer, str):
                raise HTTPException(
                    status_code=500, detail="Unexpected response format"
                )

            return ChatResponse(
                answer=answer,
                query=request.query,
                reformulated_query=context_info.get(
                    "reformulated_query", request.query
                ),
                num_documents=context_info.get("num_documents", 0),
            )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process query: {str(e)}"
        )




