import { type ImpactDirection, type Scenario, type ScenarioExpectedImpact, type ScenarioReviewView } from "@/types/api";

function titleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .split(" ")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function getScenarioReviewModel(scenario: Scenario): ScenarioReviewView {
  if (scenario.review_view) return scenario.review_view;

  return {
    id: scenario.id,
    scenario_type: scenario.scenario_type,
    scenario_title: scenario.title,
    scenario_summary: scenario.description,
    short_decision_statement: scenario.title,
    recommendation: {
      priority_rank: 1,
      recommendation_label: "Worth testing",
      recommendation_reason: "Detailed recommendation metadata is not available for this scenario yet.",
    },
    expected_impact: [],
    why_this_might_work: [],
    tradeoffs: [],
    execution_effort: {
      level: "medium",
      explanation: "Execution effort is not modeled yet for this scenario.",
    },
    linked_icp_summary: null,
    raw_parameters: scenario.input_parameters_json,
    metadata: {
      market: typeof scenario.input_parameters_json.market === "string" ? scenario.input_parameters_json.market : null,
      service_name: typeof scenario.input_parameters_json.service_name === "string" ? scenario.input_parameters_json.service_name : null,
      plan_tier: typeof scenario.input_parameters_json.plan_tier === "string" ? scenario.input_parameters_json.plan_tier : null,
      billing_period: typeof scenario.input_parameters_json.billing_period === "string" ? scenario.input_parameters_json.billing_period : null,
      scenario_tags: [titleCase(scenario.scenario_type)],
    },
  };
}

export function formatScenarioTypeLabel(value: string) {
  return titleCase(value);
}

export function formatImpactRange(impact: ScenarioExpectedImpact) {
  const min = impact.min_change_percent > 0 ? `+${impact.min_change_percent.toFixed(1)}` : impact.min_change_percent.toFixed(1);
  const max = impact.max_change_percent > 0 ? `+${impact.max_change_percent.toFixed(1)}` : impact.max_change_percent.toFixed(1);
  return `${min}% to ${max}%`;
}

export function getImpactDirectionTone(direction: ImpactDirection) {
  if (direction === "positive") {
    return {
      badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
      text: "text-emerald-800",
      surface: "bg-emerald-50/70",
    };
  }
  if (direction === "negative") {
    return {
      badge: "border-rose-200 bg-rose-50 text-rose-700",
      text: "text-rose-800",
      surface: "bg-rose-50/70",
    };
  }
  if (direction === "mixed") {
    return {
      badge: "border-amber-200 bg-amber-50 text-amber-700",
      text: "text-amber-800",
      surface: "bg-amber-50/70",
    };
  }
  return {
    badge: "border-slate-200 bg-slate-50 text-slate-600",
    text: "text-slate-700",
    surface: "bg-slate-50/70",
  };
}

export function getRecommendationTone(rank: number) {
  if (rank === 1) {
    return "border-sky-200 bg-sky-50 text-sky-700";
  }
  if (rank === 2) {
    return "border-violet-200 bg-violet-50 text-violet-700";
  }
  return "border-slate-200 bg-slate-50 text-slate-700";
}
