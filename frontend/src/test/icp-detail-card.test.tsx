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
  name: "Evaluation skeptic",
  description: "Needs proof before committing.",
  use_case: "Comparing the offer against alternatives.",
  goals_json: ["Reduce budget risk"],
  pain_points_json: ["Unclear ROI"],
  decision_drivers_json: ["price_affordability", "support_reliability", "team_enablement", "brand_habit"],
  driver_weights_json: {
    price_affordability: 0.28,
    support_reliability: 0.24,
    team_enablement: 0.18,
    brand_habit: 0.12,
  },
  price_sensitivity: 0.8,
  switching_cost: 0.3,
  alternatives_json: ["Competitor A"],
  churn_threshold: -0.2,
  retention_threshold: 0.1,
  adoption_friction: 0.4,
  value_perception_explanation: "Retains only when the value story is clear.",
  segment_weight: 0.24,
};

describe("ICPDetailCard", () => {
  it("uses the orange contrast palette for the third strongest signal", () => {
    render(<ICPDetailCard icp={icp} />);

    const thirdRankLabel = screen.getByText(/third strongest signal/i);
    expect(thirdRankLabel).toHaveClass("text-orange-800");

    const thirdRankCard = thirdRankLabel.closest("div")?.parentElement?.parentElement as HTMLElement | null;
    expect(thirdRankCard).not.toBeNull();
    expect(thirdRankCard).toHaveClass("border-orange-200", "bg-orange-50/70");

    const fillBar = thirdRankCard?.querySelector('div[style*="18%"]');
    expect(fillBar).not.toBeNull();
    expect(fillBar).toHaveClass("from-orange-500", "to-rose-500");
  });

  it("renders the expanded business-facing ICP sections", () => {
    render(<ICPDetailCard icp={icp} />);

    expect(screen.getByText(/^Goals$/i)).toBeInTheDocument();
    expect(screen.getByText(/reduce budget risk/i)).toBeInTheDocument();
    expect(screen.getByText(/^Pain points$/i)).toBeInTheDocument();
    expect(screen.getByText(/unclear roi/i)).toBeInTheDocument();
    expect(screen.getByText(/^Alternatives$/i)).toBeInTheDocument();
    expect(screen.getByText(/competitor a/i)).toBeInTheDocument();
    const segmentWeightMetric = screen.getByText(/^Estimated segment share$/i).closest("div");
    expect(segmentWeightMetric).toHaveTextContent("24%");
    expect(screen.getByText(/^Selected drivers$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Decision driver weights$/i)).toBeInTheDocument();
    expect(screen.getByText(/^High$/i)).toBeInTheDocument();
    expect(screen.getByText(/reacts strongly to pricing changes/i)).toBeInTheDocument();
    expect(screen.queryByText("0.80")).not.toBeInTheDocument();
    expect(screen.getByText(/^Switching resistance$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Retention resilience$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Expansion hurdle$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Rollout effort$/i)).toBeInTheDocument();
  });
});
