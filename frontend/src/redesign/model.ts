import type { DataFeature, HealthProbe } from "../types";

export const QUERY_HISTORY_KEY = "gisarchagent-query-history";
export const CURRENT_PLAN_KEY = "gisarchagent-current-plan";

export const ROUTE_META = {
  "/": {
    label: "Planner workspace",
    title: "Move the current project forward with less context switching.",
    description:
      "Select a plan, scan the decision signals, and move into investigation or feasibility from one grounded workspace.",
  },
  "/map": {
    label: "Investigation",
    title: "Inspect the site, geometry, and evidence in one place.",
    description:
      "Keep map context, site facts, and source actions synchronized to the selected plan.",
  },
  "/analyzer": {
    label: "Feasibility",
    title: "Stress-test the scheme before client review.",
    description:
      "Compare a proposal against heuristic rights, supporting regulations, and upload evidence without leaving project context.",
  },
  "/data": {
    label: "Operations",
    title: "Keep data, provider health, and regulations trustworthy.",
    description:
      "Separate runtime and data maintenance work from planner workflows, but keep fixes obvious when the product degrades.",
  },
} as const;

export type SurfaceTone = "info" | "warning" | "danger";

export type ComparisonMetric = {
  label: string;
  status: "ok" | "risk";
  proposedLabel: string;
  allowedLabel: string;
  message: string;
};

const STATUS_LABELS: Record<string, string> = {
  ready: "Ready",
  healthy: "Healthy",
  optional: "Optional",
  blocked: "Blocked",
  warning: "Needs attention",
  unvalidated: "Unvalidated",
  timeout: "Timed out",
  unknown: "Unknown",
  not_created: "Not created",
  needs_initialization: "Needs initialization",
};

export function readStoredHistory(): string[] {
  try {
    const raw = localStorage.getItem(QUERY_HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function writeStoredHistory(history: string[]) {
  localStorage.setItem(QUERY_HISTORY_KEY, JSON.stringify(history.slice(0, 10)));
}

export function readStoredPlan(): DataFeature | null {
  try {
    const raw = localStorage.getItem(CURRENT_PLAN_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function persistStoredPlan(plan: DataFeature | null) {
  if (plan) {
    localStorage.setItem(CURRENT_PLAN_KEY, JSON.stringify(plan));
  } else {
    localStorage.removeItem(CURRENT_PLAN_KEY);
  }
}

function getAttrs(feature?: DataFeature | null) {
  return feature?.attributes || {};
}

export function getPlanNumber(feature?: DataFeature | null) {
  return String(getAttrs(feature).pl_number || "No plan number");
}

export function getPlanTitle(feature?: DataFeature | null) {
  return String(getAttrs(feature).pl_name || "Untitled plan");
}

export function getPlanCity(feature?: DataFeature | null) {
  return String(getAttrs(feature).plan_county_name || "Unknown city");
}

export function getPlanDistrict(feature?: DataFeature | null) {
  return String(getAttrs(feature).district_name || "Unknown district");
}

export function getPlanStatus(feature?: DataFeature | null) {
  return String(
    getAttrs(feature).station_desc ||
      getAttrs(feature).internet_short_status ||
      "Unknown status",
  );
}

export function getPlanLocation(feature?: DataFeature | null) {
  return `${getPlanCity(feature)}, ${getPlanDistrict(feature)}`;
}

export function getPlanUrl(feature?: DataFeature | null) {
  const value = getAttrs(feature).pl_url;
  return value ? String(value) : "";
}

export function getPlanSource(feature?: DataFeature | null) {
  return String(getAttrs(feature).plan_source || "local_catalog");
}

export function getPlanSourceLabel(feature?: DataFeature | null) {
  return getPlanSource(feature) === "live_iplan" ? "Live iPlan" : "Local catalog";
}

export function formatArea(feature?: DataFeature | null) {
  const raw = Number(getAttrs(feature).pl_area_dunam || 0);
  if (!raw) return "Unknown";
  return `${raw.toFixed(2)} dunam`;
}

export function inferPlotSize(feature?: DataFeature | null) {
  const dunam = Number(getAttrs(feature).pl_area_dunam || 0);
  if (!dunam) return 500;
  return Math.max(250, Math.round(dunam * 1000));
}

export function buildConstraintSignals(feature: DataFeature): string[] {
  const signals = [
    `Approval state: ${getPlanStatus(feature)}.`,
    `Municipality context: ${getPlanLocation(feature)}.`,
    feature.has_geometry
      ? "Geometry is available for map review."
      : "Geometry is missing, so parcel context needs manual verification.",
  ];
  const objectives = getAttrs(feature).pl_objectives;
  if (objectives) {
    const text = String(objectives);
    signals.push(`Plan objective: ${text.slice(0, 120)}${text.length > 120 ? "..." : ""}`);
  }
  return signals;
}

export function buildNextActions(feature: DataFeature, health: HealthProbe | null): string[] {
  const actions = [
    `Verify municipality status: ${getPlanStatus(feature)}.`,
    `Run feasibility assumptions for ${getPlanNumber(feature)} before client review.`,
    "Open the source plan package and confirm setbacks, parking, and approval notes.",
  ];
  if (health?.provider?.configured && !health?.provider?.text?.healthy) {
    actions.push("Fix provider configuration before relying on synthesized summaries.");
  } else if (!health?.provider?.configured) {
    actions.push("Provider configuration is optional; retrieval-only answers remain available.");
  }
  if (!feature.has_geometry) {
    actions.push("Geometry is missing; confirm parcel boundaries before map-based review.");
  }
  return actions;
}

export function buildShareableBrief(feature: DataFeature, health: HealthProbe | null) {
  const providerReady = Boolean(health?.provider?.text?.healthy);
  const providerConfigured = Boolean(health?.provider?.configured);
  const scraperStatus = health?.scraping?.status || "unknown";
  const providerStatus = providerReady
    ? "ready"
    : providerConfigured
      ? "blocked"
      : "optional";
  return [
    `Project dossier: ${getPlanNumber(feature)} - ${getPlanTitle(feature)}`,
    `Location: ${getPlanLocation(feature)}`,
    `Approval state: ${getPlanStatus(feature)}`,
    `Area: ${formatArea(feature)}`,
    `Geometry: ${feature.has_geometry ? "available" : "missing"}`,
    `Plan source: ${getPlanSourceLabel(feature)}`,
    `Provider status: ${formatStatusLabel(providerStatus)}`,
    `Scraper status: ${formatStatusLabel(scraperStatus)}`,
    "Next review step: validate feasibility assumptions and confirm source regulations before client output.",
  ].join("\n");
}

export function compareMetric(
  label: string,
  proposed: number,
  allowed: number,
  unit: string,
  minimum = false,
): ComparisonMetric {
  const passes = minimum ? proposed >= allowed : proposed <= allowed;
  const delta = Math.abs(proposed - allowed);
  return {
    label,
    status: passes ? "ok" : "risk",
    proposedLabel: formatMetric(proposed, unit),
    allowedLabel: formatMetric(allowed, unit),
    message: passes
      ? minimum
        ? `Provision exceeds minimum by ${formatMetric(delta, unit)}.`
        : `Within allowance by ${formatMetric(delta, unit)}.`
      : minimum
        ? `Short by ${formatMetric(delta, unit)}.`
        : `Exceeds allowance by ${formatMetric(delta, unit)}.`,
  };
}

function formatMetric(value: number, unit: string) {
  const rounded = Math.round(value * 10) / 10;
  return `${rounded} ${unit}`;
}

export function buildGlobalHealthMessage(health: HealthProbe) {
  const parts: string[] = [];
  if (!health.provider?.configured) {
    parts.push(
      "Provider is optional and currently unconfigured. Retrieval-only answers remain available until synthesis is enabled.",
    );
  } else if (!health.provider?.text?.healthy) {
    parts.push(health.provider?.text?.detail || "Text provider is not healthy.");
  }
  if (health.scraping?.status !== "ready") {
    if (health.scraping?.status === "unvalidated") {
      parts.push(
        health.scraping?.detail || "Scraper has not been validated in this session yet.",
      );
    } else {
      parts.push(
        health.scraping?.detail || `Scraper probe status: ${health.scraping?.status}.`,
      );
    }
  }
  return parts.join(" ");
}

export function buildSidebarGuidance(
  routeLabel: string,
  currentPlan: DataFeature | null,
  health: HealthProbe | null,
) {
  if (!currentPlan) {
    return `You are in ${routeLabel.toLowerCase()}. Select a plan first so the product can stay project-led instead of feeling like four disconnected tools.`;
  }
  if (!health?.provider?.configured) {
    return "Provider configuration is optional. Retrieval-first workflows remain available while synthesis stays disabled.";
  }
  if (!health?.provider?.text?.healthy) {
    return "Provider health is degraded, so use the structured evidence surfaces before trusting synthesis-heavy summaries.";
  }
  return `Working on ${getPlanNumber(currentPlan)}. Keep this route focused on the current project instead of restarting context elsewhere.`;
}

export function normalizeErrorMessage(message: string) {
  if (message.includes("Unexpected token '<'")) {
    return "The endpoint returned HTML instead of API JSON. Check that the FastAPI server is running and that the current route is reaching the backend rather than a document shell.";
  }
  return message;
}

export function formatTimestamp(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function formatStatusLabel(value?: string | null) {
  const normalized = String(value || "unknown").trim().toLowerCase();
  if (!normalized) return STATUS_LABELS.unknown;
  if (normalized in STATUS_LABELS) {
    return STATUS_LABELS[normalized];
  }
  return normalized
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
