import { apiRequest } from "@/api/client";
import {
  AnalysisCreateResponse,
  AnalysisDetail,
  AnalysisListItem,
  FeedbackEvent,
  FeedbackPayload,
  ProductBusinessSignal,
  ProductCustomerLogic,
  ProductFeatureCluster,
  ProductMonetizationModel,
  ProductSimulationLever,
  ProductUncertainty,
  SimulationRun,
  WorkflowStage,
} from "@/types/api";

export function listAnalyses() {
  return apiRequest<AnalysisListItem[]>("/analyses");
}

export function createAnalysis(payload: { url: string; force_refresh?: boolean; run_async?: boolean }) {
  return apiRequest<AnalysisCreateResponse>("/analyses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getAnalysis(analysisId: string) {
  return apiRequest<AnalysisDetail>(`/analyses/${analysisId}`);
}

export function rerunScenario(
  analysisId: string,
  scenarioId: string,
  payload: { input_overrides?: Record<string, unknown>; run_version?: string },
) {
  return apiRequest<SimulationRun>(`/analyses/${analysisId}/scenarios/${scenarioId}/simulate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProductUnderstanding(
  analysisId: string,
  payload: {
    company_name: string;
    product_name: string;
    summary_line: string;
    category: string;
    subcategory: string;
    buyer_type: string;
    business_model_signals: ProductBusinessSignal[];
    customer_logic: ProductCustomerLogic;
    monetization_model: ProductMonetizationModel;
    feature_clusters: ProductFeatureCluster[];
    simulation_levers: ProductSimulationLever[];
    uncertainties: ProductUncertainty[];
  },
) {
  return apiRequest<AnalysisDetail>(`/analyses/${analysisId}/product-understanding`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateIcpProfile(
  analysisId: string,
  icpId: string,
  payload: {
    name: string;
    description: string;
    use_case: string;
    goals: string[];
    pain_points: string[];
    decision_drivers: string[];
    driver_weights: { driver: string; weight: number }[];
    price_sensitivity: number;
    switching_cost: number;
    alternatives: string[];
    churn_threshold: number;
    retention_threshold: number;
    adoption_friction: number;
    value_perception_explanation: string;
    segment_weight: number;
  },
) {
  return apiRequest<AnalysisDetail>(`/analyses/${analysisId}/icp-profiles/${icpId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function updateScenario(
  analysisId: string,
  scenarioId: string,
  payload: {
    title: string;
    scenario_type: string;
    description: string;
    input_parameters: Record<string, unknown>;
  },
) {
  return apiRequest<AnalysisDetail>(`/analyses/${analysisId}/scenarios/${scenarioId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function proceedWorkflow(
  analysisId: string,
  payload: {
    expected_stage: WorkflowStage;
    run_async?: boolean;
  },
) {
  return apiRequest<AnalysisDetail>(`/analyses/${analysisId}/workflow/proceed`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function reopenWorkflow(
  analysisId: string,
  payload: {
    stage: Extract<WorkflowStage, "product_understanding" | "icp_profiles" | "scenarios">;
    entity_id?: string | null;
  },
) {
  return apiRequest<AnalysisDetail>(`/analyses/${analysisId}/workflow/reopen`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function submitFeedback(payload: FeedbackPayload) {
  return apiRequest<FeedbackEvent>("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
