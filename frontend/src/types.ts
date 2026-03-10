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
    detail?: string | null;
    fetched_at?: string | null;
    count?: number;
    timeout_seconds?: number;
    metadata?: Record<string, unknown>;
  };
};
