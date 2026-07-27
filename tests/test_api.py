from fastapi.testclient import TestClient

from control_plane_api.main import app

client = TestClient(app)


def test_health_reports_fixture_mode() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "fixture"}


def test_capabilities_are_explicit_about_missing_dependencies() -> None:
    response = client.get("/api/v1/meta/capabilities")

    assert response.status_code == 200
    assert response.json()["a2a_registration"] is True
    assert response.json()["model_provider"] == "not_configured"
    assert response.json()["persistence"] == "not_configured"

