import { useEffect, useMemo, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  createAnalysis,
  proceedWorkflow,
  reopenWorkflow,
  rerunScenario,
  submitFeedback,
  updateIcpProfile,
  updateProductUnderstanding,
  updateScenario,
} from "@/api/analyses";
import { ApiError } from "@/api/client";
import { AnalysisPendingState } from "@/components/analysis/AnalysisPendingState";
import { AnalysisStatusCard } from "@/components/analysis/AnalysisStatusCard";
import { DecisionFlowGraph } from "@/components/analysis/DecisionFlowGraph";
import { EmptyState } from "@/components/analysis/EmptyState";
import { ErrorState } from "@/components/analysis/ErrorState";
import { FeedbackBar } from "@/components/analysis/FeedbackBar";
import { ICPCardGrid } from "@/components/analysis/ICPCardGrid";
import { ICPDetailCard } from "@/components/analysis/ICPDetailCard";
import {
  formatDriverLabel,
  formatSegmentShare,
  getEditableDriverRows,
  getDriverWeightFromLevel,
  getDriverWeightLevel,
  getRawValueFromSignalLevel,
  getSignalLevelFromRaw,
  signalScale,
  type ICPSignalKey,
  type ICPSignalLevel,
} from "@/components/analysis/icpDisplay";
import { LoadingState } from "@/components/analysis/LoadingState";
import { ProductSummaryPanel } from "@/components/analysis/ProductSummaryPanel";
import { ScenarioReviewCard } from "@/components/analysis/ScenarioReviewCard";
import { ScenarioSuggestionList } from "@/components/analysis/ScenarioSuggestionList";
import { getScenarioReviewModel } from "@/components/analysis/scenarioDisplay";
import { SimulationMetricsDashboard } from "@/components/analysis/SimulationMetricsDashboard";
import { WorkflowStepper } from "@/components/analysis/WorkflowStepper";
import { AppShell } from "@/components/layout/AppShell";
import { useAnalysisPolling } from "@/hooks/use-analysis-polling";
import { createPendingAnalysisDetail, getLatestRunForScenario, scenarioSummaries, upsertAnalysisListItem } from "@/lib/analysis";
import { useUIStore } from "@/store/ui-store";
import { AnalysisDetail, AnalysisListItem, ICPProfile, Scenario, WorkflowStage } from "@/types/api";
import { cn } from "@/lib/utils";

const decisionDriverOptions = [
  "price_affordability",
  "value_for_money",
  "content_access",
  "mobile_experience",
  "brand_habit",
  "video_quality",
  "family_fit",
  "device_support",
  "regional_content",
  "feature_completeness",
  "automation_coverage",
  "analytics_depth",
  "implementation_complexity",
  "support_reliability",
  "team_enablement",
  "budget_predictability",
  "convenience",
] as const;

const icpSignalKeys: readonly ICPSignalKey[] = [
  "priceSensitivity",
  "switchingFriction",
  "proofRequirement",
  "implementationTolerance",
  "retentionStability",
] as const;

type ProductDraft = {
  company_name: string;
  product_name: string;
  category: string;
  subcategory: string;
  positioning_summary: string;
  pricing_model: string;
  feature_clusters: string;
  monetization_hypothesis: string;
  target_customer_signals: string;
  warnings: string;
};

type IcpDraft = {
  name: string;
  description: string;
  use_case: string;
  goals: string;
  pain_points: string;
  alternatives: string;
  value_perception_explanation: string;
  price_sensitivity: number;
  switching_cost: number;
  churn_threshold: number;
  retention_threshold: number;
  adoption_friction: number;
  segment_weight: number;
  driver_rows: { driver: string; weight: number }[];
};

type ScenarioDraft = {
  title: string;
  description: string;
  input_parameters: Record<string, string | number>;
};

export function AnalysisResultPage() {
  const { analysisId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const selectedScenarioId = useUIStore((state) => state.selectedScenarioId);
  const selectedICPId = useUIStore((state) => state.selectedICPId);
  const compareICPIds = useUIStore((state) => state.compareICPIds);
  const compareScenarioIds = useUIStore((state) => state.compareScenarioIds);
  const setSelectedScenarioId = useUIStore((state) => state.setSelectedScenarioId);
  const setSelectedICPId = useUIStore((state) => state.setSelectedICPId);
  const toggleCompareICP = useUIStore((state) => state.toggleCompareICP);
  const clearCompareICPs = useUIStore((state) => state.clearCompareICPs);
  const toggleCompareScenario = useUIStore((state) => state.toggleCompareScenario);
  const clearCompareScenarios = useUIStore((state) => state.clearCompareScenarios);

  const [activeIcpIndex, setActiveIcpIndex] = useState(0);
  const [activeScenarioIndex, setActiveScenarioIndex] = useState(0);
  const [decisionFlowScenarioId, setDecisionFlowScenarioId] = useState<string | null>(null);
  const [editingProduct, setEditingProduct] = useState(false);
  const [productDraft, setProductDraft] = useState<ProductDraft | null>(null);
  const [editingIcpId, setEditingIcpId] = useState<string | null>(null);
  const [icpDraft, setIcpDraft] = useState<IcpDraft | null>(null);
  const [editingScenarioId, setEditingScenarioId] = useState<string | null>(null);
  const [scenarioDraft, setScenarioDraft] = useState<ScenarioDraft | null>(null);
  const [softRefreshOrigin, setSoftRefreshOrigin] = useState<WorkflowStage | null>(null);

  const analysisQuery = useAnalysisPolling(analysisId);
  const analysis = analysisQuery.data;

  const commitAnalysisDetail = (detail: AnalysisDetail) => {
    queryClient.setQueryData(["analysis", detail.id], detail);
    queryClient.setQueryData(["analyses"], (existing: AnalysisListItem[] | undefined) =>
      upsertAnalysisListItem(existing, {
        id: detail.id,
        input_url: detail.input_url,
        normalized_url: detail.normalized_url,
        status: detail.status,
        current_stage: detail.current_stage,
        created_at: detail.created_at,
        completed_at: detail.completed_at,
        error_message: detail.error_message,
      }),
    );
  };

  const rerunMutation = useMutation({
    mutationFn: ({ scenarioId }: { scenarioId: string }) =>
      rerunScenario(analysisId, scenarioId, { input_overrides: {}, run_version: String(Date.now()) }),
    onSuccess: (_run, variables) => {
      setSelectedScenarioId(variables.scenarioId);
      setDecisionFlowScenarioId(variables.scenarioId);
      queryClient.invalidateQueries({ queryKey: ["analysis", analysisId] });
      queryClient.invalidateQueries({ queryKey: ["analyses"] });
    },
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
  const proceedMutation = useMutation({
    mutationFn: (payload: { expected_stage: WorkflowStage; run_async?: boolean }) =>
      proceedWorkflow(analysisId, payload),
    onSuccess: (detail) => {
      commitAnalysisDetail(detail);
      resetEditingState();
    },
  });
  const reopenMutation = useMutation({
    mutationFn: (payload: { stage: Extract<WorkflowStage, "product_understanding" | "icp_profiles" | "scenarios">; entity_id?: string | null }) =>
      reopenWorkflow(analysisId, payload),
    onSuccess: (detail, variables) => {
      commitAnalysisDetail(detail);
      setSoftRefreshOrigin(variables.stage);
      resetEditingState();
    },
  });
  const updateProductMutation = useMutation({
    mutationFn: (payload: ProductDraft) =>
      updateProductUnderstanding(analysisId, {
        company_name: payload.company_name,
        product_name: payload.product_name,
        category: payload.category,
        subcategory: payload.subcategory,
        positioning_summary: payload.positioning_summary,
        pricing_model: payload.pricing_model,
        feature_clusters: splitLines(payload.feature_clusters),
        monetization_hypothesis: payload.monetization_hypothesis,
        target_customer_signals: splitLines(payload.target_customer_signals),
        warnings: splitLines(payload.warnings),
      }),
    onSuccess: (detail) => {
      commitAnalysisDetail(detail);
      setEditingProduct(false);
    },
  });
  const updateIcpMutation = useMutation({
    mutationFn: ({ icpId, payload }: { icpId: string; payload: IcpDraft }) =>
      updateIcpProfile(analysisId, icpId, {
        name: payload.name,
        description: payload.description,
        use_case: payload.use_case,
        goals: splitLines(payload.goals),
        pain_points: splitLines(payload.pain_points),
        decision_drivers: payload.driver_rows.map((row) => row.driver).filter(Boolean),
        driver_weights: payload.driver_rows
          .filter((row) => row.driver)
          .map((row) => ({ driver: row.driver, weight: Number(row.weight) || 0 })),
        price_sensitivity: Number(payload.price_sensitivity),
        switching_cost: Number(payload.switching_cost),
        alternatives: splitLines(payload.alternatives),
        churn_threshold: Number(payload.churn_threshold),
        retention_threshold: Number(payload.retention_threshold),
        adoption_friction: Number(payload.adoption_friction),
        value_perception_explanation: payload.value_perception_explanation,
        segment_weight: Number(payload.segment_weight),
      }),
    onSuccess: (detail) => {
      commitAnalysisDetail(detail);
      setEditingIcpId(null);
      setIcpDraft(null);
    },
  });
  const updateScenarioMutation = useMutation({
    mutationFn: ({ scenarioId, payload, scenario }: { scenarioId: string; payload: ScenarioDraft; scenario: Scenario }) =>
      updateScenario(analysisId, scenarioId, {
        title: payload.title,
        scenario_type: scenario.scenario_type,
        description: payload.description,
        input_parameters: buildScenarioPayload(scenario, payload.input_parameters),
      }),
    onSuccess: (detail) => {
      commitAnalysisDetail(detail);
      setEditingScenarioId(null);
      setScenarioDraft(null);
    },
  });

  useEffect(() => {
    setSelectedScenarioId(null);
    setSelectedICPId(null);
    clearCompareICPs();
    clearCompareScenarios();
    setActiveIcpIndex(0);
    setActiveScenarioIndex(0);
    setDecisionFlowScenarioId(null);
    resetEditingState();
    setSoftRefreshOrigin(null);
  }, [analysisId, clearCompareICPs, clearCompareScenarios, setSelectedICPId, setSelectedScenarioId]);

  useEffect(() => {
    if (!analysis) return;
    if (analysis.current_stage !== "final_review") {
      clearCompareICPs();
      clearCompareScenarios();
    }
    if ((!selectedICPId || !analysis.icp_profiles.find((icp) => icp.id === selectedICPId)) && analysis.icp_profiles[0]) {
      setSelectedICPId(analysis.icp_profiles[0].id);
    }
    if (!selectedScenarioId || !analysis.scenarios.find((scenario) => scenario.id === selectedScenarioId)) {
      const latestRunScenarioId = [...analysis.simulation_runs]
        .sort((left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime())[0]?.scenario_id;
      setSelectedScenarioId(latestRunScenarioId ?? analysis.scenarios[0]?.id ?? null);
    }
    if (!decisionFlowScenarioId || !analysis.scenarios.find((scenario) => scenario.id === decisionFlowScenarioId)) {
      setDecisionFlowScenarioId(analysis.scenarios[0]?.id ?? null);
    }
    setActiveIcpIndex((current) => clampIndex(current, analysis.icp_profiles.length));
    setActiveScenarioIndex((current) => clampIndex(current, analysis.scenarios.length));
  }, [
    analysis,
    clearCompareICPs,
    clearCompareScenarios,
    decisionFlowScenarioId,
    selectedICPId,
    selectedScenarioId,
    setSelectedICPId,
    setSelectedScenarioId,
  ]);

  const selectedScenario = analysis?.scenarios.find((scenario) => scenario.id === selectedScenarioId);
  const selectedRun = analysis && selectedScenario ? getLatestRunForScenario(analysis, selectedScenario.id) : undefined;
  const decisionFlowScenario = analysis?.scenarios.find((scenario) => scenario.id === decisionFlowScenarioId) ?? null;
  const summaries = useMemo(() => {
    if (!analysis) return {};
    return Object.fromEntries(
      scenarioSummaries(analysis).map(({ scenario, run }) => [scenario.id, run?.summary]),
    );
  }, [analysis]);
  const activeIcp = analysis?.icp_profiles[activeIcpIndex] ?? null;
  const editingIcp = analysis?.icp_profiles.find((profile) => profile.id === editingIcpId) ?? null;
  const activeScenario = analysis?.scenarios[activeScenarioIndex] ?? null;
  const icpSegmentWeightTotal = analysis
    ? roundToPercent(
        analysis.icp_profiles.reduce((total, icp) => {
          if (editingIcpId === icp.id && icpDraft) {
            return total + Number(icpDraft.segment_weight || 0);
          }
          return total + Number(icp.segment_weight || 0);
        }, 0),
      )
    : 0;

  function resetEditingState() {
    setEditingProduct(false);
    setProductDraft(null);
    setEditingIcpId(null);
    setIcpDraft(null);
    setEditingScenarioId(null);
    setScenarioDraft(null);
  }

  if (analysisQuery.isLoading) {
    return (
      <AppShell title="Analysis" subtitle="Preparing staged workflow">
        <LoadingState title="Loading analysis" description="Hydrating workflow state and stage outputs." />
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
          Hard refresh bypasses cached reuse and restarts the staged analysis from product understanding.
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
          <WorkflowStepper workflow={analysis.workflow} />
          <AnalysisStatusCard status={analysis.status} errorMessage={analysis.error_message} />
          <AnalysisPendingState url={analysis.normalized_url || analysis.input_url} status={analysis.status} />
          {refreshMutation.error instanceof ApiError ? (
            <ErrorState title="Hard refresh failed" message={refreshMutation.error.message} />
          ) : null}
        </div>
      </AppShell>
    );
  }

  const stage = analysis.workflow.current_stage;

  return (
    <AppShell
      title={analysis.extracted_product_data?.product_name ?? "Analysis"}
      subtitle={analysis.normalized_url}
    >
      <div className="space-y-8">
        {refreshAction}
        <WorkflowStepper workflow={analysis.workflow} />
        {analysis.status === "failed" ? (
          <AnalysisStatusCard status={analysis.status} errorMessage={analysis.error_message} />
        ) : null}

        {stage === "product_understanding" && analysis.extracted_product_data ? (
          <ProductUnderstandingStage
            data={analysis.extracted_product_data}
            editing={editingProduct}
            draft={productDraft ?? createProductDraft(analysis.extracted_product_data)}
            isSaving={updateProductMutation.isPending}
            isProceeding={proceedMutation.isPending}
            onStartEdit={() => {
              setEditingProduct(true);
              setProductDraft(createProductDraft(analysis.extracted_product_data!));
            }}
            onCancelEdit={() => {
              setEditingProduct(false);
              setProductDraft(null);
            }}
            onChange={(next) => setProductDraft(next)}
            onSave={() => {
              const draft = productDraft ?? createProductDraft(analysis.extracted_product_data!);
              updateProductMutation.mutate(draft);
            }}
            onProceed={() => proceedMutation.mutate({ expected_stage: "product_understanding", run_async: false })}
          />
        ) : null}

        {stage === "icp_profiles" && activeIcp ? (
          <ICPReviewStage
            icp={activeIcp}
            currentIndex={activeIcpIndex}
            total={analysis.icp_profiles.length}
            isConfirmed={selectedICPId === activeIcp.id}
            editing={editingIcpId === activeIcp.id}
            segmentWeightTotal={icpSegmentWeightTotal}
            isProceeding={proceedMutation.isPending}
            onPrevious={() => setActiveIcpIndex((current) => Math.max(0, current - 1))}
            onNext={() => setActiveIcpIndex((current) => Math.min(analysis.icp_profiles.length - 1, current + 1))}
            onStartEdit={() => {
              setEditingIcpId(activeIcp.id);
              setIcpDraft(createIcpDraft(activeIcp));
            }}
            onCancelEdit={() => {
              setEditingIcpId(null);
              setIcpDraft(null);
            }}
            onConfirm={() => setSelectedICPId(activeIcp.id)}
            onRegenerate={() => {
              setSoftRefreshOrigin("icp_profiles");
              reopenMutation.mutate({ stage: "icp_profiles", entity_id: activeIcp.id });
            }}
            onProceed={() => proceedMutation.mutate({ expected_stage: "icp_profiles", run_async: false })}
          />
        ) : null}

        {stage === "scenarios" && activeScenario ? (
          <ScenarioReviewStage
            scenario={activeScenario}
            currentIndex={activeScenarioIndex}
            total={analysis.scenarios.length}
            editing={editingScenarioId === activeScenario.id}
            draft={scenarioDraft ?? createScenarioDraft(activeScenario)}
            isSaving={updateScenarioMutation.isPending}
            isProceeding={proceedMutation.isPending}
            onPrevious={() => setActiveScenarioIndex((current) => Math.max(0, current - 1))}
            onNext={() => setActiveScenarioIndex((current) => Math.min(analysis.scenarios.length - 1, current + 1))}
            onStartEdit={() => {
              setEditingScenarioId(activeScenario.id);
              setScenarioDraft(createScenarioDraft(activeScenario));
            }}
            onCancelEdit={() => {
              setEditingScenarioId(null);
              setScenarioDraft(null);
            }}
            onChange={(next) => setScenarioDraft(next)}
            onSave={() => {
              const draft = scenarioDraft ?? createScenarioDraft(activeScenario);
              updateScenarioMutation.mutate({ scenarioId: activeScenario.id, payload: draft, scenario: activeScenario });
            }}
            onProceed={() => proceedMutation.mutate({ expected_stage: "scenarios", run_async: false })}
          />
        ) : null}

        {stage === "decision_flow" ? (
          <DecisionFlowStage
            scenarios={analysis.scenarios}
            selectedScenarioId={decisionFlowScenarioId}
            onSelectScenario={setDecisionFlowScenarioId}
            onRunScenario={(scenarioId) => rerunMutation.mutate({ scenarioId })}
            runningScenarioId={rerunMutation.isPending ? rerunMutation.variables?.scenarioId ?? null : null}
          />
        ) : null}

        {stage === "final_review" ? (
          <>
            {analysis.extracted_product_data ? (
              <div className="space-y-4">
                <SectionHeader
                  eyebrow="Step 1"
                  title="Product Understanding"
                  body="Soft refresh from here if the LLM misunderstood the product. Downstream stages will be regenerated from this point."
                  actionLabel="Soft refresh from here"
                  onAction={() => {
                    setSoftRefreshOrigin("product_understanding");
                    reopenMutation.mutate({ stage: "product_understanding" });
                  }}
                  actionPending={reopenMutation.isPending && softRefreshOrigin === "product_understanding"}
                />
                <ProductSummaryPanel data={analysis.extracted_product_data} />
              </div>
            ) : null}

            {analysis.icp_profiles.length > 0 ? (
              <div className="space-y-4">
                <SectionHeader
                  eyebrow="Step 2"
                  title="ICP Profiles"
                  body="Soft refresh from the ICP step if one segment needs correction. Scenarios and simulations will be rebuilt from there."
                  actionLabel="Soft refresh from here"
                  onAction={() => {
                    setSoftRefreshOrigin("icp_profiles");
                    reopenMutation.mutate({
                      stage: "icp_profiles",
                      entity_id: selectedICPId ?? analysis.icp_profiles[0]?.id ?? null,
                    });
                  }}
                  actionPending={reopenMutation.isPending && softRefreshOrigin === "icp_profiles"}
                />
                <ICPCardGrid
                  icps={analysis.icp_profiles}
                  selectedICPId={selectedICPId}
                  comparedICPIds={compareICPIds}
                  onConfirmICP={(icpId) => setSelectedICPId(icpId)}
                  onEditICP={(icpId) => {
                    const target = analysis.icp_profiles.find((profile) => profile.id === icpId);
                    if (!target) return;
                    setEditingIcpId(target.id);
                    setIcpDraft(createIcpDraft(target));
                  }}
                  onToggleCompareICP={toggleCompareICP}
                  onRegenerateICP={(icpId) => {
                    setSoftRefreshOrigin("icp_profiles");
                    reopenMutation.mutate({ stage: "icp_profiles", entity_id: icpId });
                  }}
                  onClearComparedICP={clearCompareICPs}
                />
              </div>
            ) : null}

            {analysis.scenarios.length > 0 ? (
              <div className="space-y-4">
                <SectionHeader
                  eyebrow="Step 3"
                  title="Suggested Scenarios"
                  body="Soft refresh from scenarios if the pressure-test ideas need editing. Existing simulation runs will be cleared."
                  actionLabel="Soft refresh from here"
                  onAction={() => {
                    setSoftRefreshOrigin("scenarios");
                    reopenMutation.mutate({
                      stage: "scenarios",
                      entity_id: selectedScenarioId ?? analysis.scenarios[0]?.id ?? null,
                    });
                  }}
                  actionPending={reopenMutation.isPending && softRefreshOrigin === "scenarios"}
                />
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
              </div>
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
          </>
        ) : null}

        {updateProductMutation.error instanceof ApiError ? (
          <ErrorState title="Product update failed" message={updateProductMutation.error.message} />
        ) : null}
        {updateIcpMutation.error instanceof ApiError ? (
          <ErrorState title="ICP update failed" message={updateIcpMutation.error.message} />
        ) : null}
        {updateScenarioMutation.error instanceof ApiError ? (
          <ErrorState title="Scenario update failed" message={updateScenarioMutation.error.message} />
        ) : null}
        {proceedMutation.error instanceof ApiError ? (
          <ErrorState title="Could not continue workflow" message={proceedMutation.error.message} />
        ) : null}
        {reopenMutation.error instanceof ApiError ? (
          <ErrorState title="Could not reopen stage" message={reopenMutation.error.message} />
        ) : null}
        {feedbackMutation.error instanceof ApiError ? (
          <ErrorState title="Feedback could not be saved" message={feedbackMutation.error.message} />
        ) : null}
        {refreshMutation.error instanceof ApiError ? (
          <ErrorState title="Hard refresh failed" message={refreshMutation.error.message} />
        ) : null}
      </div>
      {editingIcp && icpDraft && typeof document !== "undefined"
        ? createPortal(
            <ICPEditSheet
              icp={editingIcp}
              draft={icpDraft}
              segmentWeightTotal={icpSegmentWeightTotal}
              isSaving={updateIcpMutation.isPending}
              onClose={() => {
                setEditingIcpId(null);
                setIcpDraft(null);
              }}
              onChange={setIcpDraft}
              onSave={() => updateIcpMutation.mutate({ icpId: editingIcp.id, payload: icpDraft })}
            />,
            document.body,
          )
        : null}
    </AppShell>
  );
}

function ProductUnderstandingStage({
  data,
  editing,
  draft,
  isSaving,
  isProceeding,
  onStartEdit,
  onCancelEdit,
  onChange,
  onSave,
  onProceed,
}: {
  data: AnalysisDetail["extracted_product_data"];
  editing: boolean;
  draft: ProductDraft;
  isSaving: boolean;
  isProceeding: boolean;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onChange: (draft: ProductDraft) => void;
  onSave: () => void;
  onProceed: () => void;
}) {
  if (!data) return null;
  return (
    <div className="space-y-4">
      <SectionHeader
        eyebrow="Step 1"
        title="Review the product understanding first"
        body="Next: generate ICP profiles from the reviewed product understanding."
        reviewStateLabel={data.is_user_edited ? "Reviewed by you" : "Ready to review"}
        actionLabel={editing ? "Cancel" : "Edit"}
        onAction={editing ? onCancelEdit : onStartEdit}
        statusBadge={
          data.is_user_edited ? (
            <span className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
              User reviewed
            </span>
          ) : (
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
              AI confidence {Math.round(data.confidence_score * 100)}%
            </span>
          )
        }
      />

      {editing ? (
        <section className="panel p-6">
          <div className="grid gap-4 md:grid-cols-2">
            <TextField label="Company name" value={draft.company_name} onChange={(value) => onChange({ ...draft, company_name: value })} />
            <TextField label="Product name" value={draft.product_name} onChange={(value) => onChange({ ...draft, product_name: value })} />
            <TextField label="Category" value={draft.category} onChange={(value) => onChange({ ...draft, category: value })} />
            <TextField label="Subcategory" value={draft.subcategory} onChange={(value) => onChange({ ...draft, subcategory: value })} />
          </div>
          <div className="mt-4 grid gap-4">
            <TextareaField
              label="Positioning summary"
              value={draft.positioning_summary}
              rows={4}
              onChange={(value) => onChange({ ...draft, positioning_summary: value })}
            />
            <TextareaField
              label="Pricing model"
              value={draft.pricing_model}
              rows={3}
              onChange={(value) => onChange({ ...draft, pricing_model: value })}
            />
            <TextareaField
              label="Feature clusters"
              hint="One item per line"
              value={draft.feature_clusters}
              rows={4}
              onChange={(value) => onChange({ ...draft, feature_clusters: value })}
            />
            <TextareaField
              label="Monetization hypothesis"
              value={draft.monetization_hypothesis}
              rows={4}
              onChange={(value) => onChange({ ...draft, monetization_hypothesis: value })}
            />
            <TextareaField
              label="Target customer signals"
              hint="One item per line"
              value={draft.target_customer_signals}
              rows={4}
              onChange={(value) => onChange({ ...draft, target_customer_signals: value })}
            />
            <TextareaField
              label="Warnings"
              hint="One item per line"
              value={draft.warnings}
              rows={3}
              onChange={(value) => onChange({ ...draft, warnings: value })}
            />
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-end gap-3">
            <button type="button" onClick={onCancelEdit} className={secondaryButtonClass}>
              Cancel
            </button>
            <button type="button" onClick={onSave} disabled={isSaving} className={primaryButtonClass}>
              {isSaving ? "Saving..." : "Save changes"}
            </button>
          </div>
        </section>
      ) : (
        <ProductSummaryPanel data={data} />
      )}

      <div className="flex justify-end">
        <button type="button" onClick={onProceed} disabled={isProceeding} className={primaryButtonClass}>
          {isProceeding ? "Generating..." : "Proceed to generate ICP profiles"}
        </button>
      </div>
    </div>
  );
}

function ICPReviewStage({
  icp,
  currentIndex,
  total,
  isConfirmed,
  editing,
  segmentWeightTotal,
  isProceeding,
  onPrevious,
  onNext,
  onStartEdit,
  onCancelEdit,
  onConfirm,
  onRegenerate,
  onProceed,
}: {
  icp: ICPProfile;
  currentIndex: number;
  total: number;
  isConfirmed: boolean;
  editing: boolean;
  segmentWeightTotal: number;
  isProceeding: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onConfirm: () => void;
  onRegenerate: () => void;
  onProceed: () => void;
}) {
  return (
    <div className="space-y-4">
      <SectionHeader
        eyebrow="Step 2"
        title={`ICP ${currentIndex + 1} of ${total}`}
        body="Review each profile one at a time. Next: generate suggested scenarios from the reviewed ICP set."
        reviewStateLabel={icp.is_user_edited ? "Reviewed by you" : "Ready to review"}
        actionLabel={editing ? "Close editor" : "Edit assumptions"}
        onAction={editing ? onCancelEdit : onStartEdit}
        statusBadge={
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
            Total segment share {formatSegmentShareTotal(segmentWeightTotal)}
          </span>
        }
      />

      <div className="mx-auto max-w-6xl">
        <ICPDetailCard
          icp={icp}
          variant="detail"
          isSelected
          isConfirmed={isConfirmed}
          onConfirm={onConfirm}
          onEdit={editing ? onCancelEdit : onStartEdit}
          onRegenerate={onRegenerate}
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <button type="button" onClick={onPrevious} disabled={currentIndex === 0} className={secondaryButtonClass}>
          Previous
        </button>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onNext}
            disabled={currentIndex >= total - 1}
            className={secondaryButtonClass}
          >
            Next
          </button>
          {currentIndex === total - 1 ? (
            <button type="button" onClick={onProceed} disabled={isProceeding} className={primaryButtonClass}>
              {isProceeding ? "Generating..." : "Proceed to Suggested Scenarios"}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ScenarioReviewStage({
  scenario,
  currentIndex,
  total,
  editing,
  draft,
  isSaving,
  isProceeding,
  onPrevious,
  onNext,
  onStartEdit,
  onCancelEdit,
  onChange,
  onSave,
  onProceed,
}: {
  scenario: Scenario;
  currentIndex: number;
  total: number;
  editing: boolean;
  draft: ScenarioDraft;
  isSaving: boolean;
  isProceeding: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onChange: (draft: ScenarioDraft) => void;
  onSave: () => void;
  onProceed: () => void;
}) {
  const review = getScenarioReviewModel(scenario);

  return (
    <div className="space-y-4">
      <SectionHeader
        eyebrow="Step 3"
        title={`Scenario ${currentIndex + 1} of ${total}`}
        body="Review the modeled upside, risks, and execution effort before choosing which scenario to run first."
        reviewStateLabel={scenario.is_user_edited ? "Reviewed by you" : "Ready to review"}
        actionLabel={editing ? "Cancel" : "Edit assumptions"}
        onAction={editing ? onCancelEdit : onStartEdit}
        statusBadge={
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
            Rank #{review.recommendation.priority_rank}
          </span>
        }
      />

      {editing ? (
        <section className="panel p-6">
          <div className="space-y-4">
            <TextField label="Title" value={draft.title} onChange={(value) => onChange({ ...draft, title: value })} />
            <TextareaField label="Description" value={draft.description} rows={4} onChange={(value) => onChange({ ...draft, description: value })} />
          </div>
          <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Structured inputs</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              These parameters drive the impact preview and recommendation logic. Keep the decision statement clear.
            </p>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {scenario.input_parameters_schema.fields.map((field) =>
                field.input_type === "number" ? (
                  <NumberField
                    key={field.key}
                    label={field.label}
                    hint={field.helper_text ?? undefined}
                    value={Number(draft.input_parameters[field.key] ?? 0)}
                    min={field.minimum ?? undefined}
                    max={field.maximum ?? undefined}
                    step={field.step ?? 0.1}
                    onChange={(value) =>
                      onChange({
                        ...draft,
                        input_parameters: { ...draft.input_parameters, [field.key]: value },
                      })
                    }
                  />
                ) : (
                  <TextField
                    key={field.key}
                    label={field.label}
                    hint={field.helper_text ?? undefined}
                    value={String(draft.input_parameters[field.key] ?? "")}
                    onChange={(value) =>
                      onChange({
                        ...draft,
                        input_parameters: { ...draft.input_parameters, [field.key]: value },
                      })
                    }
                  />
                ),
              )}
            </div>
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-end gap-3">
            <button type="button" onClick={onCancelEdit} className={secondaryButtonClass}>
              Cancel
            </button>
            <button type="button" onClick={onSave} disabled={isSaving} className={primaryButtonClass}>
              {isSaving ? "Saving..." : "Save changes"}
            </button>
          </div>
        </section>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
              {review.recommendation.recommendation_label}
            </span>
            <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold capitalize text-slate-700">
              Effort {review.execution_effort.level}
            </span>
            {review.metadata.scenario_tags.slice(0, 2).map((tag) => (
              <span key={tag} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
                {tag}
              </span>
            ))}
          </div>
          <ScenarioReviewCard scenario={scenario} />
        </>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <button type="button" onClick={onPrevious} disabled={currentIndex === 0} className={secondaryButtonClass}>
          Previous
        </button>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onNext}
            disabled={currentIndex >= total - 1}
            className={secondaryButtonClass}
          >
            Next
          </button>
          {currentIndex === total - 1 ? (
            <button type="button" onClick={onProceed} disabled={isProceeding} className={primaryButtonClass}>
              {isProceeding ? "Opening..." : "Proceed to Run Selection"}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function DecisionFlowStage({
  scenarios,
  selectedScenarioId,
  onSelectScenario,
  onRunScenario,
  runningScenarioId,
}: {
  scenarios: Scenario[];
  selectedScenarioId: string | null;
  onSelectScenario: (scenarioId: string) => void;
  onRunScenario: (scenarioId: string) => void;
  runningScenarioId: string | null;
}) {
  return (
    <div className="space-y-4">
      <SectionHeader
        eyebrow="Step 4"
        title="Choose the first scenario to run"
        body="Pick one reviewed scenario, run it, and use that first decision flow as the bridge into final review."
      />
      <div className="grid gap-4 xl:grid-cols-3">
        {scenarios.map((scenario) => (
          <div
            key={scenario.id}
            className={cn(
              "panel p-5 text-left transition hover:border-slate-300",
              selectedScenarioId === scenario.id && "border-slate-900 ring-2 ring-slate-900/10",
            )}
          >
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
              {scenario.scenario_type.replaceAll("_", " ")}
            </p>
            <h3 className="mt-2 text-lg font-semibold text-slate-950">{scenario.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{scenario.description}</p>
            <div className="mt-4 flex justify-between gap-3">
              <button type="button" onClick={() => onSelectScenario(scenario.id)} className={secondaryButtonClass}>
                {selectedScenarioId === scenario.id ? "Selected" : "Select"}
              </button>
              <button
                type="button"
                onClick={() => onRunScenario(scenario.id)}
                disabled={runningScenarioId === scenario.id}
                className={primaryButtonClass}
              >
                {runningScenarioId === scenario.id ? "Running..." : "Run selected simulation"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SectionHeader({
  eyebrow,
  title,
  body,
  reviewStateLabel,
  actionLabel,
  onAction,
  actionPending = false,
  statusBadge,
}: {
  eyebrow: string;
  title: string;
  body: string;
  reviewStateLabel?: string;
  actionLabel?: string;
  onAction?: () => void;
  actionPending?: boolean;
  statusBadge?: ReactNode;
}) {
  return (
    <section className="panel p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{eyebrow}</p>
            {reviewStateLabel ? (
              <>
                <span aria-hidden className="h-1 w-1 rounded-full bg-slate-300" />
                <p className="text-xs font-medium text-slate-500">{reviewStateLabel}</p>
              </>
            ) : null}
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{body}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {statusBadge}
          {actionLabel && onAction ? (
            <button type="button" onClick={onAction} disabled={actionPending} className={secondaryButtonClass}>
              {actionPending ? "Working..." : actionLabel}
            </button>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function TextField({
  label,
  value,
  onChange,
  hint,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  hint?: string;
}) {
  return (
    <label className="space-y-2 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      {hint ? <p className="text-xs text-slate-500">{hint}</p> : null}
      <input className={fieldClass} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function TextareaField({
  label,
  value,
  onChange,
  rows,
  hint,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows: number;
  hint?: string;
}) {
  return (
    <label className="space-y-2 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      {hint ? <p className="text-xs text-slate-500">{hint}</p> : null}
      <textarea className={textareaClass} rows={rows} value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function PercentField({
  label,
  value,
  onChange,
  hint,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  hint?: string;
}) {
  const safeValue = Math.round((Number.isFinite(value) ? value : 0) * 1000) / 10;

  return (
    <label className="space-y-2 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      {hint ? <p className="text-xs text-slate-500">{hint}</p> : null}
      <div className="relative">
        <input
          type="number"
          className={cn(fieldClass, "pr-10")}
          value={safeValue}
          min={1}
          max={100}
          step={0.1}
          onChange={(event) => onChange(Number(event.target.value) / 100)}
        />
        <span className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-sm font-medium text-slate-500">
          %
        </span>
      </div>
    </label>
  );
}

function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  step,
  hint,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  hint?: string;
}) {
  return (
    <label className="space-y-2 text-sm">
      <span className="font-medium text-slate-700">{label}</span>
      {hint ? <p className="text-xs text-slate-500">{hint}</p> : null}
      <input
        type="number"
        className={fieldClass}
        value={Number.isFinite(value) ? value : 0}
        min={min}
        max={max}
        step={step}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function ICPEditSheet({
  icp,
  draft,
  segmentWeightTotal,
  isSaving,
  onClose,
  onChange,
  onSave,
}: {
  icp: ICPProfile;
  draft: IcpDraft;
  segmentWeightTotal: number;
  isSaving: boolean;
  onClose: () => void;
  onChange: (draft: IcpDraft) => void;
  onSave: () => void;
}) {
  const canAddDriver = draft.driver_rows.length < Math.min(6, decisionDriverOptions.length);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        aria-label="Close assumptions editor"
        className="absolute inset-0 bg-slate-950/25"
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="icp-assumptions-title"
        className="relative z-10 flex h-full w-full max-w-2xl flex-col border-l border-slate-200 bg-white shadow-[0_24px_80px_rgba(15,23,42,0.18)]"
      >
        <div className="border-b border-slate-200 px-6 py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Edit assumptions</p>
              <h2 id="icp-assumptions-title" className="mt-2 text-2xl font-semibold text-slate-950">
                {icp.name}
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Tune the assumptions that most affect simulation, then save to update this ICP everywhere.
              </p>
            </div>
            <button type="button" onClick={onClose} className={secondaryButtonClass}>
              Close
            </button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
              Total segment share {formatSegmentShareTotal(segmentWeightTotal)}
            </span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
              Quick edit fields only
            </span>
          </div>
        </div>

        <div className="flex-1 space-y-8 overflow-y-auto px-6 py-6">
          <section className="space-y-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Segment identity</p>
              <h3 className="mt-1 text-lg font-semibold text-slate-950">What segment are we modeling?</h3>
            </div>
            <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
              <TextField
                label="Segment name"
                value={draft.name}
                onChange={(value) => onChange({ ...draft, name: value })}
              />
              <PercentField
                label="Segment share"
                hint="Share of the total modeled ICP mix."
                value={draft.segment_weight}
                onChange={(value) => onChange({ ...draft, segment_weight: value })}
              />
            </div>
          </section>

          <section className="space-y-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Behavioral signals</p>
              <h3 className="mt-1 text-lg font-semibold text-slate-950">How does this segment evaluate and adopt?</h3>
            </div>
            <div className="space-y-4">
              {icpSignalKeys.map((signalKey) => (
                <SignalDotScaleField
                  key={signalKey}
                  signalKey={signalKey}
                  value={getSignalLevelForDraft(draft, signalKey)}
                  onChange={(level) => onChange(updateDraftSignalLevel(draft, signalKey, level))}
                />
              ))}
            </div>
          </section>

          <section className="space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Decision drivers</p>
                <h3 className="mt-1 text-lg font-semibold text-slate-950">What matters most in the buying decision?</h3>
              </div>
              <button
                type="button"
                disabled={!canAddDriver}
                onClick={() => onChange({ ...draft, driver_rows: [...draft.driver_rows, createEmptyDriverRow(draft.driver_rows)] })}
                className={secondaryButtonClass}
              >
                Add driver
              </button>
            </div>
            <div className="space-y-3">
              {draft.driver_rows.map((row, index) => (
                <DecisionDriverRowEditor
                  key={`${row.driver}-${index}`}
                  row={row}
                  index={index}
                  usedDrivers={draft.driver_rows.map((item) => item.driver)}
                  onChange={(nextRow) =>
                    onChange({
                      ...draft,
                      driver_rows: draft.driver_rows.map((item, rowIndex) => (rowIndex === index ? nextRow : item)),
                    })
                  }
                  onRemove={() =>
                    onChange({
                      ...draft,
                      driver_rows: draft.driver_rows.filter((_, rowIndex) => rowIndex !== index),
                    })
                  }
                />
              ))}
            </div>
          </section>

          <details className="rounded-3xl border border-slate-200 bg-slate-50/80 px-5 py-4">
            <summary className="cursor-pointer list-none text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 [&::-webkit-details-marker]:hidden">
              Source assumptions
            </summary>
            <div className="mt-5 space-y-4">
              <TextareaField
                label="Description"
                value={draft.description}
                rows={4}
                onChange={(value) => onChange({ ...draft, description: value })}
              />
              <TextareaField
                label="Use case"
                value={draft.use_case}
                rows={4}
                onChange={(value) => onChange({ ...draft, use_case: value })}
              />
              <TextareaField
                label="Goals"
                hint="One item per line"
                value={draft.goals}
                rows={4}
                onChange={(value) => onChange({ ...draft, goals: value })}
              />
              <TextareaField
                label="Pain points"
                hint="One item per line"
                value={draft.pain_points}
                rows={4}
                onChange={(value) => onChange({ ...draft, pain_points: value })}
              />
              <TextareaField
                label="Alternatives"
                hint="One item per line"
                value={draft.alternatives}
                rows={4}
                onChange={(value) => onChange({ ...draft, alternatives: value })}
              />
              <TextareaField
                label="Value explanation"
                value={draft.value_perception_explanation}
                rows={5}
                onChange={(value) => onChange({ ...draft, value_perception_explanation: value })}
              />
            </div>
          </details>
        </div>

        <div className="border-t border-slate-200 px-6 py-4">
          <div className="flex flex-wrap items-center justify-end gap-3">
            <button type="button" onClick={onClose} className={secondaryButtonClass}>
              Cancel
            </button>
            <button type="button" onClick={onSave} disabled={isSaving} className={primaryButtonClass}>
              {isSaving ? "Saving..." : "Save changes"}
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
}

function SignalDotScaleField({
  signalKey,
  value,
  onChange,
}: {
  signalKey: ICPSignalKey;
  value: ICPSignalLevel;
  onChange: (level: ICPSignalLevel) => void;
}) {
  const copy = signalCopy[signalKey];

  return (
    <fieldset className="space-y-3 rounded-3xl border border-slate-200 bg-slate-50 px-4 py-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <legend className="text-sm font-semibold text-slate-900">{copy.label}</legend>
          <p className="mt-1 text-xs text-slate-500">{copy.helper}</p>
        </div>
        <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
          {signalLevelLabels[value]}
        </span>
      </div>
      <DotScalePicker label={copy.label} value={value} onChange={(next) => onChange(next as ICPSignalLevel)} />
      <div className="flex items-center justify-between gap-3 text-xs font-medium text-slate-500">
        <span>{copy.minLabel}</span>
        <span>{copy.maxLabel}</span>
      </div>
    </fieldset>
  );
}

function DecisionDriverRowEditor({
  row,
  index,
  usedDrivers,
  onChange,
  onRemove,
}: {
  row: { driver: string; weight: number };
  index: number;
  usedDrivers: string[];
  onChange: (row: { driver: string; weight: number }) => void;
  onRemove: () => void;
}) {
  const selectedLevel = getDriverWeightLevel(row.weight);
  const availableDrivers = decisionDriverOptions.filter((option) => option === row.driver || !usedDrivers.includes(option));

  return (
    <div className="grid gap-3 rounded-3xl border border-slate-200 bg-white px-4 py-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] lg:items-start">
      <label className="space-y-2 text-sm">
        <span className="font-medium text-slate-700">Driver</span>
        <select
          className={fieldClass}
          value={row.driver}
          onChange={(event) => onChange({ ...row, driver: event.target.value })}
        >
          {availableDrivers.map((option) => (
            <option key={option} value={option}>
              {formatDriverLabel(option)}
            </option>
          ))}
        </select>
      </label>
      <fieldset className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <legend className="text-sm font-medium text-slate-700">Importance</legend>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
            {selectedLevel > 0 ? `${selectedLevel}/5` : "Off"}
          </span>
        </div>
        <DotScalePicker
          label={`Weight for ${formatDriverLabel(row.driver)}`}
          value={selectedLevel}
          allowZero
          onChange={(level) => onChange({ ...row, weight: getDriverWeightFromLevel(level) })}
        />
      </fieldset>
      <button type="button" onClick={onRemove} className={secondaryButtonClass}>
        Remove
      </button>
    </div>
  );
}

function DotScalePicker({
  label,
  value,
  onChange,
  allowZero = false,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  allowZero?: boolean;
}) {
  const steps = allowZero ? [0, ...signalScale] : [...signalScale];
  const groupName = label.toLowerCase().replace(/[^a-z0-9]+/g, "-");

  return (
    <div className="flex flex-wrap items-center gap-2" role="radiogroup" aria-label={label}>
      {steps.map((step) => (
        <label key={`${label}-${step}`} className="cursor-pointer">
          <input
            type="radio"
            name={groupName}
            className="sr-only"
            checked={value === step}
            aria-label={step === 0 ? `${label} off` : `${label} ${step} out of 5`}
            onChange={() => onChange(step)}
          />
          <span
            className={cn(
              "block h-3.5 w-3.5 rounded-full border transition",
              value >= step && step !== 0 ? "border-slate-900 bg-slate-900" : "border-slate-300 bg-white",
              step === 0 && "flex h-auto w-auto rounded-full px-2.5 py-1 text-[11px] font-semibold",
              step === 0 && value === 0 ? "border-slate-900 bg-slate-900 text-white" : "",
            )}
          >
            {step === 0 ? "Off" : <span className="sr-only">{step}</span>}
          </span>
        </label>
      ))}
    </div>
  );
}

function createProductDraft(data: NonNullable<AnalysisDetail["extracted_product_data"]>): ProductDraft {
  return {
    company_name: data.company_name,
    product_name: data.product_name,
    category: data.category,
    subcategory: data.subcategory,
    positioning_summary: data.positioning_summary,
    pricing_model: data.pricing_model,
    feature_clusters: data.normalized_json.feature_clusters.join("\n"),
    monetization_hypothesis: data.monetization_hypothesis,
    target_customer_signals: data.normalized_json.target_customer_signals.join("\n"),
    warnings: (data.normalized_json.warnings ?? []).join("\n"),
  };
}

function createIcpDraft(icp: ICPProfile): IcpDraft {
  return {
    name: icp.name,
    description: icp.description,
    use_case: icp.use_case,
    goals: icp.goals_json.join("\n"),
    pain_points: icp.pain_points_json.join("\n"),
    alternatives: icp.alternatives_json.join("\n"),
    value_perception_explanation: icp.value_perception_explanation,
    price_sensitivity: icp.price_sensitivity,
    switching_cost: icp.switching_cost,
    churn_threshold: icp.churn_threshold,
    retention_threshold: icp.retention_threshold,
    adoption_friction: icp.adoption_friction,
    segment_weight: icp.segment_weight,
    driver_rows: getEditableDriverRows(icp),
  };
}

function createScenarioDraft(scenario: Scenario): ScenarioDraft {
  return {
    title: scenario.title,
    description: scenario.description,
    input_parameters: Object.fromEntries(
      Object.entries(scenario.input_parameters_json).map(([key, value]) => [key, getEditableScenarioValue(scenario, key, value)]),
    ),
  };
}

function buildScenarioPayload(scenario: Scenario, values: Record<string, string | number>) {
  return Object.fromEntries(
    Object.entries(values)
      .filter(([, value]) => value !== "" && value !== null && value !== undefined)
      .map(([key, value]) => {
        if (typeof value === "number") {
          return [key, value];
        }
        const numeric = Number(value);
        return Number.isNaN(numeric) || value.trim() === "" ? [key, value] : [key, numeric];
      }),
  );
}

function getEditableScenarioValue(scenario: Scenario, key: string, value: unknown) {
  if (
    typeof value === "number" &&
    key === "price_change_percent" &&
    (scenario.scenario_type === "pricing_decrease" || scenario.scenario_type === "unbundling")
  ) {
    return Math.abs(value);
  }
  return typeof value === "number" ? value : String(value ?? "");
}

function splitLines(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function clampIndex(index: number, total: number) {
  if (total === 0) return 0;
  return Math.max(0, Math.min(index, total - 1));
}

function roundToPercent(value: number) {
  return Math.round(value * 1000) / 1000;
}

function formatSegmentShareTotal(value: number) {
  return formatSegmentShare(Math.round(value * 1000) / 10);
}

function getSignalLevelForDraft(draft: IcpDraft, signalKey: ICPSignalKey) {
  return getSignalLevelFromRaw(signalKey, {
    price_sensitivity: draft.price_sensitivity,
    switching_cost: draft.switching_cost,
    retention_threshold: draft.retention_threshold,
    adoption_friction: draft.adoption_friction,
    churn_threshold: draft.churn_threshold,
  } as ICPProfile);
}

function updateDraftSignalLevel(draft: IcpDraft, signalKey: ICPSignalKey, level: ICPSignalLevel): IcpDraft {
  const rawValue = getRawValueFromSignalLevel(signalKey, level);

  switch (signalKey) {
    case "priceSensitivity":
      return { ...draft, price_sensitivity: rawValue };
    case "switchingFriction":
      return { ...draft, switching_cost: rawValue };
    case "proofRequirement":
      return { ...draft, retention_threshold: rawValue };
    case "implementationTolerance":
      return { ...draft, adoption_friction: rawValue };
    case "retentionStability":
      return { ...draft, churn_threshold: rawValue };
    default:
      return draft;
  }
}

function createEmptyDriverRow(existingRows: { driver: string; weight: number }[]) {
  const used = new Set(existingRows.map((row) => row.driver));
  const nextDriver = decisionDriverOptions.find((option) => !used.has(option)) ?? decisionDriverOptions[0];
  return { driver: nextDriver, weight: 0 };
}

const signalLevelLabels: Record<ICPSignalLevel, string> = {
  1: "Very low",
  2: "Low",
  3: "Medium",
  4: "High",
  5: "Very high",
};

const signalCopy: Record<
  ICPSignalKey,
  { label: string; helper: string; minLabel: string; maxLabel: string }
> = {
  priceSensitivity: {
    label: "Price Sensitivity",
    helper: "How strongly price shapes the buying decision.",
    minLabel: "Price matters less",
    maxLabel: "Price matters a lot",
  },
  switchingFriction: {
    label: "Switching Friction",
    helper: "How hard it is to displace the current setup.",
    minLabel: "Easy to replace",
    maxLabel: "Hard to replace",
  },
  timeToValueExpectation: {
    label: "Time-to-Value Expectation",
    helper: "Derived from how quickly the segment expects visible value.",
    minLabel: "Can wait longer",
    maxLabel: "Needs value fast",
  },
  proofRequirement: {
    label: "Proof Requirement",
    helper: "How much evidence the segment needs before committing.",
    minLabel: "Low proof needed",
    maxLabel: "Needs strong proof",
  },
  implementationTolerance: {
    label: "Implementation Tolerance",
    helper: "How much setup and change effort this segment can absorb.",
    minLabel: "Easy rollout",
    maxLabel: "Heavy rollout",
  },
  retentionStability: {
    label: "Retention Stability",
    helper: "How resilient the segment stays when value is uneven.",
    minLabel: "Leaves quickly",
    maxLabel: "Sticks through issues",
  },
};

function formatKeyLabel(key: string) {
  return key
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function formatParameterValue(value: unknown) {
  if (typeof value === "number") return `${value}`;
  return String(value);
}

const fieldClass =
  "w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-900/10";
const textareaClass =
  "w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-900/10";
const primaryButtonClass =
  "rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400";
const secondaryButtonClass =
  "rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-500 hover:bg-slate-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400";
