import { AnalysisStatus } from "@/types/api";

const statusCopy: Record<AnalysisStatus, { label: string; body: string; tone: string }> = {
  queued: {
    label: "Queued",
    body: "The analysis request has been accepted and is waiting for the extraction pipeline.",
    tone: "border-slate-300 bg-slate-100 text-slate-700",
  },
  processing: {
    label: "Processing",
    body: "The engine is scraping the site, inferring the product model, and generating simulation artifacts.",
    tone: "border-teal-300 bg-teal-50 text-teal-700",
  },
  completed: {
    label: "Completed",
    body: "The analysis finished successfully and all default scenarios are ready to inspect.",
    tone: "border-emerald-300 bg-emerald-50 text-emerald-700",
  },
  failed: {
    label: "Failed",
    body: "The analysis could not complete. Review the error details and try again.",
    tone: "border-red-300 bg-red-50 text-red-700",
  },
};

interface AnalysisStatusCardProps {
  status: AnalysisStatus;
  errorMessage?: string | null;
}

export function AnalysisStatusCard({ status, errorMessage }: AnalysisStatusCardProps) {
  const copy = statusCopy[status];
  return (
    <div className="panel p-6">
      <div className={`metric-pill ${copy.tone}`}>{copy.label}</div>
      <p className="mt-4 text-sm text-slate-700">{copy.body}</p>
      {errorMessage ? <p className="mt-3 text-sm text-red-700">{errorMessage}</p> : null}
    </div>
  );
}
