import { apiRequest } from "@/api/client";
import {
  AnalysisCreateResponse,
  AnalysisDetail,
  AnalysisListItem,
  FeedbackEvent,
  FeedbackPayload,
  SimulationRun,
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

export function submitFeedback(payload: FeedbackPayload) {
  return apiRequest<FeedbackEvent>("/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
