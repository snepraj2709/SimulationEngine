import { BusinessSignalGrid } from "@/components/analysis/BusinessSignalGrid";
import { CustomerLogicPanel } from "@/components/analysis/CustomerLogicPanel";
import { FeatureClusterSummary } from "@/components/analysis/FeatureClusterSummary";
import { ProductSnapshotHeader } from "@/components/analysis/ProductSnapshotHeader";
import { SimulationLeversPanel } from "@/components/analysis/SimulationLeversPanel";
import { UncertaintyReviewPanel } from "@/components/analysis/UncertaintyReviewPanel";
import { ExtractedProductData } from "@/types/api";

interface ProductSummaryPanelProps {
  data: ExtractedProductData;
}

export function ProductSummaryPanel({ data }: ProductSummaryPanelProps) {
  const viewModel = data.view_model;

  return (
    <section className="panel overflow-hidden">
      <ProductSnapshotHeader viewModel={viewModel} />
      <div className="space-y-8 px-6 py-6">
        <BusinessSignalGrid signals={viewModel.business_model_signals} />
        <div className="grid gap-8 xl:grid-cols-[1.15fr_0.85fr]">
          <CustomerLogicPanel logic={viewModel.customer_logic} />
          <FeatureClusterSummary clusters={viewModel.feature_clusters} />
        </div>
        <div className="grid gap-8 xl:grid-cols-[1fr_1fr]">
          <SimulationLeversPanel levers={viewModel.simulation_levers} />
          <UncertaintyReviewPanel uncertainties={viewModel.uncertainties} sourceCoverage={viewModel.source_coverage} />
        </div>
      </div>
    </section>
  );
}
