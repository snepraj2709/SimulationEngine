import { ICPProfile } from "@/types/api";

export type IcpScalarMetricKey =
  | "segment_weight"
  | "price_sensitivity"
  | "switching_cost"
  | "churn_threshold"
  | "retention_threshold"
  | "adoption_friction";

export type IcpTraitMetricKey = Exclude<IcpScalarMetricKey, "segment_weight">;
export type IcpTraitBand = "Low" | "Medium" | "High";

type IcpMetricKind = "percent" | "trait";

type IcpMetricMetadata = {
  key: IcpScalarMetricKey;
  label: string;
  description: string;
  kind: IcpMetricKind;
  min?: number;
  max?: number;
  step?: number;
  minLabel?: string;
  maxLabel?: string;
  toUiValue: (value: number) => number;
  fromUiValue: (value: number) => number;
  interpretations?: Record<IcpTraitBand, string>;
};

const traitBandStyles: Record<IcpTraitBand, string> = {
  Low: "border-slate-200 bg-slate-100 text-slate-700",
  Medium: "border-sky-200 bg-sky-50 text-sky-700",
  High: "border-violet-200 bg-violet-50 text-violet-700",
};

const TRAIT_UI_MIN = 0;
const TRAIT_UI_MAX = 100;
const SEGMENT_SHARE_MIN = 0.01;
const SEGMENT_SHARE_MAX = 1;
const CHURN_THRESHOLD_MIN = -0.35;
const CHURN_THRESHOLD_MAX = -0.05;
const RETENTION_THRESHOLD_MIN = 0.02;
const RETENTION_THRESHOLD_MAX = 0.15;

export const icpMetricOrder: readonly IcpScalarMetricKey[] = [
  "segment_weight",
  "price_sensitivity",
  "switching_cost",
  "churn_threshold",
  "retention_threshold",
  "adoption_friction",
];

export const icpMetricMetadata: Record<IcpScalarMetricKey, IcpMetricMetadata> = {
  segment_weight: {
    key: "segment_weight",
    label: "Estimated segment share",
    description: "Percent of the total ICP mix this segment represents.",
    kind: "percent",
    min: 1,
    max: 100,
    step: 0.1,
    toUiValue: (value) => clamp(value * 100, 1, 100),
    fromUiValue: (value) => clamp(value / 100, SEGMENT_SHARE_MIN, SEGMENT_SHARE_MAX),
  },
  price_sensitivity: {
    key: "price_sensitivity",
    label: "Price sensitivity",
    description: "How strongly price affects this segment's decision.",
    kind: "trait",
    min: TRAIT_UI_MIN,
    max: TRAIT_UI_MAX,
    step: 1,
    minLabel: "Price matters less",
    maxLabel: "Price matters a lot",
    toUiValue: (value) => clamp(value * 100, TRAIT_UI_MIN, TRAIT_UI_MAX),
    fromUiValue: (value) => clamp(value / 100, 0, 1),
    interpretations: {
      Low: "This segment is less likely to react strongly to pricing changes.",
      Medium: "This segment notices pricing changes and weighs them against value.",
      High: "This segment reacts strongly to pricing changes.",
    },
  },
  switching_cost: {
    key: "switching_cost",
    label: "Switching resistance",
    description: "How hard this segment is to pull away from its current setup.",
    kind: "trait",
    min: TRAIT_UI_MIN,
    max: TRAIT_UI_MAX,
    step: 1,
    minLabel: "Easy to replace",
    maxLabel: "Hard to replace",
    toUiValue: (value) => clamp(value * 100, TRAIT_UI_MIN, TRAIT_UI_MAX),
    fromUiValue: (value) => clamp(value / 100, 0, 1),
    interpretations: {
      Low: "This segment can replace its current setup without much friction.",
      Medium: "This segment needs a credible reason to switch from its current setup.",
      High: "This segment is hard to pull away from what it already uses.",
    },
  },
  churn_threshold: {
    key: "churn_threshold",
    label: "Retention resilience",
    description: "How much disappointment this segment tolerates before leaving.",
    kind: "trait",
    min: TRAIT_UI_MIN,
    max: TRAIT_UI_MAX,
    step: 1,
    minLabel: "Leaves quickly",
    maxLabel: "Sticks through issues",
    toUiValue: (value) =>
      mapRange(clamp(value, CHURN_THRESHOLD_MIN, CHURN_THRESHOLD_MAX), CHURN_THRESHOLD_MAX, CHURN_THRESHOLD_MIN, TRAIT_UI_MIN, TRAIT_UI_MAX),
    fromUiValue: (value) =>
      mapRange(clamp(value, TRAIT_UI_MIN, TRAIT_UI_MAX), TRAIT_UI_MIN, TRAIT_UI_MAX, CHURN_THRESHOLD_MAX, CHURN_THRESHOLD_MIN),
    interpretations: {
      Low: "This segment leaves quickly when the experience slips.",
      Medium: "This segment will tolerate some issues before leaving.",
      High: "This segment tends to stick through issues before churning.",
    },
  },
  retention_threshold: {
    key: "retention_threshold",
    label: "Expansion hurdle",
    description: "How much extra proof this segment needs before upgrading or expanding.",
    kind: "trait",
    min: TRAIT_UI_MIN,
    max: TRAIT_UI_MAX,
    step: 1,
    minLabel: "Easy to expand",
    maxLabel: "Needs strong proof",
    toUiValue: (value) => mapRange(clamp(value, RETENTION_THRESHOLD_MIN, RETENTION_THRESHOLD_MAX), RETENTION_THRESHOLD_MIN, RETENTION_THRESHOLD_MAX, TRAIT_UI_MIN, TRAIT_UI_MAX),
    fromUiValue: (value) =>
      mapRange(clamp(value, TRAIT_UI_MIN, TRAIT_UI_MAX), TRAIT_UI_MIN, TRAIT_UI_MAX, RETENTION_THRESHOLD_MIN, RETENTION_THRESHOLD_MAX),
    interpretations: {
      Low: "This segment is relatively easy to expand once the core value is proven.",
      Medium: "This segment needs clear proof before expanding.",
      High: "This segment needs strong additional proof before upgrading or expanding.",
    },
  },
  adoption_friction: {
    key: "adoption_friction",
    label: "Rollout effort",
    description: "How much setup and change effort this segment can handle.",
    kind: "trait",
    min: TRAIT_UI_MIN,
    max: TRAIT_UI_MAX,
    step: 1,
    minLabel: "Easy rollout",
    maxLabel: "Heavy rollout",
    toUiValue: (value) => clamp(value * 100, TRAIT_UI_MIN, TRAIT_UI_MAX),
    fromUiValue: (value) => clamp(value / 100, 0, 1),
    interpretations: {
      Low: "This segment can adopt quickly with minimal rollout effort.",
      Medium: "This segment can handle some rollout work if the value is clear.",
      High: "This segment expects a heavier rollout and change-management effort.",
    },
  },
};

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

export function getIcpMetricMetadata(key: IcpScalarMetricKey) {
  return icpMetricMetadata[key];
}

export function getIcpMetricLabel(key: IcpScalarMetricKey) {
  return getIcpMetricMetadata(key).label;
}

export function getIcpMetricDescription(key: IcpScalarMetricKey) {
  return getIcpMetricMetadata(key).description;
}

export function getIcpMetricUiValue(key: IcpScalarMetricKey, rawValue: number) {
  return getIcpMetricMetadata(key).toUiValue(rawValue);
}

export function getIcpMetricRawValue(key: IcpScalarMetricKey, uiValue: number) {
  return getIcpMetricMetadata(key).fromUiValue(uiValue);
}

export function getIcpMetricBand(rawValue: number, key: IcpTraitMetricKey): IcpTraitBand {
  const value = getIcpMetricUiValue(key, rawValue);
  if (value <= 33) return "Low";
  if (value <= 66) return "Medium";
  return "High";
}

export function getIcpMetricBandStyle(band: IcpTraitBand) {
  return traitBandStyles[band];
}

export function getIcpMetricInterpretation(rawValue: number, key: IcpTraitMetricKey) {
  return getIcpMetricMetadata(key).interpretations?.[getIcpMetricBand(rawValue, key)] ?? "";
}

export function formatIcpMetricPercent(rawValue: number) {
  const rounded = Math.round(rawValue * 1000) / 10;
  return Number.isInteger(rounded) ? `${rounded}%` : `${rounded.toFixed(1)}%`;
}

export function isIcpTraitMetric(key: IcpScalarMetricKey): key is IcpTraitMetricKey {
  return key !== "segment_weight";
}

export function clampIcpMetricUiValue(key: IcpScalarMetricKey, value: number) {
  const metadata = getIcpMetricMetadata(key);
  return clamp(value, metadata.min ?? TRAIT_UI_MIN, metadata.max ?? TRAIT_UI_MAX);
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

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function mapRange(value: number, inputMin: number, inputMax: number, outputMin: number, outputMax: number) {
  if (inputMax === inputMin) return outputMin;
  const ratio = (value - inputMin) / (inputMax - inputMin);
  return outputMin + ratio * (outputMax - outputMin);
}
