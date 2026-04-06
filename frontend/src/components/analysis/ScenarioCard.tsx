import { Scenario, ScenarioSimulationSummary } from "@/types/api";
import { cn, formatPercent } from "@/lib/utils";

interface ScenarioCardProps {
  scenario: Scenario;
  summary?: ScenarioSimulationSummary;
  isSelected?: boolean;
  isCompared?: boolean;
  isRunning?: boolean;
  onSelect?: () => void;
  onCompare?: () => void;
  onRun?: () => void;
}

export function ScenarioCard({
  scenario,
  summary,
  isSelected = false,
  isCompared = false,
  isRunning = false,
  onSelect,
  onCompare,
  onRun,
}: ScenarioCardProps) {
  return (
    <div className={cn("panel p-5", isSelected && "border-slate-900 ring-2 ring-slate-900/10")}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            {scenario.scenario_type.replaceAll("_", " ")}
          </p>
          <h3 className="mt-2 text-lg font-semibold text-slate-950">{scenario.title}</h3>
          <p className="mt-2 text-sm text-slate-600">{scenario.description}</p>
        </div>
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={onSelect}
            className="rounded-full border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-500 hover:bg-slate-100"
          >
            Inspect
          </button>
          <button
            type="button"
            onClick={onCompare}
            className={cn(
              "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
              isCompared
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-300 text-slate-700 hover:border-slate-500 hover:bg-slate-100",
            )}
          >
            {isCompared ? "Selected" : "Compare"}
          </button>
        </div>
      </div>
      {summary ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Metric label="Retention" value={formatPercent(summary.projected_retention_pct)} />
          <Metric label="Churn" value={formatPercent(summary.projected_churn_pct)} />
          <Metric label="Downgrade" value={formatPercent(summary.projected_downgrade_pct)} />
          <Metric label="Revenue Δ" value={formatPercent(summary.estimated_revenue_delta_pct)} />
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">No simulation run yet for this scenario.</p>
      )}
      <div className="mt-4 flex justify-end">
        <button
          type="button"
          onClick={onRun}
          disabled={isRunning}
          className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isRunning ? "Running..." : "Re-run simulation"}
        </button>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-50 px-3 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}
