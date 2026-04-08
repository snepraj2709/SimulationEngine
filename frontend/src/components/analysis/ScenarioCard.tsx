import { type Scenario, type ScenarioSimulationSummary } from "@/types/api";
import { cn } from "@/lib/utils";
import {
  formatImpactRange,
  formatScenarioTypeLabel,
  getImpactDirectionTone,
  getRecommendationTone,
  getScenarioReviewModel,
} from "@/components/analysis/scenarioDisplay";

interface ScenarioCardProps {
  scenario: Scenario;
  summary?: ScenarioSimulationSummary;
  isSelected?: boolean;
  isCompared?: boolean;
  isRunning?: boolean;
  onSelect?: () => void;
  onCompare?: () => void;
  onRun?: () => void;
}

export function ScenarioCard({
  scenario,
  summary,
  isSelected = false,
  isCompared = false,
  isRunning = false,
  onSelect,
  onCompare,
  onRun,
}: ScenarioCardProps) {
  const review = getScenarioReviewModel(scenario);
  const visibleImpacts = review.expected_impact.slice(0, 3);

  return (
    <div className={cn("panel p-5", isSelected && "border-slate-900 ring-2 ring-slate-900/10")}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-600">
              {formatScenarioTypeLabel(review.scenario_type)}
            </span>
            <span className={cn("rounded-full border px-3 py-1 text-[11px] font-semibold", getRecommendationTone(review.recommendation.priority_rank))}>
              {review.recommendation.recommendation_label}
            </span>
          </div>
          <h3 className="mt-3 text-lg font-semibold leading-tight text-slate-950">{review.short_decision_statement}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">{review.scenario_summary}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-3 py-2 text-right">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Priority</p>
          <p className="mt-1 text-lg font-semibold text-slate-950">#{review.recommendation.priority_rank}</p>
        </div>
      </div>

      {visibleImpacts.length > 0 ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {visibleImpacts.map((impact) => {
            const tone = getImpactDirectionTone(impact.direction);
            return (
              <div key={impact.metric_key} className={cn("rounded-2xl px-3 py-3", tone.surface)}>
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{impact.label}</p>
                  {impact.confidence ? (
                    <span className={cn("rounded-full border px-2.5 py-1 text-[11px] font-semibold capitalize", tone.badge)}>
                      {impact.confidence}
                    </span>
                  ) : null}
                </div>
                <p className={cn("mt-2 text-base font-semibold", tone.text)}>{formatImpactRange(impact)}</p>
              </div>
            );
          })}
        </div>
      ) : summary ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <FallbackMetric label="Revenue" value={`${summary.estimated_revenue_delta_pct.toFixed(1)}%`} />
          <FallbackMetric label="Retention" value={`${summary.projected_retention_pct.toFixed(1)}%`} />
          <FallbackMetric label="Upgrade" value={`${summary.projected_upgrade_pct.toFixed(1)}%`} />
          <FallbackMetric label="Churn" value={`${summary.projected_churn_pct.toFixed(1)}%`} />
        </div>
      ) : null}

      {review.why_this_might_work[0] ? (
        <div className="mt-4 rounded-2xl bg-slate-50 px-3 py-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Why this might work</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{review.why_this_might_work[0]}</p>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
          Effort: {review.execution_effort.level}
        </span>
        {review.metadata.scenario_tags.slice(0, 2).map((tag) => (
          <span key={tag} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
            {tag}
          </span>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap justify-between gap-3">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onSelect}
            className="rounded-full border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-500 hover:bg-slate-100"
          >
            Inspect
          </button>
          <button
            type="button"
            onClick={onCompare}
            className={cn(
              "rounded-full border px-3 py-1.5 text-xs font-semibold transition",
              isCompared
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-300 text-slate-700 hover:border-slate-500 hover:bg-slate-100",
            )}
          >
            {isCompared ? "Selected" : "Compare"}
          </button>
        </div>
        <button
          type="button"
          onClick={onRun}
          disabled={isRunning}
          className="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isRunning ? "Running..." : "Run scenario"}
        </button>
      </div>
    </div>
  );
}

function FallbackMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-50 px-3 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}
