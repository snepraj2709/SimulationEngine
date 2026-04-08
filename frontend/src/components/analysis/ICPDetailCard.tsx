import { ICPProfile as ApiICPProfile } from "@/types/api";
import { cn } from "@/lib/utils";
import {
  formatDriverLabel,
  formatSegmentShare,
  formatSignalDots,
  getDriverRankStyle,
  getSignalLevelLabel,
  getSignalToneClass,
  mapApiICPToCardModel,
  type ICPCardVariant,
  type ICPDecisionDriver,
  type ICPSignal,
  type ICPSimulationImpact,
} from "@/components/analysis/icpDisplay";

interface ICPDetailCardProps {
  icp: ApiICPProfile;
  variant?: ICPCardVariant;
  isSelected?: boolean;
  isConfirmed?: boolean;
  isCompared?: boolean;
  showCompare?: boolean;
  onConfirm?: () => void;
  onEdit?: () => void;
  onToggleCompare?: () => void;
  onRegenerate?: () => void;
}

export function ICPDetailCard({
  icp,
  variant = "detail",
  isSelected = false,
  isConfirmed = false,
  isCompared = false,
  showCompare = false,
  onConfirm,
  onEdit,
  onToggleCompare,
  onRegenerate,
}: ICPDetailCardProps) {
  const profile = mapApiICPToCardModel(icp, { isConfirmed });
  const isSummary = variant === "summary";

  return (
    <section
      className={cn(
        "panel overflow-hidden text-left",
        isSummary ? "p-5 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-[0_24px_70px_-34px_rgba(15,23,42,0.35)]" : "p-6",
        isSelected && "border-slate-900 ring-2 ring-slate-900/10",
      )}
    >
      <div className={cn("flex flex-col gap-5", !isSummary && "xl:grid xl:grid-cols-[1.15fr_0.95fr] xl:gap-6")}>
        <div className="space-y-5">
          <ICPIdentityHeader
            name={profile.identity.name}
            summary={profile.identity.summary}
            segmentSharePct={profile.identity.segmentSharePct}
            statusLabel={profile.identity.statusLabel}
            confidence={profile.identity.confidence}
            isCompared={isCompared}
            onRegenerate={onRegenerate}
          />
          <ICPBuyingLogic blocks={profile.buyingLogic} compact={isSummary} />
          {isSummary ? null : <ICPSourceAssumptionsAccordion profile={profile} />}
          <ICPDecisionDriversCompact drivers={profile.decisionDrivers} compact={isSummary} />
        </div>

        <div className="space-y-5">
          <ICPSignalList signals={profile.signals} compact={isSummary} />
          <ICPSimulationImpactList impacts={profile.simulationImpact} />
        </div>
      </div>

      <ICPActionBar
        isConfirmed={isConfirmed}
        isCompared={isCompared}
        showCompare={showCompare}
        onConfirm={onConfirm}
        onEdit={onEdit}
        onToggleCompare={onToggleCompare}
      />
    </section>
  );
}

function ICPIdentityHeader({
  name,
  summary,
  segmentSharePct,
  statusLabel,
  confidence,
  isCompared,
  onRegenerate,
}: {
  name: string;
  summary: string;
  segmentSharePct: number;
  statusLabel: string;
  confidence?: { score: number; label: "Low" | "Medium" | "High"; source: "llm" | "derived" };
  isCompared: boolean;
  onRegenerate?: () => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">ICP segment</p>
          <h3 className="mt-2 text-xl font-semibold leading-tight text-slate-950">{name}</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">{summary}</p>
        </div>
        {onRegenerate ? <ICPOverflowMenu onRegenerate={onRegenerate} /> : null}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <StatusChip>{statusLabel}</StatusChip>
        <StatusChip>{`${formatSegmentShare(segmentSharePct)} share`}</StatusChip>
        {isCompared ? <StatusChip>In compare</StatusChip> : null}
        {confidence ? <StatusChip>{`${confidence.label} confidence`}</StatusChip> : null}
      </div>
    </div>
  );
}

function ICPBuyingLogic({
  blocks,
  compact,
}: {
  blocks: {
    buysFor: string[];
    avoidsBecause: string[];
    winsWith: string[];
  };
  compact: boolean;
}) {
  const columns = [
    { label: "Buys for", items: blocks.buysFor, tone: "bg-slate-50" },
    { label: "Avoids because", items: blocks.avoidsBecause, tone: "bg-slate-50" },
    { label: "Wins with", items: blocks.winsWith, tone: "bg-slate-50" },
  ] as const;

  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Buying logic</p>
      <div className="grid gap-3 lg:grid-cols-3">
        {columns.map((column) => (
          <div key={column.label} className={cn("rounded-2xl px-3 py-3", column.tone)}>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{column.label}</p>
            <ul className="mt-2 space-y-2">
              {column.items.slice(0, compact ? 1 : 2).map((item) => (
                <li key={item} className="flex gap-2 text-sm font-medium leading-5 text-slate-800">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" aria-hidden />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            {column.items.length > (compact ? 1 : 2) ? (
              <p className="mt-2 text-xs font-medium text-slate-500">+{column.items.length - (compact ? 1 : 2)} more</p>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function ICPSignalList({ signals, compact }: { signals: ICPSignal[]; compact: boolean }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Behavioral signals</p>
        {!compact ? <p className="text-xs text-slate-500">Modeled assumptions for simulation</p> : null}
      </div>
      <div className="rounded-2xl bg-slate-50 px-4 py-3">
        <div className="space-y-3">
          {signals.map((signal) => (
            <ICPSignalRow key={signal.key} signal={signal} compact={compact} />
          ))}
        </div>
      </div>
    </div>
  );
}

function ICPSignalRow({ signal, compact }: { signal: ICPSignal; compact: boolean }) {
  const dots = formatSignalDots(signal.level);
  const levelLabel = getSignalLevelLabel(signal.level);

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-900">{signal.label}</p>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1" role="img" aria-label={`${signal.label} ${signal.level} out of 5`}>
          {dots.map((filled, index) => (
            <span
              key={`${signal.key}-${index}`}
              className={cn(
                "h-2.5 w-2.5 rounded-full border border-slate-300",
                filled ? getSignalToneClass(signal.level).replace("text-", "bg-") : "bg-white",
              )}
            />
          ))}
        </div>
        {!compact ? <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{levelLabel}</span> : null}
      </div>
    </div>
  );
}

function ICPDecisionDriversCompact({
  drivers,
  compact,
}: {
  drivers: ICPDecisionDriver[];
  compact: boolean;
}) {
  const visibleDrivers = compact ? drivers.slice(0, 2) : drivers.slice(0, 3);
  const hiddenCount = Math.max(0, drivers.length - visibleDrivers.length);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Decision drivers</p>
        {hiddenCount > 0 ? <p className="text-xs text-slate-500">+{hiddenCount} more</p> : null}
      </div>
      {compact ? (
        <div className="flex flex-wrap gap-2">
          {visibleDrivers.map((driver) => (
            <span
              key={driver.key}
              className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700"
            >
              <span className="text-slate-400">#{driver.rank}</span>
              <span>{driver.label}</span>
              <span>{driver.weightPct}%</span>
            </span>
          ))}
          {hiddenCount > 0 ? (
            <span className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-500">
              +{hiddenCount} more
            </span>
          ) : null}
        </div>
      ) : (
        <div className="space-y-2">
          {visibleDrivers.map((driver, index) => {
            const driverStyle = getDriverRankStyle(index);
            return (
              <div key={driver.key} className="grid grid-cols-[auto_minmax(0,1fr)_auto_auto] items-center gap-3 rounded-2xl bg-slate-50 px-3 py-2.5">
                <span className={cn("text-xs font-semibold uppercase tracking-[0.14em]", driverStyle.tone)}>
                  #{driver.rank}
                </span>
                <span className="min-w-0 truncate text-sm font-medium text-slate-900">{driver.label}</span>
                <span className="text-xs font-semibold text-slate-600">{driver.weightPct}%</span>
                <span className={cn("h-2 w-12 overflow-hidden rounded-full", driverStyle.rail)}>
                  <span
                    className={cn("block h-full rounded-full bg-gradient-to-r", driverStyle.fill)}
                    style={{ width: `${Math.max(18, driver.visualWeight * 100)}%` }}
                  />
                </span>
              </div>
            );
          })}
          {hiddenCount > 0 ? <p className="text-xs text-slate-500">+{hiddenCount} additional supporting drivers hidden</p> : null}
        </div>
      )}
    </div>
  );
}

function ICPSimulationImpactList({ impacts }: { impacts: ICPSimulationImpact[] }) {
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Simulation impact</p>
      <div className="space-y-2">
        {impacts.map((impact) => (
          <div
            key={impact.id}
            className={cn(
              "flex items-center justify-between gap-3 rounded-2xl px-3 py-3",
              impact.severity === "high"
                ? "bg-rose-50 text-rose-900"
                : impact.severity === "medium"
                  ? "bg-amber-50 text-amber-900"
                  : "bg-emerald-50 text-emerald-900",
            )}
          >
            <span className="text-sm font-semibold">{impact.label}</span>
            <span className="text-[11px] font-semibold uppercase tracking-[0.14em]">
              {impact.severity}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ICPSourceAssumptionsAccordion({ profile }: { profile: ReturnType<typeof mapApiICPToCardModel> }) {
  return (
    <details className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3">
      <summary className="cursor-pointer list-none text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 [&::-webkit-details-marker]:hidden">
        Source assumptions
      </summary>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <SourceField label="Use case" value={profile.sourceAssumptions.useCase} />
        <SourceField label="Description" value={profile.sourceAssumptions.description} />
        <SourceList label="Goals" items={profile.sourceAssumptions.goals} />
        <SourceList label="Pain points" items={profile.sourceAssumptions.painPoints} />
        <SourceList label="Alternatives" items={profile.sourceAssumptions.alternatives} />
        <SourceField label="Value explanation" value={profile.sourceAssumptions.valueExplanation} />
      </div>
    </details>
  );
}

function SourceField({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="text-sm leading-6 text-slate-700">{value}</p>
    </div>
  );
}

function SourceList({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="space-y-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function ICPActionBar({
  isConfirmed,
  isCompared,
  showCompare,
  onConfirm,
  onEdit,
  onToggleCompare,
}: {
  isConfirmed: boolean;
  isCompared: boolean;
  showCompare: boolean;
  onConfirm?: () => void;
  onEdit?: () => void;
  onToggleCompare?: () => void;
}) {
  if (!onConfirm && !onEdit && !showCompare) return null;

  return (
    <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4">
      <div className="flex flex-wrap items-center gap-2">
        {onConfirm ? (
          <button
            type="button"
            onClick={onConfirm}
            className={cn(
              "rounded-full px-4 py-2 text-sm font-semibold transition",
              isConfirmed
                ? "bg-slate-950 text-white"
                : "border border-slate-300 text-slate-700 hover:border-slate-500 hover:bg-slate-100",
            )}
          >
            {isConfirmed ? "Confirmed" : "Confirm ICP"}
          </button>
        ) : null}
        {onEdit ? (
          <button
            type="button"
            onClick={onEdit}
            className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-500 hover:bg-slate-100"
          >
            Edit assumptions
          </button>
        ) : null}
      </div>
      {showCompare && onToggleCompare ? (
        <button
          type="button"
          onClick={onToggleCompare}
          className={cn(
            "rounded-full border px-4 py-2 text-sm font-semibold transition",
            isCompared
              ? "border-slate-900 bg-slate-900 text-white"
              : "border-slate-300 text-slate-700 hover:border-slate-500 hover:bg-slate-100",
          )}
        >
          {isCompared ? "Compared" : "Compare"}
        </button>
      ) : null}
    </div>
  );
}

function StatusChip({ children }: { children: string }) {
  return (
    <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
      {children}
    </span>
  );
}

function ICPOverflowMenu({ onRegenerate }: { onRegenerate: () => void }) {
  return (
    <details className="relative">
      <summary className="cursor-pointer list-none rounded-full border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-slate-500 hover:bg-slate-100 [&::-webkit-details-marker]:hidden">
        More
      </summary>
      <div className="absolute right-0 top-[calc(100%+0.5rem)] z-10 min-w-[180px] rounded-2xl border border-slate-200 bg-white p-2 shadow-xl">
        <button
          type="button"
          onClick={onRegenerate}
          className="w-full rounded-xl px-3 py-2 text-left text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        >
          Regenerate ICP
        </button>
      </div>
    </details>
  );
}
