import { AnalysisWorkflow } from "@/types/api";
import { cn } from "@/lib/utils";

interface WorkflowStepperProps {
  workflow: AnalysisWorkflow;
}

const statusStyles = {
  completed: "border-emerald-300 bg-emerald-50 text-emerald-700",
  processing: "border-teal-300 bg-teal-50 text-teal-700",
  awaiting_review: "border-indigo-300 bg-indigo-50 text-indigo-700",
  failed: "border-red-300 bg-red-50 text-red-700",
  stale: "border-amber-300 bg-amber-50 text-amber-700",
  not_started: "border-slate-200 bg-slate-50 text-slate-500",
} as const;

export function WorkflowStepper({ workflow }: WorkflowStepperProps) {
  return (
    <section className="panel p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Analysis Workflow</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-950">Review each stage before unlocking the next</h2>
        </div>
        {workflow.next_stage ? (
          <p className="text-sm text-slate-600">
            Up next: <span className="font-semibold text-slate-900">{workflow.steps.find((step) => step.stage === workflow.next_stage)?.label}</span>
          </p>
        ) : null}
      </div>
      <div className="mt-5 grid gap-3 lg:grid-cols-5">
        {workflow.steps.map((step, index) => (
          <div
            key={step.stage}
            className={cn(
              "rounded-2xl border px-4 py-4 transition",
              statusStyles[step.status],
              step.is_current && "ring-2 ring-slate-900/10",
            )}
          >
            <div className="flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.16em]">Step {index + 1}</span>
              {step.edited ? (
                <span className="rounded-full bg-white/80 px-2 py-1 text-[11px] font-semibold text-slate-700">Edited</span>
              ) : null}
            </div>
            <p className="mt-3 text-sm font-semibold">{step.label}</p>
            <p className="mt-2 text-xs capitalize">{step.status.replaceAll("_", " ")}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
