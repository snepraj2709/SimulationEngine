from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ExtractedProductData(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extracted_product_data"

    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    subcategory: Mapped[str] = mapped_column(Text, nullable=False)
    positioning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    pricing_model: Mapped[str] = mapped_column(Text, nullable=False)
    monetization_hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    raw_extracted_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    normalized_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_user_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    analysis = relationship("Analysis", back_populates="extracted_product_data")
