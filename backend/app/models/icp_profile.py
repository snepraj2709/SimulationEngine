from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ICPProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "icp_profiles"
    __table_args__ = (Index("ix_icp_profiles_analysis", "analysis_id"),)

    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    use_case: Mapped[str] = mapped_column(Text, nullable=False)
    goals_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    pain_points_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    decision_drivers_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    driver_weights_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    price_sensitivity: Mapped[float] = mapped_column(Float, nullable=False)
    switching_cost: Mapped[float] = mapped_column(Float, nullable=False)
    alternatives_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    churn_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    retention_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    adoption_friction: Mapped[float] = mapped_column(Float, nullable=False)
    value_perception_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    segment_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_user_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    analysis = relationship("Analysis", back_populates="icp_profiles")
    simulation_results = relationship("SimulationResult", back_populates="icp_profile")
