import { ICPProfile } from "@/types/api";
import { cn } from "@/lib/utils";

interface ICPDetailCardProps {
  icp: ICPProfile;
  isSelected?: boolean;
  onSelect?: () => void;
}

export function ICPDetailCard({ icp, isSelected = false, onSelect }: ICPDetailCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "panel flex h-full flex-col gap-4 p-5 text-left transition",
        isSelected && "border-slate-900 ring-2 ring-slate-900/10",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-950">{icp.name}</h3>
          <p className="mt-1 text-sm text-slate-600">{icp.description}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          {(icp.segment_weight * 100).toFixed(0)}% segment
        </span>
      </div>
      <div className="space-y-2 text-sm text-slate-700">
        <p><span className="font-medium text-slate-900">Use case:</span> {icp.use_case}</p>
        <p><span className="font-medium text-slate-900">Value logic:</span> {icp.value_perception_explanation}</p>
      </div>
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Decision Drivers</p>
        <div className="mt-3 space-y-2">
          {Object.entries(icp.driver_weights_json).map(([driver, weight]) => (
            <div key={driver}>
              <div className="flex items-center justify-between text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
                <span>{driver.replaceAll("_", " ")}</span>
                <span>{Math.round(weight * 100)}%</span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-slate-100">
                <div className="h-2 rounded-full bg-slate-800" style={{ width: `${weight * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </button>
  );
}
