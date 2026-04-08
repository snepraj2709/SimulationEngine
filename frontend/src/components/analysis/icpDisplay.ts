import { ICPProfile } from "@/types/api";

export const driverRankStyles = [
  {
    badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
    fill: "from-emerald-500 to-teal-500",
    panel: "border-emerald-100 bg-emerald-50/60",
    rail: "bg-emerald-100/80",
    tone: "text-emerald-700",
    accent: "accent-emerald-600",
  },
  {
    badge: "border-sky-200 bg-sky-50 text-sky-700",
    fill: "from-sky-500 to-blue-500",
    panel: "border-sky-100 bg-sky-50/60",
    rail: "bg-sky-100/80",
    tone: "text-sky-700",
    accent: "accent-sky-600",
  },
  {
    badge: "border-orange-200 bg-orange-50 text-orange-800",
    fill: "from-orange-500 to-rose-500",
    panel: "border-orange-200 bg-orange-50/70",
    rail: "bg-orange-100",
    tone: "text-orange-800",
    accent: "accent-orange-600",
  },
  {
    badge: "border-violet-200 bg-violet-50 text-violet-700",
    fill: "from-violet-500 to-fuchsia-500",
    panel: "border-violet-100 bg-violet-50/60",
    rail: "bg-violet-100/80",
    tone: "text-violet-700",
    accent: "accent-violet-600",
  },
  {
    badge: "border-slate-200 bg-slate-100 text-slate-700",
    fill: "from-slate-500 to-slate-600",
    panel: "border-slate-200 bg-slate-50/80",
    rail: "bg-slate-200/80",
    tone: "text-slate-700",
    accent: "accent-slate-600",
  },
] as const;

export function formatDriverLabel(driver: string) {
  return driver
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function getDriverRankStyle(index: number) {
  return driverRankStyles[Math.min(index, driverRankStyles.length - 1)];
}

export function getDriverRankLabel(index: number) {
  if (index === 0) return "Primary driver";
  if (index === 1) return "Secondary driver";
  if (index === 2) return "Third strongest signal";
  return "Supporting signal";
}

export function getSelectedDrivers(icp: Pick<ICPProfile, "decision_drivers_json" | "driver_weights_json">) {
  const orderedDrivers = [...icp.decision_drivers_json];
  for (const driver of Object.keys(icp.driver_weights_json)) {
    if (!orderedDrivers.includes(driver)) {
      orderedDrivers.push(driver);
    }
  }
  return orderedDrivers;
}

export function getRankedDriverWeights(icp: Pick<ICPProfile, "decision_drivers_json" | "driver_weights_json">) {
  return getSelectedDrivers(icp)
    .map((driver) => [driver, Number(icp.driver_weights_json[driver] ?? 0)] as const)
    .sort(([, left], [, right]) => right - left);
}

export function getEditableDriverRows(icp: Pick<ICPProfile, "decision_drivers_json" | "driver_weights_json">) {
  return getRankedDriverWeights(icp).map(([driver, weight]) => ({ driver, weight }));
}
