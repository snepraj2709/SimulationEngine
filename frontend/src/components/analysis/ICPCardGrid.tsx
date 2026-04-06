import { ICPProfile } from "@/types/api";
import { ICPDetailCard } from "@/components/analysis/ICPDetailCard";

interface ICPCardGridProps {
  icps: ICPProfile[];
  selectedICPId?: string | null;
  onSelectICP?: (icpId: string) => void;
}

export function ICPCardGrid({ icps, selectedICPId, onSelectICP }: ICPCardGridProps) {
  return (
    <section className="space-y-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Ideal Customer Profiles</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-950">Who moves first when the offer changes?</h2>
      </div>
      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {icps.map((icp) => (
          <ICPDetailCard
            key={icp.id}
            icp={icp}
            isSelected={selectedICPId === icp.id}
            onSelect={() => onSelectICP?.(icp.id)}
          />
        ))}
      </div>
    </section>
  );
}
