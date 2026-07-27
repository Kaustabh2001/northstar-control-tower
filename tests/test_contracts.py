from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from northstar_contracts import (
    AssetRef,
    GovernanceState,
    HumanReviewRequest,
    RunStatus,
    WorkflowManifest,
    WorkflowRun,
    WorkflowStage,
)
from northstar_contracts.runtime import CorrelationIds


def workflow_manifest() -> WorkflowManifest:
    agent = AssetRef(asset_id="agent.policy", version="0.1.0")
    return WorkflowManifest(
        asset_id="workflow.access-request",
        version="0.1.0",
        display_name="Employee Access Request",
        owner="IAM Platform",
        intended_use="Process governed employee application access requests.",
        governance_state=GovernanceState.BUILD_TEST,
        input_schema_ref="schema://access-request/1.0.0",
        output_schema_ref="schema://access-result/1.0.0",
        participating_agents=[agent],
        stages=[
            WorkflowStage(
                stage_id="policy-check",
                display_name="Policy check",
                agent=agent,
            )
        ],
    )


def test_workflow_rejects_undeclared_agent() -> None:
    manifest = workflow_manifest().model_dump()
    manifest["stages"][0]["agent"]["version"] = "9.9.9"

    with pytest.raises(ValidationError, match="undeclared agent versions"):
        WorkflowManifest.model_validate(manifest)


def test_failed_run_requires_error_code() -> None:
    with pytest.raises(ValidationError, match="require error_code"):
        WorkflowRun(
            run_id=uuid4(),
            workflow=AssetRef(asset_id="workflow.access-request", version="0.1.0"),
            status=RunStatus.FAILED,
            correlation=CorrelationIds(
                trace_id="trace-1",
                langgraph_thread_id="thread-1",
            ),
        )


def test_human_review_requires_future_expiry() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError, match="must be after"):
        HumanReviewRequest(
            review_id=uuid4(),
            run_id=uuid4(),
            stage_id="manager-approval",
            title="Approve requested access",
            reason="Cross-cost-centre access requires manager approval.",
            policy_evidence=["AC-14 section 3.2"],
            requested_action={"tool": "keycloak.grant_role"},
            requested_at=now,
            expires_at=now - timedelta(minutes=1),
        )
