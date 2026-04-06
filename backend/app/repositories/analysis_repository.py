from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.analysis import Analysis, AnalysisStatus
from app.models.simulation import SimulationRun


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, user_id: str, input_url: str, normalized_url: str, status: AnalysisStatus) -> Analysis:
        analysis = Analysis(
            user_id=user_id,
            input_url=input_url,
            normalized_url=normalized_url,
            status=status.value if isinstance(status, AnalysisStatus) else status,
        )
        self.session.add(analysis)
        self.session.flush()
        return analysis

    def get_by_id_for_user(self, analysis_id: str, user_id: str) -> Analysis | None:
        stmt = (
            select(Analysis)
            .where(Analysis.id == analysis_id, Analysis.user_id == user_id)
            .options(
                joinedload(Analysis.extracted_product_data),
                selectinload(Analysis.icp_profiles),
                selectinload(Analysis.scenarios),
                selectinload(Analysis.simulation_runs).selectinload(SimulationRun.results),
            )
        )
        return self.session.scalar(stmt)

    def list_for_user(self, user_id: str) -> list[Analysis]:
        stmt = select(Analysis).where(Analysis.user_id == user_id).order_by(desc(Analysis.created_at))
        return list(self.session.scalars(stmt))

    def get_latest_by_user_and_url(self, user_id: str, normalized_url: str) -> Analysis | None:
        stmt = (
            select(Analysis)
            .where(Analysis.user_id == user_id, Analysis.normalized_url == normalized_url)
            .order_by(desc(Analysis.created_at))
        )
        return self.session.scalar(stmt)

    def get_latest_completed_by_normalized_url(
        self,
        normalized_url: str,
        *,
        cache_hours: int,
    ) -> Analysis | None:
        min_completed_at = datetime.now(UTC) - timedelta(hours=cache_hours)
        stmt = (
            select(Analysis)
            .where(
                Analysis.normalized_url == normalized_url,
                Analysis.status == AnalysisStatus.completed.value,
                Analysis.completed_at.is_not(None),
                Analysis.completed_at >= min_completed_at,
            )
            .options(
                joinedload(Analysis.extracted_product_data),
                selectinload(Analysis.icp_profiles),
                selectinload(Analysis.scenarios),
                selectinload(Analysis.simulation_runs).selectinload(SimulationRun.results),
            )
            .order_by(desc(Analysis.completed_at))
        )
        return self.session.scalar(stmt)

    def mark_processing(self, analysis: Analysis) -> None:
        analysis.status = AnalysisStatus.processing.value
        analysis.started_at = datetime.now(UTC)

    def mark_completed(self, analysis: Analysis) -> None:
        analysis.status = AnalysisStatus.completed.value
        analysis.completed_at = datetime.now(UTC)
        analysis.error_message = None

    def mark_failed(self, analysis: Analysis, message: str) -> None:
        analysis.status = AnalysisStatus.failed.value
        analysis.error_message = message
        analysis.completed_at = datetime.now(UTC)
