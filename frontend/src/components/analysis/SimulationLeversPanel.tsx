import { ProductSimulationLever } from "@/types/api";

interface SimulationLeversPanelProps {
  levers: ProductSimulationLever[];
}

export function SimulationLeversPanel({ levers }: SimulationLeversPanelProps) {
  return (
    <section className="space-y-3">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Likely Simulation Levers</p>
        <p className="mt-1 text-sm text-slate-600">These are the variables the system believes matter most for scenario generation and simulation.</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {levers.map((lever) => (
          <article key={lever.key} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-900">{lever.label}</p>
              <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                {Math.round(lever.confidence * 100)}%
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">{lever.why_it_matters}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
