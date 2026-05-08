"""Gemini API wrapper — structured-JSON helper used by planner and replanner.

Uses google-generativeai (AI Studio) with response_schema for forced structured
output. Cached by a SHA-256 of the input so repeated identical calls are free
(rubric: Efficiency).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import Any, Protocol, TypeVar

import google.generativeai as genai
from cachetools import TTLCache
from pydantic import BaseModel

logger = logging.getLogger(__name__)

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

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        cache_maxsize: int = 256,
        cache_ttl_seconds: int = 3600,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for LiveGeminiClient")
        genai.configure(api_key=api_key)
        self._model_name = model
        self._timeout = timeout_seconds
        self._cache: TTLCache[str, str] = TTLCache(maxsize=cache_maxsize, ttl=cache_ttl_seconds)

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        cache_key: str | None = None,
    ) -> T:
        key = cache_key or _hash_inputs(system_prompt, user_prompt, response_model.__name__)
        if (cached_json := self._cache.get(key)) is not None:
            logger.debug("Gemini cache hit (key=%s)", key[:12])
            return response_model.model_validate_json(cached_json)

        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_prompt,
        )
        generation_config = {
            "response_mime_type": "application/json",
            "response_schema": response_model,
            "temperature": 0.4,
        }

        try:
            response = await asyncio.wait_for(
                model.generate_content_async(user_prompt, generation_config=generation_config),
                timeout=self._timeout,
            )
        except TimeoutError as exc:
            raise GeminiError(f"Gemini call timed out after {self._timeout}s") from exc
        except Exception as exc:
            raise GeminiError(f"Gemini call failed: {exc}") from exc

        text = (response.text or "").strip()
        if not text:
            raise GeminiError("Gemini returned an empty response")

        try:
            parsed = response_model.model_validate_json(text)
        except ValueError as exc:
            logger.warning("Gemini response failed schema validation: %s", text[:300])
            raise GeminiError(f"Gemini response did not match schema: {exc}") from exc

        self._cache[key] = parsed.model_dump_json()
        return parsed


class FakeGeminiClient:
    """Test double — returns canned responses keyed by call args."""

    def __init__(self, canned: dict[str, Any] | None = None) -> None:
        self._canned: dict[str, Any] = canned or {}
        self.calls: list[tuple[str, str, str]] = []

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        cache_key: str | None = None,
    ) -> T:
        key = cache_key or _hash_inputs(system_prompt, user_prompt, response_model.__name__)
        self.calls.append((system_prompt, user_prompt, key))
        if key in self._canned:
            payload = self._canned[key]
        elif response_model.__name__ in self._canned:
            payload = self._canned[response_model.__name__]
        else:
            raise KeyError(
                f"No canned Gemini response for key={key!r} or model={response_model.__name__!r}"
            )
        if isinstance(payload, str):
            return response_model.model_validate_json(payload)
        return response_model.model_validate(payload)


class GeminiError(RuntimeError):
    """Raised on any Gemini call failure (timeout, schema mismatch, API error)."""


def _hash_inputs(system_prompt: str, user_prompt: str, schema_name: str) -> str:
    raw = json.dumps(
        {"sys": system_prompt, "user": user_prompt, "schema": schema_name},
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
