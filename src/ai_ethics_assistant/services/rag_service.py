import logging
from typing import Any, AsyncGenerator, Dict, List

from ai_ethics_assistant.pipeline.embedder import HuggingFaceEmbedder
from ai_ethics_assistant.prompts import RAG_PROMPT_TEMPLATE, SYSTEM_PROMPT
from ai_ethics_assistant.services.llm_service import LLMService
from ai_ethics_assistant.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class RAGService:
    """Simplified RAG service that handles retrieval and generation"""

    def __init__(
        self,
        llm_service: LLMService,
        embedder: HuggingFaceEmbedder,
        vector_store_service: VectorStoreService,
    ):
        self.llm_service = llm_service
        self.embedder = embedder
        self.vector_store_service = vector_store_service

    async def ask(
        self, user_query: str, stream: bool = False, top_k: int = 5
    ) -> str | AsyncGenerator[str, None]:
        """Process a user query through the complete RAG pipeline

        Args:
            user_query: The user's question
            stream: Whether to stream the response
            top_k: Number of documents to retrieve for context

        Returns:
            Complete response string or async generator of response chunks
        """
        try:
            # Get context for the query
            context_info = await self.get_context_for_query(user_query, top_k)
            context = context_info["context"]

            # Build prompt with context
            prompt = self._build_prompt(user_query, context)

            # Generate response with separate system prompt
            return await self.llm_service.generate_response(
                prompt, stream=stream, system_prompt=SYSTEM_PROMPT
            )

        except Exception as e:
            logger.error(f"RAG pipeline failed for query '{user_query}': {e}")
            return "I encountered an error processing your question. Please try rephrasing or ask a different question."

    async def get_context_for_query(
        self, user_query: str, top_k: int = 5
    ) -> Dict[str, Any]:
        """Get context for a query by searching vector store

        Args:
            user_query: The user's question
            top_k: Number of documents to retrieve

        Returns:
            Query processing result with context and metadata
        """
        # Reformulate query for better search
        reformulated_query = await self.llm_service.reformulate_query(user_query)

        # Generate embedding for reformulated query
        query_embedding = await self.embedder.embed_text(reformulated_query)

        # Search for similar documents
        similar_docs = await self.vector_store_service.search_similar(
            query_embedding=query_embedding, limit=top_k
        )

        # Format context from retrieved documents
        context = self._format_context(similar_docs)

        return {
            "original_query": user_query,
            "reformulated_query": reformulated_query,
            "retrieved_documents": similar_docs,
            "context": context,
            "num_documents": len(similar_docs),
        }

    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context string"""
        if not documents:
            return "No relevant documents found."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            payload = doc.get("payload", {})
            text = payload.get("text", "")
            filename = payload.get("filename", "Unknown")
            context_parts.append(f"Document {i} (from {filename}):\n{text}\n")

        return "\n---\n".join(context_parts)

    def _build_prompt(self, user_query: str, context: str) -> str:
        """Build the user content for the LLM (context + query only)"""
        return RAG_PROMPT_TEMPLATE.format(context=context, user_query=user_query)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of RAG components"""
        health_status = {
            "rag_service": "healthy",
            "llm_service": "unknown",
            "vector_store": "unknown",
            "overall": "unknown",
        }

        try:
            # Test LLM service
            llm_healthy = await self.llm_service.test_connection()
            health_status["llm_service"] = "healthy" if llm_healthy else "unhealthy"

            # Test vector store
            vector_healthy = await self.vector_store_service.test_connection()
            health_status["vector_store"] = "healthy" if vector_healthy else "unhealthy"

            # Overall health
            if llm_healthy and vector_healthy:
                health_status["overall"] = "healthy"
            elif llm_healthy or vector_healthy:
                health_status["overall"] = "degraded"
            else:
                health_status["overall"] = "unhealthy"

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["overall"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status
