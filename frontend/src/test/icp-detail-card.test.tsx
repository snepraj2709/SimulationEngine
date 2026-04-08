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
    expect(screen.getByText(/Simulation impact/i)).toBeInTheDocument();
    expect(screen.getByText(/Pricing ->/i)).toBeInTheDocument();
    expect(screen.getByText(/Activation ->/i)).toBeInTheDocument();
    expect(screen.getByText(/Retention ->/i)).toBeInTheDocument();

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
    expect(screen.getAllByText(/\+2 more/i)).toHaveLength(2);

    expect(screen.getByText(/^36%$/i)).toBeInTheDocument();
    expect(screen.queryByText(/Source assumptions/i)).not.toBeInTheDocument();
  });
});
