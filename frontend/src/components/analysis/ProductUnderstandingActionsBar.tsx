interface ProductUnderstandingActionsBarProps {
  isProceeding: boolean;
  onEdit: () => void;
  onProceed: () => void;
}

export function ProductUnderstandingActionsBar({
  isProceeding,
  onEdit,
  onProceed,
}: ProductUnderstandingActionsBarProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-slate-200 bg-slate-50 px-5 py-4">
      <div>
        <p className="text-sm font-semibold text-slate-950">Ready to move into ICP generation?</p>
        <p className="mt-1 text-sm text-slate-600">
          Confirm the interpretation first so the next stage uses the right buyer, value logic, and business levers.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onEdit}
          className="rounded-2xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-500 hover:bg-white"
        >
          Edit key assumptions
        </button>
        <button
          type="button"
          onClick={onProceed}
          disabled={isProceeding}
          className="rounded-2xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isProceeding ? "Generating ICPs..." : "Confirm understanding and continue"}
        </button>
      </div>
    </div>
  );
}
