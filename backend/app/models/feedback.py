import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class FeedbackType(str, enum.Enum):
    thumbs_up = "thumbs_up"
    thumbs_down = "thumbs_down"


class FeedbackEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "feedback_events"
    __table_args__ = (
        Index("ix_feedback_user_run", "user_id", "simulation_run_id", unique=True),
        Index("ix_feedback_analysis", "analysis_id"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    simulation_run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    feedback_type: Mapped[FeedbackType] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = relationship("User", back_populates="feedback_events")
    analysis = relationship("Analysis", back_populates="feedback_events")
    simulation_run = relationship("SimulationRun", back_populates="feedback_events")
