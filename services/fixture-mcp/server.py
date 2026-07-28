import os
from typing import Literal

from mcp.server.fastmcp import FastMCP


mcp = FastMCP(
    "Northstar Identity Governance Tools",
    instructions=(
        "Read-only and approval-bound identity governance tools for local "
        "workflow development."
    ),
    host="0.0.0.0",
    port=int(os.getenv("NORTHSTAR_MCP_PORT", "8000")),
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def lookup_access_policy(application: str, entitlement: str) -> dict:
    """Return the governing policy and approval requirements for an entitlement."""
    elevated = any(
        marker in entitlement.lower()
        for marker in ("admin", "owner", "privileged")
    )
    return {
        "application": application,
        "entitlement": entitlement,
        "policy_id": "POL-IAM-017",
        "risk": "high" if elevated else "medium",
        "human_approval_required": elevated,
        "allowed_requester_types": ["employee", "contractor"],
        "source": "approved-policy-taxonomy:2026.07",
    }


@mcp.tool()
def validate_entitlement(
    requester_role: str,
    application: str,
    entitlement: str,
) -> dict:
    """Evaluate a requested entitlement against deterministic least-privilege rules."""
    conflict = (
        requester_role.lower() == "contractor"
        and "admin" in entitlement.lower()
    )
    return {
        "decision": "deny" if conflict else "review",
        "reasons": (
            ["Contractors cannot receive administrative entitlements."]
            if conflict
            else ["No deterministic conflict; steward review remains required."]
        ),
        "policy_id": "POL-IAM-017",
        "application": application,
    }


@mcp.tool()
def submit_access_decision(
    request_id: str,
    decision: Literal["approve", "deny"],
    reviewer: str,
    evidence_reference: str,
) -> dict:
    """Record a fixture approval decision without mutating a real identity system."""
    return {
        "accepted": True,
        "fixture": True,
        "request_id": request_id,
        "decision": decision,
        "reviewer": reviewer,
        "evidence_reference": evidence_reference,
        "message": "Decision accepted by the local fixture; no external change was made.",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
