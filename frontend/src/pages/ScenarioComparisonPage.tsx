import { Link, useParams } from "react-router-dom";

import { EmptyState } from "@/components/analysis/EmptyState";
import { ErrorState } from "@/components/analysis/ErrorState";
import { LoadingState } from "@/components/analysis/LoadingState";
import { ScenarioComparisonTable } from "@/components/analysis/ScenarioComparisonTable";
import { SimulationMetricsDashboard } from "@/components/analysis/SimulationMetricsDashboard";
import { AppShell } from "@/components/layout/AppShell";
import { useAnalysisPolling } from "@/hooks/use-analysis-polling";
import { getLatestRunForScenario } from "@/lib/analysis";
import { useUIStore } from "@/store/ui-store";
import { ApiError } from "@/api/client";

export function ScenarioComparisonPage() {
  const { analysisId = "" } = useParams();
  const compareScenarioIds = useUIStore((state) => state.compareScenarioIds);
  const analysisQuery = useAnalysisPolling(analysisId);

  if (analysisQuery.isLoading) {
    return (
      <AppShell title="Scenario comparison">
        <LoadingState title="Loading comparison" />
      </AppShell>
    );
  }

  if (analysisQuery.error instanceof ApiError) {
    return (
      <AppShell title="Scenario comparison">
        <ErrorState title="Comparison unavailable" message={analysisQuery.error.message} />
      </AppShell>
    );
  }

  const analysis = analysisQuery.data;
  if (!analysis) {
    return (
      <AppShell title="Scenario comparison">
        <EmptyState title="Missing analysis" message="The underlying analysis could not be loaded." />
      </AppShell>
    );
  }

  const summaries = (compareScenarioIds.length ? compareScenarioIds : analysis.scenarios.slice(0, 2).map((scenario) => scenario.id))
    .map((scenarioId) => getLatestRunForScenario(analysis, scenarioId)?.summary)
    .filter((summary): summary is NonNullable<typeof summary> => Boolean(summary));

  return (
    <AppShell title="Scenario comparison" subtitle={analysis.normalized_url}>
      <div className="mb-6">
        <Link to={`/analyses/${analysis.id}`} className="text-sm font-semibold text-slate-700 underline">
          Back to analysis
        </Link>
      </div>
      {summaries.length === 0 ? (
        <EmptyState
          title="No scenario runs selected"
          message="Select scenarios from the analysis page to compare them here."
        />
      ) : (
        <div className="space-y-8">
          <SimulationMetricsDashboard summaries={summaries} />
          <ScenarioComparisonTable summaries={summaries} />
        </div>
      )}
    </AppShell>
  );
}
