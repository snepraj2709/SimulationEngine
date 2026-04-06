import { useEffect, useMemo } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import { createAnalysis, rerunScenario, submitFeedback } from "@/api/analyses";
import { ApiError } from "@/api/client";
import { AnalysisPendingState } from "@/components/analysis/AnalysisPendingState";
import { AnalysisStatusCard } from "@/components/analysis/AnalysisStatusCard";
import { DecisionFlowGraph } from "@/components/analysis/DecisionFlowGraph";
import { EmptyState } from "@/components/analysis/EmptyState";
import { ErrorState } from "@/components/analysis/ErrorState";
import { FeedbackBar } from "@/components/analysis/FeedbackBar";
import { ICPCardGrid } from "@/components/analysis/ICPCardGrid";
import { LoadingState } from "@/components/analysis/LoadingState";
import { ProductSummaryPanel } from "@/components/analysis/ProductSummaryPanel";
import { ScenarioSuggestionList } from "@/components/analysis/ScenarioSuggestionList";
import { SimulationMetricsDashboard } from "@/components/analysis/SimulationMetricsDashboard";
import { AppShell } from "@/components/layout/AppShell";
import { useAnalysisPolling } from "@/hooks/use-analysis-polling";
import { createPendingAnalysisDetail, getLatestRunForScenario, scenarioSummaries, upsertAnalysisListItem } from "@/lib/analysis";
import { useUIStore } from "@/store/ui-store";
import { AnalysisDetail, AnalysisListItem } from "@/types/api";

export function AnalysisResultPage() {
  const { analysisId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const selectedScenarioId = useUIStore((state) => state.selectedScenarioId);
  const selectedICPId = useUIStore((state) => state.selectedICPId);
  const compareScenarioIds = useUIStore((state) => state.compareScenarioIds);
  const setSelectedScenarioId = useUIStore((state) => state.setSelectedScenarioId);
  const setSelectedICPId = useUIStore((state) => state.setSelectedICPId);
  const toggleCompareScenario = useUIStore((state) => state.toggleCompareScenario);
  const clearCompareScenarios = useUIStore((state) => state.clearCompareScenarios);

  const analysisQuery = useAnalysisPolling(analysisId);
  const rerunMutation = useMutation({
    mutationFn: ({ scenarioId }: { scenarioId: string }) =>
      rerunScenario(analysisId, scenarioId, { input_overrides: {}, run_version: String(Date.now()) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["analysis", analysisId] }),
  });
  const feedbackMutation = useMutation({
    mutationFn: submitFeedback,
  });
  const refreshMutation = useMutation({
    mutationFn: ({ url }: { url: string }) => createAnalysis({ url, force_refresh: true, run_async: true }),
    onSuccess: (data) => {
      queryClient.setQueryData(["analysis", data.analysis.id], (existing: AnalysisDetail | undefined) => {
        if (existing && data.analysis.status === "completed") {
          return existing;
        }
        return createPendingAnalysisDetail(data.analysis);
      });
      queryClient.setQueryData(["analyses"], (existing: AnalysisListItem[] | undefined) =>
        upsertAnalysisListItem(existing, data.analysis),
      );
      navigate(`/analyses/${data.analysis.id}`);
    },
  });

  const analysis = analysisQuery.data;

  useEffect(() => {
    setSelectedScenarioId(null);
    setSelectedICPId(null);
    clearCompareScenarios();
  }, [analysisId, clearCompareScenarios, setSelectedICPId, setSelectedScenarioId]);

  useEffect(() => {
    if (!analysis) return;
    if (!selectedScenarioId || !analysis.scenarios.find((scenario) => scenario.id === selectedScenarioId)) {
      setSelectedScenarioId(analysis.scenarios[0]?.id ?? null);
    }
    if (!selectedICPId && analysis.icp_profiles[0]) {
      setSelectedICPId(analysis.icp_profiles[0].id);
    }
  }, [analysis, selectedScenarioId, selectedICPId, setSelectedICPId, setSelectedScenarioId]);

  const selectedScenario = analysis?.scenarios.find((scenario) => scenario.id === selectedScenarioId);
  const selectedRun = analysis && selectedScenario ? getLatestRunForScenario(analysis, selectedScenario.id) : undefined;
  const summaries = useMemo(() => {
    if (!analysis) return {};
    return Object.fromEntries(
      scenarioSummaries(analysis).map(({ scenario, run }) => [scenario.id, run?.summary]),
    );
  }, [analysis]);

  if (analysisQuery.isLoading) {
    return (
      <AppShell title="Analysis" subtitle="Preparing simulation">
        <LoadingState title="Loading analysis" description="Hydrating analysis payload and simulation results." />
      </AppShell>
    );
  }

  if (analysisQuery.error instanceof ApiError) {
    return (
      <AppShell title="Analysis" subtitle="Unable to load">
        <ErrorState title="Analysis unavailable" message={analysisQuery.error.message} />
      </AppShell>
    );
  }

  if (!analysis) {
    return (
      <AppShell title="Analysis" subtitle="Missing">
        <EmptyState title="Analysis not found" message="The requested analysis could not be loaded." />
      </AppShell>
    );
  }

  const isPending = analysis.status === "queued" || analysis.status === "processing";
  const refreshAction = (
    <div className="flex flex-col gap-4 rounded-3xl border border-slate-200 bg-slate-50 p-5 md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-sm font-semibold text-slate-950">Need a fresh recompute?</p>
        <p className="mt-1 text-sm text-slate-600">
          Hard refresh bypasses cached reuse and reruns the current URL analysis from scratch.
        </p>
      </div>
      <button
        type="button"
        onClick={() => refreshMutation.mutate({ url: analysis.input_url || analysis.normalized_url })}
        disabled={isPending || refreshMutation.isPending}
        className="rounded-2xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-500 hover:bg-white disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
      >
        {refreshMutation.isPending ? "Refreshing..." : "Hard refresh"}
      </button>
    </div>
  );

  if (isPending) {
    return (
      <AppShell
        title={analysis.extracted_product_data?.product_name ?? "Analysis"}
        subtitle={analysis.normalized_url}
      >
        <div className="space-y-8">
          {refreshAction}
          <AnalysisStatusCard status={analysis.status} errorMessage={analysis.error_message} />
          <AnalysisPendingState url={analysis.normalized_url || analysis.input_url} status={analysis.status} />
          {refreshMutation.error instanceof ApiError ? (
            <ErrorState title="Hard refresh failed" message={refreshMutation.error.message} />
          ) : null}
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      title={analysis.extracted_product_data?.product_name ?? "Analysis"}
      subtitle={analysis.normalized_url}
    >
      <div className="space-y-8">
        {refreshAction}
        <AnalysisStatusCard status={analysis.status} errorMessage={analysis.error_message} />

        {analysis.extracted_product_data ? <ProductSummaryPanel data={analysis.extracted_product_data} /> : null}

        {analysis.icp_profiles.length > 0 ? (
          <ICPCardGrid
            icps={analysis.icp_profiles}
            selectedICPId={selectedICPId}
            onSelectICP={(icpId) => setSelectedICPId(icpId)}
          />
        ) : null}

        {analysis.scenarios.length > 0 ? (
          <ScenarioSuggestionList
            scenarios={analysis.scenarios}
            summaries={summaries}
            selectedScenarioId={selectedScenarioId}
            comparedScenarioIds={compareScenarioIds}
            runningScenarioId={rerunMutation.isPending ? rerunMutation.variables?.scenarioId ?? null : null}
            onSelectScenario={setSelectedScenarioId}
            onToggleCompare={toggleCompareScenario}
            onRunScenario={(scenarioId) => rerunMutation.mutate({ scenarioId })}
          />
        ) : null}

        {compareScenarioIds.length > 0 ? (
          <div className="flex justify-end">
            <Link
              to={`/analyses/${analysis.id}/scenarios/compare`}
              className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:border-slate-500 hover:bg-slate-100"
            >
              Compare selected scenarios
            </Link>
          </div>
        ) : null}

        {selectedRun ? <SimulationMetricsDashboard summaries={[selectedRun.summary]} /> : null}

        {selectedScenario ? (
          <DecisionFlowGraph
            analysis={analysis}
            scenario={selectedScenario}
            run={selectedRun}
            selectedICPId={selectedICPId}
          />
        ) : null}

        {selectedRun && selectedScenario ? (
          <FeedbackBar
            isSubmitting={feedbackMutation.isPending}
            onSubmit={async ({ feedbackType, comment }) => {
              await feedbackMutation.mutateAsync({
                analysis_id: analysis.id,
                scenario_id: selectedScenario.id,
                simulation_run_id: selectedRun.id,
                feedback_type: feedbackType,
                comment,
              });
            }}
          />
        ) : null}

        {feedbackMutation.error instanceof ApiError ? (
          <ErrorState title="Feedback could not be saved" message={feedbackMutation.error.message} />
        ) : null}
        {refreshMutation.error instanceof ApiError ? (
          <ErrorState title="Hard refresh failed" message={refreshMutation.error.message} />
        ) : null}
      </div>
    </AppShell>
  );
}
