"""Smoke tests: liveness probe and auth gate."""

from fastapi.testclient import TestClient


def test_health_returns_ok(unauthed_client: TestClient) -> None:
    response = unauthed_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_me_requires_auth(unauthed_client: TestClient) -> None:
    response = unauthed_client.get("/me")
    assert response.status_code == 401


def test_me_returns_user_when_authed(authed_client: TestClient) -> None:
    response = authed_client.get("/me")
    assert response.status_code == 200
    body = response.json()
    assert body["uid"] == "user-1"
    assert body["email"] == "user@example.com"
