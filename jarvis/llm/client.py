"""LLM client abstraction using LiteLLM Gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jarvis.config.settings import Settings, get_settings
from jarvis.observability.tracing import instrument_async
from jarvis.llm.litellm_provider import get_litellm_provider


@dataclass
class ToolDeclaration:
    """Unified tool declaration format for any provider."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ToolCall:
    """Normalized tool call."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Normalized LLM response."""

    content: str | None
    tool_calls: list[ToolCall]
    finish_reason: str | None
    model: str
    usage: dict[str, Any] | None = None


class LLMClient:
    """Simplified LLM client using LiteLLM Gateway only."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.provider = get_litellm_provider()

    def _get_model(self, model: str | None = None) -> str:
        """Get the model name for LiteLLM."""
        if model and model != "auto":
            return model
        return self.settings.default_model

    def _normalize_tools(self, tools: list[ToolDeclaration] | None) -> list[dict[str, Any]] | None:
        """Convert internal tool declarations to LiteLLM/OpenAI format."""
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def _normalize_response(self, raw: Any, model: str) -> LLMResponse:
        """Normalize a LiteLLM response."""
        message = raw.choices[0].message
        content = getattr(message, "content", None)
        finish_reason = getattr(raw.choices[0], "finish_reason", None)

        tool_calls: list[ToolCall] = []
        raw_tools = getattr(message, "tool_calls", None) or []
        for t in raw_tools:
            tool_calls.append(
                ToolCall(
                    id=getattr(t, "id", ""),
                    name=getattr(t, "function", {}).get("name", ""),
                    arguments=self._parse_arguments(getattr(t, "function", {}).get("arguments", "{}")),
                )
            )

        usage = getattr(raw, "usage", None)
        if usage:
            usage = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            model=model,
            usage=usage,
        )

    @staticmethod
    def _parse_arguments(raw: Any) -> dict[str, Any]:
        """Parse tool call arguments from string or dict."""
        import json

        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}

    @instrument_async("llm.chat")
    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        tools: list[ToolDeclaration] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        tool_choice: str | None = None,
    ) -> LLMResponse:
        """Send a chat request to LiteLLM Gateway."""
        
        # Use LiteLLM provider directly
        raw_response = await self.provider.chat(
            messages=messages,
            model=self._get_model(model),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            tools=self._normalize_tools(tools),
            tool_choice=tool_choice,
        )

        return self._normalize_response(raw_response, self._get_model(model))

    async def achat_stream(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        tools: list[ToolDeclaration] | None = None,
    ) -> AsyncIterator[LLMResponse]:
        """Send an async streaming chat request."""
        model = self._get_model(model)
        api_key = self._api_key_for(model)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": self.settings.llm_temperature,
        }
        if api_key:
            kwargs["api_key"] = api_key
        if tools:
            kwargs["tools"] = self._normalize_tools(tools)

        stream = await acompletion(**kwargs)
        async for chunk in stream:
            # Stream chunks are partial; we yield minimal responses
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            tool_calls = getattr(delta, "tool_calls", None) or []
            yield LLMResponse(
                content=content,
                tool_calls=[
                    ToolCall(
                        id=getattr(t, "id", ""),
                        name=getattr(t, "function", {}).get("name", ""),
                        arguments=self._parse_arguments(getattr(t, "function", {}).get("arguments", "")),
                    )
                    for t in tool_calls
                ],
                finish_reason=getattr(chunk.choices[0], "finish_reason", None),
                model=model,
            )


class LLMRouter:
    """Route requests to the best available model."""

    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()

    def route(self, task: str, preferred_model: str | None = None) -> str:
        """Select a model based on task type and availability."""
        if preferred_model:
            return preferred_model

        if "code" in task.lower() or "debug" in task.lower():
            return "anthropic/claude-3-5-sonnet-20241022"
        if "fast" in task.lower() or "quick" in task.lower():
            return "gemini/gemini-2.5-flash"
        return self.client.settings.llm_model

    def chat_with_fallback(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        tools: list[ToolDeclaration] | None = None,
    ) -> LLMResponse:
        """Try the preferred model, then fallback if it fails."""
        models = [model]
        if self.client.settings.llm_fallback_model:
            models.append(self.client.settings.llm_fallback_model)
        models.append("gemini/gemini-2.5-flash")

        for m in models:
            if not m:
                continue
            try:
                return self.client.chat(messages, model=m, tools=tools)
            except Exception as e:
                print(f"[LLM] Model {m} failed: {e}")
                continue

        raise RuntimeError("All LLM models failed")


def get_llm_client() -> LLMClient:
    """Return the default LLM client."""
    return LLMClient()


def get_llm_router() -> LLMRouter:
    """Return the default LLM router."""
    return LLMRouter()
