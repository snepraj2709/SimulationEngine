from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import ORMModel
from app.schemas.product import ExtractedProductDataResponse
from app.schemas.simulation import ICPProfileResponse, ScenarioResponse, SimulationRunResponse


class AnalysisCreateRequest(BaseModel):
    url: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    force_refresh: bool = False
    run_async: bool = True


class AnalysisListItemResponse(ORMModel):
    id: str
    input_url: str
    normalized_url: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None


class AnalysisCreateResponse(BaseModel):
    analysis: AnalysisListItemResponse
    reused: bool = False
    cloned_from_analysis_id: str | None = None


class AnalysisDetailResponse(ORMModel):
    id: str
    input_url: str
    normalized_url: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    extracted_product_data: ExtractedProductDataResponse | None = None
    icp_profiles: list[ICPProfileResponse] = Field(default_factory=list)
    scenarios: list[ScenarioResponse] = Field(default_factory=list)
    simulation_runs: list[SimulationRunResponse] = Field(default_factory=list)
