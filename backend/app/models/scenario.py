import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ScenarioType(str, enum.Enum):
    pricing_increase = "pricing_increase"
    pricing_decrease = "pricing_decrease"
    feature_removal = "feature_removal"
    premium_feature_addition = "premium_feature_addition"
    bundling = "bundling"
    unbundling = "unbundling"


class Scenario(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scenarios"
    __table_args__ = (Index("ix_scenarios_analysis", "analysis_id"),)

    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    scenario_type: Mapped[ScenarioType] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_parameters_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_user_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    analysis = relationship("Analysis", back_populates="scenarios")
    simulation_runs = relationship("SimulationRun", back_populates="scenario", cascade="all, delete-orphan")
