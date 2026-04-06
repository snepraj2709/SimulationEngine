import { AnalysisDetail, ICPProfile, Scenario, SimulationRun } from "@/types/api";

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
