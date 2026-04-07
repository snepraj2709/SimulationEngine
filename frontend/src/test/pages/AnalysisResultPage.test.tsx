import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createAnalysis } from "@/api/analyses";
import { AnalysisResultPage } from "@/pages/AnalysisResultPage";
import { useAuthStore } from "@/store/auth-store";
import { useUIStore } from "@/store/ui-store";

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

function buildWorkflow(currentStage: "product_understanding" | "icp_profiles" | "scenarios" | "decision_flow" | "final_review") {
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
      status:
        index < currentIndex ? "completed" : index === currentIndex ? (currentStage === "final_review" ? "completed" : "awaiting_review") : "not_started",
      is_current: index === currentIndex,
      is_complete: index < currentIndex || currentStage === "final_review",
      started_at: null,
      completed_at: null,
      edited: false,
      error_message: null,
    })),
  };
}

describe("AnalysisResultPage", () => {
  beforeEach(() => {
    mockUseAnalysisPolling.mockReset();
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
        extracted_product_data: {
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
          normalized_json: {
            company_name: "Acme",
            product_name: "Acme Growth Platform",
            category: "B2B Software",
            subcategory: "Revenue Operations",
            positioning_summary: "Automates onboarding and revenue expansion workflows.",
            pricing_model: "sales_led_custom_pricing",
            feature_clusters: ["workflow automation", "renewal analytics"],
            monetization_hypothesis: "Annual contracts for revenue teams.",
            target_customer_signals: ["revenue teams"],
            confidence_score: 0.84,
            confidence_scores: { category: 0.84 },
            warnings: [],
          },
          confidence_score: 0.84,
          is_user_edited: false,
          edited_at: null,
        },
        icp_profiles: [],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getByText(/review the product understanding first/i)).toBeInTheDocument();
    expect(screen.getByText(/ready to review/i)).toBeInTheDocument();
    expect(screen.getByText(/proceed to generate icp profiles/i)).toBeInTheDocument();
    expect(screen.queryByText(/ready for review/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/who moves first when the offer changes/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/default simulations worth pressure-testing/i)).not.toBeInTheDocument();
  });

  it("shows the review cue inside the ICP stage header instead of a separate status card", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
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
        icp_profiles: [
          {
            id: "icp-1",
            analysis_id: "analysis-1",
            display_order: 0,
            is_user_edited: true,
            edited_at: new Date().toISOString(),
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
            segment_weight: 1,
          },
        ],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getByText(/icp 1 of 1/i)).toBeInTheDocument();
    expect(screen.getByText(/reviewed by you/i)).toBeInTheDocument();
    expect(screen.queryByText(/ready for review/i)).not.toBeInTheDocument();
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
        extracted_product_data: {
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
          normalized_json: {
            company_name: "Acme",
            product_name: "Acme Growth Platform",
            category: "B2B Software",
            subcategory: "Revenue Operations",
            positioning_summary: "Automates onboarding and revenue expansion workflows.",
            pricing_model: "sales_led_custom_pricing",
            feature_clusters: ["workflow automation", "renewal analytics"],
            monetization_hypothesis: "Annual contracts for revenue teams.",
            target_customer_signals: ["revenue teams"],
            confidence_score: 0.84,
            confidence_scores: { category: 0.84 },
            warnings: [],
          },
          confidence_score: 0.84,
          is_user_edited: false,
          edited_at: null,
        },
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
    expect(screen.getByText(/default simulations worth pressure-testing/i)).toBeInTheDocument();
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
