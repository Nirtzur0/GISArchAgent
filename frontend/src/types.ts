export type SystemStatus = {
  provider?: {
    configured?: boolean;
    base_url?: string;
    model?: string;
    vision_model?: string;
    text?: Record<string, unknown>;
    vision?: Record<string, unknown>;
  };
  scraping?: Record<string, unknown>;
  vector_db: Record<string, unknown>;
  cache: Record<string, unknown>;
  regulation_repository: Record<string, unknown>;
  data_store: {
    total_plans: number;
    by_district: Record<string, number>;
    by_city: Record<string, number>;
    by_status: Record<string, number>;
    metadata?: Record<string, unknown>;
  };
};

export type Regulation = {
  id: string;
  type: string;
  title: string;
  content: string;
  summary?: string | null;
  jurisdiction: string;
  metadata?: Record<string, unknown>;
};

export type RegulationResult = {
  regulations: Regulation[];
  total_found: number;
  answer?: string | null;
  answer_status?: string;
  answer_warning?: string | null;
  timestamp?: string;
};

export type DataFeature = {
  attributes: Record<string, any>;
  geometry_wgs84?: {
    rings: number[][][];
    centroid?: {
      lat: number;
      lon: number;
    } | null;
  } | null;
  has_geometry: boolean;
};

export type DataSearchResponse = {
  total: number;
  items: DataFeature[];
  filters: Record<string, string | null>;
};

export type LivePlan = {
  id: string;
  name: string;
  location: string;
  region?: string | null;
  status: string;
  zone_type: string;
  plan_type: string;
  geometry?: Record<string, unknown> | null;
  extent?: Record<string, unknown> | null;
  metadata?: Record<string, unknown>;
  submitted_date?: string | null;
  approved_date?: string | null;
  effective_date?: string | null;
  image_url?: string | null;
  document_url?: string | null;
};

export type LivePlanAnalysis = {
  plan: LivePlan;
  vision_analysis?: {
    description?: string | null;
    ocr_text?: string | null;
    zones_identified?: string[];
  } | null;
  image_bytes?: string | null;
};

export type LivePlanSearchResponse = {
  plans: LivePlanAnalysis[];
  total_found: number;
  query: {
    plan_id?: string | null;
    location?: string | null;
    keyword?: string | null;
    status?: string | null;
    include_vision_analysis: boolean;
    max_results: number;
  };
  execution_time_ms?: number;
  timestamp?: string;
  warning?: string | null;
  warning_code?: string | null;
};

export type BuildingRightsResult = {
  building_rights: {
    max_floors: number;
    max_height_meters: number;
    max_coverage_percent: number;
    max_coverage_sqm: number;
    floor_area_ratio: number;
    max_building_area_sqm: number;
    parking_spaces_required: number;
    front_setback_meters: number;
    side_setback_meters: number;
    rear_setback_meters: number;
  };
  applicable_regulations: Regulation[];
};

export type UploadAnalysis = {
  vision_analysis: {
    description: string;
    ocr_text?: string | null;
    zones_identified: string[];
  };
  matching_regulations: Regulation[];
  similarity_scores: number[];
  extracted_text?: string | null;
  identified_zones: string[];
};

export type VectorDbStatus = {
  initialized?: boolean;
  total_regulations?: number;
  statistics?: Record<string, any>;
  status?: string;
  health?: string;
};

export type HealthProbe = {
  status: string;
  provider: {
    configured?: boolean;
    base_url?: string;
    model?: string;
    vision_model?: string;
    text?: {
      healthy?: boolean;
      status?: string;
      detail?: string;
      endpoint?: string;
      content_type?: string;
    };
    vision?: {
      healthy?: boolean;
      status?: string;
      detail?: string;
      endpoint?: string;
      content_type?: string;
    };
  };
  scraping?: {
    available?: boolean;
    status?: string;
    runtime_ready?: boolean;
    detail?: string | null;
    fetched_at?: string | null;
    count?: number;
    last_probe_at?: string | null;
    last_probe_duration_ms?: number | null;
    last_probe_count?: number;
    timeout_seconds?: number;
    metadata?: Record<string, unknown>;
  };
};

export type WorkspaceOverview = {
  selected_plan: DataFeature | null;
  brief: {
    plan_number: string;
    title: string;
    location: string;
    district: string;
    city: string;
    status: string;
    area: string;
    geometry: string;
    source_url?: string | null;
  } | null;
  summary_metrics: {
    tracked_plans: number;
    vector_status: string;
    provider_status: string;
    scraper_status: string;
  };
  constraint_signals: string[];
  next_actions: string[];
  shareable_brief: string | null;
  readiness: {
    has_selected_plan: boolean;
    provider_ready: boolean;
    scraper_ready: boolean;
    vector_status: string;
  };
};

export type OperationsOverview = {
  provider: HealthProbe["provider"];
  scraper: HealthProbe["scraping"];
  data_store: {
    total_plans: number;
    by_district: Record<string, number>;
    by_city: Record<string, number>;
    by_status: Record<string, number>;
    metadata?: Record<string, unknown>;
  };
  vector_db: VectorDbStatus & {
    health?: string;
  };
  inventory: {
    total_plans: number;
    districts: number;
    cities: number;
    statuses: number;
  };
  freshness: {
    last_updated?: string | null;
    update_note?: string | null;
    source?: string | null;
    endpoint?: string | null;
    fetched_at?: string | null;
    probe_status?: string | null;
    probe_detail?: string | null;
    last_probe_at?: string | null;
    last_probe_duration_ms?: number | null;
  };
  recommended_actions: string[];
};
