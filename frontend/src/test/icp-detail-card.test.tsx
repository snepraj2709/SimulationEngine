import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ICPDetailCard } from "@/components/analysis/ICPDetailCard";
import { ICPProfile } from "@/types/api";

const icp: ICPProfile = {
  id: "icp-1",
  analysis_id: "analysis-1",
  display_order: 0,
  is_user_edited: false,
  edited_at: null,
  name: "Founder-led SaaS consolidator",
  description: "Early-stage B2B SaaS teams replacing support and feedback sprawl with one operating layer.",
  use_case: "Consolidate support, feedback, and roadmap updates in one lightweight workflow.",
  goals_json: ["Reduce tool sprawl", "Respond without hiring support ops", "Capture requests in one place"],
  pain_points_json: ["Seat-heavy pricing grows fast", "Long setup delays adoption", "Manual follow-up after releases"],
  decision_drivers_json: ["value_for_money", "implementation_complexity", "convenience", "team_enablement"],
  driver_weights_json: {
    value_for_money: 0.36,
    implementation_complexity: 0.24,
    convenience: 0.18,
    team_enablement: 0.12,
  },
  price_sensitivity: 0.8,
  switching_cost: 0.2,
  alternatives_json: ["Intercom Starter", "Notion + Slack + forms"],
  churn_threshold: -0.28,
  retention_threshold: 0.11,
  adoption_friction: 0.7,
  value_perception_explanation: "Visible value in the first week and low setup burden keep this segment engaged.",
  segment_weight: 0.3,
  view_model: {
    id: "icp-1",
    segment_name: "Founder-led SaaS consolidator",
    segment_summary: "Early-stage B2B SaaS teams replacing support and feedback sprawl with one operating layer.",
    estimated_segment_share: 30,
    confidence: { score: 0.84, label: "high", source: "derived" },
    best_fit_use_case: "Consolidate support, feedback, and roadmap updates in one lightweight workflow.",
    buying_logic: {
      buys_for: ["Reduce tool sprawl", "Respond without hiring support ops"],
      avoids_because: ["Seat-heavy pricing grows fast", "Long setup delays adoption"],
      wins_with: ["Visible value in the first week", "Low setup burden keeps the team engaged"],
    },
    behavioral_signals: [
      { signal_key: "priceSensitivity", label: "Price Sensitivity", value_1_to_5: 4, editable: true, derived: false, source_field: "price_sensitivity" },
      { signal_key: "switchingFriction", label: "Switching Friction", value_1_to_5: 2, editable: true, derived: false, source_field: "switching_cost" },
      { signal_key: "timeToValueExpectation", label: "Time-to-Value Expectation", value_1_to_5: 5, editable: false, derived: true, source_field: null },
      { signal_key: "proofRequirement", label: "Proof Requirement", value_1_to_5: 4, editable: true, derived: false, source_field: "retention_threshold" },
      { signal_key: "implementationTolerance", label: "Implementation Tolerance", value_1_to_5: 2, editable: true, derived: true, source_field: "adoption_friction" },
      { signal_key: "retentionStability", label: "Retention Stability", value_1_to_5: 2, editable: true, derived: true, source_field: "churn_threshold" },
    ],
    decision_drivers: [
      { key: "value_for_money", label: "Value For Money", weight_percent: 36, rank: 1 },
      { key: "implementation_complexity", label: "Implementation Complexity", weight_percent: 24, rank: 2 },
      { key: "convenience", label: "Convenience", weight_percent: 18, rank: 3 },
    ],
    simulation_impact: [
      { title: "Pricing changes will strongly affect conversion", explanation: "High price sensitivity makes offer changes visible quickly.", severity: "high" },
      { title: "Activation depends on fast proof", explanation: "The segment expects value in the first week.", severity: "medium" },
      { title: "Retention is vulnerable to weak rollout", explanation: "Trust and rollout quality shape renewal behavior.", severity: "high" },
    ],
    editable_fields: [],
  },
};

describe("ICPDetailCard", () => {
  it("renders the detail card as a compact simulation-assumption view", () => {
    render(<ICPDetailCard icp={icp} isConfirmed onConfirm={() => undefined} onEdit={() => undefined} />);

    expect(screen.getByText(/ICP segment/i)).toBeInTheDocument();
    expect(screen.getByText(/Founder-led SaaS consolidator/i)).toBeInTheDocument();
    expect(screen.getByText(/30% share/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Confirmed/i)).toHaveLength(2);

    expect(screen.getByText(/^Buys for$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Avoids because$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Wins with$/i)).toBeInTheDocument();

    expect(screen.getByText(/Behavioral signals/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Price Sensitivity 4 out of 5/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Time-to-Value Expectation 5 out of 5/i)).toBeInTheDocument();
    expect(screen.getByText(/Simulation impact/i)).toBeInTheDocument();
    expect(screen.getByText(/Pricing changes will strongly affect conversion/i)).toBeInTheDocument();
    expect(screen.getByText(/Activation depends on fast proof/i)).toBeInTheDocument();
    expect(screen.getByText(/Retention is vulnerable to weak rollout/i)).toBeInTheDocument();

    expect(screen.getByText(/Decision drivers/i)).toBeInTheDocument();
    expect(screen.getByText(/^#1$/)).toBeInTheDocument();
    expect(screen.getByText(/^Value For Money$/i)).toBeInTheDocument();
    const sourceAccordion = screen.getByText(/Source assumptions/i).closest("details");
    expect(sourceAccordion).not.toBeNull();
    expect(sourceAccordion).not.toHaveAttribute("open");
  });

  it("renders the summary variant with compact drivers and compare action", () => {
    render(
      <ICPDetailCard
        icp={icp}
        variant="summary"
        isCompared
        showCompare
        onConfirm={() => undefined}
        onEdit={() => undefined}
        onToggleCompare={() => undefined}
      />,
    );

    expect(screen.getByText(/In compare/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^compare$/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^compared$/i })).toBeInTheDocument();
    expect(screen.getAllByText(/\+1 more/i).length).toBeGreaterThan(0);

    expect(screen.getByText(/^36%$/i)).toBeInTheDocument();
    expect(screen.queryByText(/Source assumptions/i)).not.toBeInTheDocument();
  });
});
