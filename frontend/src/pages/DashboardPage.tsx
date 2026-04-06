import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { createAnalysis, listAnalyses } from "@/api/analyses";
import { ApiError } from "@/api/client";
import { EmptyState } from "@/components/analysis/EmptyState";
import { ErrorState } from "@/components/analysis/ErrorState";
import { LoadingState } from "@/components/analysis/LoadingState";
import { URLSubmitForm } from "@/components/forms/URLSubmitForm";
import { AppShell } from "@/components/layout/AppShell";
import { formatDate } from "@/lib/utils";

export function DashboardPage() {
  const navigate = useNavigate();
  const analysesQuery = useQuery({
    queryKey: ["analyses"],
    queryFn: listAnalyses,
  });
  const createMutation = useMutation({
    mutationFn: createAnalysis,
    onSuccess: (data) => {
      navigate(`/analyses/${data.analysis.id}`);
    },
  });

  return (
    <AppShell
      title="Decision Simulation Workspace"
      subtitle="Submit a product URL, inspect generated ICPs, and compare scenario outcomes."
    >
      <div className="space-y-8">
        <URLSubmitForm
          isLoading={createMutation.isPending}
          onSubmit={async (values) => {
            await createMutation.mutateAsync({ url: values.url, run_async: true });
          }}
        />

        {createMutation.error instanceof ApiError ? (
          <ErrorState title="Unable to create analysis" message={createMutation.error.message} />
        ) : null}

        <section className="panel overflow-hidden">
          <div className="panel-header">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Recent Analyses</p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950">Continue where you left off</h2>
            </div>
          </div>
          <div className="p-6">
            {analysesQuery.isLoading ? <LoadingState title="Loading analyses" /> : null}
            {analysesQuery.error instanceof ApiError ? (
              <ErrorState title="Could not load analyses" message={analysesQuery.error.message} />
            ) : null}
            {analysesQuery.data && analysesQuery.data.length > 0 ? (
              <div className="grid gap-4 xl:grid-cols-2">
                {analysesQuery.data.map((analysis) => (
                  <Link key={analysis.id} to={`/analyses/${analysis.id}`} className="rounded-3xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-400 hover:bg-white">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{analysis.status}</p>
                    <h3 className="mt-3 text-lg font-semibold text-slate-950">{analysis.normalized_url}</h3>
                    <p className="mt-2 text-sm text-slate-600">Created {formatDate(analysis.created_at)}</p>
                    {analysis.error_message ? <p className="mt-3 text-sm text-red-700">{analysis.error_message}</p> : null}
                  </Link>
                ))}
              </div>
            ) : null}
            {analysesQuery.data && analysesQuery.data.length === 0 ? (
              <EmptyState
                title="No analyses yet"
                message="Start with a URL. The engine will build a product model, ICPs, and scenario simulations automatically."
              />
            ) : null}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
