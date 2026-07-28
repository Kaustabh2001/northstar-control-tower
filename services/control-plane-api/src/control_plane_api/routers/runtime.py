from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import CurrentUser, require_roles
from ..database import get_session
from ..runtime.service import (
    decide_human_review,
    run_detail,
    runtime_portfolio,
    start_dummy_run,
)
from ..schemas import (
    HumanReviewDecisionRequest,
    RunDetailResponse,
    RuntimePortfolio,
    DummyRunRequest,
)

router = APIRouter(prefix="/api/v1/runtime", tags=["runtime"])


@router.post("/dummy-runs", response_model=RunDetailResponse, status_code=201)
def create_dummy_run(
    request: DummyRunRequest,
    session: Session = Depends(get_session),
    user: CurrentUser = Depends(require_roles("operator", "admin")),
) -> RunDetailResponse:
    try:
        return start_dummy_run(session, request=request, actor=user)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("", response_model=RuntimePortfolio)
def get_runtime_portfolio(
    session: Session = Depends(get_session),
    _user: CurrentUser = Depends(require_roles("viewer")),
) -> RuntimePortfolio:
    return runtime_portfolio(session)


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def get_run_detail(
    run_id: str,
    session: Session = Depends(get_session),
    _user: CurrentUser = Depends(require_roles("viewer")),
) -> RunDetailResponse:
    detail = run_detail(session, run_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Workflow run not found.")
    return detail


@router.post(
    "/reviews/{review_id}/decision",
    response_model=RunDetailResponse,
)
def decide_runtime_review(
    review_id: str,
    decision: HumanReviewDecisionRequest,
    session: Session = Depends(get_session),
    user: CurrentUser = Depends(require_roles("reviewer", "admin")),
) -> RunDetailResponse:
    detail = decide_human_review(
        session,
        review_id=review_id,
        decision=decision.decision,
        rationale=decision.rationale,
        actor=user,
    )
    if not detail:
        raise HTTPException(status_code=404, detail="Pending human review not found.")
    return detail
