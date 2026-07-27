import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from control_plane_api.app import create_app


@pytest.fixture
def client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with TestClient(create_app(engine)) as test_client:
        yield test_client


def test_health_reports_fixture_mode(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "fixture"}


def test_dashboard_uses_persisted_registry_data(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.json()["total_assets"] == 6
    assert response.json()["awaiting_review"] == 2
    assert response.json()["model_provider"] == "not_configured"


def test_asset_inventory_filters_by_type(client: TestClient) -> None:
    response = client.get("/api/v1/assets", params={"asset_type": "agent"})

    assert response.status_code == 200
    assert [asset["asset_id"] for asset in response.json()] == ["agent.policy-risk"]


def test_register_and_fetch_asset_version(client: TestClient) -> None:
    asset = {
        "asset_id": "prompt.entitlement-recommendation",
        "version": "3.1.0",
        "asset_type": "prompt",
        "display_name": "Entitlement Recommendation",
        "owner": "IAM Platform",
        "intended_use": "Recommend least-privilege entitlements.",
    }
    created = client.post("/api/v1/assets", json=asset)
    fetched = client.get(
        "/api/v1/assets/prompt.entitlement-recommendation/versions/3.1.0"
    )

    assert created.status_code == 201
    assert fetched.status_code == 200
    assert fetched.json()["display_name"] == asset["display_name"]


def test_duplicate_asset_version_is_conflict(client: TestClient) -> None:
    existing = {
        "asset_id": "agent.policy-risk",
        "version": "0.4.0",
        "asset_type": "agent",
        "display_name": "Policy and Risk Agent",
        "owner": "Ravi Kumar",
        "intended_use": "Evaluate approved policies.",
    }

    response = client.post("/api/v1/assets", json=existing)

    assert response.status_code == 409
