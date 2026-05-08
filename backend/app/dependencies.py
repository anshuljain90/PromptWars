"""FastAPI dependency providers — single source of truth for runtime wiring.

Tests override these via app.dependency_overrides[...] in conftest.py.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, HTTPException, status

from app.clients.firestore import FirestoreTripRepository, TripRepository
from app.clients.gemini import GeminiClient, LiveGeminiClient
from app.clients.places import FixturePlacesClient, LivePlacesClient, PlacesClient
from app.services.classifier import DisruptionClassifier
from app.services.planner import Planner
from app.services.replanner import Replanner
from app.settings import Settings, get_settings

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@lru_cache(maxsize=1)
def _build_gemini(settings: Settings) -> GeminiClient:
    return LiveGeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.external_call_timeout_seconds,
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _build_places(settings: Settings) -> PlacesClient:
    if settings.places_backend == "fixture":
        return FixturePlacesClient(fixtures_dir=_FIXTURES_DIR)
    return LivePlacesClient(
        api_key=settings.google_maps_api_key,
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _build_trip_repo(settings: Settings) -> TripRepository:
    return FirestoreTripRepository(project_id=settings.firebase_project_id)


def get_gemini(settings: Settings = Depends(get_settings)) -> GeminiClient:
    try:
        return _build_gemini(settings)
    except ValueError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


def get_places(settings: Settings = Depends(get_settings)) -> PlacesClient:
    try:
        return _build_places(settings)
    except ValueError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


def get_trip_repo(settings: Settings = Depends(get_settings)) -> TripRepository:
    return _build_trip_repo(settings)


def get_planner(
    gemini: GeminiClient = Depends(get_gemini),
    places: PlacesClient = Depends(get_places),
) -> Planner:
    return Planner(gemini=gemini, places=places)


def get_replanner(
    gemini: GeminiClient = Depends(get_gemini),
    places: PlacesClient = Depends(get_places),
) -> Replanner:
    return Replanner(gemini=gemini, places=places)


def get_classifier() -> DisruptionClassifier:
    return DisruptionClassifier()
