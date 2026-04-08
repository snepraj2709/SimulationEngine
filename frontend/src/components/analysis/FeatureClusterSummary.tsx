import { ProductFeatureCluster } from "@/types/api";

interface FeatureClusterSummaryProps {
  clusters: ProductFeatureCluster[];
}

const importanceStyles: Record<ProductFeatureCluster["importance"], string> = {
  high: "border-slate-300 bg-slate-950 text-white",
  medium: "border-slate-300 bg-slate-100 text-slate-800",
  low: "border-slate-200 bg-white text-slate-600",
};

export function FeatureClusterSummary({ clusters }: FeatureClusterSummaryProps) {
  return (
    <section className="space-y-3">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Feature Clusters</p>
        <p className="mt-1 text-sm text-slate-600">The product surface area most likely to matter in evaluation and expansion.</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {clusters.map((cluster) => (
          <article key={cluster.key} className="rounded-3xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-900">{cluster.label}</p>
              <span className={`rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${importanceStyles[cluster.importance]}`}>
                {cluster.importance}
              </span>
            </div>
            {cluster.description ? <p className="mt-3 text-sm leading-6 text-slate-600">{cluster.description}</p> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
