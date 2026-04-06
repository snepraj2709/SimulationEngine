from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.feedback import FeedbackEvent
from app.models.user import User
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse

router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreateRequest,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FeedbackResponse:
    analysis = AnalysisRepository(session).get_by_id_for_user(payload.analysis_id, user.id)
    if analysis is None:
        raise AppException(404, "analysis_not_found", "Analysis not found.")
    if not any(scenario.id == payload.scenario_id for scenario in analysis.scenarios):
        raise AppException(404, "scenario_not_found", "Scenario not found for this analysis.")
    run = next((run for run in analysis.simulation_runs if run.id == payload.simulation_run_id), None)
    if run is None:
        raise AppException(404, "simulation_run_not_found", "Simulation run not found for this analysis.")

    repository = FeedbackRepository(session)
    existing = repository.get_existing(user_id=user.id, simulation_run_id=payload.simulation_run_id)
    if existing:
        existing.feedback_type = payload.feedback_type
        existing.comment = payload.comment
        feedback = existing
    else:
        feedback = FeedbackEvent(
            user_id=user.id,
            analysis_id=payload.analysis_id,
            scenario_id=payload.scenario_id,
            simulation_run_id=payload.simulation_run_id,
            feedback_type=payload.feedback_type,
            comment=payload.comment,
        )
        repository.save(feedback)
    session.commit()
    session.refresh(feedback)
    return FeedbackResponse.model_validate(feedback)
