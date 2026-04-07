import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createAnalysis } from "@/api/analyses";
import { DashboardPage } from "@/pages/DashboardPage";
import { useAuthStore } from "@/store/auth-store";

vi.mock("@/api/analyses", () => ({
  listAnalyses: vi.fn().mockResolvedValue([
    {
      id: "analysis-1",
      input_url: "https://acme.example/",
      normalized_url: "https://acme.example",
      status: "completed",
      current_stage: "final_review",
      created_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      error_message: null,
    },
  ]),
  createAnalysis: vi.fn().mockResolvedValue({
    analysis: {
      id: "analysis-2",
      input_url: "https://acme.example/",
      normalized_url: "https://acme.example",
      status: "queued",
      current_stage: "product_understanding",
      created_at: new Date().toISOString(),
      completed_at: null,
      error_message: null,
    },
    reused: false,
    cloned_from_analysis_id: null,
  }),
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.mocked(createAnalysis).mockClear();
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
  });

  it("renders recent analyses and submits a new URL", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText(/https:\/\/acme.example/i)).toBeInTheDocument();
    const input = screen.getByPlaceholderText("https://www.netflix.com/");
    await user.clear(input);
    await user.type(input, "https://acme.example/");
    await user.click(screen.getByRole("button", { name: /analyze url/i }));

    await waitFor(() => {
      expect(screen.getByText(/continue where you left off/i)).toBeInTheDocument();
    });
  });

  it("normalizes bare domains before creating an analysis", async () => {
    const user = userEvent.setup();
    const createAnalysisMock = vi.mocked(createAnalysis);

    renderPage();

    const input = screen.getByPlaceholderText("https://www.netflix.com/");
    await user.clear(input);
    await user.type(input, "incommon.ai");
    await user.click(screen.getByRole("button", { name: /analyze url/i }));

    await waitFor(() => {
      expect(createAnalysisMock.mock.calls.at(-1)?.[0]).toEqual({ url: "http://incommon.ai/", run_async: true });
    });
  });

  it("does not render a netflix demo action", () => {
    renderPage();

    expect(screen.queryByRole("button", { name: /load netflix demo/i })).not.toBeInTheDocument();
  });
});
