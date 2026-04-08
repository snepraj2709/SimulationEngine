import { DotScaleIndicator } from "@/components/analysis/DotScaleIndicator";
import {
  formatImpactRange,
  formatScenarioTypeLabel,
  getImpactDirectionTone,
  getRecommendationTone,
  getScenarioReviewModel,
} from "@/components/analysis/scenarioDisplay";
import { cn } from "@/lib/utils";
import { type Scenario } from "@/types/api";

interface ScenarioReviewCardProps {
  scenario: Scenario;
}

export function ScenarioReviewCard({ scenario }: ScenarioReviewCardProps) {
  const review = getScenarioReviewModel(scenario);

  return (
    <section className="panel p-6">
      <div className="flex flex-col gap-6 xl:grid xl:grid-cols-[1.15fr_0.95fr] xl:gap-6">
        <div className="space-y-5">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-600">
                {formatScenarioTypeLabel(review.scenario_type)}
              </span>
              <span className={cn("rounded-full border px-3 py-1 text-[11px] font-semibold", getRecommendationTone(review.recommendation.priority_rank))}>
                {review.recommendation.recommendation_label}
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold capitalize text-slate-700">
                Effort {review.execution_effort.level}
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-semibold leading-tight text-slate-950">{review.short_decision_statement}</h3>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{review.scenario_summary}</p>
            </div>
            <div className="rounded-2xl bg-sky-50 px-4 py-4 text-sky-900">
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-sky-700">Recommendation</p>
              <p className="mt-2 text-sm font-semibold">
                Ranked #{review.recommendation.priority_rank}
              </p>
              <p className="mt-1 text-sm leading-6">{review.recommendation.recommendation_reason}</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Why this might work</p>
              <h4 className="mt-1 text-lg font-semibold text-slate-950">Why this fits the selected ICP behavior</h4>
            </div>
            <div className="space-y-2">
              {review.why_this_might_work.map((reason) => (
                <div key={reason} className="rounded-2xl bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700">
                  {reason}
                </div>
              ))}
            </div>
            {review.linked_icp_summary ? (
              <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Linked ICP</p>
                <p className="mt-2 text-sm font-semibold text-slate-950">{review.linked_icp_summary.segment_name}</p>
                <div className="mt-3 space-y-2">
                  {review.linked_icp_summary.relevant_signals.map((signal) => (
                    <div key={signal.signal_key} className="flex items-center justify-between gap-3">
                      <span className="text-sm text-slate-700">{signal.label}</span>
                      <DotScaleIndicator label={signal.label} value={signal.value_1_to_5} compact />
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>

        <div className="space-y-5">
          <div className="space-y-3">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Expected impact</p>
              <h4 className="mt-1 text-lg font-semibold text-slate-950">Modeled upside and downside</h4>
            </div>
            <div className="grid gap-3">
              {review.expected_impact.map((impact) => {
                const tone = getImpactDirectionTone(impact.direction);
                return (
                  <div key={impact.metric_key} className={cn("rounded-2xl px-4 py-4", tone.surface)}>
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-slate-900">{impact.label}</p>
                      <span className={cn("rounded-full border px-2.5 py-1 text-[11px] font-semibold capitalize", tone.badge)}>
                        {impact.direction}
                      </span>
                    </div>
                    <p className={cn("mt-2 text-xl font-semibold", tone.text)}>{formatImpactRange(impact)}</p>
                    {impact.confidence ? (
                      <p className="mt-2 text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
                        {impact.confidence} confidence
                      </p>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-2xl bg-amber-50 px-4 py-4 text-amber-950">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-amber-700">Trade-offs</p>
            <div className="mt-3 space-y-2">
              {review.tradeoffs.map((tradeoff) => (
                <p key={tradeoff} className="text-sm leading-6">
                  {tradeoff}
                </p>
              ))}
            </div>
          </div>

          <details className="rounded-2xl border border-slate-200 bg-slate-50/70 px-4 py-4">
            <summary className="cursor-pointer list-none text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 [&::-webkit-details-marker]:hidden">
              Secondary metadata
            </summary>
            <div className="mt-4 space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  ["Market", review.metadata.market],
                  ["Service", review.metadata.service_name],
                  ["Plan tier", review.metadata.plan_tier],
                  ["Billing period", review.metadata.billing_period],
                ]
                  .filter(([, value]) => Boolean(value))
                  .map(([label, value]) => (
                    <div key={label} className="rounded-2xl bg-white px-3 py-3">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p>
                      <p className="mt-2 text-sm font-medium text-slate-800">{value}</p>
                    </div>
                  ))}
              </div>
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Raw parameters</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(review.raw_parameters).map(([key, value]) => (
                    <span key={key} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700">
                      {key.replaceAll("_", " ")}: {String(value)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </details>
        </div>
      </div>
    </section>
  );
}
