import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProductSummaryPanel } from "@/components/analysis/ProductSummaryPanel";
import { ExtractedProductData } from "@/types/api";

const productData: ExtractedProductData = {
  id: "product-1",
  analysis_id: "analysis-1",
  company_name: "Acme",
  product_name: "Acme Growth Platform",
  category: "B2B Software",
  subcategory: "Revenue Operations",
  positioning_summary: "Automates onboarding and revenue expansion workflows.",
  pricing_model: "sales_led_custom_pricing",
  monetization_hypothesis: "Annual contracts for revenue teams.",
  raw_extracted_json: {},
  normalized_json: {},
  view_model: {
    id: "product-1",
    company_name: "Acme",
    product_name: "Acme Growth Platform",
    summary_line: "Automates onboarding and revenue expansion workflows.",
    category: "B2B Software",
    subcategory: "Revenue Operations",
    confidence: 0.84,
    review_status: "needs_review",
    business_model_signals: [
      { key: "buyer_type", label: "Buyer Type", value: "Revenue teams", score_1_to_5: null, confidence: 0.82, editable: true },
      { key: "pricing_visibility", label: "Pricing Visibility", value: "Medium", score_1_to_5: 3, confidence: 0.78, editable: true },
    ],
    customer_logic: {
      core_job_to_be_done: "Automate onboarding and renewal workflows.",
      why_they_buy: ["Reduce manual work", "Improve renewal visibility"],
      why_they_hesitate: ["Implementation complexity"],
      what_it_replaces: ["spreadsheets", "point tools"],
    },
    monetization_model: {
      pricing_visibility: "medium",
      pricing_model: "sales_led_custom_pricing",
      monetization_hypothesis: "Annual contracts for revenue teams.",
      sales_motion: "Demo-led / enterprise sales",
    },
    feature_clusters: [
      { key: "workflow-automation", label: "workflow automation", importance: "high", description: "Automates lifecycle work." },
    ],
    simulation_levers: [
      { key: "pricing", label: "Pricing", why_it_matters: "Pricing affects conversion and renewals.", confidence: 0.8, editable: true },
    ],
    uncertainties: [
      {
        key: "pricing_visibility",
        label: "Pricing visibility",
        reason: "Public pricing is limited.",
        severity: "high",
        needs_user_review: true,
      },
    ],
    source_coverage: {
      fields_observed_explicitly: ["Company name"],
      fields_inferred: ["Deployment complexity"],
      fields_missing: ["Public pricing detail"],
    },
  },
  confidence_score: 0.84,
  is_user_edited: false,
  edited_at: null,
};

describe("ProductSummaryPanel", () => {
  it("renders the structured business interpretation layout", () => {
    render(<ProductSummaryPanel data={productData} />);

    expect(screen.getByText(/business interpretation/i)).toBeInTheDocument();
    expect(screen.getByText(/business model signals/i)).toBeInTheDocument();
    expect(screen.getByText(/customer logic/i)).toBeInTheDocument();
    expect(screen.getByText(/likely simulation levers/i)).toBeInTheDocument();
    expect(screen.getByText(/^Needs review$/)).toBeInTheDocument();
    expect(screen.getByText(/public pricing is limited/i)).toBeInTheDocument();
  });
});
