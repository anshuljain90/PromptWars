"""Disruption classifier — pure rules, identifies which slots are affected.

Implementation lands in Phase 4.
"""

from dataclasses import dataclass

from app.models import Disruption, Itinerary


@dataclass(frozen=True)
class ClassificationResult:
    affected_slot_ids: list[str]
    reasoning: str


class DisruptionClassifier:
    """Deterministic rule-based classifier — no LLM call."""

    def classify(self, itinerary: Itinerary, disruption: Disruption) -> ClassificationResult:
        raise NotImplementedError("DisruptionClassifier.classify implemented in Phase 4")
