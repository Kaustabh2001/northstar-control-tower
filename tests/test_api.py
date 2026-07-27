import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from control_plane_api.app import create_app

VIEWER = {"Authorization": "Bearer fixture-viewer"}
OPERATOR = {"Authorization": "Bearer fixture-operator"}
REVIEWER = {"Authorization": "Bearer fixture-reviewer"}


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
    response = client.get("/api/v1/dashboard", headers=VIEWER)

    assert response.status_code == 200
    assert response.json()["total_assets"] == 6
    assert response.json()["awaiting_review"] == 2
    assert response.json()["model_provider"] == "not_configured"


def test_asset_inventory_filters_by_type(client: TestClient) -> None:
    response = client.get(
        "/api/v1/assets",
        params={"asset_type": "agent"},
        headers=VIEWER,
    )

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
    created = client.post("/api/v1/assets", json=asset, headers=OPERATOR)
    fetched = client.get(
        "/api/v1/assets/prompt.entitlement-recommendation/versions/3.1.0",
        headers=VIEWER,
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

    response = client.post("/api/v1/assets", json=existing, headers=OPERATOR)

    assert response.status_code == 409


def test_registry_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/assets")

    assert response.status_code == 401


def test_viewer_cannot_register_asset(client: TestClient) -> None:
    response = client.post(
        "/api/v1/assets",
        headers=VIEWER,
        json={
            "asset_id": "agent.denied",
            "version": "0.1.0",
            "asset_type": "agent",
            "display_name": "Denied",
            "owner": "Test",
            "intended_use": "Verify authorization.",
        },
    )

    assert response.status_code == 403


def test_agent_detail_exposes_a2a_and_governance_metadata(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/agents/agent.policy-risk/versions/0.4.0",
        headers=VIEWER,
    )

    assert response.status_code == 200
    detail = response.json()
    assert detail["agent_card"]["protocol_version"] == "0.3.0"
    assert len(detail["agent_card"]["skills"]) == 2
    assert len(detail["dependencies"]) == 3
    assert detail["runtime_connected"] is False


def test_operator_submits_agent_for_review_and_audit_is_recorded(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/agents/agent.policy-risk/versions/0.4.0/governance-state",
        headers=OPERATOR,
        json={
            "target_state": "steward_review",
            "note": "Evidence package is ready.",
        },
    )

    assert response.status_code == 200
    detail = response.json()
    assert detail["asset"]["governance_state"] == "steward_review"
    assert detail["audit_events"][0]["actor_email"] == "operator@northstar.local"


def test_operator_cannot_approve_agent_to_shadow(client: TestClient) -> None:
    response = client.post(
        "/api/v1/agents/agent.policy-risk/versions/0.4.0/governance-state",
        headers=OPERATOR,
        json={"target_state": "shadow", "note": "Attempted approval."},
    )

    assert response.status_code == 403


def test_reviewer_can_approve_agent_to_shadow(client: TestClient) -> None:
    response = client.post(
        "/api/v1/agents/agent.policy-risk/versions/0.4.0/governance-state",
        headers=REVIEWER,
        json={"target_state": "shadow", "note": "Controls verified."},
    )

    assert response.status_code == 200
    assert response.json()["asset"]["governance_state"] == "shadow"
