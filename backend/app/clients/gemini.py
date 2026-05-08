"""Gemini API wrapper — structured-JSON helper used by planner and replanner.

Implementation lands in Phase 2.
"""

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class GeminiClient(Protocol):
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        cache_key: str | None = None,
    ) -> T: ...


class LiveGeminiClient:
    """Real Gemini client backed by google-generativeai."""

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 30.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        cache_key: str | None = None,
    ) -> T:
        raise NotImplementedError("LiveGeminiClient.generate_structured implemented in Phase 2")


class FakeGeminiClient:
    """Test double — returns canned responses keyed by call args."""

    def __init__(self, canned: dict[str, Any] | None = None) -> None:
        self._canned: dict[str, Any] = canned or {}

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        cache_key: str | None = None,
    ) -> T:
        key = cache_key or user_prompt
        if key not in self._canned:
            raise KeyError(f"No canned Gemini response for key: {key!r}")
        payload = self._canned[key]
        return response_model.model_validate(payload)
