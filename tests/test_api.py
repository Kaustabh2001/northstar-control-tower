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


def test_dataset_detail_exposes_schema_quality_and_lineage(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/assets/dataset.access-tickets/versions/2026.7.0/detail",
        headers=VIEWER,
    )

    assert response.status_code == 200
    detail = response.json()
    assert detail["detail_kind"] == "dataset"
    assert detail["metadata"]["quality"]["overall_score"] == 91.4
    assert detail["metadata"]["schema"][1]["privacy"] == "sensitive_free_text"
    assert "model.ticket-intent:1.3.0" in detail["metadata"]["lineage"]["consumers"]


def test_mcp_detail_is_available_without_requiring_live_service(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/assets/mcp.keycloak/versions/0.2.0/detail",
        headers=VIEWER,
    )

    assert response.status_code == 200
    detail = response.json()
    assert detail["metadata"]["transport"] == "streamable_http"
    assert detail["metadata"]["declared_tools"] == [
        "lookup_access_policy",
        "validate_entitlement",
        "submit_access_decision",
    ]
    assert detail["live_status"] is None


def test_shared_detail_contract_covers_assets_without_specialized_metadata(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/assets/model.ticket-intent/versions/1.3.0/detail",
        headers=VIEWER,
    )

    assert response.status_code == 200
    detail = response.json()
    assert detail["detail_kind"] == "model"
    assert detail["metadata"] == {}


def test_asset_detail_requires_authentication(client: TestClient) -> None:
    response = client.get(
        "/api/v1/assets/dataset.access-tickets/versions/2026.7.0/detail",
    )

    assert response.status_code == 401


def test_governance_portfolio_exposes_evidence_and_pending_approvals(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/governance", headers=VIEWER)

    assert response.status_code == 200
    portfolio = response.json()
    assert len(portfolio["evidence"]) == 5
    assert portfolio["approvals"][0]["asset_id"] == "mcp.keycloak"
    assert portfolio["allowed_transitions"]["build_test"] == [
        "steward_review",
        "retired",
    ]


def test_operator_can_request_evidence_gated_asset_approval(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/assets/agent.policy-risk/versions/0.4.0/approvals",
        headers=OPERATOR,
        json={
            "target_state": "steward_review",
            "note": "Regression evidence is attached.",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_reviewer_approval_advances_generic_asset_lifecycle(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/governance/approvals/5cd59c92-9c44-46e7-8f03-7769518d9398/decision",
        headers=REVIEWER,
        json={"decision": "approve", "note": "Gateway controls verified."},
    )

    assert response.status_code == 200
    assert response.json()["current_state"] == "shadow"


def test_runtime_portfolio_exposes_stage_progress_and_review_queue(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/runtime", headers=VIEWER)

    assert response.status_code == 200
    runtime = response.json()
    assert len(runtime["runs"]) == 4
    assert runtime["status_counts"]["waiting_for_human"] == 1
    assert runtime["reviews"][0]["status"] == "pending"
    assert len(runtime["runs"][0]["stages"]) == 5


def test_reviewer_decision_resumes_paused_workflow(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/runtime/reviews/68101460-9d40-4b13-897f-142574567bb8/decision",
        headers=REVIEWER,
        json={"decision": "approve", "rationale": "Manager evidence verified."},
    )

    assert response.status_code == 200
    detail = response.json()
    assert detail["run"]["status"] == "running"
    assert detail["run"]["current_stage_id"] == "provision-access"
    assert detail["events"][-1]["event_type"] == "human.decision.recorded"


def test_mcp_gateway_denies_unauthorised_tool_and_keeps_audit(
    client: TestClient,
) -> None:
    denied = client.post(
        "/api/v1/mcp-gateway/invoke",
        headers=VIEWER,
        json={
            "tool_name": "validate_entitlement",
            "arguments": {
                "requester_role": "employee",
                "application": "Finance",
                "entitlement": "Viewer",
            },
            "run_id": "db2cb166-890b-4ca4-82bd-2e7de99b0e58",
            "stage_id": "policy-evaluation",
        },
    )
    audit = client.get("/api/v1/mcp-gateway/invocations", headers=VIEWER)

    assert denied.status_code == 403
    assert audit.status_code == 200
    assert audit.json()[0]["decision"] == "denied"
    assert audit.json()[0]["actor_email"] == "viewer@northstar.local"


def test_mcp_gateway_allows_registered_tool_and_audits_result(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fixture_call(
        endpoint: str,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        return {
            "content": [{"type": "text", "text": "fixture-policy"}],
            "isError": False,
        }

    monkeypatch.setattr(
        "control_plane_api.routers.mcp_gateway.invoke_mcp_tool",
        fixture_call,
    )
    response = client.post(
        "/api/v1/mcp-gateway/invoke",
        headers=OPERATOR,
        json={
            "tool_name": "lookup_access_policy",
            "arguments": {
                "application": "Finance",
                "entitlement": "Viewer",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "allowed"
    audit = client.get("/api/v1/mcp-gateway/invocations", headers=VIEWER).json()
    assert audit[0]["decision"] == "allowed"
    assert audit[0]["result"]["isError"] is False


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
