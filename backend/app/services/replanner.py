"""Re-planner — patches affected itinerary slots without rebuilding the whole trip.

Implementation lands in Phase 4.
"""

from app.clients.gemini import GeminiClient
from app.clients.places import PlacesClient
from app.models import Disruption, Itinerary, ItinerarySlot


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
        """Return replacement slots for the affected ids; same length, same intent."""
        raise NotImplementedError("Replanner.patch implemented in Phase 4")
