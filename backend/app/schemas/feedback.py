from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class FeedbackCreateRequest(BaseModel):
    analysis_id: str
    scenario_id: str
    simulation_run_id: str
    feedback_type: Literal["thumbs_up", "thumbs_down"]
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(ORMModel):
    id: str
    user_id: str
    analysis_id: str
    scenario_id: str
    simulation_run_id: str
    feedback_type: str
    comment: str | None
    created_at: datetime
    updated_at: datetime
