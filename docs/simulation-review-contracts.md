# Simulation Review Contracts

## Overview

The analysis detail payload now carries two layers of data for ICPs and scenarios:

- Raw editable entities:
  - `icp_profiles[]`
  - `scenarios[]`
- Nested review-ready view models:
  - `icp_profiles[].view_model`
  - `scenarios[].review_view`

The raw fields remain the source of truth for editing and persistence. The nested view models are additive and exist to reduce frontend transformation work for review and decision-support screens.

## ICP Contract

`icp_profiles[].view_model` includes:

- `segment_name`
- `segment_summary`
- `estimated_segment_share`
- `confidence`
- `best_fit_use_case`
- `buying_logic`
- `behavioral_signals`
- `decision_drivers`
- `simulation_impact`
- `editable_fields`

### Behavioral signal model

Signals are normalized to a compact `1..5` scale:

- `priceSensitivity`
- `switchingFriction`
- `timeToValueExpectation`
- `proofRequirement`
- `implementationTolerance`
- `retentionStability`

`timeToValueExpectation` is derived. The other signals map back to existing raw ICP fields.

### Editability model

Only simulation-relevant assumptions are exposed as quick-edit metadata:

- segment name
- segment share
- core behavioral signals
- top decision drivers

The raw descriptive/source fields still exist on the base ICP record and remain available behind progressive disclosure in the frontend edit sheet.

## Scenario Contract

`scenarios[].review_view` includes:

- `scenario_title`
- `scenario_summary`
- `short_decision_statement`
- `recommendation`
- `expected_impact`
- `why_this_might_work`
- `tradeoffs`
- `execution_effort`
- `linked_icp_summary`
- `raw_parameters`
- `metadata`

### Recommendation and ranking logic

Scenario ranking is derived in `backend/app/services/review_view_builder.py`.

The scorer combines:

- expected revenue movement
- expected conversion movement
- expected activation movement
- churn-risk penalty
- execution-effort modifier

This produces `priority_rank`, a `recommendation_label`, and a short `recommendation_reason`.

### Expected impact logic

Expected impacts are produced before a user runs a scenario by using the existing simulation engine and a lightweight heuristic layer. The contract intentionally surfaces compact decision metrics:

- revenue
- conversion
- churn risk
- activation speed

The existing full simulation run payload remains unchanged and is still used for post-run dashboards.

## Frontend Components

Key components introduced or refactored:

- `frontend/src/components/analysis/DotScaleIndicator.tsx`
- `frontend/src/components/analysis/ScenarioCard.tsx`
- `frontend/src/components/analysis/ScenarioReviewCard.tsx`
- `frontend/src/components/analysis/scenarioDisplay.ts`

The ICP side continues to use:

- `frontend/src/components/analysis/ICPDetailCard.tsx`
- `frontend/src/components/analysis/ICPCardGrid.tsx`
- `frontend/src/components/analysis/icpDisplay.ts`

## Migration Notes

- Existing API consumers that read raw `icp_profiles` and `scenarios` will continue to work.
- New UI should prefer `view_model` and `review_view` when present.
- Frontend fallback mapping still exists for older payloads and incomplete fixtures.
