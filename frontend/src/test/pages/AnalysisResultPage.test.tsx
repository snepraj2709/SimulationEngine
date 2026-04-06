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
        started_at: null,
        completed_at: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        extracted_product_data: null,
        icp_profiles: [],
        scenarios: [],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getByText(/preparing results for the submitted url/i)).toBeInTheDocument();
    expect(screen.getAllByText(/https:\/\/acme.example/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/who moves first when the offer changes/i)).not.toBeInTheDocument();
    expect(useUIStore.getState().selectedScenarioId).toBeNull();
    expect(useUIStore.getState().selectedICPId).toBeNull();
    expect(useUIStore.getState().compareScenarioIds).toEqual([]);
  });

  it("renders only the current completed analysis content", () => {
    mockUseAnalysisPolling.mockReturnValue({
      isLoading: false,
      error: null,
      data: {
        id: "analysis-1",
        input_url: "https://acme.example/",
        normalized_url: "https://acme.example",
        status: "completed",
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
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
        },
        icp_profiles: [
          {
            id: "icp-1",
            analysis_id: "analysis-1",
            name: "Revenue operations lead",
            description: "Owns retention tooling.",
            use_case: "Standardize renewals.",
            goals_json: ["Reduce churn"],
            pain_points_json: ["Disconnected tooling"],
            decision_drivers_json: ["team_enablement", "analytics_depth"],
            driver_weights_json: { team_enablement: 0.6, analytics_depth: 0.4 },
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
            title: "Increase annual price by 9%",
            scenario_type: "pricing_increase",
            description: "Test renewal sensitivity.",
            input_parameters_json: { price_change_percent: 9 },
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        simulation_runs: [],
      },
    });

    renderPage();

    expect(screen.getAllByText(/acme growth platform/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/revenue operations lead/i)).toBeInTheDocument();
    expect(screen.getByText(/increase annual price by 9%/i)).toBeInTheDocument();
    expect(screen.queryByText(/preparing results for the submitted url/i)).not.toBeInTheDocument();
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
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
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
