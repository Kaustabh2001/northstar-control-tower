from datetime import datetime
from typing import Any, Literal

from pydantic import AnyHttpUrl, Field

from .base import ContractModel, Identifier, NonEmptyString, SemanticVersion, utc_now
from .enums import AssetType, GovernanceState, RiskLevel


class AssetRef(ContractModel):
    asset_id: Identifier
    version: SemanticVersion


class AssetRegistration(AssetRef):
    asset_type: AssetType
    display_name: NonEmptyString
    owner: NonEmptyString
    intended_use: NonEmptyString
    prohibited_uses: list[NonEmptyString] = Field(default_factory=list)
    governance_state: GovernanceState = GovernanceState.REGISTERED
    risk_level: RiskLevel = RiskLevel.UNASSESSED
    source_commit: str | None = Field(default=None, min_length=7, max_length=64)
    labels: dict[str, str] = Field(default_factory=dict)


class AgentRegistration(AssetRegistration):
    """Portal metadata around an official A2A Agent Card.

    The official card remains authoritative. Its JSON is retained without
    reimplementing the evolving A2A protocol schema in this package.
    """

    asset_type: Literal[AssetType.AGENT] = AssetType.AGENT
    agent_card_url: AnyHttpUrl
    a2a_protocol_version: NonEmptyString
    card_content_hash: str | None = Field(default=None, min_length=16, max_length=128)
    card_snapshot: dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=utc_now)
