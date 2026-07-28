from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..models import AssetRecord, HumanReviewRecord, WorkflowRunRecord

TOOL_POLICY = {
    "lookup_access_policy": {
        "roles": {"viewer", "operator", "reviewer", "admin"},
        "stage": None,
    },
    "validate_entitlement": {
        "roles": {"operator", "reviewer", "admin"},
        "stage": "policy-evaluation",
    },
    "submit_access_decision": {
        "roles": {"reviewer", "admin"},
        "stage": "manager-approval",
    },
}


def authorize_mcp_invocation(
    session: Session,
    *,
    tool_name: str,
    server_asset_id: str,
    server_version: str,
    run_id: str | None,
    stage_id: str | None,
    actor: CurrentUser,
) -> tuple[bool, str]:
    server = session.get(AssetRecord, (server_asset_id, server_version))
    if not server or server.asset_type != "mcp_server":
        return False, "MCP server version is not registered."
    if server.governance_state not in {"shadow", "canary", "production"}:
        return False, "MCP server is not approved for runtime invocation."
    policy = TOOL_POLICY.get(tool_name)
    if not policy:
        return False, "Tool is not registered in the gateway allowlist."
    if not actor.roles.intersection(policy["roles"]):
        return False, "Caller roles do not permit this tool."
    required_stage = policy["stage"]
    if required_stage and (not run_id or stage_id != required_stage):
        return False, f"Tool is restricted to workflow stage {required_stage}."
    if run_id:
        run = session.get(WorkflowRunRecord, run_id)
        if not run:
            return False, "Referenced workflow run does not exist."
        if stage_id not in {stage["stage_id"] for stage in run.stages}:
            return False, "Stage is not declared by the workflow run."
    if tool_name == "submit_access_decision":
        approved_review = session.scalar(
            select(HumanReviewRecord)
            .where(HumanReviewRecord.run_id == run_id)
            .where(HumanReviewRecord.stage_id == stage_id)
            .where(HumanReviewRecord.status == "approved")
        )
        if not approved_review:
            return False, "An approved human review is required before this tool."
    return True, "Allowed by gateway policy."
