import logging
from typing import AsyncGenerator

from huggingface_hub import InferenceClient

from ai_ethics_assistant.configuration import LLMConfig
from ai_ethics_assistant.prompts import QUERY_REFORMULATION_TEMPLATE

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    pass


class LLMService:
    """Modern LLM service using HuggingFace InferenceClient"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = InferenceClient(
            provider="featherless-ai", api_key=config.api_key.get_secret_value()
        )

    async def reformulate_query(self, user_query: str) -> str:
        """Reformulate user query to improve search results"""
        reformulation_prompt = QUERY_REFORMULATION_TEMPLATE.format(
            user_query=user_query
        )

        try:
            reformulated = self._generate_text(
                reformulation_prompt, system_prompt="", max_tokens=100, temperature=0.3
            )

            reformulated = reformulated.strip()
            if not reformulated:
                logger.warning(
                    "Query reformulation returned empty result, using original query"
                )
                return user_query

            logger.info(f"Query reformulated: '{user_query}' -> '{reformulated}'")
            return reformulated

        except Exception as e:
            logger.warning(f"Query reformulation failed: {e}. Using original query.")
            return user_query

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        stream: bool | None = None,
    ) -> str | AsyncGenerator[str, None]:
        """Generate LLM response, optionally streaming"""
        should_stream = stream if stream is not None else self.config.streaming

        if should_stream:
            return self._generate_streaming(prompt, system_prompt=system_prompt)
        else:
            return self._generate_text(prompt, system_prompt=system_prompt)

    def _generate_text(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate complete text response using chat completions"""
        try:
            # Build proper message structure with mandatory system prompt
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

            completion = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                stream=False,
            )

            content = completion.choices[0].message.content
            return content.strip() if content else ""

        except Exception as e:
            raise LLMServiceError(f"Generation failed: {e}")

    async def _generate_streaming(
        self, prompt: str, system_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Generate streaming text response using chat completions"""
        try:
            # Build proper message structure with mandatory system prompt
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

            stream = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise LLMServiceError(f"Streaming failed: {e}")

    async def test_connection(self) -> bool:
        """Test connection to HuggingFace API"""
        try:
            self._generate_text(
                "Hello", system_prompt="", max_tokens=1, temperature=0.1
            )
            logger.info("Successfully connected to HuggingFace Inference API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to HuggingFace API: {e}")
            return False
