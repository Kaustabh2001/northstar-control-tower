from datetime import datetime

from pydantic import BaseModel, ConfigDict

from northstar_contracts import AssetRegistration


class AssetResponse(AssetRegistration):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        str_strip_whitespace=True,
    )

    created_at: datetime
    updated_at: datetime


class DashboardSummary(BaseModel):
    total_assets: int
    managed_assets: int
    discovered_assets: int
    awaiting_review: int
    high_risk_assets: int
    by_type: dict[str, int]
    model_provider: str = "not_configured"

