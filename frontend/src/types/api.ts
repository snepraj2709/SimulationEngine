export type AnalysisStatus = "queued" | "processing" | "awaiting_review" | "completed" | "failed";
export type Reaction = "retain" | "upgrade" | "downgrade" | "churn";
export type FeedbackType = "thumbs_up" | "thumbs_down";
export type WorkflowStage =
  | "product_understanding"
  | "icp_profiles"
  | "scenarios"
  | "decision_flow"
  | "final_review";
export type WorkflowStepStatus = "not_started" | "processing" | "awaiting_review" | "completed" | "failed" | "stale";

export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface AnalysisListItem {
  id: string;
  input_url: string;
  normalized_url: string;
  status: AnalysisStatus;
  current_stage: WorkflowStage;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

export interface AnalysisCreateResponse {
  analysis: AnalysisListItem;
  reused: boolean;
  cloned_from_analysis_id: string | null;
}

export interface ExtractedProductData {
  id: string;
  analysis_id: string;
  company_name: string;
  product_name: string;
  category: string;
  subcategory: string;
  positioning_summary: string;
  pricing_model: string;
  monetization_hypothesis: string;
  raw_extracted_json: Record<string, unknown>;
  normalized_json: {
    company_name: string;
    product_name: string;
    category: string;
    subcategory: string;
    positioning_summary: string;
    pricing_model: string;
    feature_clusters: string[];
    monetization_hypothesis: string;
    target_customer_signals: string[];
    confidence_score: number;
    confidence_scores: Record<string, number>;
    warnings: string[];
  };
  confidence_score: number;
  is_user_edited: boolean;
  edited_at: string | null;
}

export interface ICPProfile {
  id: string;
  analysis_id: string;
  display_order: number;
  is_user_edited: boolean;
  edited_at: string | null;
  name: string;
  description: string;
  use_case: string;
  goals_json: string[];
  pain_points_json: string[];
  decision_drivers_json: string[];
  driver_weights_json: Record<string, number>;
  price_sensitivity: number;
  switching_cost: number;
  alternatives_json: string[];
  churn_threshold: number;
  retention_threshold: number;
  adoption_friction: number;
  value_perception_explanation: string;
  segment_weight: number;
}

export interface ScenarioInputField {
  key: string;
  label: string;
  input_type: "text" | "number";
  required: boolean;
  minimum: number | null;
  maximum: number | null;
  step: number | null;
  placeholder: string | null;
  helper_text: string | null;
}

export interface ScenarioInputSchema {
  fields: ScenarioInputField[];
}

export interface Scenario {
  id: string;
  analysis_id: string;
  display_order: number;
  is_user_edited: boolean;
  edited_at: string | null;
  title: string;
  scenario_type: string;
  description: string;
  input_parameters_json: Record<string, unknown>;
  input_parameters_schema: ScenarioInputSchema;
  created_at: string;
  updated_at: string;
}

export interface SimulationResult {
  id: string;
  simulation_run_id: string;
  icp_profile_id: string;
  reaction: Reaction;
  utility_score_before: number;
  utility_score_after: number;
  delta_score: number;
  revenue_delta: number;
  perception_shift: number;
  second_order_effects_json: string[];
  driver_impacts_json: Record<string, number>;
  explanation: string;
  created_at: string;
}

export interface ScenarioSimulationSummary {
  scenario_id: string;
  scenario_title: string;
  projected_retention_pct: number;
  projected_downgrade_pct: number;
  projected_upgrade_pct: number;
  projected_churn_pct: number;
  estimated_revenue_delta_pct: number;
  weighted_revenue_delta: number;
  perception_shift_score: number;
  perception_shift_label: string;
  highest_risk_icps: string[];
  top_negative_drivers: string[];
  top_positive_drivers: string[];
  second_order_effects: string[];
}

export interface SimulationRun {
  id: string;
  analysis_id: string;
  scenario_id: string;
  run_version: string;
  engine_version: string;
  assumptions_json: Record<string, unknown>;
  created_at: string;
  results: SimulationResult[];
  summary: ScenarioSimulationSummary;
}

export interface AnalysisDetail {
  id: string;
  input_url: string;
  normalized_url: string;
  status: AnalysisStatus;
  current_stage: WorkflowStage;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  workflow: AnalysisWorkflow;
  extracted_product_data: ExtractedProductData | null;
  icp_profiles: ICPProfile[];
  scenarios: Scenario[];
  simulation_runs: SimulationRun[];
}

export interface WorkflowStep {
  stage: WorkflowStage;
  label: string;
  status: WorkflowStepStatus;
  is_current: boolean;
  is_complete: boolean;
  started_at: string | null;
  completed_at: string | null;
  edited: boolean;
  error_message: string | null;
}

export interface AnalysisWorkflow {
  current_stage: WorkflowStage;
  next_stage: WorkflowStage | null;
  steps: WorkflowStep[];
  available_actions: string[];
}

export interface FeedbackPayload {
  analysis_id: string;
  scenario_id: string;
  simulation_run_id: string;
  feedback_type: FeedbackType;
  comment?: string;
}

export interface FeedbackEvent {
  id: string;
  user_id: string;
  analysis_id: string;
  scenario_id: string;
  simulation_run_id: string;
  feedback_type: FeedbackType;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    request_id: string;
    details?: Record<string, unknown>;
  };
}
