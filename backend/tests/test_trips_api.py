"""Trip CRUD route tests — covers happy paths, validation, and authorization."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.clients.firestore import InMemoryTripRepository
from app.models import Trip, TripInput


def _trip_input_payload(payload: TripInput) -> dict:
    return payload.model_dump(mode="json")


def test_create_trip_returns_201_with_planner_itinerary(
    authed_client: TestClient,
    sample_trip_input: TripInput,
) -> None:
    response = authed_client.post("/trips", json=_trip_input_payload(sample_trip_input))
    assert response.status_code == 201
    body = response.json()
    assert body["owner_uid"] == "user-1"
    assert body["constraints"]["destination"] == "Jaipur"
    assert len(body["itinerary"]["days"]) >= 1
    assert body["change_log"] == []


def test_create_trip_persists_to_repository(
    authed_client: TestClient,
    sample_trip_input: TripInput,
    trip_repository: InMemoryTripRepository,
) -> None:
    response = authed_client.post("/trips", json=_trip_input_payload(sample_trip_input))
    trip_id = response.json()["trip_id"]
    assert ("user-1", trip_id) in trip_repository._store


def test_create_trip_rejects_inverted_dates(
    authed_client: TestClient,
    sample_trip_input: TripInput,
) -> None:
    bad_payload = _trip_input_payload(sample_trip_input)
    bad_payload["constraints"]["arrival_date"] = "2026-06-10"
    bad_payload["constraints"]["departure_date"] = "2026-06-05"
    response = authed_client.post("/trips", json=bad_payload)
    assert response.status_code == 400


def test_list_trips_returns_user_trips_only(
    authed_client: TestClient,
    sample_trip_input: TripInput,
    trip_repository: InMemoryTripRepository,
    sample_trip: Trip,
) -> None:
    other_trip = sample_trip.model_copy(
        update={"trip_id": "other-trip-id", "owner_uid": "other-user"}
    )
    trip_repository._store[(other_trip.owner_uid, other_trip.trip_id)] = other_trip

    authed_client.post("/trips", json=_trip_input_payload(sample_trip_input))
    response = authed_client.get("/trips")
    assert response.status_code == 200
    summaries = response.json()
    assert all(s["trip_id"] != "other-trip-id" for s in summaries)
    assert len(summaries) == 1


def test_get_trip_returns_owned_trip(
    authed_client: TestClient,
    sample_trip_input: TripInput,
) -> None:
    created = authed_client.post("/trips", json=_trip_input_payload(sample_trip_input))
    trip_id = created.json()["trip_id"]
    response = authed_client.get(f"/trips/{trip_id}")
    assert response.status_code == 200
    assert response.json()["trip_id"] == trip_id


def test_get_trip_returns_404_for_unknown_id(authed_client: TestClient) -> None:
    response = authed_client.get("/trips/does-not-exist")
    assert response.status_code == 404


def test_get_trip_denies_other_users_trip(
    authed_client: TestClient,
    trip_repository: InMemoryTripRepository,
    sample_trip: Trip,
) -> None:
    """The fake user is user-1; we plant a trip owned by other-user.

    The route MUST scope by request.state.user.uid and return 404 — never leak
    another user's trip id existence.
    """
    other = sample_trip.model_copy(update={"trip_id": "secret", "owner_uid": "other-user"})
    trip_repository._store[(other.owner_uid, other.trip_id)] = other

    response = authed_client.get("/trips/secret")
    assert response.status_code == 404


def test_delete_trip_removes_owned_trip(
    authed_client: TestClient,
    sample_trip_input: TripInput,
) -> None:
    created = authed_client.post("/trips", json=_trip_input_payload(sample_trip_input))
    trip_id = created.json()["trip_id"]
    response = authed_client.delete(f"/trips/{trip_id}")
    assert response.status_code == 204
    follow_up = authed_client.get(f"/trips/{trip_id}")
    assert follow_up.status_code == 404


def test_delete_trip_returns_404_for_unknown(authed_client: TestClient) -> None:
    response = authed_client.delete("/trips/nope")
    assert response.status_code == 404


def test_disruption_closure_replaces_affected_slot_and_logs_change(
    authed_client: TestClient,
    sample_trip_input: TripInput,
) -> None:
    """End-to-end: closure → classifier → replanner → patched itinerary + change-log entry."""
    created = authed_client.post("/trips", json=_trip_input_payload(sample_trip_input))
    trip_id = created.json()["trip_id"]
    # The stub planner returns sample_itinerary which has 'pid-d1-m' (Amber Fort).
    response = authed_client.post(
        f"/trips/{trip_id}/disruptions",
        json={"type": "closure", "place_id": "pid-d1-m", "reason": "maintenance"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["change_log"]) == 1
    entry = body["change_log"][0]
    assert entry["disruption_type"] == "closure"
    assert "d1-m" in entry["affected_slot_ids"]
    assert entry["replaced_with"], "expected at least one replacement place_id"
    # The first slot of day 1 should have a new place_id (the alt suffix from stub).
    day1_morning = body["itinerary"]["days"][0]["slots"][0]
    assert day1_morning["slot_id"] == "d1-m"
    assert day1_morning["place_id"].endswith("-alt")


def test_disruption_with_no_affected_slot_records_log_only(
    authed_client: TestClient,
    sample_trip_input: TripInput,
) -> None:
    """Closure of a place not on the itinerary leaves the plan unchanged but logs."""
    created = authed_client.post("/trips", json=_trip_input_payload(sample_trip_input))
    trip_id = created.json()["trip_id"]
    response = authed_client.post(
        f"/trips/{trip_id}/disruptions",
        json={"type": "closure", "place_id": "no-such-place"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["change_log"]) == 1
    assert body["change_log"][0]["affected_slot_ids"] == []
    # Itinerary unchanged.
    assert body["itinerary"]["days"][0]["slots"][0]["slot_id"] == "d1-m"


def test_disruption_returns_404_for_unknown_trip(authed_client: TestClient) -> None:
    response = authed_client.post(
        "/trips/nope/disruptions",
        json={"type": "closure", "place_id": "x"},
    )
    assert response.status_code == 404


def test_disruption_rejects_invalid_payload(
    authed_client: TestClient,
    sample_trip_input: TripInput,
) -> None:
    created = authed_client.post("/trips", json=_trip_input_payload(sample_trip_input))
    trip_id = created.json()["trip_id"]
    response = authed_client.post(
        f"/trips/{trip_id}/disruptions",
        json={"type": "closure"},  # missing place_id
    )
    assert response.status_code == 400


def test_unauthed_request_to_trips_returns_401(unauthed_client: TestClient) -> None:
    response = unauthed_client.get("/trips")
    assert response.status_code == 401
