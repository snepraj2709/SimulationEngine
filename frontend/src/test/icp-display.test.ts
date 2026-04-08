import { describe, expect, it } from "vitest";

import {
  formatSegmentShare,
  getRawValueFromSignalLevel,
  getSignalLevelFromRaw,
  mapApiICPToCardModel,
} from "@/components/analysis/icpDisplay";
import { ICPProfile } from "@/types/api";

const icp: ICPProfile = {
  id: "icp-1",
  analysis_id: "analysis-1",
  display_order: 0,
  is_user_edited: false,
  edited_at: null,
  name: "Founder-led SaaS consolidator",
  description: "Early-stage B2B SaaS teams replacing support and feedback sprawl with one operating layer.",
  use_case: "Consolidate support, feedback, and updates in one lightweight workflow.",
  goals_json: ["Reduce tool sprawl", "Respond without hiring support ops"],
  pain_points_json: ["Seat-heavy pricing grows fast", "Long setup delays adoption"],
  decision_drivers_json: ["value_for_money", "implementation_complexity", "team_enablement"],
  driver_weights_json: {
    value_for_money: 0.4,
    implementation_complexity: 0.35,
    team_enablement: 0.25,
  },
  price_sensitivity: 0.8,
  switching_cost: 0.2,
  alternatives_json: ["Notion + Slack + forms"],
  churn_threshold: -0.32,
  retention_threshold: 0.12,
  adoption_friction: 0.8,
  value_perception_explanation: "Visible value in the first week keeps the team engaged.",
  segment_weight: 0.3,
};

describe("icpDisplay adapter", () => {
  it("maps raw ICP payloads into the card model", () => {
    const profile = mapApiICPToCardModel(icp, { isConfirmed: true });

    expect(profile.identity.name).toBe("Founder-led SaaS consolidator");
    expect(profile.identity.segmentSharePct).toBe(30);
    expect(profile.identity.statusLabel).toBe("Confirmed");
    expect(profile.buyingLogic.buysFor).toEqual(["Reduce tool sprawl", "Respond without hiring support ops"]);
    expect(profile.buyingLogic.avoidsBecause).toEqual(["Seat-heavy pricing grows fast", "Long setup delays adoption"]);
    expect(profile.decisionDrivers[0]).toMatchObject({
      key: "value_for_money",
      rank: 1,
      weightPct: 40,
    });
    expect(profile.simulationImpact).toHaveLength(3);
    expect(profile.simulationImpact[0].label).toMatch(/Pricing ->/);
  });

  it("uses inverse mappings for implementation tolerance and retention stability", () => {
    expect(getSignalLevelFromRaw("implementationTolerance", { adoption_friction: 0.1 } as ICPProfile)).toBe(5);
    expect(getSignalLevelFromRaw("implementationTolerance", { adoption_friction: 0.9 } as ICPProfile)).toBe(1);
    expect(getSignalLevelFromRaw("retentionStability", { churn_threshold: -0.05 } as ICPProfile)).toBe(1);
    expect(getSignalLevelFromRaw("retentionStability", { churn_threshold: -0.35 } as ICPProfile)).toBe(5);
  });

  it("round-trips signal levels back into backend-facing raw values", () => {
    expect(getRawValueFromSignalLevel("priceSensitivity", 4)).toBeCloseTo(0.75, 2);
    expect(getRawValueFromSignalLevel("switchingFriction", 2)).toBeCloseTo(0.25, 2);
    expect(getRawValueFromSignalLevel("proofRequirement", 5)).toBeCloseTo(0.15, 2);
    expect(getRawValueFromSignalLevel("implementationTolerance", 5)).toBeCloseTo(0, 2);
    expect(getRawValueFromSignalLevel("retentionStability", 5)).toBeCloseTo(-0.35, 2);
  });

  it("formats segment share as a percentage string", () => {
    expect(formatSegmentShare(30)).toBe("30%");
    expect(formatSegmentShare(33.3)).toBe("33.3%");
  });

  it("prefers backend view models when present", () => {
    const profile = mapApiICPToCardModel({
      ...icp,
      view_model: {
        id: "icp-1",
        segment_name: "Founder-led SaaS consolidator",
        segment_summary: "Early-stage teams replacing support and feedback sprawl with one operating layer.",
        estimated_segment_share: 30,
        confidence: { score: 0.82, label: "high", source: "derived" },
        best_fit_use_case: "Consolidate support, feedback, and updates in one lightweight workflow.",
        buying_logic: {
          buys_for: ["Reduce tool sprawl"],
          avoids_because: ["Long setup delays adoption"],
          wins_with: ["Visible value in the first week"],
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
          { key: "value_for_money", label: "Value For Money", weight_percent: 40, rank: 1 },
        ],
        simulation_impact: [
          { title: "Pricing changes will strongly affect conversion", explanation: "High price sensitivity makes pricing more visible in evaluation.", severity: "high" },
          { title: "Activation depends on fast proof", explanation: "The segment expects value quickly.", severity: "medium" },
          { title: "Retention is vulnerable to weak rollout", explanation: "Trust and proof quality shape renewal behavior.", severity: "high" },
        ],
        editable_fields: [],
      },
    }, { isConfirmed: true });

    expect(profile.identity.confidence?.label).toBe("High");
    expect(profile.signals.some((signal) => signal.key === "timeToValueExpectation")).toBe(true);
    expect(profile.simulationImpact[0].label).toBe("Pricing changes will strongly affect conversion");
  });
});
