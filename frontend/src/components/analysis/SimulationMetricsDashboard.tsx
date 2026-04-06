import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ScenarioSimulationSummary } from "@/types/api";
import { formatPercent } from "@/lib/utils";

interface SimulationMetricsDashboardProps {
  summaries: ScenarioSimulationSummary[];
}

export function SimulationMetricsDashboard({ summaries }: SimulationMetricsDashboardProps) {
  const chartData = summaries.map((summary) => ({
    name: summary.scenario_title,
    retention: summary.projected_retention_pct,
    downgrade: summary.projected_downgrade_pct,
    upgrade: summary.projected_upgrade_pct,
    churn: summary.projected_churn_pct,
    revenueDelta: summary.estimated_revenue_delta_pct,
  }));

  return (
    <section className="panel p-6">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Scenario Metrics</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-950">Retention, downgrade, upgrade, churn, and revenue movement</h2>
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <div className="h-[320px]">
          <ResponsiveContainer>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" hide />
              <YAxis />
              <Tooltip />
              <Bar dataKey="retention" fill="#0f766e" radius={[8, 8, 0, 0]} />
              <Bar dataKey="downgrade" fill="#f59e0b" radius={[8, 8, 0, 0]} />
              <Bar dataKey="upgrade" fill="#2563eb" radius={[8, 8, 0, 0]} />
              <Bar dataKey="churn" fill="#dc2626" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-3">
          {summaries.map((summary) => (
            <div key={summary.scenario_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">{summary.scenario_title}</p>
              <dl className="mt-3 grid gap-2 text-sm text-slate-700">
                <div className="flex justify-between gap-3">
                  <dt>Retention</dt>
                  <dd>{formatPercent(summary.projected_retention_pct)}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt>Churn</dt>
                  <dd>{formatPercent(summary.projected_churn_pct)}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt>Revenue delta</dt>
                  <dd>{formatPercent(summary.estimated_revenue_delta_pct)}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt>Perception</dt>
                  <dd className="capitalize">{summary.perception_shift_label}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
