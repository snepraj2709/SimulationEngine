import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ScenarioCard } from "@/components/analysis/ScenarioCard";
import { ScenarioReviewCard } from "@/components/analysis/ScenarioReviewCard";
import { type Scenario } from "@/types/api";

const scenario: Scenario = {
  id: "scenario-1",
  analysis_id: "analysis-1",
  display_order: 0,
  is_user_edited: false,
  edited_at: null,
  title: "Decrease annual price by 10%",
  scenario_type: "pricing_decrease",
  description: "Test whether a lower annual entry point increases evaluation among healthcare teams.",
  input_parameters_json: { price_change_percent: 10, market: "Healthcare" },
  input_parameters_schema: { fields: [] },
  review_view: {
    id: "scenario-1",
    scenario_type: "pricing_decrease",
    scenario_title: "Decrease annual price by 10%",
    scenario_summary: "Test whether a lower annual entry point increases evaluation among healthcare teams.",
    short_decision_statement: "Decrease annual pricing by 10% for healthcare teams.",
    recommendation: {
      priority_rank: 1,
      recommendation_label: "Recommended first",
      recommendation_reason: "Ranked #1 of 3: revenue is supportive while churn risk is neutral.",
    },
    expected_impact: [
      {
        metric_key: "revenue",
        label: "Revenue",
        direction: "positive",
        min_change_percent: 4,
        max_change_percent: 8,
        confidence: "high",
      },
      {
        metric_key: "conversion",
        label: "Conversion",
        direction: "positive",
        min_change_percent: 10,
        max_change_percent: 16,
        confidence: "medium",
      },
      {
        metric_key: "churn_risk",
        label: "Churn risk",
        direction: "neutral",
        min_change_percent: -1,
        max_change_percent: 1,
        confidence: "medium",
      },
    ],
    why_this_might_work: ["High price sensitivity means a lower entry point can change evaluation quickly."],
    tradeoffs: ["Lower pricing can anchor buyers to discount expectations."],
    execution_effort: {
      level: "low",
      explanation: "Pricing and packaging messaging can be tested without changing core delivery.",
    },
    linked_icp_summary: {
      segment_name: "Healthcare operations lead",
      relevant_signals: [
        {
          signal_key: "priceSensitivity",
          label: "Price Sensitivity",
          value_1_to_5: 4,
          editable: true,
          derived: false,
          source_field: "price_sensitivity",
        },
      ],
    },
    raw_parameters: { price_change_percent: 10, market: "Healthcare" },
    metadata: {
      market: "Healthcare",
      service_name: null,
      plan_tier: null,
      billing_period: null,
      scenario_tags: ["pricing", "conversion"],
    },
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe("ScenarioCard", () => {
  it("renders a compact decision-first summary card", () => {
    render(<ScenarioCard scenario={scenario} onSelect={() => undefined} onCompare={() => undefined} onRun={() => undefined} />);

    expect(screen.getByText(/recommended first/i)).toBeInTheDocument();
    expect(screen.getByText(/decrease annual pricing by 10% for healthcare teams/i)).toBeInTheDocument();
    expect(screen.getByText(/revenue/i)).toBeInTheDocument();
    expect(screen.getByText(/\+4.0% to \+8.0%/i)).toBeInTheDocument();
    expect(screen.getByText(/why this might work/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /run scenario/i })).toBeInTheDocument();
  });
});

describe("ScenarioReviewCard", () => {
  it("renders the detailed review layout with impact, reasoning, and trade-offs", () => {
    render(<ScenarioReviewCard scenario={scenario} />);

    expect(screen.getByText(/expected impact/i)).toBeInTheDocument();
    expect(screen.getByText(/recommended first/i)).toBeInTheDocument();
    expect(screen.getByText(/linked icp/i)).toBeInTheDocument();
    expect(screen.getByText(/trade-offs/i)).toBeInTheDocument();
    expect(screen.getByText(/secondary metadata/i)).toBeInTheDocument();
  });
});
