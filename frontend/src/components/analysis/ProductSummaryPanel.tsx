import { ExtractedProductData } from "@/types/api";

interface ProductSummaryPanelProps {
  data: ExtractedProductData;
}

export function ProductSummaryPanel({ data }: ProductSummaryPanelProps) {
  const normalized = data.normalized_json;
  return (
    <section className="panel overflow-hidden">
      <div className="panel-header">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Product Understanding</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-950">{data.product_name}</h2>
          <p className="mt-1 text-sm text-slate-600">{data.company_name}</p>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Confidence</p>
          <p className="text-3xl font-semibold text-slate-950">{Math.round(data.confidence_score * 100)}%</p>
        </div>
      </div>
      <div className="grid gap-6 px-6 py-6 lg:grid-cols-[1.6fr_1fr]">
        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Positioning</p>
            <p className="mt-2 text-sm leading-6 text-slate-700">{data.positioning_summary}</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Category</p>
              <p className="mt-2 text-sm text-slate-700">
                {data.category} / {data.subcategory}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Pricing Model</p>
              <p className="mt-2 text-sm text-slate-700">{data.pricing_model.replaceAll("_", " ")}</p>
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Monetization Hypothesis</p>
            <p className="mt-2 text-sm text-slate-700">{data.monetization_hypothesis}</p>
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Feature Clusters</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {normalized.feature_clusters.map((feature) => (
                <span key={feature} className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700">
                  {feature}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Target Customer Signals</p>
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {normalized.target_customer_signals.map((signal) => (
                <li key={signal}>• {signal}</li>
              ))}
            </ul>
          </div>
          {normalized.warnings?.length ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              {normalized.warnings.map((warning) => (
                <p key={warning}>• {warning}</p>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
