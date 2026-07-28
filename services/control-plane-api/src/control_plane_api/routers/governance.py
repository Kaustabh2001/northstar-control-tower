from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import CurrentUser, require_roles
from ..database import get_session
from ..governance.service import (
    decide_asset_approval,
    emergency_lifecycle_action,
    governance_portfolio,
    request_asset_approval,
)
from ..schemas import (
    ApprovalDecisionRequest,
    GovernanceApproval,
    GovernancePortfolio,
    GovernanceTransitionRequest,
    EmergencyLifecycleRequest,
    AssetResponse,
)

router = APIRouter(prefix="/api/v1", tags=["governance"])


@router.get("/governance", response_model=GovernancePortfolio)
def get_governance_portfolio(
    session: Session = Depends(get_session),
    _user: CurrentUser = Depends(require_roles("viewer")),
) -> GovernancePortfolio:
    return governance_portfolio(session)


@router.post(
    "/assets/{asset_id}/versions/{version}/approvals",
    response_model=GovernanceApproval,
    status_code=status.HTTP_201_CREATED,
)
def request_governance_approval(
    asset_id: str,
    version: str,
    transition: GovernanceTransitionRequest,
    session: Session = Depends(get_session),
    user: CurrentUser = Depends(require_roles("operator", "admin")),
) -> GovernanceApproval:
    try:
        return request_asset_approval(
            session,
            asset_id=asset_id,
            version=version,
            target_state=transition.target_state,
            note=transition.note,
            actor=user,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post(
    "/governance/approvals/{approval_id}/decision",
    response_model=GovernanceApproval,
)
def decide_governance_approval(
    approval_id: str,
    decision: ApprovalDecisionRequest,
    session: Session = Depends(get_session),
    user: CurrentUser = Depends(require_roles("reviewer", "admin")),
) -> GovernanceApproval:
    try:
        approval = decide_asset_approval(
            session,
            approval_id=approval_id,
            decision=decision.decision,
            note=decision.note,
            actor=user,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if not approval:
        raise HTTPException(status_code=404, detail="Pending approval not found.")
    return approval


@router.post(
    "/assets/{asset_id}/versions/{version}/emergency-action",
    response_model=AssetResponse,
)
def perform_emergency_action(
    asset_id: str,
    version: str,
    request: EmergencyLifecycleRequest,
    session: Session = Depends(get_session),
    user: CurrentUser = Depends(require_roles("admin")),
) -> AssetResponse:
    try:
        return emergency_lifecycle_action(
            session,
            asset_id=asset_id,
            version=version,
            action=request.action,
            reason=request.reason,
            target_version=request.target_version,
            actor=user,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
