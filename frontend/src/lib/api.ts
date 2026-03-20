import type {
  BuildingRightsResult,
  DataSearchResponse,
  HealthProbe,
  LivePlanSearchResponse,
  OperationsOverview,
  RegulationResult,
  SystemStatus,
  UploadAnalysis,
  VectorDbStatus,
  WorkspaceOverview
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // keep default
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export async function getSystemStatus(): Promise<SystemStatus> {
  return parseResponse<SystemStatus>(await fetch(`${API_BASE}/api/system/status`));
}

export async function getHealth(): Promise<HealthProbe> {
  return parseResponse<HealthProbe>(await fetch(`${API_BASE}/api/health`));
}

export async function getWorkspaceOverview(planNumber?: string): Promise<WorkspaceOverview> {
  const query = new URLSearchParams();
  if (planNumber) {
    query.set("plan_number", planNumber);
  }
  const suffix = query.toString() ? `?${query}` : "";
  return parseResponse<WorkspaceOverview>(
    await fetch(`${API_BASE}/api/workspace/overview${suffix}`)
  );
}

export async function getOperationsOverview(): Promise<OperationsOverview> {
  return parseResponse<OperationsOverview>(await fetch(`${API_BASE}/api/operations/overview`));
}

export async function postUiEvent(payload: {
  event_name: string;
  route?: string;
  plan_number?: string;
  status?: string;
  context?: Record<string, unknown>;
}) {
  return parseResponse<{ ok: boolean; event_id: string; received_at: string }>(
    await fetch(`${API_BASE}/api/ui/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
    })
  );
}

export async function queryRegulations(
  queryText: string,
  options: { location?: string; maxResults?: number } = {}
): Promise<RegulationResult> {
  return parseResponse<RegulationResult>(
    await fetch(`${API_BASE}/api/regulations/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query_text: queryText,
        location: options.location,
        max_results: options.maxResults ?? 5
      })
    })
  );
}

export async function getDataStatus() {
  return parseResponse<any>(await fetch(`${API_BASE}/api/data/status`));
}

export async function searchData(params: Record<string, string>): Promise<DataSearchResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  query.set("limit", "250");
  return parseResponse<DataSearchResponse>(await fetch(`${API_BASE}/api/data/search?${query}`));
}

export async function searchLivePlans(params: {
  location?: string;
  keyword?: string;
  status?: string;
  includeVisionAnalysis?: boolean;
  maxResults?: number;
}): Promise<LivePlanSearchResponse> {
  const query = new URLSearchParams();
  if (params.location) query.set("location", params.location);
  if (params.keyword) query.set("keyword", params.keyword);
  if (params.status) query.set("status", params.status);
  query.set("include_vision_analysis", String(Boolean(params.includeVisionAnalysis)));
  query.set("max_results", String(params.maxResults ?? 8));
  return parseResponse<LivePlanSearchResponse>(
    await fetch(`${API_BASE}/api/plans/search?${query}`)
  );
}

export async function calculateRights(payload: {
  plot_size_sqm: number;
  zone_type: string;
  location: string;
  include_regulations: boolean;
}): Promise<BuildingRightsResult> {
  return parseResponse<BuildingRightsResult>(
    await fetch(`${API_BASE}/api/building-rights/calculate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
  );
}

export async function analyzeUpload(file: File): Promise<UploadAnalysis> {
  const body = new FormData();
  body.append("file", file);
  return parseResponse<UploadAnalysis>(
    await fetch(`${API_BASE}/api/uploads/analyze`, {
      method: "POST",
      body
    })
  );
}

export async function getVectorDbStatus(): Promise<VectorDbStatus> {
  return parseResponse<VectorDbStatus>(await fetch(`${API_BASE}/api/vectordb/status`));
}

export async function initializeVectorDb() {
  return parseResponse<any>(
    await fetch(`${API_BASE}/api/vectordb/initialize`, {
      method: "POST"
    })
  );
}

export async function rebuildVectorDb() {
  return parseResponse<any>(
    await fetch(`${API_BASE}/api/vectordb/rebuild`, {
      method: "POST"
    })
  );
}

export async function searchVectorDb(query: string) {
  return parseResponse<any>(
    await fetch(`${API_BASE}/api/vectordb/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, limit: 8 })
    })
  );
}

export async function addVectorDbRegulation(payload: {
  title: string;
  content: string;
  reg_type: string;
  jurisdiction: string;
  summary?: string;
}) {
  return parseResponse<any>(
    await fetch(`${API_BASE}/api/vectordb/regulations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
  );
}

export async function importData(file: File) {
  const body = new FormData();
  body.append("file", file);
  return parseResponse<any>(
    await fetch(`${API_BASE}/api/data/import`, {
      method: "POST",
      body
    })
  );
}

export async function fetchFreshData(payload: {
  source: string;
  service_name: string;
  max_plans: number;
  where: string;
  timeout_seconds?: number;
}) {
  return parseResponse<any>(
    await fetch(`${API_BASE}/api/data/fetch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
  );
}

export async function getFetcherHealth() {
  return parseResponse<NonNullable<HealthProbe["scraping"]>>(
    await fetch(`${API_BASE}/api/data/fetcher-health`)
  );
}
