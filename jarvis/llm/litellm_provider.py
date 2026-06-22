"""LiteLLM Provider - Single point of contact for all LLM operations."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import litellm
from litellm import acompletion, completion

from jarvis.config.settings import Settings, get_settings
from jarvis.observability.logger import get_logger
from jarvis.observability.tracing import instrument_async

logger = get_logger(__name__)


@dataclass
class LiteLLMStats:
    """Statistics for LiteLLM operations."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    last_error: str | None = None
    last_success_time: float | None = None
    
    @property
    def success_rate(self) -> float:
        """Success rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def avg_response_time(self) -> float:
        """Average response time in seconds."""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests


class LiteLLMProvider:
    """Single LiteLLM provider for all LLM operations.
    
    This provider delegates all routing, fallback, and retry logic
    to the LiteLLM gateway at http://192.168.1.198:4000
    """
    
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.stats = LiteLLMStats()
        self._configure_litellm()
    
    def _configure_litellm(self) -> None:
        """Configure LiteLLM with gateway settings."""
        # Set LiteLLM to use our gateway
        litellm.api_base = self.settings.litellm_base_url
        
        # Use empty API key or None for gateway without auth
        if self.settings.litellm_api_key == "dummy":
            litellm.api_key = None
        else:
            litellm.api_key = self.settings.litellm_api_key
        
        # Configure logging
        litellm.set_verbose = self.settings.debug
        
        logger.info(
            "litellm_configured",
            base_url=self.settings.litellm_base_url,
            model=self.settings.default_model
        )
    
    def _get_model(self, model: str | None = None) -> str:
        """Get the model name for LiteLLM with proper provider prefix."""
        if model and model != "auto":
            # Add provider prefix if not present
            if "/" not in model:
                # Map common models to their providers
                model_mapping = {
                    "qwen-fast": "openai/qwen-fast",
                    "deepseek-chat": "deepseek/deepseek-chat", 
                    "nemotron": "nvidia/nemotron",
                    "llama-3.1-8b": "ollama/llama-3.1-8b",
                    "gemini-flash": "gemini/gemini-flash",
                }
                return model_mapping.get(model, f"openai/{model}")
            return model
        
        # Use default model from settings with provider prefix
        default_model = self.settings.default_model
        if "/" not in default_model:
            return f"openai/{default_model}"
        return default_model
    
    def _update_stats_success(self, response_time: float) -> None:
        """Update statistics after successful request."""
        self.stats.total_requests += 1
        self.stats.successful_requests += 1
        self.stats.total_response_time += response_time
        self.stats.last_success_time = time.time()
    
    def _update_stats_error(self, error: str) -> None:
        """Update statistics after failed request."""
        self.stats.total_requests += 1
        self.stats.failed_requests += 1
        self.stats.last_error = error
    
    def get_stats(self) -> dict[str, Any]:
        """Get current provider statistics."""
        return {
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "success_rate": self.stats.success_rate,
            "avg_response_time": self.stats.avg_response_time,
            "last_error": self.stats.last_error,
            "last_success_time": self.stats.last_success_time,
            "base_url": self.settings.litellm_base_url,
            "default_model": self.settings.default_model,
        }
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.stats = LiteLLMStats()
        logger.info("litellm_stats_reset")
    
    @instrument_async("llm.litellm.chat")
    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Send a chat request to LiteLLM gateway.
        
        Args:
            messages: Chat messages in OpenAI format
            model: Model name (uses default if not specified)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters for LiteLLM
            
        Returns:
            Raw response from LiteLLM
        """
        start_time = time.time()
        model_name = self._get_model(model)
        
        try:
            logger.info("litellm_request_start", model=model_name)
            
            # Prepare request parameters
            request_params = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature or self.settings.llm_temperature,
                "stream": stream,
            }
            
            if max_tokens or self.settings.llm_max_tokens:
                request_params["max_tokens"] = max_tokens or self.settings.llm_max_tokens
            
            # Add any additional kwargs
            request_params.update(kwargs)
            
            # Make request to LiteLLM gateway
            response = await acompletion(**request_params)
            
            response_time = time.time() - start_time
            self._update_stats_success(response_time)
            
            logger.info(
                "litellm_request_success",
                model=model_name,
                response_time=response_time,
                usage=getattr(response, 'usage', None)
            )
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            self._update_stats_error(error_msg)
            
            logger.error(
                "litellm_request_error",
                model=model_name,
                error=error_msg,
                response_time=response_time
            )
            
            raise Exception(f"LiteLLM request failed: {error_msg}") from e
    
    def chat_sync(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Send a synchronous chat request to LiteLLM gateway."""
        start_time = time.time()
        model_name = self._get_model(model)
        
        try:
            logger.info("litellm_sync_request_start", model=model_name)
            
            # Prepare request parameters
            request_params = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature or self.settings.llm_temperature,
            }
            
            if max_tokens or self.settings.llm_max_tokens:
                request_params["max_tokens"] = max_tokens or self.settings.llm_max_tokens
            
            # Add any additional kwargs
            request_params.update(kwargs)
            
            # Make synchronous request to LiteLLM gateway
            response = completion(**request_params)
            
            response_time = time.time() - start_time
            self._update_stats_success(response_time)
            
            logger.info(
                "litellm_sync_request_success",
                model=model_name,
                response_time=response_time
            )
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            self._update_stats_error(error_msg)
            
            logger.error(
                "litellm_sync_request_error",
                model=model_name,
                error=error_msg,
                response_time=response_time
            )
            
            raise Exception(f"LiteLLM sync request failed: {error_msg}") from e
    
    async def test_connection(self, model: str | None = None) -> dict[str, Any]:
        """Test connection to LiteLLM gateway.
        
        Args:
            model: Model to test with (uses default if not specified)
            
        Returns:
            Test results with timing and model info
        """
        test_model = self._get_model(model)
        
        try:
            start_time = time.time()
            
            # Simple test message
            response = await self.chat(
                messages=[{"role": "user", "content": "test"}],
                model=test_model,
                max_tokens=10
            )
            
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "model": test_model,
                "response_time": response_time,
                "response": response.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "usage": response.get("usage", {}),
            }
            
        except Exception as e:
            return {
                "success": False,
                "model": test_model,
                "error": str(e),
                "response_time": time.time() - start_time,
            }
    
    async def list_available_models(self) -> list[str]:
        """List available models from LiteLLM gateway.
        
        Note: This depends on the LiteLLM gateway configuration.
        The gateway should expose available models.
        """
        try:
            # Try to get models from LiteLLM
            # This is a simplified approach - actual implementation depends on gateway
            known_models = [
                "qwen-fast",
                "deepseek-chat", 
                "nemotron",
                "llama-3.1-8b",
                "gemini-flash",
            ]
            
            logger.info("litellm_models_listed", count=len(known_models))
            return known_models
            
        except Exception as e:
            logger.error("litellm_models_error", error=str(e))
            return []


# Global provider instance
_provider: LiteLLMProvider | None = None


def get_litellm_provider() -> LiteLLMProvider:
    """Get the global LiteLLM provider instance."""
    global _provider
    if _provider is None:
        _provider = LiteLLMProvider()
    return _provider


def reset_litellm_provider() -> None:
    """Reset the global LiteLLM provider instance."""
    global _provider
    _provider = None
