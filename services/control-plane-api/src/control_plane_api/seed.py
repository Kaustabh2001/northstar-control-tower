from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from northstar_contracts import (
    AssetRegistration,
    AssetType,
    GovernanceState,
    RiskLevel,
)

from .models import (
    AgentDetailRecord,
    AssetDetailRecord,
    AssetRecord,
    AuditEventRecord,
)
from .repository import create_asset


def seed_demo_assets(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        has_assets = bool(
            session.scalar(select(func.count()).select_from(AssetRecord))
        )
        assets = [
            AssetRegistration(
                asset_id="system.access-copilot",
                version="0.7.0",
                asset_type=AssetType.AI_SYSTEM,
                display_name="Employee Access Copilot",
                owner="Priya Nair",
                intended_use="Govern employee application access requests.",
                governance_state=GovernanceState.STEWARD_REVIEW,
                risk_level=RiskLevel.MEDIUM,
            ),
            AssetRegistration(
                asset_id="workflow.access-request",
                version="0.7.0",
                asset_type=AssetType.AGENTIC_WORKFLOW,
                display_name="Employee Access Request",
                owner="IAM Platform",
                intended_use="Coordinate policy, approval and provisioning agents.",
                governance_state=GovernanceState.SHADOW,
                risk_level=RiskLevel.HIGH,
            ),
            AssetRegistration(
                asset_id="agent.policy-risk",
                version="0.4.0",
                asset_type=AssetType.AGENT,
                display_name="Policy and Risk Agent",
                owner="Ravi Kumar",
                intended_use="Evaluate requests against approved access policies.",
                governance_state=GovernanceState.BUILD_TEST,
                risk_level=RiskLevel.MEDIUM,
            ),
            AssetRegistration(
                asset_id="model.ticket-intent",
                version="1.3.0",
                asset_type=AssetType.MODEL,
                display_name="Ticket Intent Classifier",
                owner="Aisha Mehta",
                intended_use="Classify access and non-access service requests.",
                governance_state=GovernanceState.PRODUCTION,
                risk_level=RiskLevel.LOW,
            ),
            AssetRegistration(
                asset_id="dataset.access-tickets",
                version="2026.7.0",
                asset_type=AssetType.DATASET,
                display_name="Access Ticket Corpus",
                owner="Sarah Osei",
                intended_use="Train and evaluate ticket intent classification.",
                governance_state=GovernanceState.ASSESS,
                risk_level=RiskLevel.MEDIUM,
            ),
            AssetRegistration(
                asset_id="mcp.keycloak",
                version="0.2.0",
                asset_type=AssetType.MCP_SERVER,
                display_name="Keycloak MCP Server",
                owner="IAM Platform",
                intended_use="Execute approval-bound identity operations.",
                governance_state=GovernanceState.STEWARD_REVIEW,
                risk_level=RiskLevel.HIGH,
            ),
        ]
        for asset in assets:
            if not has_assets:
                create_asset(session, asset)
        if not session.get(AgentDetailRecord, ("agent.policy-risk", "0.4.0")):
            session.add(AgentDetailRecord(
                asset_id="agent.policy-risk",
                version="0.4.0",
                agent_card={
                    "name": "Policy and Risk Agent",
                    "description": "Evaluates access requests against approved policy, risk and segregation-of-duties controls.",
                    "protocol_version": "0.3.0",
                    "url": "http://policy-risk-agent:9010/a2a",
                    "preferred_transport": "JSONRPC",
                    "capabilities": {
                        "streaming": False,
                        "push_notifications": True,
                        "state_transition_history": True,
                    },
                    "skills": [
                        {
                            "skill_id": "evaluate-access-request",
                            "name": "Evaluate access request",
                            "description": "Returns policy findings and a governed risk recommendation.",
                            "tags": ["iam", "policy", "risk"],
                            "input_modes": ["application/json"],
                            "output_modes": ["application/json"],
                        },
                        {
                            "skill_id": "explain-policy-decision",
                            "name": "Explain policy decision",
                            "description": "Produces evidence-linked reasons for reviewers.",
                            "tags": ["explainability", "evidence"],
                            "input_modes": ["application/json"],
                            "output_modes": ["text/plain", "application/json"],
                        },
                    ],
                },
                dependencies=[
                    {
                        "asset_id": "model.ticket-intent",
                        "version": "1.3.0",
                        "relationship": "uses",
                        "display_name": "Ticket Intent Classifier",
                        "asset_type": "model",
                    },
                    {
                        "asset_id": "dataset.access-tickets",
                        "version": "2026.7.0",
                        "relationship": "evaluated_with",
                        "display_name": "Access Ticket Corpus",
                        "asset_type": "dataset",
                    },
                    {
                        "asset_id": "mcp.keycloak",
                        "version": "0.2.0",
                        "relationship": "tool_access",
                        "display_name": "Keycloak MCP Server",
                        "asset_type": "mcp_server",
                    },
                ],
                controls=[
                    {
                        "control_id": "CTRL-HITL-01",
                        "name": "Human approval for elevated access",
                        "status": "implemented",
                        "evidence": "Workflow approval gate policy v0.7",
                    },
                    {
                        "control_id": "CTRL-DATA-03",
                        "name": "Sensitive field minimisation",
                        "status": "implemented",
                        "evidence": "MCP gateway redaction policy",
                    },
                    {
                        "control_id": "CTRL-EVAL-02",
                        "name": "Policy decision regression suite",
                        "status": "attention",
                        "evidence": "82% scenario coverage; target 90%",
                    },
                ],
                health_status="not_checked",
            ))
            session.add(AuditEventRecord(
                event_id=str(uuid4()),
                asset_id="agent.policy-risk",
                version="0.4.0",
                action="asset.registered",
                actor_subject="system-seed",
                actor_email="platform@northstar.local",
                detail="Agent version registered from the local demonstration catalog.",
            ))

        detail_records = [
            AssetDetailRecord(
                asset_id="dataset.access-tickets",
                version="2026.7.0",
                detail_kind="dataset",
                payload={
                    "source": {
                        "system": "Synthetic service-management export",
                        "format": "Parquet",
                        "refresh_cadence": "Weekly",
                        "record_count": 12840,
                    },
                    "classification": "confidential",
                    "license": "Internal evaluation only",
                    "retention": "180 days; derived aggregates retained for 13 months",
                    "schema": [
                        {"name": "ticket_id", "type": "string", "privacy": "internal_identifier", "nullable": False},
                        {"name": "summary", "type": "string", "privacy": "sensitive_free_text", "nullable": False},
                        {"name": "requester_role", "type": "string", "privacy": "quasi_identifier", "nullable": True},
                        {"name": "category", "type": "string", "privacy": "non_personal", "nullable": False},
                        {"name": "resolution_code", "type": "string", "privacy": "non_personal", "nullable": True},
                        {"name": "opened_at", "type": "timestamp", "privacy": "non_personal", "nullable": False},
                    ],
                    "quality": {
                        "overall_score": 91.4,
                        "completeness": 96.8,
                        "duplicate_rate": 0.7,
                        "label_agreement": 88.2,
                        "freshness_days": 4,
                        "last_validation": "2026-07-24T09:30:00Z",
                    },
                    "lineage": {
                        "sources": ["synthetic-ticket-generator", "approved-policy-taxonomy"],
                        "transformations": ["PII redaction", "taxonomy normalization", "stratified split"],
                        "consumers": ["model.ticket-intent:1.3.0", "agent.policy-risk:0.4.0"],
                    },
                    "controls": [
                        {"name": "Free-text PII scan", "status": "passed"},
                        {"name": "Training-serving skew", "status": "passed"},
                        {"name": "Minority class coverage", "status": "attention"},
                    ],
                },
            ),
            AssetDetailRecord(
                asset_id="mcp.keycloak",
                version="0.2.0",
                detail_kind="mcp_server",
                payload={
                    "endpoint": "http://fixture-mcp:8000/mcp",
                    "local_endpoint": "http://localhost:8090/mcp",
                    "transport": "streamable_http",
                    "protocol": "MCP",
                    "protocol_version": "2025-11-25",
                    "auth": {
                        "method": "gateway_service_identity",
                        "required_roles": ["operator", "reviewer"],
                        "secret_storage": "environment-backed development secret",
                    },
                    "policy": {
                        "network_zone": "local_control_plane",
                        "default_action": "deny",
                        "human_approval_for": ["elevated_access", "role_assignment"],
                    },
                    "declared_tools": [
                        "lookup_access_policy",
                        "validate_entitlement",
                        "submit_access_decision",
                    ],
                    "dependencies": ["Keycloak", "MCP gateway (planned)", "audit event store"],
                },
            ),
        ]
        for detail_record in detail_records:
            if not session.get(
                AssetDetailRecord,
                (detail_record.asset_id, detail_record.version),
            ):
                session.add(detail_record)
        session.commit()

