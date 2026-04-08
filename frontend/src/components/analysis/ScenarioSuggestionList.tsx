import { Scenario, ScenarioSimulationSummary } from "@/types/api";
import { ScenarioCard } from "@/components/analysis/ScenarioCard";

interface ScenarioSuggestionListProps {
  scenarios: Scenario[];
  summaries: Record<string, ScenarioSimulationSummary | undefined>;
  selectedScenarioId?: string | null;
  comparedScenarioIds: string[];
  runningScenarioId?: string | null;
  onSelectScenario: (scenarioId: string) => void;
  onToggleCompare: (scenarioId: string) => void;
  onRunScenario: (scenarioId: string) => void;
}

export function ScenarioSuggestionList({
  scenarios,
  summaries,
  selectedScenarioId,
  comparedScenarioIds,
  runningScenarioId,
  onSelectScenario,
  onToggleCompare,
  onRunScenario,
}: ScenarioSuggestionListProps) {
  return (
    <section className="space-y-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Suggested Scenarios</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-950">Which decision is worth simulating first?</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Review the modeled upside, risks, and effort first. Metadata is secondary.
        </p>
      </div>
      <div className="grid gap-4 xl:grid-cols-3">
        {scenarios.map((scenario) => (
          <ScenarioCard
            key={scenario.id}
            scenario={scenario}
            summary={summaries[scenario.id]}
            isSelected={selectedScenarioId === scenario.id}
            isCompared={comparedScenarioIds.includes(scenario.id)}
            isRunning={runningScenarioId === scenario.id}
            onSelect={() => onSelectScenario(scenario.id)}
            onCompare={() => onToggleCompare(scenario.id)}
            onRun={() => onRunScenario(scenario.id)}
          />
        ))}
      </div>
    </section>
  );
}
