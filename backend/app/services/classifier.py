"""Disruption classifier — pure rule-based detection of affected itinerary slots.

No LLM in the hot path: closures match by place_id, weather affects outdoor
slots inside the time window, and traffic affects the route segment between
two specific slots. Deterministic, ~10ms, free, and trivially testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import (
    ClosureDisruption,
    Disruption,
    DisruptionType,
    Itinerary,
    SlotPeriod,
    TrafficDisruption,
    WeatherDisruption,
)


@dataclass(frozen=True)
class ClassificationResult:
    """The outcome of classifying a single disruption against an itinerary."""

    affected_slot_ids: list[str]
    reasoning: str


class DisruptionClassifier:
    """Deterministic rule-based classifier — no LLM call.

    Returns a `ClassificationResult` with the slots that need replanning and a
    short reasoning string used in the change-log.
    """

    def classify(self, itinerary: Itinerary, disruption: Disruption) -> ClassificationResult:
        match disruption.type:
            case DisruptionType.CLOSURE:
                return self._closure(itinerary, disruption)
            case DisruptionType.WEATHER:
                return self._weather(itinerary, disruption)
            case DisruptionType.TRAFFIC:
                return self._traffic(itinerary, disruption)
        # mypy/exhaustive-check guard
        raise ValueError(f"Unknown disruption type: {disruption.type}")

    @staticmethod
    def _closure(itinerary: Itinerary, disruption: ClosureDisruption) -> ClassificationResult:
        affected = [
            slot.slot_id
            for day in itinerary.days
            for slot in day.slots
            if slot.place_id == disruption.place_id
        ]
        if not affected:
            return ClassificationResult([], "Closed venue is not on the itinerary.")
        return ClassificationResult(
            affected,
            f"Venue {disruption.place_id} is closed: {disruption.reason}.",
        )

    @staticmethod
    def _weather(itinerary: Itinerary, disruption: WeatherDisruption) -> ClassificationResult:
        try:
            target_period = SlotPeriod(disruption.period)
        except ValueError:
            return ClassificationResult([], f"Unknown weather period: {disruption.period!r}.")

        affected: list[str] = []
        for day in itinerary.days:
            if day.day_index != disruption.day_index:
                continue
            for slot in day.slots:
                if slot.period != target_period:
                    continue
                tags_lower = {t.lower() for t in slot.tags}
                if "outdoor" in tags_lower:
                    affected.append(slot.slot_id)

        if not affected:
            return ClassificationResult(
                [],
                f"No outdoor activities scheduled during {disruption.condition} on day "
                f"{disruption.day_index} {disruption.period}.",
            )
        return ClassificationResult(
            affected,
            f"{disruption.condition.capitalize()} forecast for day {disruption.day_index} "
            f"{disruption.period} affects outdoor plans.",
        )

    @staticmethod
    def _traffic(itinerary: Itinerary, disruption: TrafficDisruption) -> ClassificationResult:
        # The disruption names two slot ids — we replace the destination slot
        # (the one being arrived at), since rerouting/alternative-place fits
        # there more naturally than the origin.
        slot_ids = {slot.slot_id for day in itinerary.days for slot in day.slots}
        target = disruption.to_slot_id
        if target not in slot_ids:
            return ClassificationResult([], "Traffic disruption refers to an unknown slot.")
        return ClassificationResult(
            [target],
            f"Route from {disruption.from_slot_id} → {target} blocked: {disruption.reason}.",
        )
