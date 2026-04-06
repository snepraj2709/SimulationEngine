import { ScenarioSimulationSummary } from "@/types/api";
import { formatPercent } from "@/lib/utils";

interface ScenarioComparisonTableProps {
  summaries: ScenarioSimulationSummary[];
}

export function ScenarioComparisonTable({ summaries }: ScenarioComparisonTableProps) {
  return (
    <section className="panel overflow-hidden">
      <div className="panel-header">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Scenario Comparison</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-950">Which move creates the cleanest downstream profile?</h2>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr className="text-left text-xs uppercase tracking-[0.16em] text-slate-500">
              <th className="px-6 py-4">Scenario</th>
              <th className="px-6 py-4">Retention</th>
              <th className="px-6 py-4">Downgrade</th>
              <th className="px-6 py-4">Upgrade</th>
              <th className="px-6 py-4">Churn</th>
              <th className="px-6 py-4">Revenue Δ</th>
              <th className="px-6 py-4">Highest risk ICPs</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {summaries.map((summary) => (
              <tr key={summary.scenario_id} className="align-top text-sm text-slate-700">
                <td className="px-6 py-4 font-semibold text-slate-950">{summary.scenario_title}</td>
                <td className="px-6 py-4">{formatPercent(summary.projected_retention_pct)}</td>
                <td className="px-6 py-4">{formatPercent(summary.projected_downgrade_pct)}</td>
                <td className="px-6 py-4">{formatPercent(summary.projected_upgrade_pct)}</td>
                <td className="px-6 py-4">{formatPercent(summary.projected_churn_pct)}</td>
                <td className="px-6 py-4">{formatPercent(summary.estimated_revenue_delta_pct)}</td>
                <td className="px-6 py-4">{summary.highest_risk_icps.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
