import { ProductSourceCoverage, ProductUncertainty } from "@/types/api";

interface UncertaintyReviewPanelProps {
  uncertainties: ProductUncertainty[];
  sourceCoverage: ProductSourceCoverage;
}

const severityStyles: Record<ProductUncertainty["severity"], string> = {
  high: "border-rose-200 bg-rose-50 text-rose-800",
  medium: "border-amber-200 bg-amber-50 text-amber-800",
  low: "border-slate-200 bg-slate-50 text-slate-700",
};

export function UncertaintyReviewPanel({ uncertainties, sourceCoverage }: UncertaintyReviewPanelProps) {
  return (
    <section className="space-y-3">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Needs Review</p>
        <p className="mt-1 text-sm text-slate-600">Ambiguities are surfaced here so the next ICP step is built on clearer assumptions.</p>
      </div>
      {uncertainties.length ? (
        <div className="space-y-3">
          {uncertainties.map((item) => (
            <article key={item.key} className="rounded-3xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-slate-900">{item.label}</p>
                <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${severityStyles[item.severity]}`}>
                  {item.severity}
                </span>
                {item.needs_user_review ? (
                  <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-800">
                    Review
                  </span>
                ) : null}
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-600">{item.reason}</p>
            </article>
          ))}
        </div>
      ) : (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          No major uncertainties were flagged from the current public evidence.
        </div>
      )}
      <SourceCoverageGrid sourceCoverage={sourceCoverage} />
    </section>
  );
}

function SourceCoverageGrid({ sourceCoverage }: { sourceCoverage: ProductSourceCoverage }) {
  const groups = [
    { label: "Observed", items: sourceCoverage.fields_observed_explicitly },
    { label: "Inferred", items: sourceCoverage.fields_inferred },
    { label: "Missing", items: sourceCoverage.fields_missing },
  ] as const;

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {groups.map((group) => (
        <article key={group.label} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{group.label}</p>
          <ul className="mt-3 space-y-2">
            {group.items.length ? (
              group.items.map((item) => (
                <li key={item} className="text-sm text-slate-700">
                  {item}
                </li>
              ))
            ) : (
              <li className="text-sm text-slate-500">None</li>
            )}
          </ul>
        </article>
      ))}
    </div>
  );
}
