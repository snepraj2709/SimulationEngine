import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class SimulationReaction(str, enum.Enum):
    retain = "retain"
    upgrade = "upgrade"
    downgrade = "downgrade"
    churn = "churn"


class SimulationRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "simulation_runs"
    __table_args__ = (Index("ix_simulation_runs_analysis_scenario", "analysis_id", "scenario_id"),)

    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    run_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1")
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False, default="utility-v1")
    assumptions_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    analysis = relationship("Analysis", back_populates="simulation_runs")
    scenario = relationship("Scenario", back_populates="simulation_runs")
    results = relationship("SimulationResult", back_populates="simulation_run", cascade="all, delete-orphan")
    feedback_events = relationship("FeedbackEvent", back_populates="simulation_run")


class SimulationResult(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "simulation_results"
    __table_args__ = (
        Index("ix_simulation_results_run", "simulation_run_id"),
        Index("ix_simulation_results_icp", "icp_profile_id"),
    )

    simulation_run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    icp_profile_id: Mapped[str] = mapped_column(ForeignKey("icp_profiles.id", ondelete="CASCADE"), nullable=False)
    reaction: Mapped[SimulationReaction] = mapped_column(String(32), nullable=False)
    utility_score_before: Mapped[float] = mapped_column(Float, nullable=False)
    utility_score_after: Mapped[float] = mapped_column(Float, nullable=False)
    delta_score: Mapped[float] = mapped_column(Float, nullable=False)
    revenue_delta: Mapped[float] = mapped_column(Float, nullable=False)
    perception_shift: Mapped[float] = mapped_column(Float, nullable=False)
    second_order_effects_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    driver_impacts_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    simulation_run = relationship("SimulationRun", back_populates="results")
    icp_profile = relationship("ICPProfile", back_populates="simulation_results")
