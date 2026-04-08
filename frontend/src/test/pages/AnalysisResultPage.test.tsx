import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createAnalysis, updateIcpProfile } from "@/api/analyses";
import { AnalysisResultPage } from "@/pages/AnalysisResultPage";
import { useAuthStore } from "@/store/auth-store";
import { useUIStore } from "@/store/ui-store";
import { AnalysisDetail, AnalysisWorkflow, ICPProfile, WorkflowStepStatus } from "@/types/api";

const mockUseAnalysisPolling = vi.fn();

vi.mock("@/api/analyses", async () => {
  const actual = await vi.importActual<typeof import("@/api/analyses")>("@/api/analyses");
  return {
    ...actual,
    createAnalysis: vi.fn().mockResolvedValue({
      analysis: {
        id: "analysis-2",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example/",
        status: "queued",
        current_stage: "product_understanding",
        created_at: new Date().toISOString(),
        completed_at: null,
        error_message: null,
      },
      reused: false,
      cloned_from_analysis_id: null,
    }),
    updateIcpProfile: vi.fn(),
  };
});

vi.mock("@/hooks/use-analysis-polling", () => ({
  useAnalysisPolling: (analysisId: string) => mockUseAnalysisPolling(analysisId),
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/analyses/analysis-1"]}>
        <Routes>
          <Route path="/analyses/:analysisId" element={<AnalysisResultPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function buildWorkflow(currentStage: "product_understanding" | "icp_profiles" | "scenarios" | "decision_flow" | "final_review"): AnalysisWorkflow {
  const order = [
    ["product_understanding", "Product Understanding"],
    ["icp_profiles", "ICP Profiles"],
    ["scenarios", "Suggested Scenarios"],
    ["decision_flow", "Decision Flow"],
    ["final_review", "Final Review"],
  ] as const;
  const currentIndex = order.findIndex(([stage]) => stage === currentStage);
  return {
    current_stage: currentStage,
    next_stage: order[currentIndex + 1]?.[0] ?? null,
    available_actions: [],
    steps: order.map(([stage, label], index) => ({
      stage,
      label,
      status: (
        index < currentIndex ? "completed" : index === currentIndex ? (currentStage === "final_review" ? "completed" : "awaiting_review") : "not_started"
      ) as WorkflowStepStatus,
      is_current: index === currentIndex,
      is_complete: index < currentIndex || currentStage === "final_review",
      started_at: null,
      completed_at: null,
      edited: false,
      error_message: null,
    })),
  };
}

function buildIcpProfile(overrides: Partial<ICPProfile> = {}): ICPProfile {
  return {
    id: "icp-1",
    analysis_id: "analysis-1",
    display_order: 0,
    is_user_edited: false,
    edited_at: null,
    name: "Revenue operations lead",
    description: "Owns retention tooling.",
    use_case: "Standardize renewals.",
    goals_json: ["Reduce churn", "Improve forecasting"],
    pain_points_json: ["Disconnected tooling", "Manual handoffs"],
    decision_drivers_json: ["team_enablement", "analytics_depth", "automation_coverage"],
    driver_weights_json: { team_enablement: 0.4, analytics_depth: 0.35, automation_coverage: 0.25 },
    price_sensitivity: 0.4,
    switching_cost: 0.5,
    alternatives_json: ["CRM", "Spreadsheet workflow"],
    churn_threshold: -0.2,
    retention_threshold: 0.07,
    adoption_friction: 0.2,
    value_perception_explanation: "Needs strong workflow breadth.",
    segment_weight: 1,
    ...overrides,
  };
}

function buildIcpStageDetail(icps: ICPProfile[] = [buildIcpProfile()], overrides: Partial<AnalysisDetail> = {}): AnalysisDetail {
  return {
    id: "analysis-1",
    input_url: "https://acme.example/",
    normalized_url: "https://acme.example",
    status: "awaiting_review",
    current_stage: "icp_profiles",
    started_at: new Date().toISOString(),
    completed_at: null,
    error_message: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    workflow: buildWorkflow("icp_profiles"),
    extracted_product_data: null,
    icp_profiles: icps,
    scenarios: [],
    simulation_runs: [],
    ...overrides,
  };
}

function buildProductUnderstandingData(
  overrides: Partial<NonNullable<AnalysisDetail["extracted_product_data"]>> = {},
): NonNullable<AnalysisDetail["extracted_product_data"]> {
  return {
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
        { key: "sales_motion", label: "Sales Motion", value: "Demo-led / enterprise sales", score_1_to_5: null, confidence: 0.81, editable: true },
        { key: "pricing_visibility", label: "Pricing Visibility", value: "Medium", score_1_to_5: 3, confidence: 0.8, editable: true },
        { key: "deployment_complexity", label: "Deployment Complexity", value: "High", score_1_to_5: 4, confidence: 0.78, editable: true },
      ],
      customer_logic: {
        core_job_to_be_done: "Automate onboarding and revenue expansion workflows.",
        why_they_buy: ["Reduce manual work", "Improve renewal visibility"],
        why_they_hesitate: ["Implementation complexity", "Pricing is not fully visible"],
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
        { key: "renewal-analytics", label: "renewal analytics", importance: "high", description: "Tracks renewal health." },
      ],
      simulation_levers: [
        { key: "pricing", label: "Pricing", why_it_matters: "Pricing affects conversion and renewals.", confidence: 0.8, editable: true },
        { key: "deployment_effort", label: "Deployment Effort", why_it_matters: "Rollout friction affects activation.", confidence: 0.76, editable: true },
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
        fields_observed_explicitly: ["Company name", "Buyer audience"],
        fields_inferred: ["Deployment complexity"],
        fields_missing: ["Public pricing detail"],
      },
    },
    confidence_score: 0.84,
    is_user_edited: false,
    edited_at: null,
    ...overrides,
  };
}

function expectInDocumentOrder(elements: HTMLElement[]) {
  elements.reduce((previous, current) => {
    expect(previous.compareDocumentPosition(current) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    return current;
  });
}

describe("AnalysisResultPage", () => {
  beforeEach(() => {
    mockUseAnalysisPolling.mockReset();
    vi.mocked(updateIcpProfile).mockReset();
    useAuthStore.setState({
      token: "token",
      user: {
        id: "user-1",
        email: "architect@example.com",
        full_name: "Architect User",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    });
    useUIStore.setState({
      selectedScenarioId: "stale-scenario",
      selectedICPId: "stale-icp",
      compareICPIds: ["stale-icp"],
      compareScenarioIds: ["stale-scenario"],
    });
  });

  it("shows a queue-safe shimmer for queued analyses", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example",
        status: "queued",
        current_stage: "product_understanding",
        started_at: null,
        completed_at: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("product_understanding"),
        extracted_product_data: null,
        icp_profiles: [],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getByText(/preparing results for the submitted url/i)).toBeInTheDocument();
    expect(screen.getByText(/analysis workflow/i)).toBeInTheDocument();
    expect(screen.getByText(/^queued$/i)).toBeInTheDocument();
    expect(screen.getByText(/waiting for the extraction pipeline/i)).toBeInTheDocument();
    expect(useUIStore.getState().selectedScenarioId).toBeNull();
    expect(useUIStore.getState().selectedICPId).toBeNull();
    expect(useUIStore.getState().compareScenarioIds).toEqual([]);
  });

  it("keeps the status card for processing analyses", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example",
        status: "processing",
        current_stage: "product_understanding",
        started_at: new Date().toISOString(),
        completed_at: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("product_understanding"),
        extracted_product_data: null,
        icp_profiles: [],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getByText(/^processing$/i)).toBeInTheDocument();
    expect(screen.getByText(/scraping the site, inferring the product model, and generating simulation artifacts/i)).toBeInTheDocument();
  });

  it("renders only product understanding while the first stage is under review", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example",
        status: "awaiting_review",
        current_stage: "product_understanding",
        started_at: new Date().toISOString(),
        completed_at: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("product_understanding"),
        extracted_product_data: buildProductUnderstandingData(),
        icp_profiles: [],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getByText(/confirm the business interpretation/i)).toBeInTheDocument();
    expect(screen.getByText(/ready to review/i)).toBeInTheDocument();
    expect(screen.getByText(/confirm understanding and continue/i)).toBeInTheDocument();
    expect(screen.queryByText(/ready for review/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/who moves first when the offer changes/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/default simulations worth pressure-testing/i)).not.toBeInTheDocument();
  });

  it("shows full product text in Step 1 edit mode without truncating long fields", async () => {
    const user = userEvent.setup();
    const longPositioningSummary =
      "Featurebase positions itself as an all-in-one platform for customer support, feedback collection, product updates, and cross-functional follow-through with AI-assisted routing, a shared inbox, workflow automation, and centralized feedback operations for scaling teams.";
    const longPricingModel =
      "Likely SaaS subscription with a free entry option, annual team plans, premium feature upgrades, and custom enterprise pricing for larger rollouts.";

    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://featurebase.app/",
        normalized_url: "https://featurebase.app",
        status: "awaiting_review",
        current_stage: "product_understanding",
        started_at: new Date().toISOString(),
        completed_at: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("product_understanding"),
        extracted_product_data: buildProductUnderstandingData({
          company_name: "Featurebase",
          product_name: "Featurebase",
          category: "Customer Support and Feedback Software",
          subcategory: "AI-powered omnichannel support and product feedback platform",
          positioning_summary: longPositioningSummary,
          pricing_model: longPricingModel,
          monetization_hypothesis: "Recurring software subscriptions for support and product teams.",
          confidence_score: 0.89,
          view_model: {
            ...buildProductUnderstandingData().view_model,
            company_name: "Featurebase",
            product_name: "Featurebase",
            summary_line: longPositioningSummary,
            category: "Customer Support and Feedback Software",
            subcategory: "AI-powered omnichannel support and product feedback platform",
            confidence: 0.89,
            business_model_signals: [
              { key: "buyer_type", label: "Buyer Type", value: "Product and support teams", score_1_to_5: null, confidence: 0.84, editable: true },
              { key: "sales_motion", label: "Sales Motion", value: "Product-led self-serve", score_1_to_5: null, confidence: 0.82, editable: true },
              { key: "pricing_visibility", label: "Pricing Visibility", value: "Medium", score_1_to_5: 3, confidence: 0.8, editable: true },
              { key: "deployment_complexity", label: "Deployment Complexity", value: "Moderate", score_1_to_5: 3, confidence: 0.76, editable: true },
            ],
            monetization_model: {
              pricing_visibility: "medium",
              pricing_model: longPricingModel,
              monetization_hypothesis: "Recurring software subscriptions for support and product teams.",
              sales_motion: "Product-led self-serve",
            },
            customer_logic: {
              core_job_to_be_done: "Centralize support and feedback workflows.",
              why_they_buy: ["Shared inbox", "AI routing"],
              why_they_hesitate: ["Proof of ROI"],
              what_it_replaces: ["separate point tools"],
            },
            feature_clusters: [
              { key: "shared-inbox", label: "shared inbox", importance: "high", description: "Central support inbox." },
              { key: "feedback-workflows", label: "feedback workflows", importance: "high", description: "Collects and routes product feedback." },
            ],
            simulation_levers: [
              { key: "pricing", label: "Pricing", why_it_matters: "Price changes affect conversion.", confidence: 0.8, editable: true },
            ],
            uncertainties: [],
            source_coverage: {
              fields_observed_explicitly: ["Product summary"],
              fields_inferred: [],
              fields_missing: [],
            },
          },
        }),
        icp_profiles: [],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    await user.click(screen.getAllByRole("button", { name: /edit key assumptions/i })[0]);

    const positioningSummaryField = screen.getByLabelText(/summary line/i);
    const pricingModelField = screen.getByLabelText(/pricing model/i);

    expect(positioningSummaryField).toHaveValue(longPositioningSummary);
    expect(pricingModelField).toHaveValue(longPricingModel);
    expect(positioningSummaryField.tagName).toBe("TEXTAREA");
    expect(pricingModelField.tagName).toBe("TEXTAREA");
  });

  it("shows the review cue inside the ICP stage header instead of a separate status card", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: buildIcpStageDetail([
        buildIcpProfile({
          is_user_edited: true,
          edited_at: new Date().toISOString(),
        }),
      ]),
    });

    renderPage();

    expect(screen.getByText(/icp 1 of 1/i)).toBeInTheDocument();
    expect(screen.getByText(/reviewed by you/i)).toBeInTheDocument();
    expect(screen.queryByText(/ready for review/i)).not.toBeInTheDocument();
  });

  it("renders the compact simulation-oriented ICP review card before edit mode", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: buildIcpStageDetail(),
    });

    renderPage();

    expect(screen.getByText(/^Buys for$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Avoids because$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Wins with$/i)).toBeInTheDocument();
    expect(screen.getByText(/Behavioral signals/i)).toBeInTheDocument();
    expect(screen.getByText(/Simulation impact/i)).toBeInTheDocument();
    expect(screen.getByText(/Decision drivers/i)).toBeInTheDocument();
    const sourceAccordion = screen.getByText(/Source assumptions/i).closest("details");
    expect(sourceAccordion).not.toBeNull();
    expect(screen.getByText(/total segment share 100%/i)).toBeInTheDocument();
    expect(sourceAccordion).not.toHaveAttribute("open");
  });

  it("opens the ICP assumptions sheet with quick edit first and source assumptions behind disclosure", async () => {
    const user = userEvent.setup();

    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: buildIcpStageDetail(),
    });

    renderPage();

    await user.click(screen.getAllByRole("button", { name: /edit assumptions/i })[0]);

    const dialog = screen.getByRole("dialog", { name: /revenue operations lead/i });
    const dialogQueries = within(dialog);

    expectInDocumentOrder([
      dialogQueries.getByText(/^Segment name$/),
      dialogQueries.getByText(/^Segment share$/),
      dialogQueries.getByText(/^Behavioral signals$/),
      dialogQueries.getByText(/^Decision drivers$/),
      dialogQueries.getByText(/^Source assumptions$/),
    ]);

    expect(dialog).toBeInTheDocument();
    expect(dialogQueries.getByRole("spinbutton", { name: /segment share/i })).toBeInTheDocument();
    expect(dialogQueries.getByRole("radio", { name: /Price Sensitivity 5 out of 5/i })).toBeInTheDocument();
    expect(dialogQueries.getByRole("radio", { name: /Switching Friction 3 out of 5/i })).toBeInTheDocument();
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();

    const details = dialogQueries.getByText(/^Source assumptions$/i).closest("details");
    expect(details).not.toBeNull();
    expect(details).not.toHaveAttribute("open");
  });

  it("saves added, removed, and reweighted drivers back into the read-only card", async () => {
    const user = userEvent.setup();
    const updateIcpProfileMock = vi.mocked(updateIcpProfile);
    const initialDetail = buildIcpStageDetail();
    let analysisState = initialDetail;

    mockUseAnalysisPolling.mockImplementation(() => ({
      isLoading: false,
      error: null,
      data: analysisState,
    }));

    updateIcpProfileMock.mockImplementation(async () => {
      analysisState = buildIcpStageDetail([
        buildIcpProfile({
          decision_drivers_json: ["team_enablement", "automation_coverage", "price_affordability"],
          driver_weights_json: { team_enablement: 0.6, automation_coverage: 0.25, price_affordability: 0 },
          is_user_edited: true,
          edited_at: new Date().toISOString(),
        }),
      ]);
      return analysisState;
    });

    renderPage();

    await user.click(screen.getAllByRole("button", { name: /edit assumptions/i })[0]);
    await user.click(screen.getByRole("button", { name: /add driver/i }));

    const driverInputs = screen.getAllByRole("combobox");
    expect(driverInputs).toHaveLength(4);

    await user.click(screen.getAllByRole("button", { name: /remove/i })[1]);
    await user.click(screen.getByRole("radio", { name: /Weight for Team Enablement 3 out of 5/i }));

    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(updateIcpProfileMock).toHaveBeenCalledWith(
        "analysis-1",
        "icp-1",
        expect.objectContaining({
          decision_drivers: ["team_enablement", "automation_coverage", "price_affordability"],
          driver_weights: [
            { driver: "team_enablement", weight: 0.6 },
            { driver: "automation_coverage", weight: 0.25 },
            { driver: "price_affordability", weight: 0 },
          ],
        }),
      );
    });

    await waitFor(() => {
      expect(screen.getByText(/^Price Affordability$/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/^Analytics Depth$/)).not.toBeInTheDocument();
    expect(screen.getByText(/^Reviewed by you$/i)).toBeInTheDocument();
    expect(screen.getByText(/^60%$/)).toBeInTheDocument();
  });

  it("lets users compare ICPs from the final review grid", async () => {
    const user = userEvent.setup();

    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example",
        status: "completed",
        current_stage: "final_review",
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("final_review"),
        extracted_product_data: null,
        icp_profiles: [
          buildIcpProfile(),
          buildIcpProfile({
            id: "icp-2",
            name: "Scaling support operator",
            price_sensitivity: 0.2,
            segment_weight: 0.45,
          }),
        ],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    const compareButtons = screen.getAllByRole("button", { name: /^compare$/i });
    await user.click(compareButtons[0]);
    await user.click(compareButtons[1]);

    const comparePanel = screen.getByText(/Side-by-side simulation assumptions/i).closest("section");
    expect(comparePanel).not.toBeNull();
    expect(within(comparePanel as HTMLElement).getByText(/Scaling support operator/i)).toBeInTheDocument();
    expect(useUIStore.getState().compareICPIds).toEqual(["icp-1", "icp-2"]);

    await user.click(screen.getByRole("button", { name: /clear compare/i }));
    expect(screen.queryByText(/Side-by-side simulation assumptions/i)).not.toBeInTheDocument();
  });

  it("shows the review cue inside the scenario stage header instead of a separate status card", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example",
        status: "awaiting_review",
        current_stage: "scenarios",
        started_at: new Date().toISOString(),
        completed_at: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("scenarios"),
        extracted_product_data: null,
        icp_profiles: [],
        scenarios: [
          {
            id: "scenario-1",
            analysis_id: "analysis-1",
            display_order: 0,
            is_user_edited: false,
            edited_at: null,
            title: "Increase annual price by 9%",
            scenario_type: "pricing_increase",
            description: "Test renewal sensitivity.",
            input_parameters_json: { price_change_percent: 9 },
            input_parameters_schema: {
              fields: [],
            },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getByText(/scenario 1 of 1/i)).toBeInTheDocument();
    expect(screen.getByText(/ready to review/i)).toBeInTheDocument();
    expect(screen.queryByText(/ready for review/i)).not.toBeInTheDocument();
  });

  it("renders the scenario review screen as a decision-support surface", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example",
        status: "awaiting_review",
        current_stage: "scenarios",
        started_at: new Date().toISOString(),
        completed_at: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("scenarios"),
        extracted_product_data: null,
        icp_profiles: [],
        scenarios: [
          {
            id: "scenario-1",
            analysis_id: "analysis-1",
            display_order: 0,
            is_user_edited: false,
            edited_at: null,
            title: "Decrease annual price by 10%",
            scenario_type: "pricing_decrease",
            description: "Test whether a lower annual entry point increases evaluation among healthcare teams.",
            input_parameters_json: { price_change_percent: 10, market: "Healthcare" },
            input_parameters_schema: {
              fields: [],
            },
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
              ],
              why_this_might_work: [
                "High price sensitivity means a lower entry point can change evaluation quickly.",
              ],
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
          },
        ],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getByText(/expected impact/i)).toBeInTheDocument();
    expect(screen.getAllByText(/recommended first/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/decrease annual pricing by 10% for healthcare teams/i)).toBeInTheDocument();
    expect(screen.getByText(/why this might work/i)).toBeInTheDocument();
    expect(screen.getByText(/secondary metadata/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /proceed to run selection/i })).toBeInTheDocument();
  });

  it("shows the status card for failed analyses in the main review layout", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example",
        status: "failed",
        current_stage: "product_understanding",
        started_at: new Date().toISOString(),
        completed_at: null,
        error_message: "The provider timed out.",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("product_understanding"),
        extracted_product_data: null,
        icp_profiles: [],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getByText(/^failed$/i)).toBeInTheDocument();
    expect(screen.getByText(/the provider timed out/i)).toBeInTheDocument();
  });

  it("renders the full final review once a scenario has been simulated", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example",
        status: "completed",
        current_stage: "final_review",
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("final_review"),
        extracted_product_data: buildProductUnderstandingData(),
        icp_profiles: [
          {
            id: "icp-1",
            analysis_id: "analysis-1",
            display_order: 0,
            is_user_edited: false,
            edited_at: null,
            name: "Revenue operations lead",
            description: "Owns retention tooling.",
            use_case: "Standardize renewals.",
            goals_json: ["Reduce churn"],
            pain_points_json: ["Disconnected tooling"],
            decision_drivers_json: ["team_enablement", "analytics_depth", "automation_coverage"],
            driver_weights_json: { team_enablement: 0.4, analytics_depth: 0.35, automation_coverage: 0.25 },
            price_sensitivity: 0.4,
            switching_cost: 0.5,
            alternatives_json: ["CRM"],
            churn_threshold: -0.2,
            retention_threshold: 0.07,
            adoption_friction: 0.2,
            value_perception_explanation: "Needs strong workflow breadth.",
            segment_weight: 0.5,
          },
        ],
        scenarios: [
          {
            id: "scenario-1",
            analysis_id: "analysis-1",
            display_order: 0,
            is_user_edited: false,
            edited_at: null,
            title: "Increase annual price by 9%",
            scenario_type: "pricing_increase",
            description: "Test renewal sensitivity.",
            input_parameters_json: { price_change_percent: 9 },
            input_parameters_schema: {
              fields: [],
            },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        simulation_runs: [
          {
            id: "run-1",
            analysis_id: "analysis-1",
            scenario_id: "scenario-1",
            run_version: "1",
            engine_version: "utility-v1",
            assumptions_json: {},
            created_at: new Date().toISOString(),
            results: [],
            summary: {
              scenario_id: "scenario-1",
              scenario_title: "Increase annual price by 9%",
              projected_retention_pct: 75,
              projected_downgrade_pct: 15,
              projected_upgrade_pct: 10,
              projected_churn_pct: 0,
              estimated_revenue_delta_pct: 18,
              weighted_revenue_delta: 1200,
              perception_shift_score: 0.2,
              perception_shift_label: "Positive",
              highest_risk_icps: ["Revenue operations lead"],
              top_negative_drivers: ["price_affordability"],
              top_positive_drivers: ["analytics_depth"],
              second_order_effects: ["renewal scrutiny increases"],
            },
          },
        ],
      },
    });

    renderPage();

    expect(screen.getAllByText(/soft refresh from here/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/who moves first when the offer changes/i)).toBeInTheDocument();
    expect(screen.getByText(/which decision is worth simulating first/i)).toBeInTheDocument();
    expect(screen.getByText(/retention, downgrade, upgrade, churn, and revenue movement/i)).toBeInTheDocument();
  });

  it("shows a hard refresh button and reruns the current URL with force refresh", async () => {
    const user = userEvent.setup();
    const createAnalysisMock = vi.mocked(createAnalysis);

    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example/",
        status: "completed",
        current_stage: "final_review",
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        workflow: buildWorkflow("final_review"),
        extracted_product_data: null,
        icp_profiles: [],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    await user.click(screen.getByRole("button", { name: /hard refresh/i }));

    await waitFor(() => {
      expect(createAnalysisMock).toHaveBeenCalledWith({
        url: "https://acme.example/",
        force_refresh: true,
        run_async: true,
      });
    });
  });
});
