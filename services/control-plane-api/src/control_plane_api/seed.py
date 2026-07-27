from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from northstar_contracts import (
    AssetRegistration,
    AssetType,
    GovernanceState,
    RiskLevel,
)

from .models import AssetRecord
from .repository import create_asset


def seed_demo_assets(session_factory: sessionmaker[Session]) -> None:
    with session_factory() as session:
        if session.scalar(select(func.count()).select_from(AssetRecord)):
            return
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
            create_asset(session, asset)

