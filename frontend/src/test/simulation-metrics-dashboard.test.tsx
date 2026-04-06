import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SimulationMetricsDashboard } from "@/components/analysis/SimulationMetricsDashboard";

describe("SimulationMetricsDashboard", () => {
  it("renders scenario metric labels", () => {
    render(
      <SimulationMetricsDashboard
        summaries={[
          {
            scenario_id: "scenario-1",
            scenario_title: "Increase premium plan price in India by 12%",
            projected_retention_pct: 61,
            projected_downgrade_pct: 18,
            projected_upgrade_pct: 4,
            projected_churn_pct: 17,
            estimated_revenue_delta_pct: 6.4,
            weighted_revenue_delta: 1200,
            perception_shift_score: -0.14,
            perception_shift_label: "negative",
            highest_risk_icps: ["Price-sensitive solo mobile viewer"],
            top_negative_drivers: ["price affordability"],
            top_positive_drivers: ["brand habit"],
            second_order_effects: ["increased plan comparison behavior"],
          },
        ]}
      />,
    );

    expect(screen.getByText(/increase premium plan price in india by 12%/i)).toBeInTheDocument();
    expect(screen.getAllByText(/retention/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/6.4%/i)).toBeInTheDocument();
  });
});
