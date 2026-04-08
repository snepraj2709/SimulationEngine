import { ICPProfile as ApiICPProfile } from "@/types/api";
import { ICPDetailCard } from "@/components/analysis/ICPDetailCard";
import { formatSignalDots, mapApiICPToCardModel } from "@/components/analysis/icpDisplay";

interface ICPCardGridProps {
  icps: ApiICPProfile[];
  selectedICPId?: string | null;
  comparedICPIds?: string[];
  onConfirmICP?: (icpId: string) => void;
  onEditICP?: (icpId: string) => void;
  onToggleCompareICP?: (icpId: string) => void;
  onRegenerateICP?: (icpId: string) => void;
  onClearComparedICP?: () => void;
}

export function ICPCardGrid({
  icps,
  selectedICPId,
  comparedICPIds = [],
  onConfirmICP,
  onEditICP,
  onToggleCompareICP,
  onRegenerateICP,
  onClearComparedICP,
}: ICPCardGridProps) {
  const comparedProfiles = icps
    .filter((icp) => comparedICPIds.includes(icp.id))
    .map((icp) => mapApiICPToCardModel(icp, { isConfirmed: selectedICPId === icp.id }));

  return (
    <section className="space-y-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Ideal Customer Profiles</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-950">Who moves first when the offer changes?</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Confirm the segment you trust most, or compare a few before choosing the one that should anchor simulation.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {icps.map((icp) => (
          <ICPDetailCard
            key={icp.id}
            icp={icp}
            variant="summary"
            isSelected={selectedICPId === icp.id}
            isConfirmed={selectedICPId === icp.id}
            isCompared={comparedICPIds.includes(icp.id)}
            showCompare
            onConfirm={() => onConfirmICP?.(icp.id)}
            onEdit={() => onEditICP?.(icp.id)}
            onToggleCompare={() => onToggleCompareICP?.(icp.id)}
            onRegenerate={() => onRegenerateICP?.(icp.id)}
          />
        ))}
      </div>
      {comparedProfiles.length > 0 ? (
        <section className="panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Compare ICPs</p>
              <h3 className="mt-1 text-lg font-semibold text-slate-950">Side-by-side simulation assumptions</h3>
            </div>
            {onClearComparedICP ? (
              <button
                type="button"
                onClick={onClearComparedICP}
                className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-500 hover:bg-slate-100"
              >
                Clear compare
              </button>
            ) : null}
          </div>
          <div className="mt-4 grid gap-3 xl:grid-cols-3">
            {comparedProfiles.map((profile) => (
              <div key={profile.id} className="rounded-2xl bg-slate-50 px-4 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-950">{profile.identity.name}</p>
                    <p className="mt-1 text-xs text-slate-500">{profile.identity.segmentSharePct}% share</p>
                  </div>
                  <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                    {profile.identity.statusLabel}
                  </span>
                </div>
                <div className="mt-4 space-y-2">
                  {profile.signals.slice(0, 3).map((signal) => (
                    <div key={signal.key} className="flex items-center justify-between gap-3 text-sm text-slate-700">
                      <span className="truncate">{signal.label}</span>
                      <div className="flex items-center gap-1" role="img" aria-label={`${signal.label} ${signal.level} out of 5`}>
                        {formatSignalDots(signal.level).map((filled, index) => (
                          <span
                            key={`${signal.key}-${index}`}
                            className={`h-2.5 w-2.5 rounded-full border border-slate-300 ${filled ? "bg-slate-900" : "bg-white"}`}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 rounded-2xl bg-white px-3 py-3 text-sm font-semibold text-slate-800">
                  {profile.simulationImpact[0]?.label}
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </section>
  );
}
