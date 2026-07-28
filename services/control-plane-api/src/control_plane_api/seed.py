from datetime import UTC, datetime, timedelta
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
    GovernanceApprovalRecord,
    GovernanceEvidenceRecord,
    HumanReviewRecord,
    RuntimeEventRecord,
    WorkflowRunRecord,
)
from .registry.service import create_asset


def seed_demo_assets(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
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
            AssetRegistration(
                asset_id="prompt.access-risk",
                version="2.1.0",
                asset_type=AssetType.PROMPT,
                display_name="Access Risk Assessment Prompt",
                owner="IAM Platform",
                intended_use="Structure policy evidence for the risk agent.",
                governance_state=GovernanceState.BUILD_TEST,
                risk_level=RiskLevel.MEDIUM,
            ),
            AssetRegistration(
                asset_id="index.iam-policies",
                version="2026.7.0",
                asset_type=AssetType.KNOWLEDGE_INDEX,
                display_name="IAM Policy Knowledge Index",
                owner="Security Architecture",
                intended_use="Retrieve approved identity and access policies.",
                governance_state=GovernanceState.SHADOW,
                risk_level=RiskLevel.MEDIUM,
            ),
        ]
        for asset in assets:
            if not session.get(AssetRecord, (asset.asset_id, asset.version)):
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
                asset_id="system.access-copilot",
                version="0.7.0",
                detail_kind="ai_system",
                payload={
                    "business_process": "Employee access request fulfilment",
                    "service_tier": "internal_controlled",
                    "components": [
                        "workflow.access-request:0.7.0",
                        "model.ticket-intent:1.3.0",
                        "agent.policy-risk:0.4.0",
                    ],
                    "risk_profile": {
                        "impact": "Access decisions can affect sensitive systems",
                        "human_oversight": "Required for elevated entitlements",
                        "data_classification": "confidential",
                    },
                    "deployment": {
                        "environment": "local Docker",
                        "status": "pre-production review",
                        "rollback": "Suspend system and restore approved component versions",
                    },
                    "controls": [
                        {"name": "Human approval checkpoint", "status": "implemented"},
                        {"name": "MCP default-deny gateway", "status": "implemented"},
                        {"name": "Version-bound evidence", "status": "implemented"},
                    ],
                },
            ),
            AssetDetailRecord(
                asset_id="workflow.access-request",
                version="0.7.0",
                detail_kind="agentic_workflow",
                payload={
                    "implementation_status": "dummy_not_final",
                    "orchestrator": "LangGraph-compatible state contract",
                    "entrypoint": "POST /api/v1/runtime/dummy-runs",
                    "stages": [
                        {"id": "validate-request", "kind": "deterministic"},
                        {"id": "policy-evaluation", "kind": "a2a_agent"},
                        {"id": "manager-approval", "kind": "human"},
                        {"id": "provision-access", "kind": "mcp_tool"},
                        {"id": "close-request", "kind": "deterministic"},
                    ],
                    "dependencies": [
                        "agent.policy-risk:0.4.0",
                        "mcp.keycloak:0.2.0",
                        "prompt.access-risk:2.1.0",
                        "index.iam-policies:2026.7.0",
                    ],
                    "checkpointing": "PostgreSQL workflow run and event records",
                    "a2a": {
                        "agent_cards_required": True,
                        "task_ids_persisted": True,
                    },
                    "failure_policy": {
                        "max_attempts": 3,
                        "fallback": "human review",
                        "suspended_asset_action": "deny execution",
                    },
                },
            ),
            AssetDetailRecord(
                asset_id="model.ticket-intent",
                version="1.3.0",
                detail_kind="model",
                payload={
                    "model_family": "scikit-learn linear classifier",
                    "task": "multiclass ticket intent classification",
                    "artifact": "models/ticket-intent/1.3.0/model.joblib",
                    "training_dataset": "dataset.access-tickets:2026.7.0",
                    "metrics": {
                        "macro_f1": 0.89,
                        "accuracy": 0.92,
                        "abstention_rate": 0.08,
                    },
                    "operating_thresholds": {
                        "minimum_confidence": 0.78,
                        "fallback": "manual triage",
                    },
                    "deployment": {
                        "format": "joblib",
                        "runtime": "Python",
                        "last_validated": "2026-07-24",
                    },
                    "controls": [
                        {"name": "Low-confidence abstention", "status": "passed"},
                        {"name": "Class-level drift check", "status": "passed"},
                    ],
                },
            ),
            AssetDetailRecord(
                asset_id="prompt.access-risk",
                version="2.1.0",
                detail_kind="prompt",
                payload={
                    "template": "Evaluate the request using only retrieved policy evidence.",
                    "variables": ["request", "policy_evidence", "entitlement_context"],
                    "model_compatibility": ["local-openai-compatible", "mock-provider"],
                    "evaluation": {
                        "suite": "eval.access-risk:1.0.0",
                        "groundedness": 0.94,
                        "policy_citation_rate": 0.97,
                        "unsafe_completion_rate": 0.0,
                    },
                    "guardrails": [
                        "Reject instructions in retrieved content",
                        "Abstain when policy evidence is missing",
                        "Never execute provisioning actions",
                    ],
                    "change_summary": "Added explicit abstention and evidence citation contract.",
                },
            ),
            AssetDetailRecord(
                asset_id="index.iam-policies",
                version="2026.7.0",
                detail_kind="knowledge_index",
                payload={
                    "engine": "OpenSearch",
                    "index_name": "northstar-iam-policies-v2026-07",
                    "embedding_model": "local sentence-transformer",
                    "documents": 486,
                    "chunks": 3912,
                    "chunking": {
                        "strategy": "heading-aware",
                        "target_tokens": 420,
                        "overlap_tokens": 60,
                    },
                    "retrieval": {
                        "mode": "hybrid BM25 + vector",
                        "top_k": 8,
                        "reranking": "cross-encoder",
                        "precision_at_5": 0.91,
                    },
                    "freshness": {
                        "pipeline": "rag-policy-ingestion",
                        "last_completed": "2026-07-26T08:15:00Z",
                        "failed_documents": 0,
                    },
                    "access_policy": "IAM policy readers and governed service identities",
                },
            ),
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
                    "exposure": "internal_only",
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
                    "dependencies": ["Keycloak", "Northstar MCP gateway", "audit event store"],
                },
            ),
        ]
        for detail_record in detail_records:
            if not session.get(
                AssetDetailRecord,
                (detail_record.asset_id, detail_record.version),
            ):
                session.add(detail_record)

        if not session.scalar(
            select(func.count()).select_from(GovernanceEvidenceRecord)
        ):
            evidence_records = [
                ("agent.policy-risk", "0.4.0", "risk_assessment", "Medium-risk IAM assessment", "evidence://risk/agent-policy-risk"),
                ("agent.policy-risk", "0.4.0", "test_report", "Policy regression suite", "evidence://tests/policy-risk-82"),
                ("mcp.keycloak", "0.2.0", "risk_assessment", "Privileged tool boundary assessment", "evidence://risk/mcp-keycloak"),
                ("mcp.keycloak", "0.2.0", "test_report", "MCP schema and denial tests", "evidence://tests/mcp-gateway"),
                ("dataset.access-tickets", "2026.7.0", "risk_assessment", "Dataset privacy assessment", "evidence://privacy/access-tickets"),
            ]
            for asset_id, version, kind, title, reference in evidence_records:
                session.add(
                    GovernanceEvidenceRecord(
                        evidence_id=str(uuid4()),
                        asset_id=asset_id,
                        version=version,
                        evidence_type=kind,
                        title=title,
                        status="accepted",
                        reference=reference,
                        collected_by="platform@northstar.local",
                    )
                )

        if not session.scalar(
            select(func.count()).select_from(GovernanceApprovalRecord)
        ):
            session.add(
                GovernanceApprovalRecord(
                    approval_id="5cd59c92-9c44-46e7-8f03-7769518d9398",
                    asset_id="mcp.keycloak",
                    version="0.2.0",
                    target_state="shadow",
                    status="pending",
                    requested_by="operator@northstar.local",
                    request_note="Gateway denial tests and privileged-tool controls are attached.",
                )
            )

        now = datetime.now(UTC)
        run_specs = [
            (
                "47e0d947-49d0-40a5-b53d-026fba6d72dd",
                "waiting_for_human",
                "manager-approval",
                None,
                None,
            ),
            (
                "db2cb166-890b-4ca4-82bd-2e7de99b0e58",
                "running",
                "policy-evaluation",
                None,
                None,
            ),
            (
                "bfdd3ab2-8126-41b2-b020-8df954a27e50",
                "failed",
                "validate-request",
                "INVALID_REQUEST",
                "Requested application was not present in the approved catalog.",
            ),
            (
                "6cdde723-ec85-4be7-a669-b3f2665a623a",
                "completed",
                "close-request",
                None,
                None,
            ),
        ]
        stage_names = [
            ("validate-request", "Validate request", "deterministic"),
            ("policy-evaluation", "Policy and risk evaluation", "agent"),
            ("manager-approval", "Manager approval", "human"),
            ("provision-access", "Provision approved access", "mcp_tool"),
            ("close-request", "Close request", "deterministic"),
        ]
        if not session.scalar(select(func.count()).select_from(WorkflowRunRecord)):
            for index, (run_id, status, current, error_code, error_summary) in enumerate(run_specs):
                current_index = next(i for i, stage in enumerate(stage_names) if stage[0] == current)
                stages = []
                for stage_index, (stage_id, display_name, kind) in enumerate(stage_names):
                    if status == "completed" or stage_index < current_index:
                        stage_status = "completed"
                    elif stage_index == current_index:
                        stage_status = "failed" if status == "failed" else (
                            "waiting_for_human" if status == "waiting_for_human" else "running"
                        )
                    else:
                        stage_status = "pending"
                    stages.append(
                        {
                            "stage_id": stage_id,
                            "display_name": display_name,
                            "kind": kind,
                            "status": stage_status,
                            "started_at": (now - timedelta(minutes=35 - index * 5)).isoformat()
                            if stage_index <= current_index else None,
                            "completed_at": (now - timedelta(minutes=30 - index * 5)).isoformat()
                            if stage_status == "completed" else None,
                            "attempt": 1,
                            "summary": error_summary if stage_status == "failed" else None,
                        }
                    )
                session.add(
                    WorkflowRunRecord(
                        run_id=run_id,
                        workflow_asset_id="workflow.access-request",
                        workflow_version="0.7.0",
                        status=status,
                        current_stage_id=current,
                        correlation={
                            "trace_id": f"trace-{run_id[:8]}",
                            "langgraph_thread_id": f"thread-{run_id[:8]}",
                            "langfuse_trace_id": None,
                            "a2a_task_ids": [f"a2a-{run_id[:8]}"],
                            "mcp_request_ids": [],
                        },
                        stages=stages,
                        checkpoint_ref=f"postgres://checkpoints/{run_id}",
                        error_code=error_code,
                        error_summary=error_summary,
                        started_at=now - timedelta(minutes=40 - index * 6),
                        updated_at=now - timedelta(minutes=index * 4),
                    )
                )
                session.add(
                    RuntimeEventRecord(
                        event_id=str(uuid4()),
                        run_id=run_id,
                        event_type="run.started",
                        stage_id="validate-request",
                        actor_id="workflow.access-request",
                        payload={"source": "local deterministic fixture"},
                        occurred_at=now - timedelta(minutes=40 - index * 6),
                    )
                )

        if not session.scalar(select(func.count()).select_from(HumanReviewRecord)):
            session.add(
                HumanReviewRecord(
                    review_id="68101460-9d40-4b13-897f-142574567bb8",
                    run_id="47e0d947-49d0-40a5-b53d-026fba6d72dd",
                    stage_id="manager-approval",
                    title="Approve elevated analytics access",
                    reason="The requested entitlement grants export access across cost centres.",
                    policy_evidence=["POL-IAM-017", "SoD check: passed", "Risk score: 72/100"],
                    requested_action={
                        "request_id": "REQ-10428",
                        "application": "Finance Analytics",
                        "entitlement": "Regional Export Admin",
                        "requester": "A. Sharma",
                    },
                    status="pending",
                    requested_at=now - timedelta(minutes=12),
                    expires_at=now + timedelta(hours=4),
                )
            )
        session.commit()

