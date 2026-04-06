import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AnalysisStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyses"
    __table_args__ = (
        Index("ix_analyses_user_created", "user_id", "created_at"),
        Index("ix_analyses_normalized_status", "normalized_url", "status"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    input_url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AnalysisStatus] = mapped_column(String(32), default=AnalysisStatus.queued.value, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="analyses")
    extracted_product_data = relationship(
        "ExtractedProductData",
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan",
    )
    icp_profiles = relationship("ICPProfile", back_populates="analysis", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="analysis", cascade="all, delete-orphan")
    simulation_runs = relationship("SimulationRun", back_populates="analysis", cascade="all, delete-orphan")
    feedback_events = relationship("FeedbackEvent", back_populates="analysis")
