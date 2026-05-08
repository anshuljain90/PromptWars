"""Re-planner — patches affected itinerary slots without rebuilding the whole trip.

Takes the list of affected slots (from DisruptionClassifier) plus a pool of
alternative places (from PlacesClient) and returns replacement slots only.
Preserves slot_id, period, and intent — Gemini fills in a fresh place + rationale.
"""

from __future__ import annotations

import json
import logging

from pydantic import BaseModel, Field

from app.clients.gemini import GeminiClient
from app.clients.places import PlaceCandidate, PlacesClient
from app.models import Disruption, Itinerary, ItinerarySlot

logger = logging.getLogger(__name__)


class PatchedSlots(BaseModel):
    """Gemini's structured output: only the replacement slots."""

    slots: list[ItinerarySlot] = Field(min_length=1, max_length=10)


_SYSTEM_PROMPT = """You are a travel planner that patches a single trip slot
when a disruption hits.

You will be given the current itinerary, the slots that need replacement, the
disruption details, and a pool of alternative candidate places. Your job:

1. For each affected slot, return ONE replacement slot with the SAME slot_id,
   the SAME period (morning/afternoon/evening), and matching intent
   (cultural / outdoor / food / nightlife etc.) inferred from the original slot's tags.
2. Use ONLY places from the alternative candidate list. Do not invent places.
3. The replacement must NOT trigger the same disruption — e.g., for a weather
   disruption, the replacement must NOT have the "outdoor" tag.
4. The `rationale` MUST mention what was disrupted and why this alternative is suitable
   (e.g., "Indoor swap for the rainy afternoon, matching your history interest").
5. Return ONLY the replacement slots, in the same order as the input affected_slot_ids.
"""


class Replanner:
    """Replaces one or more slots, preserving the rest of the itinerary."""

    def __init__(self, gemini: GeminiClient, places: PlacesClient) -> None:
        self._gemini = gemini
        self._places = places

    async def patch(
        self,
        itinerary: Itinerary,
        affected_slot_ids: list[str],
        disruption: Disruption,
    ) -> list[ItinerarySlot]:
        if not affected_slot_ids:
            return []

        affected_slots = _collect_slots(itinerary, affected_slot_ids)
        if len(affected_slots) != len(affected_slot_ids):
            raise ReplannerError(
                f"Some affected slot ids not found in itinerary: {affected_slot_ids!r}"
            )

        destination = _infer_destination(affected_slots)
        used_place_ids = {s.place_id for d in itinerary.days for s in d.slots}
        candidates = await self._gather_alternatives(
            destination=destination,
            affected_slots=affected_slots,
            exclude_place_ids=used_place_ids,
        )
        if not candidates:
            raise ReplannerError(f"No alternative places available for destination {destination!r}")

        user_prompt = _build_user_prompt(
            itinerary=itinerary,
            affected_slots=affected_slots,
            disruption=disruption,
            candidates=candidates,
        )

        try:
            patched = await self._gemini.generate_structured(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=PatchedSlots,
            )
        except Exception as exc:
            raise ReplannerError(f"Replanner Gemini call failed: {exc}") from exc

        if len(patched.slots) != len(affected_slots):
            raise ReplannerError(
                f"Replanner returned {len(patched.slots)} slots, " f"expected {len(affected_slots)}"
            )
        return patched.slots

    async def _gather_alternatives(
        self,
        destination: str,
        affected_slots: list[ItinerarySlot],
        exclude_place_ids: set[str],
    ) -> list[PlaceCandidate]:
        interest_tags = sorted({tag for slot in affected_slots for tag in slot.tags if tag})
        pool = await self._places.search(
            destination=destination,
            interests=interest_tags,
            limit=40,
        )
        return [p for p in pool if p.place_id not in exclude_place_ids]


class ReplannerError(RuntimeError):
    """Raised when re-planning cannot complete."""


def _collect_slots(itinerary: Itinerary, slot_ids: list[str]) -> list[ItinerarySlot]:
    by_id = {s.slot_id: s for d in itinerary.days for s in d.slots}
    return [by_id[sid] for sid in slot_ids if sid in by_id]


def _infer_destination(slots: list[ItinerarySlot]) -> str:
    """Use the address city heuristic — last comma-separated token before postcode."""
    for slot in slots:
        parts = [p.strip() for p in slot.address.split(",") if p.strip()]
        if len(parts) >= 2:
            return parts[-2]
    return ""


def _build_user_prompt(
    itinerary: Itinerary,
    affected_slots: list[ItinerarySlot],
    disruption: Disruption,
    candidates: list[PlaceCandidate],
) -> str:
    payload = {
        "disruption": disruption.model_dump(mode="json"),
        "current_itinerary_summary": itinerary.summary,
        "affected_slots": [
            {
                "slot_id": s.slot_id,
                "period": s.period.value,
                "place_name": s.place_name,
                "tags": s.tags,
                "duration_min": s.duration_min,
                "original_rationale": s.rationale,
            }
            for s in affected_slots
        ],
        "alternative_candidates": [
            {
                "place_id": p.place_id,
                "name": p.name,
                "type": p.place_type,
                "lat": p.lat,
                "lng": p.lng,
                "tags": p.tags,
                "rating": p.rating,
                "price_level": p.price_level,
            }
            for p in candidates
        ],
    }
    return (
        "Replace each affected slot with a suitable alternative. Preserve the "
        "slot_id and period exactly. Each rationale must reference the disruption.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
