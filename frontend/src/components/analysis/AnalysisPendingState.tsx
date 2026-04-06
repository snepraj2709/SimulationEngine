import { AnalysisStatus } from "@/types/api";

interface AnalysisPendingStateProps {
  url: string;
  status: AnalysisStatus;
}

function PendingCard({ title, lines }: { title: string; lines: number[] }) {
  return (
    <section className="panel overflow-hidden">
      <div className="panel-header">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{title}</p>
          <div className="mt-3 h-5 w-48 animate-pulse rounded-full bg-slate-200" />
        </div>
      </div>
      <div className="space-y-4 px-6 py-6">
        {lines.map((width) => (
          <div key={width} className="h-4 animate-pulse rounded-full bg-slate-200" style={{ width: `${width}%` }} />
        ))}
      </div>
    </section>
  );
}

export function AnalysisPendingState({ url, status }: AnalysisPendingStateProps) {
  const verb = status === "queued" ? "Queued for analysis" : "Analyzing website";

  return (
    <div className="space-y-6">
      <section className="panel p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{verb}</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">Preparing results for the submitted URL</h2>
            <p className="mt-2 break-all text-sm text-slate-600">{url}</p>
          </div>
          <div className="flex items-center gap-4 rounded-3xl border border-slate-200 bg-slate-50 px-5 py-4">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-700" />
            <div>
              <p className="text-sm font-semibold text-slate-900">
                {status === "queued" ? "The request is waiting for the pipeline." : "The pipeline is extracting and generating."}
              </p>
              <p className="text-xs text-slate-500">
                Product summary, ICPs, and scenarios will appear here when the current URL is ready.
              </p>
            </div>
          </div>
        </div>
      </section>

      <PendingCard title="Product Understanding" lines={[72, 94, 86, 56]} />
      <PendingCard title="Ideal Customer Profiles" lines={[92, 88, 75, 81, 68]} />
      <PendingCard title="Suggested Scenarios" lines={[90, 84, 78, 88]} />
    </div>
  );
}
