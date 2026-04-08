import {
  type BehavioralSignal,
  type ICPProfile as ApiICPProfile,
  type ICPViewModel,
  type SimulationImpactItem,
} from "@/types/api";

export type ICPCardVariant = "summary" | "detail";
export type ICPSignalLevel = 1 | 2 | 3 | 4 | 5;
export type ICPSignalKey =
  | "priceSensitivity"
  | "switchingFriction"
  | "timeToValueExpectation"
  | "proofRequirement"
  | "implementationTolerance"
  | "retentionStability";
export type ICPSimulationImpactSeverity = "high" | "medium" | "low";
export type ICPDecisionDriverTone = "primary" | "secondary" | "supporting";
export type ICPEditableFieldKey =
  | "name"
  | "segmentSharePct"
  | "priceSensitivity"
  | "switchingFriction"
  | "timeToValueExpectation"
  | "proofRequirement"
  | "implementationTolerance"
  | "retentionStability"
  | "decisionDrivers";

export interface ICPSignal {
  key: ICPSignalKey;
  label: string;
  level: ICPSignalLevel;
  editable: boolean;
  derived: boolean;
  sourceField: keyof ApiICPProfile;
}

export interface ICPDecisionDriver {
  key: string;
  label: string;
  rank: number;
  weightPct: number;
  visualWeight: number;
  tone: ICPDecisionDriverTone;
  editable: boolean;
}

export interface ICPSimulationImpact {
  id: string;
  label: string;
  explanation?: string;
  type: "pricing" | "activation" | "retention";
  severity: ICPSimulationImpactSeverity;
  sourceSignals: ICPSignalKey[];
}

export interface ICPEditableFieldConfig {
  field: ICPEditableFieldKey;
  label: string;
  control: "text" | "percentage" | "dotScale" | "rankedDriverEditor";
  visibleInQuickEdit: boolean;
  min?: number;
  max?: number;
}

export interface ICPCardProfile {
  id: string;
  identity: {
    name: string;
    summary: string;
    segmentSharePct: number;
    confidence?: {
      score: number;
      label: "Low" | "Medium" | "High";
      source: "llm" | "derived";
    };
    statusLabel: "AI inferred" | "Edited" | "Confirmed";
  };
  buyingLogic: {
    buysFor: string[];
    avoidsBecause: string[];
    winsWith: string[];
    comparedAgainst?: string[];
  };
  signals: ICPSignal[];
  decisionDrivers: ICPDecisionDriver[];
  simulationImpact: ICPSimulationImpact[];
  editableFields: ICPEditableFieldConfig[];
  sourceAssumptions: {
    description: string;
    useCase: string;
    goals: string[];
    painPoints: string[];
    alternatives: string[];
    valueExplanation: string;
  };
  meta: {
    isEdited: boolean;
    isConfirmed: boolean;
    displayOrder: number;
  };
}

const backendSignalKeyMap: Record<string, ICPSignalKey> = {
  priceSensitivity: "priceSensitivity",
  switchingFriction: "switchingFriction",
  timeToValueExpectation: "timeToValueExpectation",
  proofRequirement: "proofRequirement",
  implementationTolerance: "implementationTolerance",
  retentionStability: "retentionStability",
};

type SignalDescriptor = {
  key: ICPSignalKey;
  label: string;
  editable: boolean;
  derived: boolean;
  sourceField: keyof ApiICPProfile;
  getLevel: (icp: ApiICPProfile) => ICPSignalLevel;
  getRawValue: (level: ICPSignalLevel) => number;
};

const CHURN_THRESHOLD_MIN = -0.35;
const CHURN_THRESHOLD_MAX = -0.05;
const RETENTION_THRESHOLD_MIN = 0.02;
const RETENTION_THRESHOLD_MAX = 0.15;

export const signalScale = [1, 2, 3, 4, 5] as const;

const signalDescriptors: SignalDescriptor[] = [
  {
    key: "priceSensitivity",
    label: "Price Sensitivity",
    editable: true,
    derived: false,
    sourceField: "price_sensitivity",
    getLevel: (icp) => mapRawToLevel(icp.price_sensitivity, 0, 1),
    getRawValue: (level) => mapLevelToRaw(level, 0, 1),
  },
  {
    key: "switchingFriction",
    label: "Switching Friction",
    editable: true,
    derived: false,
    sourceField: "switching_cost",
    getLevel: (icp) => mapRawToLevel(icp.switching_cost, 0, 1),
    getRawValue: (level) => mapLevelToRaw(level, 0, 1),
  },
  {
    key: "proofRequirement",
    label: "Proof Requirement",
    editable: true,
    derived: false,
    sourceField: "retention_threshold",
    getLevel: (icp) => mapRawToLevel(icp.retention_threshold, RETENTION_THRESHOLD_MIN, RETENTION_THRESHOLD_MAX),
    getRawValue: (level) => mapLevelToRaw(level, RETENTION_THRESHOLD_MIN, RETENTION_THRESHOLD_MAX),
  },
  {
    key: "implementationTolerance",
    label: "Implementation Tolerance",
    editable: true,
    derived: true,
    sourceField: "adoption_friction",
    getLevel: (icp) => mapRawToLevel(icp.adoption_friction, 1, 0),
    getRawValue: (level) => mapLevelToRaw(level, 1, 0),
  },
  {
    key: "retentionStability",
    label: "Retention Stability",
    editable: true,
    derived: true,
    sourceField: "churn_threshold",
    getLevel: (icp) => mapRawToLevel(icp.churn_threshold, CHURN_THRESHOLD_MAX, CHURN_THRESHOLD_MIN),
    getRawValue: (level) => mapLevelToRaw(level, CHURN_THRESHOLD_MAX, CHURN_THRESHOLD_MIN),
  },
];

export const icpQuickEditFields: ICPEditableFieldConfig[] = [
  { field: "name", label: "Segment name", control: "text", visibleInQuickEdit: true },
  { field: "segmentSharePct", label: "Segment share", control: "percentage", visibleInQuickEdit: true, min: 1, max: 100 },
  { field: "priceSensitivity", label: "Price Sensitivity", control: "dotScale", visibleInQuickEdit: true, min: 1, max: 5 },
  { field: "switchingFriction", label: "Switching Friction", control: "dotScale", visibleInQuickEdit: true, min: 1, max: 5 },
  { field: "proofRequirement", label: "Proof Requirement", control: "dotScale", visibleInQuickEdit: true, min: 1, max: 5 },
  { field: "implementationTolerance", label: "Implementation Tolerance", control: "dotScale", visibleInQuickEdit: true, min: 1, max: 5 },
  { field: "retentionStability", label: "Retention Stability", control: "dotScale", visibleInQuickEdit: true, min: 1, max: 5 },
  { field: "decisionDrivers", label: "Top decision drivers", control: "rankedDriverEditor", visibleInQuickEdit: true },
];

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

export function mapApiICPToCardModel(
  icp: ApiICPProfile,
  options: { isConfirmed?: boolean; confidence?: ICPCardProfile["identity"]["confidence"] } = {},
): ICPCardProfile {
  if (icp.view_model) {
    return mapBackendViewModelToCardModel(icp, icp.view_model, options);
  }

  const decisionDrivers = buildDecisionDrivers(icp);
  const signals = signalDescriptors.map((descriptor) => ({
    key: descriptor.key,
    label: descriptor.label,
    level: descriptor.getLevel(icp),
    editable: descriptor.editable,
    derived: descriptor.derived,
    sourceField: descriptor.sourceField,
  }));

  return {
    id: icp.id,
    identity: {
      name: icp.name,
      summary: buildSegmentSummary(icp.description, icp.use_case),
      segmentSharePct: Math.round(icp.segment_weight * 1000) / 10,
      confidence: options.confidence,
      statusLabel: options.isConfirmed ? "Confirmed" : icp.is_user_edited ? "Edited" : "AI inferred",
    },
    buyingLogic: {
      buysFor: compressList(icp.goals_json, 2),
      avoidsBecause: compressList(icp.pain_points_json, 2),
      winsWith: buildWinsWith(icp),
      comparedAgainst: icp.alternatives_json,
    },
    signals,
    decisionDrivers,
    simulationImpact: buildSimulationImpact(signals, decisionDrivers),
    editableFields: icpQuickEditFields,
    sourceAssumptions: {
      description: icp.description,
      useCase: icp.use_case,
      goals: icp.goals_json,
      painPoints: icp.pain_points_json,
      alternatives: icp.alternatives_json,
      valueExplanation: icp.value_perception_explanation,
    },
    meta: {
      isEdited: icp.is_user_edited,
      isConfirmed: Boolean(options.isConfirmed),
      displayOrder: icp.display_order,
    },
  };
}

function mapBackendViewModelToCardModel(
  icp: ApiICPProfile,
  viewModel: ICPViewModel,
  options: { isConfirmed?: boolean; confidence?: ICPCardProfile["identity"]["confidence"] } = {},
): ICPCardProfile {
  const signals = viewModel.behavioral_signals
    .map((signal) => mapBackendSignal(signal))
    .filter((signal): signal is ICPSignal => Boolean(signal));
  const decisionDrivers: ICPDecisionDriver[] = viewModel.decision_drivers.map((driver, index, rows) => ({
    key: driver.key,
    label: driver.label,
    rank: driver.rank,
    weightPct: driver.weight_percent,
    visualWeight: rows[0]?.weight_percent ? driver.weight_percent / rows[0].weight_percent : 0,
    tone: index === 0 ? "primary" : index === 1 ? "secondary" : "supporting",
    editable: true,
  }));
  const editableFields: ICPEditableFieldConfig[] = viewModel.editable_fields.map((field) => {
    const control: ICPEditableFieldConfig["control"] =
      field.control === "percentage"
        ? "percentage"
        : field.control === "ranked_driver_editor"
          ? "rankedDriverEditor"
          : field.control === "dot_scale"
            ? "dotScale"
            : "text";
    return {
      field: (field.field === "segment_name" ? "name" : field.field === "segment_share" ? "segmentSharePct" : field.field) as ICPEditableFieldKey,
      label: field.label,
      control,
      visibleInQuickEdit: field.visible_by_default,
      min: field.min ?? undefined,
      max: field.max ?? undefined,
    };
  });

  return {
    id: icp.id,
    identity: {
      name: viewModel.segment_name,
      summary: viewModel.segment_summary,
      segmentSharePct: viewModel.estimated_segment_share,
      confidence: viewModel.confidence
        ? {
            score: viewModel.confidence.score,
            label:
              viewModel.confidence.label === "high"
                ? "High"
                : viewModel.confidence.label === "medium"
                  ? "Medium"
                  : "Low",
            source: viewModel.confidence.source,
          }
        : options.confidence,
      statusLabel: options.isConfirmed ? "Confirmed" : icp.is_user_edited ? "Edited" : "AI inferred",
    },
    buyingLogic: {
      buysFor: viewModel.buying_logic.buys_for,
      avoidsBecause: viewModel.buying_logic.avoids_because,
      winsWith: viewModel.buying_logic.wins_with,
      comparedAgainst: icp.alternatives_json,
    },
    signals,
    decisionDrivers,
    simulationImpact: viewModel.simulation_impact.map((impact, index) => mapBackendSimulationImpact(impact, index)),
    editableFields: editableFields.length ? editableFields : icpQuickEditFields,
    sourceAssumptions: {
      description: icp.description,
      useCase: viewModel.best_fit_use_case || icp.use_case,
      goals: icp.goals_json,
      painPoints: icp.pain_points_json,
      alternatives: icp.alternatives_json,
      valueExplanation: icp.value_perception_explanation,
    },
    meta: {
      isEdited: icp.is_user_edited,
      isConfirmed: Boolean(options.isConfirmed),
      displayOrder: icp.display_order,
    },
  };
}

export function formatDriverLabel(driver: string) {
  return driver
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function formatSegmentShare(value: number) {
  return `${Number.isInteger(value) ? value : value.toFixed(1)}%`;
}

export function formatSignalDots(level: ICPSignalLevel) {
  return signalScale.map((step) => step <= level);
}

export function getSignalLevelLabel(level: ICPSignalLevel) {
  if (level <= 2) return "Low";
  if (level === 3) return "Medium";
  return "High";
}

function mapBackendSignal(signal: BehavioralSignal): ICPSignal | null {
  const key = backendSignalKeyMap[signal.signal_key];
  if (!key) return null;
  return {
    key,
    label: signal.label,
    level: signal.value_1_to_5,
    editable: signal.editable,
    derived: signal.derived,
    sourceField: (signal.source_field ?? "price_sensitivity") as keyof ApiICPProfile,
  };
}

function mapBackendSimulationImpact(impact: SimulationImpactItem, index: number): ICPSimulationImpact {
  const type = index === 0 ? "pricing" : index === 1 ? "activation" : "retention";
  const sourceSignals: ICPSignalKey[] =
    type === "pricing"
      ? ["priceSensitivity"]
      : type === "activation"
        ? ["timeToValueExpectation", "implementationTolerance"]
        : ["proofRequirement", "retentionStability"];
  return {
    id: `${type}-${index}`,
    label: impact.title,
    explanation: impact.explanation,
    type,
    severity: impact.severity,
    sourceSignals,
  };
}

export function getSignalToneClass(level: ICPSignalLevel) {
  if (level <= 2) return "text-slate-500";
  if (level === 3) return "text-slate-700";
  return "text-slate-950";
}

export function getSignalLevelFromRaw(key: ICPSignalKey, icp: Pick<ApiICPProfile, keyof ApiICPProfile>) {
  const descriptor = signalDescriptors.find((item) => item.key === key);
  if (!descriptor) return 3;
  return descriptor.getLevel(icp as ApiICPProfile);
}

export function getRawValueFromSignalLevel(key: ICPSignalKey, level: ICPSignalLevel) {
  const descriptor = signalDescriptors.find((item) => item.key === key);
  if (!descriptor) return 0;
  return descriptor.getRawValue(level);
}

export function getSignalDescriptor(key: ICPSignalKey) {
  return signalDescriptors.find((item) => item.key === key);
}

export function getSelectedDrivers(icp: Pick<ApiICPProfile, "decision_drivers_json" | "driver_weights_json">) {
  const orderedDrivers = [...icp.decision_drivers_json];
  for (const driver of Object.keys(icp.driver_weights_json)) {
    if (!orderedDrivers.includes(driver)) {
      orderedDrivers.push(driver);
    }
  }
  return orderedDrivers;
}

export function getRankedDriverWeights(icp: Pick<ApiICPProfile, "decision_drivers_json" | "driver_weights_json">) {
  return getSelectedDrivers(icp)
    .map((driver) => [driver, Number(icp.driver_weights_json[driver] ?? 0)] as const)
    .sort(([, left], [, right]) => right - left);
}

export function getEditableDriverRows(icp: Pick<ApiICPProfile, "decision_drivers_json" | "driver_weights_json">) {
  return getRankedDriverWeights(icp).map(([driver, weight]) => ({ driver, weight }));
}

export function getDriverRankStyle(index: number) {
  return driverRankStyles[Math.min(index, driverRankStyles.length - 1)];
}

export function getDriverRankLabel(index: number) {
  if (index === 0) return "Primary";
  if (index === 1) return "Secondary";
  if (index === 2) return "Third";
  return "Support";
}

export function getDriverWeightLevel(weight: number) {
  if (weight <= 0) return 0;
  return Math.min(5, Math.max(1, Math.round(weight * 5)));
}

export function getDriverWeightFromLevel(level: number) {
  if (level <= 0) return 0;
  return Math.min(1, Math.max(0.1, level / 5));
}

function buildDecisionDrivers(icp: ApiICPProfile): ICPDecisionDriver[] {
  const ranked = getRankedDriverWeights(icp);
  const topWeight = ranked[0]?.[1] ?? 1;

  return ranked.map(([driver, weight], index) => ({
    key: driver,
    label: formatDriverLabel(driver),
    rank: index + 1,
    weightPct: Math.round(weight * 100),
    visualWeight: topWeight > 0 ? weight / topWeight : 0,
    tone: index === 0 ? "primary" : index === 1 ? "secondary" : "supporting",
    editable: true,
  }));
}

function buildSimulationImpact(signals: ICPSignal[], drivers: ICPDecisionDriver[]): ICPSimulationImpact[] {
  const signalMap = Object.fromEntries(signals.map((signal) => [signal.key, signal])) as Record<ICPSignalKey, ICPSignal>;
  const topDriverKeys = drivers.slice(0, 3).map((driver) => driver.key);
  const priceWeightBonus = topDriverKeys.some((driver) => ["price_affordability", "value_for_money", "budget_predictability"].includes(driver)) ? 1 : 0;
  const rolloutBonus = topDriverKeys.some((driver) => ["implementation_complexity", "team_enablement", "automation_coverage"].includes(driver)) ? 1 : 0;
  const retentionBonus = topDriverKeys.some((driver) => ["support_reliability", "team_enablement", "feature_completeness"].includes(driver)) ? 1 : 0;

  const pricingLevel = clampLevel(signalMap.priceSensitivity.level + priceWeightBonus);
  const rolloutDragLevel = clampLevel((6 - signalMap.implementationTolerance.level) + rolloutBonus);
  const retentionRiskLevel = clampLevel(Math.max(6 - signalMap.retentionStability.level, signalMap.proofRequirement.level) + retentionBonus);

  return [
    {
      id: "pricing-elasticity",
      label:
        pricingLevel >= 4
          ? "Pricing -> High elasticity"
          : pricingLevel === 3
            ? "Pricing -> Medium elasticity"
            : "Pricing -> Low elasticity",
      type: "pricing",
      severity: levelToSeverity(pricingLevel),
      sourceSignals: ["priceSensitivity"],
    },
    {
      id: "activation-drag",
      label:
        rolloutDragLevel >= 4
          ? "Activation -> High rollout drag"
          : rolloutDragLevel === 3
            ? "Activation -> Medium rollout drag"
            : "Activation -> Low rollout drag",
      type: "activation",
      severity: levelToSeverity(rolloutDragLevel),
      sourceSignals: ["implementationTolerance"],
    },
    {
      id: "retention-risk",
      label:
        retentionRiskLevel >= 4
          ? "Retention -> Low churn tolerance"
          : retentionRiskLevel === 3
            ? "Retention -> Moderate churn tolerance"
            : "Retention -> Stable renewal base",
      type: "retention",
      severity: levelToSeverity(retentionRiskLevel),
      sourceSignals: ["retentionStability", "proofRequirement"],
    },
  ];
}

function buildSegmentSummary(description: string, useCase: string) {
  const segments = [description.trim(), useCase.trim()].filter(Boolean);
  const combined = segments.join(" ");
  return truncateSentence(combined || description || useCase, 110);
}

function buildWinsWith(icp: ApiICPProfile) {
  const useCase = trimSentence(icp.use_case);
  const valueLines = splitSentences(icp.value_perception_explanation).map(trimSentence).filter(Boolean);
  return compressList([useCase, ...valueLines], 2);
}

function compressList(items: string[], maxItems: number) {
  return items
    .map((item) => trimSentence(item))
    .filter(Boolean)
    .slice(0, maxItems)
    .map((item) => truncateSentence(item, 72));
}

function trimSentence(value: string) {
  return value.trim().replace(/[.:\s]+$/g, "");
}

function truncateSentence(value: string, maxLength: number) {
  if (value.length <= maxLength) return value;
  const slice = value.slice(0, maxLength - 1).trim();
  const boundary = Math.max(slice.lastIndexOf(" "), slice.lastIndexOf(","), slice.lastIndexOf(";"));
  return `${(boundary > 20 ? slice.slice(0, boundary) : slice).trim()}...`;
}

function splitSentences(value: string) {
  return value
    .split(/[.!?]\s+/)
    .map((segment) => segment.trim())
    .filter(Boolean);
}

function mapRawToLevel(value: number, inputMin: number, inputMax: number): ICPSignalLevel {
  const scaled = mapRange(clamp(value, Math.min(inputMin, inputMax), Math.max(inputMin, inputMax)), inputMin, inputMax, 1, 5);
  return clampLevel(Math.round(scaled) as ICPSignalLevel);
}

function mapLevelToRaw(level: ICPSignalLevel, outputMin: number, outputMax: number) {
  return roundToTwoDecimals(mapRange(level, 1, 5, outputMin, outputMax));
}

function levelToSeverity(level: number): ICPSimulationImpactSeverity {
  if (level >= 4) return "high";
  if (level === 3) return "medium";
  return "low";
}

function roundToTwoDecimals(value: number) {
  return Math.round(value * 100) / 100;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function clampLevel(value: number): ICPSignalLevel {
  return Math.min(5, Math.max(1, Math.round(value))) as ICPSignalLevel;
}

function mapRange(value: number, inputMin: number, inputMax: number, outputMin: number, outputMax: number) {
  if (inputMax === inputMin) return outputMin;
  const ratio = (value - inputMin) / (inputMax - inputMin);
  return outputMin + ratio * (outputMax - outputMin);
}
