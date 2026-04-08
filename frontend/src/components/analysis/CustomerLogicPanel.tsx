import { ProductCustomerLogic } from "@/types/api";

interface CustomerLogicPanelProps {
  logic: ProductCustomerLogic;
}

const sections = [
  { key: "why_they_buy", label: "Why They Buy" },
  { key: "why_they_hesitate", label: "Why They Hesitate" },
  { key: "what_it_replaces", label: "What It Replaces" },
] as const;

export function CustomerLogicPanel({ logic }: CustomerLogicPanelProps) {
  return (
    <section className="space-y-3">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Customer Logic</p>
        <p className="mt-1 text-sm text-slate-600">Why this product gets bought, questioned, and compared.</p>
      </div>
      <div className="grid gap-3 xl:grid-cols-[1.1fr_1fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Core Job-To-Be-Done</p>
          <p className="mt-3 text-sm font-medium leading-6 text-slate-900">{logic.core_job_to_be_done}</p>
        </article>
        <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
          {sections.map((section) => (
            <article key={section.key} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{section.label}</p>
              <ul className="mt-3 space-y-2">
                {logic[section.key].map((item) => (
                  <li key={item} className="flex gap-2 text-sm leading-5 text-slate-700">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
