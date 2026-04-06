import { AnalysisDetail, AnalysisListItem, ICPProfile, Scenario, SimulationRun } from "@/types/api";

export function createPendingAnalysisDetail(analysis: AnalysisListItem): AnalysisDetail {
  return {
    id: analysis.id,
    input_url: analysis.input_url,
    normalized_url: analysis.normalized_url,
    status: analysis.status,
    started_at: null,
    completed_at: analysis.completed_at,
    error_message: analysis.error_message,
    created_at: analysis.created_at,
    updated_at: analysis.created_at,
    extracted_product_data: null,
    icp_profiles: [],
    scenarios: [],
    simulation_runs: [],
  };
}

export function upsertAnalysisListItem(
  analyses: AnalysisListItem[] | undefined,
  analysis: AnalysisListItem,
): AnalysisListItem[] {
  const current = analyses ?? [];
  const withoutMatch = current.filter((item) => item.id !== analysis.id);
  return [analysis, ...withoutMatch];
}

export function getLatestRunForScenario(analysis: AnalysisDetail, scenarioId: string): SimulationRun | undefined {
  return [...analysis.simulation_runs]
    .filter((run) => run.scenario_id === scenarioId)
    .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())[0];
}

export function getScenarioById(analysis: AnalysisDetail, scenarioId: string): Scenario | undefined {
  return analysis.scenarios.find((scenario) => scenario.id === scenarioId);
}

export function getICPById(analysis: AnalysisDetail, icpId: string): ICPProfile | undefined {
  return analysis.icp_profiles.find((icp) => icp.id === icpId);
}

export function scenarioSummaries(analysis: AnalysisDetail) {
  return analysis.scenarios.map((scenario) => ({
    scenario,
    run: getLatestRunForScenario(analysis, scenario.id),
  }));
}
