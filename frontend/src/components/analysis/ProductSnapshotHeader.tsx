import { ProductUnderstandingViewModel } from "@/types/api";

interface ProductSnapshotHeaderProps {
  viewModel: ProductUnderstandingViewModel;
}

export function ProductSnapshotHeader({ viewModel }: ProductSnapshotHeaderProps) {
  const showDistinctProductName = viewModel.product_name.trim().toLowerCase() !== viewModel.company_name.trim().toLowerCase();

  return (
    <div className="border-b border-slate-200 px-6 py-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Business Interpretation</p>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
              {viewModel.category}
            </span>
            <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
              {viewModel.subcategory}
            </span>
            {viewModel.review_status === "needs_review" ? (
              <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
                Needs review
              </span>
            ) : null}
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">{viewModel.company_name}</p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-950">
              {showDistinctProductName ? viewModel.product_name : viewModel.company_name}
            </h2>
            {showDistinctProductName ? <p className="mt-1 text-sm text-slate-500">Company: {viewModel.company_name}</p> : null}
          </div>
          <p className="max-w-3xl text-sm leading-6 text-slate-700">{viewModel.summary_line}</p>
        </div>
        <div className="min-w-[180px] rounded-3xl border border-slate-200 bg-slate-50 px-5 py-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Confidence</p>
          <p className="mt-2 text-3xl font-semibold text-slate-950">{Math.round(viewModel.confidence * 100)}%</p>
          <p className="mt-2 text-xs leading-5 text-slate-500">
            {viewModel.review_status === "needs_review"
              ? "Key assumptions still need confirmation before ICP generation."
              : "Strong enough to move into ICP generation."}
          </p>
        </div>
      </div>
    </div>
  );
}
