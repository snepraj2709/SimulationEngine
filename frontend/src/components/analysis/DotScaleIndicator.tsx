import { cn } from "@/lib/utils";

interface DotScaleIndicatorProps {
  label: string;
  value: 1 | 2 | 3 | 4 | 5;
  compact?: boolean;
  tone?: "default" | "positive" | "warning" | "critical";
  className?: string;
}

const scale = [1, 2, 3, 4, 5] as const;

export function DotScaleIndicator({
  label,
  value,
  compact = false,
  tone = "default",
  className,
}: DotScaleIndicatorProps) {
  const toneClass =
    tone === "positive"
      ? "border-emerald-400 bg-emerald-500"
      : tone === "warning"
        ? "border-amber-400 bg-amber-500"
        : tone === "critical"
          ? "border-rose-400 bg-rose-500"
          : "border-slate-400 bg-slate-900";

  return (
    <div
      className={cn("flex items-center gap-1", className)}
      role="img"
      aria-label={`${label} ${value} out of 5`}
    >
      {scale.map((step) => (
        <span
          key={`${label}-${step}`}
          className={cn(
            compact ? "h-2.5 w-2.5" : "h-3 w-3",
            "rounded-full border",
            step <= value ? toneClass : "border-slate-300 bg-white",
          )}
        />
      ))}
    </div>
  );
}
