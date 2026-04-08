# Simulation Review Contracts

## Overview

The analysis detail payload now carries review-oriented view models across the core simulation setup flow:

- `extracted_product_data.view_model`
- `icp_profiles[].view_model`
- `scenarios[].review_view`

These view models are additive. The raw persisted entities remain the source of truth for editing and downstream orchestration, while the nested models give the frontend compact, simulation-ready structures with less transformation work.

## Product Understanding Contract

`extracted_product_data.view_model` is the business interpretation layer that sits between website extraction and ICP generation.

Its purpose is not to restate scraped content. It translates crawl evidence into structured assumptions about:

- what the company likely sells
- who likely buys it
- how it is sold and monetized
- where adoption friction or expansion potential likely sits
- which variables should be exposed to scenario generation and simulation

### View model fields

`extracted_product_data.view_model` includes:

- `id`
- `company_name`
- `product_name`
- `summary_line`
- `category`
- `subcategory`
- `confidence`
- `review_status`
- `business_model_signals[]`
- `customer_logic`
- `monetization_model`
- `feature_clusters[]`
- `simulation_levers[]`
- `uncertainties[]`
- `source_coverage`

### Business model signal model

`business_model_signals[]` is a normalized list of compact business facts and inferences. Each signal includes:

- `key`
- `label`
- `value`
- `score_1_to_5`
- `confidence`
- `editable`

The current normalized signals are:

- `buyer_type`
- `sales_motion`
- `pricing_visibility`
- `deployment_complexity`
- `time_to_value`
- `workflow_criticality`
- `compliance_sensitivity`
- `switching_friction`
- `expansion_potential`
- `monetization_style`

Signals may use both a human-readable `value` and a compact `score_1_to_5`. The score is intended for dense UI rendering and later downstream heuristics.

### Customer logic model

`customer_logic` captures the minimum buyer reasoning needed before ICP generation:

- `core_job_to_be_done`
- `why_they_buy[]`
- `why_they_hesitate[]`
- `what_it_replaces[]`

This structure is intentionally terse. It should help the user validate the buying logic in seconds instead of reading long descriptive paragraphs.

### Monetization model

`monetization_model` separates commercial interpretation from the rest of the summary:

- `pricing_visibility`
- `pricing_model`
- `monetization_hypothesis`
- `sales_motion`

This block is used to distinguish clearly observed pricing detail from inferred go-to-market assumptions.

### Simulation lever model

`simulation_levers[]` captures the business variables that matter most for scenario generation and simulation.

Each lever includes:

- `key`
- `label`
- `why_it_matters`
- `confidence`
- `editable`

Current lever families include:

- pricing
- packaging
- deployment effort
- onboarding time
- automation coverage
- integration depth
- compliance readiness
- proof and case studies
- feature breadth

Levers are derived from the business signals, monetization interpretation, and customer hesitation patterns. They are meant to bridge Product Understanding directly into scenario design.

### Uncertainty model

`uncertainties[]` makes ambiguity explicit instead of burying it in a generic caveat block.

Each item includes:

- `key`
- `label`
- `reason`
- `severity`
- `needs_user_review`

Typical cases include:

- pricing not visible publicly
- buyer or deployment model inferred rather than observed
- product and company name ambiguity
- missing proof, compliance, or rollout evidence

### Source coverage model

`source_coverage` tracks how much of the interpretation came from direct evidence versus inference:

- `fields_observed_explicitly[]`
- `fields_inferred[]`
- `fields_missing[]`

This lets the UI show both what the system knows and what it is assuming before the user moves into ICP review.

### Derivation notes

The product interpretation pipeline is centered in:

- [backend/app/services/product_understanding_service.py](/Users/snehaprajapati/Desktop/Sneha_Develop/SimulationEngine/backend/app/services/product_understanding_service.py)
- [backend/app/services/llm/openai_analysis_service.py](/Users/snehaprajapati/Desktop/Sneha_Develop/SimulationEngine/backend/app/services/llm/openai_analysis_service.py)
- [backend/app/services/presenters.py](/Users/snehaprajapati/Desktop/Sneha_Develop/SimulationEngine/backend/app/services/presenters.py)

The current flow is:

1. Raw website evidence is scraped and normalized.
2. The LLM produces a structured business understanding payload.
3. `ProductUnderstandingService` backfills missing structure, normalizes signals, derives uncertainties, and generates simulation levers.
4. The presenter emits `view_model` for frontend review.

### Connection to ICP generation

The Product Understanding contract is upstream of ICP generation.

It improves ICP quality by giving the next stage normalized guidance on:

- likely buyer type
- likely sales motion
- pricing visibility and pricing sensitivity implications
- adoption friction and time-to-value expectations
- compliance or workflow criticality
- competitive replacement context

ICP generation should treat these fields as business priors rather than raw website excerpts.

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
