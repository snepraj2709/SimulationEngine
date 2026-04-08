import { ICPProfile } from "@/types/api";
import { cn } from "@/lib/utils";
import {
  formatDriverLabel,
  getDriverRankLabel,
  getDriverRankStyle,
  getRankedDriverWeights,
  getSelectedDrivers,
} from "@/components/analysis/icpDisplay";

interface ICPDetailCardProps {
  icp: ICPProfile;
  isSelected?: boolean;
  onSelect?: () => void;
}

export function ICPDetailCard({ icp, isSelected = false, onSelect }: ICPDetailCardProps) {
  const rankedDrivers = getRankedDriverWeights(icp);
  const selectedDrivers = getSelectedDrivers(icp);
  const [topDriver, topDriverWeight] = rankedDrivers[0] ?? [];
  const primaryDriverStyle = getDriverRankStyle(0);

  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "panel flex h-full flex-col gap-5 overflow-hidden p-5 text-left transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-[0_24px_70px_-34px_rgba(15,23,42,0.35)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/20",
        isSelected && "border-slate-900 ring-2 ring-slate-900/10",
      )}
    >
      <div className={cn("h-1.5 w-full rounded-full bg-gradient-to-r", primaryDriverStyle.fill)} />

      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">ICP segment</p>
        <h3 className="mt-2 text-xl font-semibold leading-tight text-slate-950">{icp.name}</h3>
        <p className="mt-2 text-sm leading-6 text-slate-600">{icp.description}</p>
      </div>

      <InfoPanel eyebrow="Best-fit use case" title={icp.use_case} toneClass="border-signal/15 bg-signal/5" />

      <ListPanel eyebrow="Goals" items={icp.goals_json} toneClass="border-emerald-100 bg-emerald-50/50" />
      <ListPanel eyebrow="Pain points" items={icp.pain_points_json} toneClass="border-rose-100 bg-rose-50/50" />
      <ListPanel eyebrow="Alternatives" items={icp.alternatives_json} toneClass="border-sky-100 bg-sky-50/50" />

      <InfoPanel
        eyebrow="Value perception explanation"
        title={icp.value_perception_explanation}
        toneClass="border-amber/15 bg-amber/5"
      />

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <MetricPanel label="Segment weight" value={formatMetricPercent(icp.segment_weight)} />
        <MetricPanel label="Price sensitivity" value={formatMetricDecimal(icp.price_sensitivity)} />
        <MetricPanel label="Switching cost" value={formatMetricDecimal(icp.switching_cost)} />
        <MetricPanel label="Churn threshold" value={formatMetricSignedDecimal(icp.churn_threshold)} />
        <MetricPanel label="Retention threshold" value={formatMetricSignedDecimal(icp.retention_threshold)} />
        <MetricPanel label="Adoption friction" value={formatMetricDecimal(icp.adoption_friction)} />
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Selected drivers</p>
        <div className="flex flex-wrap gap-2">
          {selectedDrivers.map((driver) => (
            <span
              key={driver}
              className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700"
            >
              {formatDriverLabel(driver)}
            </span>
          ))}
        </div>
      </div>

      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Decision driver weights</p>
          {topDriver ? (
            <span
              className={cn(
                "inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold",
                primaryDriverStyle.badge,
              )}
            >
              Primary driver: {formatDriverLabel(topDriver)} {Math.round((topDriverWeight ?? 0) * 100)}%
            </span>
          ) : null}
        </div>
        <div className="mt-4 space-y-3">
          {rankedDrivers.map(([driver, weight], index) => {
            const driverStyle = getDriverRankStyle(index);
            return (
              <div key={driver} className={cn("rounded-2xl border px-4 py-3", driverStyle.panel)}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className={cn("text-[11px] font-semibold uppercase tracking-[0.16em]", driverStyle.tone)}>
                      {getDriverRankLabel(index)}
                    </p>
                    <p className="mt-1 text-sm font-semibold text-slate-950">{formatDriverLabel(driver)}</p>
                  </div>
                  <div className="shrink-0 rounded-full bg-white/80 px-2.5 py-1 text-sm font-semibold text-slate-800">
                    {Math.round(weight * 100)}%
                  </div>
                </div>
                <div className={cn("mt-3 h-3 overflow-hidden rounded-full", driverStyle.rail)}>
                  <div
                    className={cn("h-full rounded-full bg-gradient-to-r", driverStyle.fill)}
                    style={{ width: `${weight * 100}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </button>
  );
}

function InfoPanel({
  eyebrow,
  title,
  toneClass,
}: {
  eyebrow: string;
  title: string;
  toneClass: string;
}) {
  return (
    <div className={cn("rounded-2xl border px-4 py-3", toneClass)}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{eyebrow}</p>
      <p className="mt-2 text-sm leading-6 text-slate-800">{title}</p>
    </div>
  );
}

function ListPanel({
  eyebrow,
  items,
  toneClass,
}: {
  eyebrow: string;
  items: string[];
  toneClass: string;
}) {
  return (
    <div className={cn("rounded-2xl border px-4 py-3", toneClass)}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{eyebrow}</p>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-800">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" aria-hidden />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MetricPanel({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function formatMetricDecimal(value: number) {
  return value.toFixed(2);
}

function formatMetricSignedDecimal(value: number) {
  return value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2);
}

function formatMetricPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}
