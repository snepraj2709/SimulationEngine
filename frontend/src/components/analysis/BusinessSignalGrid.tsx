import { DotScaleIndicator } from "@/components/analysis/DotScaleIndicator";
import { ProductBusinessSignal } from "@/types/api";

interface BusinessSignalGridProps {
  signals: ProductBusinessSignal[];
}

export function BusinessSignalGrid({ signals }: BusinessSignalGridProps) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Business Model Signals</p>
          <p className="mt-1 text-sm text-slate-600">Compact assumptions that will shape ICP quality and scenario realism.</p>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {signals.map((signal) => (
          <BusinessSignalRow key={signal.key} signal={signal} />
        ))}
      </div>
    </section>
  );
}

function BusinessSignalRow({ signal }: { signal: ProductBusinessSignal }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{signal.label}</p>
          <p className="mt-2 text-sm font-semibold text-slate-950">{signal.value}</p>
        </div>
        <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600">
          {Math.round(signal.confidence * 100)}%
        </span>
      </div>
      {signal.score_1_to_5 ? (
        <div className="mt-4 flex items-center justify-between gap-3">
          <DotScaleIndicator label={signal.label} value={signal.score_1_to_5} compact />
          <p className="text-xs font-medium text-slate-500">1 low to 5 high</p>
        </div>
      ) : null}
    </article>
  );
}
