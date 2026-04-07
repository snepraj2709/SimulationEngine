from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Literal


WorkflowStage = Literal[
    "product_understanding",
    "icp_profiles",
    "scenarios",
    "decision_flow",
    "final_review",
]
WorkflowStepStatus = Literal[
    "not_started",
    "processing",
    "awaiting_review",
    "completed",
    "failed",
    "stale",
]

WORKFLOW_STAGES: tuple[WorkflowStage, ...] = (
    "product_understanding",
    "icp_profiles",
    "scenarios",
    "decision_flow",
    "final_review",
)

WORKFLOW_STAGE_LABELS: dict[WorkflowStage, str] = {
    "product_understanding": "Product Understanding",
    "icp_profiles": "ICP Profiles",
    "scenarios": "Suggested Scenarios",
    "decision_flow": "Decision Flow",
    "final_review": "Final Review",
}


def default_workflow_state() -> dict[str, dict[str, str | bool | None]]:
    return {
        stage: {
            "status": "not_started",
            "started_at": None,
            "completed_at": None,
            "edited": False,
            "error_message": None,
        }
        for stage in WORKFLOW_STAGES
    }


def final_review_workflow_state() -> dict[str, dict[str, str | bool | None]]:
    state = default_workflow_state()
    timestamp = _now()
    for stage in WORKFLOW_STAGES:
        state[stage] = {
            "status": "completed",
            "started_at": timestamp,
            "completed_at": timestamp,
            "edited": False,
            "error_message": None,
        }
    return state


def ensure_workflow_state(raw_state: dict | None) -> dict[str, dict[str, str | bool | None]]:
    state = default_workflow_state()
    if not raw_state:
        return state
    for stage in WORKFLOW_STAGES:
        payload = raw_state.get(stage, {})
        state[stage] = {
            "status": str(payload.get("status", state[stage]["status"])),
            "started_at": payload.get("started_at"),
            "completed_at": payload.get("completed_at"),
            "edited": bool(payload.get("edited", state[stage]["edited"])),
            "error_message": payload.get("error_message"),
        }
    return state


def next_stage(stage: WorkflowStage) -> WorkflowStage | None:
    try:
        index = WORKFLOW_STAGES.index(stage)
    except ValueError:
        return None
    if index >= len(WORKFLOW_STAGES) - 1:
        return None
    return WORKFLOW_STAGES[index + 1]


def previous_stage(stage: WorkflowStage) -> WorkflowStage | None:
    try:
        index = WORKFLOW_STAGES.index(stage)
    except ValueError:
        return None
    if index == 0:
        return None
    return WORKFLOW_STAGES[index - 1]


def mark_processing(raw_state: dict | None, stage: WorkflowStage) -> dict[str, dict[str, str | bool | None]]:
    state = ensure_workflow_state(raw_state)
    started_at = state[stage]["started_at"] or _now()
    state[stage] = {
        **state[stage],
        "status": "processing",
        "started_at": started_at,
        "completed_at": None,
        "error_message": None,
    }
    return state


def mark_awaiting_review(
    raw_state: dict | None,
    stage: WorkflowStage,
    *,
    edited: bool | None = None,
) -> dict[str, dict[str, str | bool | None]]:
    state = ensure_workflow_state(raw_state)
    timestamp = _now()
    state[stage] = {
        **state[stage],
        "status": "awaiting_review",
        "started_at": state[stage]["started_at"] or timestamp,
        "completed_at": timestamp,
        "error_message": None,
        "edited": state[stage]["edited"] if edited is None else edited,
    }
    return state


def mark_completed(
    raw_state: dict | None,
    stage: WorkflowStage,
) -> dict[str, dict[str, str | bool | None]]:
    state = ensure_workflow_state(raw_state)
    timestamp = _now()
    state[stage] = {
        **state[stage],
        "status": "completed",
        "started_at": state[stage]["started_at"] or timestamp,
        "completed_at": timestamp,
        "error_message": None,
    }
    return state


def mark_failed(
    raw_state: dict | None,
    stage: WorkflowStage,
    message: str,
) -> dict[str, dict[str, str | bool | None]]:
    state = ensure_workflow_state(raw_state)
    timestamp = _now()
    state[stage] = {
        **state[stage],
        "status": "failed",
        "started_at": state[stage]["started_at"] or timestamp,
        "completed_at": timestamp,
        "error_message": message,
    }
    return state


def mark_edited(
    raw_state: dict | None,
    stage: WorkflowStage,
) -> dict[str, dict[str, str | bool | None]]:
    state = ensure_workflow_state(raw_state)
    state[stage] = {
        **state[stage],
        "edited": True,
        "status": "awaiting_review",
        "completed_at": state[stage]["completed_at"] or _now(),
        "error_message": None,
    }
    return state


def mark_downstream_stale(
    raw_state: dict | None,
    stage: WorkflowStage,
) -> dict[str, dict[str, str | bool | None]]:
    state = ensure_workflow_state(raw_state)
    current_index = WORKFLOW_STAGES.index(stage)
    for stale_stage in WORKFLOW_STAGES[current_index + 1 :]:
        state[stale_stage] = {
            **state[stale_stage],
            "status": "stale",
            "started_at": None,
            "completed_at": None,
            "error_message": None,
        }
    return state


def reset_from_stage(
    raw_state: dict | None,
    stage: WorkflowStage,
) -> dict[str, dict[str, str | bool | None]]:
    state = ensure_workflow_state(raw_state)
    current_index = WORKFLOW_STAGES.index(stage)
    for reset_stage in WORKFLOW_STAGES[current_index:]:
        previous = state[reset_stage]
        state[reset_stage] = {
            "status": "not_started" if reset_stage != stage else "awaiting_review",
            "started_at": None if reset_stage != stage else previous.get("started_at"),
            "completed_at": None if reset_stage != stage else previous.get("completed_at") or _now(),
            "edited": bool(previous.get("edited", False)),
            "error_message": None,
        }
    return state


def clone_workflow_state(raw_state: dict | None) -> dict[str, dict[str, str | bool | None]]:
    return deepcopy(ensure_workflow_state(raw_state))


def _now() -> str:
    return datetime.now(UTC).isoformat()
