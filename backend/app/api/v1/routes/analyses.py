from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.db.session import get_db, get_session_factory
from app.models.analysis import AnalysisStatus
from app.models.user import User
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisCreateRequest, AnalysisCreateResponse, AnalysisDetailResponse, AnalysisListItemResponse
from app.schemas.simulation import SimulateScenarioRequest, SimulationRunResponse
from app.services.analysis_cloner import AnalysisCloner
from app.services.analysis_pipeline import AnalysisPipelineService
from app.services.presenters import (
    build_analysis_create_response,
    build_analysis_detail_response,
    build_analysis_list_item,
    build_simulation_run_response,
)
from app.utils.url import validate_safe_public_url

router = APIRouter()


async def _process_analysis_background(analysis_id: str) -> None:
    session = get_session_factory()()
    try:
        await AnalysisPipelineService(session).process_analysis(analysis_id)
    finally:
        session.close()


@router.post("", response_model=AnalysisCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    payload: AnalysisCreateRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisCreateResponse:
    settings = get_settings()
    normalized_url = validate_safe_public_url(str(payload.url), allow_private_network=settings.allow_private_network_scraping)
    repository = AnalysisRepository(session)

    if not payload.force_refresh:
        existing_for_user = repository.get_latest_by_user_and_url(user.id, normalized_url)
        if existing_for_user and existing_for_user.status in {
            AnalysisStatus.queued.value,
            AnalysisStatus.processing.value,
            AnalysisStatus.completed.value,
        }:
            return build_analysis_create_response(existing_for_user, reused=True)

        cached_analysis = repository.get_latest_completed_by_normalized_url(normalized_url, cache_hours=settings.analysis_cache_hours)
        if cached_analysis is not None:
            cloned = AnalysisCloner(repository).clone(
                source=cached_analysis,
                target_user_id=user.id,
                input_url=str(payload.url),
                normalized_url=normalized_url,
            )
            session.commit()
            return build_analysis_create_response(cloned, reused=True, cloned_from_analysis_id=cached_analysis.id)

    analysis = repository.create(
        user_id=user.id,
        input_url=str(payload.url),
        normalized_url=normalized_url,
        status=AnalysisStatus.queued,
    )
    session.commit()
    session.refresh(analysis)

    if payload.run_async:
        background_tasks.add_task(_process_analysis_background, analysis.id)
    else:
        await AnalysisPipelineService(session).process_analysis(analysis.id)
        session.refresh(analysis)

    return build_analysis_create_response(analysis)


@router.get("", response_model=list[AnalysisListItemResponse])
def list_analyses(
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AnalysisListItemResponse]:
    analyses = AnalysisRepository(session).list_for_user(user.id)
    return [build_analysis_list_item(analysis) for analysis in analyses]


@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
def get_analysis(
    analysis_id: str,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalysisDetailResponse:
    analysis = AnalysisRepository(session).get_by_id_for_user(analysis_id, user.id)
    if analysis is None:
        raise AppException(404, "analysis_not_found", "Analysis not found.")
    return build_analysis_detail_response(analysis)


@router.post("/{analysis_id}/scenarios/{scenario_id}/simulate", response_model=SimulationRunResponse)
async def simulate_scenario(
    analysis_id: str,
    scenario_id: str,
    payload: SimulateScenarioRequest,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SimulationRunResponse:
    repository = AnalysisRepository(session)
    analysis = repository.get_by_id_for_user(analysis_id, user.id)
    if analysis is None:
        raise AppException(404, "analysis_not_found", "Analysis not found.")
    scenario = next((item for item in analysis.scenarios if item.id == scenario_id), None)
    if scenario is None:
        raise AppException(404, "scenario_not_found", "Scenario not found for this analysis.")
    if analysis.status != AnalysisStatus.completed.value:
        raise AppException(409, "analysis_not_ready", "Simulation cannot run until analysis is complete.")

    service = AnalysisPipelineService(session)
    run = await service.rerun_scenario(
        analysis=analysis,
        scenario=scenario,
        input_overrides=payload.input_overrides,
        run_version=payload.run_version,
    )
    refreshed = repository.get_by_id_for_user(analysis_id, user.id)
    assert refreshed is not None
    refreshed_run = next(item for item in refreshed.simulation_runs if item.id == run.id)
    return build_simulation_run_response(refreshed_run, refreshed)
