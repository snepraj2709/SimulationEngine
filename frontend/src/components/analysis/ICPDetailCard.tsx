import { ICPProfile } from "@/types/api";
import { cn } from "@/lib/utils";

interface ICPDetailCardProps {
  icp: ICPProfile;
  isSelected?: boolean;
  onSelect?: () => void;
}

const driverRankStyles = [
  {
    badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
    fill: "from-emerald-500 to-teal-500",
    panel: "border-emerald-100 bg-emerald-50/60",
    rail: "bg-emerald-100/80",
    tone: "text-emerald-700",
  },
  {
    badge: "border-sky-200 bg-sky-50 text-sky-700",
    fill: "from-sky-500 to-blue-500",
    panel: "border-sky-100 bg-sky-50/60",
    rail: "bg-sky-100/80",
    tone: "text-sky-700",
  },
  {
    badge: "border-orange-200 bg-orange-50 text-orange-800",
    fill: "from-orange-500 to-rose-500",
    panel: "border-orange-200 bg-orange-50/70",
    rail: "bg-orange-100",
    tone: "text-orange-800",
  },
  {
    badge: "border-violet-200 bg-violet-50 text-violet-700",
    fill: "from-violet-500 to-fuchsia-500",
    panel: "border-violet-100 bg-violet-50/60",
    rail: "bg-violet-100/80",
    tone: "text-violet-700",
  },
  {
    badge: "border-slate-200 bg-slate-100 text-slate-700",
    fill: "from-slate-500 to-slate-600",
    panel: "border-slate-200 bg-slate-50/80",
    rail: "bg-slate-200/80",
    tone: "text-slate-700",
  },
] as const;

export function ICPDetailCard({ icp, isSelected = false, onSelect }: ICPDetailCardProps) {
  const rankedDrivers = Object.entries(icp.driver_weights_json).sort(([, left], [, right]) => right - left);
  const [topDriver, topDriverWeight] = rankedDrivers[0] ?? [];
  const segmentShare = Math.round(icp.segment_weight * 100);
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

      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">ICP segment</p>
          <h3 className="mt-2 text-xl font-semibold leading-tight text-slate-950">{icp.name}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">{icp.description}</p>
        </div>
        <div className="shrink-0 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-right">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Segment share</p>
          <p className="mt-1 text-2xl font-semibold leading-none text-slate-950">{segmentShare}%</p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <InfoPanel
          eyebrow="Best-fit use case"
          title={icp.use_case}
          toneClass="border-signal/15 bg-signal/5"
        />
        <InfoPanel
          eyebrow="What keeps them engaged"
          title={icp.value_perception_explanation}
          toneClass="border-amber/15 bg-amber/5"
        />
      </div>

      <div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Decision Drivers</p>
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
              <div
                key={driver}
                className={cn("rounded-2xl border px-4 py-3", driverStyle.panel)}
              >
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

function formatDriverLabel(driver: string) {
  return driver
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function getDriverRankStyle(index: number) {
  return driverRankStyles[Math.min(index, driverRankStyles.length - 1)];
}

function getDriverRankLabel(index: number) {
  if (index === 0) return "Primary driver";
  if (index === 1) return "Secondary driver";
  if (index === 2) return "Third strongest signal";
  return "Supporting signal";
}
