import { FormEvent, useState } from "react";

import { FeedbackType } from "@/types/api";
import { cn } from "@/lib/utils";

interface FeedbackBarProps {
  disabled?: boolean;
  isSubmitting?: boolean;
  onSubmit: (payload: { feedbackType: FeedbackType; comment?: string }) => Promise<void> | void;
}

export function FeedbackBar({ disabled = false, isSubmitting = false, onSubmit }: FeedbackBarProps) {
  const [selectedType, setSelectedType] = useState<FeedbackType | null>(null);
  const [comment, setComment] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedType) return;
    await onSubmit({ feedbackType: selectedType, comment: comment || undefined });
    setComment("");
  }

  return (
    <form onSubmit={handleSubmit} className="panel p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Feedback</p>
          <h3 className="text-lg font-semibold text-slate-950">Was this simulation useful?</h3>
          <div className="flex gap-3">
            {[
              { label: "Thumbs up", value: "thumbs_up" as const },
              { label: "Thumbs down", value: "thumbs_down" as const },
            ].map((option) => (
              <button
                key={option.value}
                type="button"
                disabled={disabled}
                onClick={() => setSelectedType(option.value)}
                className={cn(
                  "rounded-full border px-4 py-2 text-sm font-semibold transition",
                  selectedType === option.value
                    ? "border-slate-950 bg-slate-950 text-white"
                    : "border-slate-300 text-slate-700 hover:border-slate-500 hover:bg-slate-100",
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        <div className="flex w-full flex-col gap-3 lg:max-w-xl">
          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Optional comment for later analysis calibration"
            className="min-h-24 rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-500"
          />
          <button
            type="submit"
            disabled={disabled || isSubmitting || !selectedType}
            className="self-end rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isSubmitting ? "Saving..." : "Save feedback"}
          </button>
        </div>
      </div>
    </form>
  );
}
