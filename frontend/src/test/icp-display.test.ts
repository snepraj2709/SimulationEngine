import { describe, expect, it } from "vitest";

import {
  formatIcpMetricPercent,
  getIcpMetricBand,
  getIcpMetricLabel,
  getIcpMetricRawValue,
  getIcpMetricUiValue,
} from "@/components/analysis/icpDisplay";

describe("icpDisplay metric helpers", () => {
  it("maps backend fields to founder-facing labels", () => {
    expect(getIcpMetricLabel("segment_weight")).toBe("Estimated segment share");
    expect(getIcpMetricLabel("switching_cost")).toBe("Switching resistance");
    expect(getIcpMetricLabel("churn_threshold")).toBe("Retention resilience");
    expect(getIcpMetricLabel("retention_threshold")).toBe("Expansion hurdle");
    expect(getIcpMetricLabel("adoption_friction")).toBe("Rollout effort");
  });

  it("formats segment share as a percentage", () => {
    expect(formatIcpMetricPercent(0.24)).toBe("24%");
    expect(formatIcpMetricPercent(0.333)).toBe("33.3%");
  });

  it("classifies direct-mapped traits into low medium and high bands", () => {
    expect(getIcpMetricBand(0.2, "price_sensitivity")).toBe("Low");
    expect(getIcpMetricBand(0.5, "switching_cost")).toBe("Medium");
    expect(getIcpMetricBand(0.8, "adoption_friction")).toBe("High");
  });

  it("inverts churn threshold so more negative values mean higher resilience", () => {
    expect(getIcpMetricUiValue("churn_threshold", -0.05)).toBe(0);
    expect(getIcpMetricUiValue("churn_threshold", -0.35)).toBe(100);
    expect(getIcpMetricBand(-0.05, "churn_threshold")).toBe("Low");
    expect(getIcpMetricBand(-0.35, "churn_threshold")).toBe("High");
    expect(getIcpMetricRawValue("churn_threshold", 100)).toBeCloseTo(-0.35, 3);
  });
});
