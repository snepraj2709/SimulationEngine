from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.common import ORMModel
from app.schemas.product import ExtractedProductDataResponse
from app.schemas.simulation import ICPProfileResponse, ScenarioResponse, SimulationRunResponse

WorkflowStage = Literal[
    "product_understanding",
    "icp_profiles",
    "scenarios",
    "decision_flow",
    "final_review",
]
WorkflowStepStatus = Literal["not_started", "processing", "awaiting_review", "completed", "failed", "stale"]


class AnalysisCreateRequest(BaseModel):
    url: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    force_refresh: bool = False
    run_async: bool = True


class WorkflowStepResponse(BaseModel):
    stage: WorkflowStage
    label: str
    status: WorkflowStepStatus
    is_current: bool
    is_complete: bool
    started_at: datetime | None = None
    completed_at: datetime | None = None
    edited: bool = False
    error_message: str | None = None


class AnalysisWorkflowResponse(BaseModel):
    current_stage: WorkflowStage
    next_stage: WorkflowStage | None = None
    steps: list[WorkflowStepResponse] = Field(default_factory=list)
    available_actions: list[str] = Field(default_factory=list)


class AnalysisListItemResponse(ORMModel):
    id: str
    input_url: str
    normalized_url: str
    status: str
    current_stage: WorkflowStage
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
    current_stage: WorkflowStage
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    workflow: AnalysisWorkflowResponse
    extracted_product_data: ExtractedProductDataResponse | None = None
    icp_profiles: list[ICPProfileResponse] = Field(default_factory=list)
    scenarios: list[ScenarioResponse] = Field(default_factory=list)
    simulation_runs: list[SimulationRunResponse] = Field(default_factory=list)


class WorkflowProceedRequest(BaseModel):
    expected_stage: WorkflowStage
    run_async: bool = True


class WorkflowReopenRequest(BaseModel):
    stage: Literal["product_understanding", "icp_profiles", "scenarios"]
    entity_id: str | None = None
