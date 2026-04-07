import { AnalysisDetail, AnalysisListItem, ICPProfile, Scenario, SimulationRun, WorkflowStage } from "@/types/api";

const STAGES: WorkflowStage[] = [
  "product_understanding",
  "icp_profiles",
  "scenarios",
  "decision_flow",
  "final_review",
];

const STAGE_LABELS: Record<WorkflowStage, string> = {
  product_understanding: "Product Understanding",
  icp_profiles: "ICP Profiles",
  scenarios: "Suggested Scenarios",
  decision_flow: "Decision Flow",
  final_review: "Final Review",
};

export function createPendingAnalysisDetail(analysis: AnalysisListItem): AnalysisDetail {
  return {
    id: analysis.id,
    input_url: analysis.input_url,
    normalized_url: analysis.normalized_url,
    status: analysis.status,
    current_stage: analysis.current_stage,
    started_at: null,
    completed_at: analysis.completed_at,
    error_message: analysis.error_message,
    created_at: analysis.created_at,
    updated_at: analysis.created_at,
    workflow: {
      current_stage: analysis.current_stage,
      next_stage: nextStage(analysis.current_stage),
      steps: STAGES.map((stage) => ({
        stage,
        label: STAGE_LABELS[stage],
        status:
          stage === analysis.current_stage
            ? analysis.status === "queued"
              ? "not_started"
              : "processing"
            : "not_started",
        is_current: stage === analysis.current_stage,
        is_complete: false,
        started_at: null,
        completed_at: null,
        edited: false,
        error_message: null,
      })),
      available_actions: [],
    },
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

export function nextStage(stage: WorkflowStage): WorkflowStage | null {
  const index = STAGES.indexOf(stage);
  if (index === -1 || index >= STAGES.length - 1) return null;
  return STAGES[index + 1];
}
