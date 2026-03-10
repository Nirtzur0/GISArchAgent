import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowUpRight,
  Database,
  FileSearch,
  Layers3,
  Map as MapIcon,
  Radar,
  Search,
  Settings2,
  Sparkles
} from "lucide-react";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { MapContainer, Marker, Polygon, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import {
  addVectorDbRegulation,
  analyzeUpload,
  calculateRights,
  fetchFreshData,
  getDataStatus,
  getSystemStatus,
  getVectorDbStatus,
  importData,
  initializeVectorDb,
  queryRegulations,
  rebuildVectorDb,
  searchData,
  searchVectorDb
} from "./lib/api";
import type {
  BuildingRightsResult,
  DataFeature,
  DataSearchResponse,
  RegulationResult,
  SystemStatus,
  UploadAnalysis,
  VectorDbStatus
} from "./types";

const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

function App() {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand-block">
          <div className="brand-mark">
            <Layers3 size={22} />
          </div>
          <div>
            <p className="eyebrow">GIS planning workspace</p>
            <h1>GISArchAgent</h1>
          </div>
        </div>
        <nav className="nav-list">
          <NavCard to="/" icon={<Sparkles size={18} />} title="Intelligence" caption="Query regulations and system status" />
          <NavCard to="/map" icon={<MapIcon size={18} />} title="Map Workspace" caption="Explore plans, geometry, and districts" />
          <NavCard to="/analyzer" icon={<Radar size={18} />} title="Analyzer" caption="Rights, compliance, and upload analysis" />
          <NavCard to="/data" icon={<Database size={18} />} title="Data Ops" caption="DataStore and vector DB controls" />
        </nav>
        <div className="sidebar-note">
          <p className="eyebrow">New stack</p>
          <p>React UI backed by FastAPI endpoints over the existing Python service layer.</p>
        </div>
      </aside>
      <main className="app-main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Professional GIS interface</p>
            <h2>Map-forward planning operations</h2>
          </div>
          <a className="topbar-link" href="/api/health" target="_blank" rel="noreferrer">
            API health
            <ArrowUpRight size={16} />
          </a>
        </header>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/analyzer" element={<AnalyzerPage />} />
          <Route path="/data" element={<DataPage />} />
        </Routes>
      </main>
    </div>
  );
}

function NavCard(props: { to: string; icon: JSX.Element; title: string; caption: string }) {
  return (
    <NavLink to={props.to} className={({ isActive }) => `nav-card${isActive ? " active" : ""}`}>
      <div className="nav-icon">{props.icon}</div>
      <div>
        <strong>{props.title}</strong>
        <span>{props.caption}</span>
      </div>
    </NavLink>
  );
}

function DashboardPage() {
  const [queryText, setQueryText] = useState("What are the parking requirements for residential buildings?");
  const [result, setResult] = useState<RegulationResult | null>(null);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>(() => {
    const raw = localStorage.getItem("gisarchagent-query-history");
    return raw ? JSON.parse(raw) : [];
  });

  useEffect(() => {
    getSystemStatus().then(setStatus).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    localStorage.setItem("gisarchagent-query-history", JSON.stringify(history.slice(0, 10)));
  }, [history]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await queryRegulations(queryText);
      setResult(response);
      setHistory((current) => [queryText, ...current.filter((item) => item !== queryText)].slice(0, 10));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const districts = status?.data_store?.by_district ?? {};
  const districtRows = Object.entries(districts).slice(0, 5);

  return (
    <section className="page-grid">
      <div className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">Intelligence cockpit</p>
          <h3>Ask the regulation corpus, inspect sources, and monitor the system state.</h3>
          <p>
            The new interface keeps semantic query, status telemetry, and audit-friendly source references in one workspace.
          </p>
        </div>
        <div className="hero-stats">
          <StatTile label="Plans in DataStore" value={String(status?.data_store?.total_plans ?? "—")} />
          <StatTile
            label="Vector DB health"
            value={String((status?.vector_db as any)?.status ?? "—")}
          />
          <StatTile label="Cached entries" value={String((status?.cache as any)?.valid_entries ?? "—")} />
        </div>
      </div>

      <div className="panel panel--query">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Regulation query</p>
            <h4>Semantic answer synthesis</h4>
          </div>
          <Search size={18} />
        </div>
        <form onSubmit={onSubmit} className="stack">
          <textarea
            value={queryText}
            onChange={(event) => setQueryText(event.target.value)}
            rows={6}
            className="field field--textarea"
          />
          <div className="button-row">
            <button className="btn btn--primary" disabled={loading || !queryText.trim()}>
              {loading ? "Querying..." : "Run query"}
            </button>
            <button type="button" className="btn btn--ghost" onClick={() => setQueryText("")}>
              Clear
            </button>
          </div>
        </form>
        {error ? <ErrorBanner message={error} /> : null}
        {result ? (
          <div className="stack">
            <div className="answer-block">
              <p className="eyebrow">Answer</p>
              <p>{result.answer || "No synthesized answer returned."}</p>
            </div>
            <div className="stack sources-list">
              {result.regulations.map((regulation) => (
                <article key={regulation.id} className="source-card">
                  <div className="source-card__meta">
                    <strong>{regulation.title}</strong>
                    <span>
                      {regulation.type} · {regulation.jurisdiction}
                    </span>
                  </div>
                  <p>{regulation.summary || regulation.content.slice(0, 220)}</p>
                </article>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Operational readout</p>
            <h4>Top district coverage</h4>
          </div>
          <Settings2 size={18} />
        </div>
        <div className="stack">
          {districtRows.length ? districtRows.map(([label, count]) => (
            <BarRow key={label} label={label} value={count} max={Math.max(...Object.values(districts), 1)} />
          )) : <p className="muted">No DataStore stats available.</p>}
        </div>
        <div className="history-block">
          <p className="eyebrow">Session history</p>
          {history.length ? history.map((item) => <button key={item} className="history-chip" onClick={() => setQueryText(item)}>{item}</button>) : <p className="muted">No queries yet.</p>}
        </div>
      </div>
    </section>
  );
}

function MapPage() {
  const [filters, setFilters] = useState({ district: "", city: "", status: "", text: "" });
  const [response, setResponse] = useState<DataSearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    searchData(filters)
      .then(setResponse)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [filters]);

  const features = response?.items ?? [];
  const center = useMemo(() => {
    const first = features.find((item) => item.geometry_wgs84?.centroid)?.geometry_wgs84?.centroid;
    return first ? [first.lat, first.lon] as [number, number] : [31.7683, 35.2137] as [number, number];
  }, [features]);

  return (
    <section className="page-grid map-page">
      <div className="panel panel--map">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Map workspace</p>
            <h4>Geo-browse local plan data</h4>
          </div>
          <MapIcon size={18} />
        </div>
        <div className="filters-grid">
          <input className="field" placeholder="District" value={filters.district} onChange={(e) => setFilters({ ...filters, district: e.target.value })} />
          <input className="field" placeholder="City" value={filters.city} onChange={(e) => setFilters({ ...filters, city: e.target.value })} />
          <input className="field" placeholder="Status" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} />
          <input className="field" placeholder="Text search" value={filters.text} onChange={(e) => setFilters({ ...filters, text: e.target.value })} />
        </div>
        {error ? <ErrorBanner message={error} /> : null}
        <div className="map-stage">
          {loading ? (
            <div className="empty-state">Loading map data...</div>
          ) : (
            <MapContainer center={center} zoom={8} scrollWheelZoom className="map-canvas">
              <TileLayer
                attribution='&copy; OpenStreetMap contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {features.map((feature, index) => {
                const geometry = feature.geometry_wgs84;
                const attrs = feature.attributes;
                return (
                  <div key={`${attrs.pl_number || index}`}>
                    {geometry?.rings?.map((ring, ringIndex) => (
                      <Polygon key={`${attrs.pl_number}-poly-${ringIndex}`} positions={ring.map(([lat, lon]) => [lat, lon])} pathOptions={{ color: "#ff7b54", weight: 2, fillOpacity: 0.14 }}>
                        <Popup>
                          <strong>{attrs.pl_number || "Unknown plan"}</strong>
                          <p>{attrs.pl_name}</p>
                        </Popup>
                      </Polygon>
                    ))}
                    {geometry?.centroid ? (
                      <Marker position={[geometry.centroid.lat, geometry.centroid.lon]} icon={markerIcon}>
                        <Popup>
                          <strong>{attrs.pl_number || "Unknown plan"}</strong>
                          <p>{attrs.pl_name}</p>
                          <p>{attrs.plan_county_name || attrs.district_name}</p>
                        </Popup>
                      </Marker>
                    ) : null}
                  </div>
                );
              })}
            </MapContainer>
          )}
        </div>
      </div>
      <div className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Results</p>
            <h4>{response?.total ?? 0} plans matched</h4>
          </div>
          <FileSearch size={18} />
        </div>
        <div className="stack scroll-panel">
          {features.slice(0, 12).map((feature) => (
            <article key={String(feature.attributes.pl_number)} className="list-card">
              <strong>{feature.attributes.pl_number || "No plan number"}</strong>
              <p>{feature.attributes.pl_name || "Untitled plan"}</p>
              <span>
                {feature.attributes.plan_county_name || "Unknown city"} · {feature.attributes.station_desc || "Unknown status"}
              </span>
            </article>
          ))}
          {!features.length && !loading ? <p className="muted">No plans matched the current filters.</p> : null}
        </div>
      </div>
    </section>
  );
}

function AnalyzerPage() {
  const [location, setLocation] = useState("Tel Aviv");
  const [zone, setZone] = useState("R2");
  const [plotSize, setPlotSize] = useState(500);
  const [includeRegs, setIncludeRegs] = useState(true);
  const [result, setResult] = useState<BuildingRightsResult | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    calculateRights({
      plot_size_sqm: plotSize,
      zone_type: zone,
      location,
      include_regulations: includeRegs
    })
      .then(setResult)
      .catch((err) => setError(err.message));
  }, [includeRegs, location, plotSize, zone]);

  async function onUpload(file: File | undefined) {
    if (!file) return;
    setUploadError(null);
    try {
      setUploadResult(await analyzeUpload(file));
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err));
    }
  }

  const rights = result?.building_rights;

  return (
    <section className="page-grid analyzer-page">
      <div className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Rights engine</p>
            <h4>Program comparison and compliance</h4>
          </div>
          <Radar size={18} />
        </div>
        <div className="filters-grid filters-grid--three">
          <input className="field" value={location} onChange={(e) => setLocation(e.target.value)} />
          <select className="field" value={zone} onChange={(e) => setZone(e.target.value)}>
            <option value="R1">R1</option>
            <option value="R2">R2</option>
            <option value="R3">R3</option>
            <option value="C1">C1</option>
            <option value="MIXED">MIXED</option>
            <option value="TAMA35">TAMA35</option>
          </select>
          <input className="field" type="number" min={50} value={plotSize} onChange={(e) => setPlotSize(Number(e.target.value))} />
        </div>
        <label className="toggle">
          <input type="checkbox" checked={includeRegs} onChange={(e) => setIncludeRegs(e.target.checked)} />
          Include applicable regulations from the vector DB
        </label>
        {error ? <ErrorBanner message={error} /> : null}
        {rights ? (
          <div className="metric-grid">
            <StatTile label="Max floors" value={String(rights.max_floors)} />
            <StatTile label="Max height" value={`${rights.max_height_meters} m`} />
            <StatTile label="Coverage" value={`${rights.max_coverage_percent}%`} />
            <StatTile label="Max area" value={`${Math.round(rights.max_building_area_sqm)} sqm`} />
            <StatTile label="FAR" value={String(rights.floor_area_ratio)} />
            <StatTile label="Parking" value={String(rights.parking_spaces_required)} />
          </div>
        ) : (
          <div className="empty-state">Calculating building rights...</div>
        )}
        <div className="stack">
          <p className="eyebrow">Applicable regulations</p>
          {(result?.applicable_regulations ?? []).slice(0, 5).map((regulation) => (
            <article key={regulation.id} className="source-card">
              <div className="source-card__meta">
                <strong>{regulation.title}</strong>
                <span>{regulation.type}</span>
              </div>
              <p>{regulation.summary || regulation.content.slice(0, 180)}</p>
            </article>
          ))}
          {!result?.applicable_regulations?.length ? <p className="muted">No applicable regulations returned for this scenario.</p> : null}
        </div>
      </div>
      <div className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Upload analysis</p>
            <h4>Vision-backed document review</h4>
          </div>
          <AlertCircle size={18} />
        </div>
        <label className="upload-zone">
          <input type="file" accept=".pdf,.png,.jpg,.jpeg,.tiff" onChange={(e) => onUpload(e.target.files?.[0])} />
          <span>Drop a planning document or browse for a file</span>
        </label>
        {uploadError ? <ErrorBanner message={uploadError} /> : null}
        {uploadResult ? (
          <div className="stack">
            <div className="answer-block">
              <p className="eyebrow">Description</p>
              <p>{uploadResult.vision_analysis.description}</p>
            </div>
            <div className="tag-row">
              {uploadResult.identified_zones.map((zoneItem) => <span key={zoneItem} className="history-chip">{zoneItem}</span>)}
            </div>
            <div className="stack">
              {uploadResult.matching_regulations.map((regulation, index) => (
                <article key={regulation.id} className="source-card">
                  <div className="source-card__meta">
                    <strong>{regulation.title}</strong>
                    <span>{Math.round((uploadResult.similarity_scores[index] || 0) * 100)}% similarity</span>
                  </div>
                  <p>{regulation.summary || regulation.content.slice(0, 180)}</p>
                </article>
              ))}
            </div>
          </div>
        ) : (
          <p className="muted">Upload a file to run OCR, zoning extraction, and regulation matching.</p>
        )}
      </div>
    </section>
  );
}

function DataPage() {
  const [dataStatus, setDataStatus] = useState<any>(null);
  const [vectordbStatus, setVectordbStatus] = useState<VectorDbStatus | null>(null);
  const [searchTerm, setSearchTerm] = useState("parking");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setDataStatus(await getDataStatus());
      setVectordbStatus(await getVectorDbStatus());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function onVectorSearch(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const response = await searchVectorDb(searchTerm);
      setSearchResults(response.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function onImportData(file: File | undefined) {
    if (!file) return;
    try {
      const response = await importData(file);
      setMessage(`Imported ${response.imported} features, added ${response.added}.`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <section className="page-grid data-page">
      <div className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">DataStore</p>
            <h4>Local plan inventory</h4>
          </div>
          <Database size={18} />
        </div>
        <div className="metric-grid">
          <StatTile label="Plans" value={String(dataStatus?.total_plans ?? "—")} />
          <StatTile label="Districts" value={String(Object.keys(dataStatus?.by_district ?? {}).length)} />
          <StatTile label="Cities" value={String(Object.keys(dataStatus?.by_city ?? {}).length)} />
          <StatTile label="Statuses" value={String(Object.keys(dataStatus?.by_status ?? {}).length)} />
        </div>
        <div className="button-row">
          <button className="btn btn--primary" onClick={() => initializeVectorDb().then(refresh)}>Initialize vector DB</button>
          <button className="btn btn--ghost" onClick={() => rebuildVectorDb().then(refresh)}>Rebuild vector DB</button>
          <button className="btn btn--ghost" onClick={() => fetchFreshData({ source: "iplan", service_name: "xplan", max_plans: 50, where: "1=1" }).then(refresh)}>Fetch fresh data</button>
        </div>
        <label className="upload-zone upload-zone--compact">
          <input type="file" accept=".json" onChange={(e) => onImportData(e.target.files?.[0])} />
          <span>Import JSON plan data</span>
        </label>
        {message ? <div className="status-banner">{message}</div> : null}
        {error ? <ErrorBanner message={error} /> : null}
      </div>
      <div className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Vector DB</p>
            <h4>Search and author regulations</h4>
          </div>
          <FileSearch size={18} />
        </div>
        <div className="metric-grid">
          <StatTile label="Status" value={String(vectordbStatus?.status ?? "—")} />
          <StatTile label="Health" value={String(vectordbStatus?.health ?? "—")} />
          <StatTile label="Regulations" value={String(vectordbStatus?.total_regulations ?? "—")} />
        </div>
        <form onSubmit={onVectorSearch} className="stack">
          <input className="field" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
          <button className="btn btn--primary">Search vector DB</button>
        </form>
        <div className="stack scroll-panel">
          {searchResults.map((item) => (
            <article key={item.id} className="source-card">
              <div className="source-card__meta">
                <strong>{item.title}</strong>
                <span>{item.type}</span>
              </div>
              <p>{item.summary || item.content?.slice(0, 180)}</p>
            </article>
          ))}
        </div>
        <QuickRegulationForm onSuccess={refresh} onError={(value) => setError(value)} />
      </div>
    </section>
  );
}

function QuickRegulationForm(props: { onSuccess: () => void; onError: (value: string) => void }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await addVectorDbRegulation({
        title,
        content,
        reg_type: "local",
        jurisdiction: "national"
      });
      setTitle("");
      setContent("");
      props.onSuccess();
    } catch (err) {
      props.onError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <form onSubmit={onSubmit} className="stack inset-form">
      <p className="eyebrow">Add regulation</p>
      <input className="field" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
      <textarea className="field field--textarea" placeholder="Content" rows={4} value={content} onChange={(e) => setContent(e.target.value)} />
      <button className="btn btn--primary" disabled={!title.trim() || !content.trim()}>
        Add regulation
      </button>
    </form>
  );
}

function StatTile(props: { label: string; value: string }) {
  return (
    <div className="stat-tile">
      <span>{props.label}</span>
      <strong>{props.value}</strong>
    </div>
  );
}

function BarRow(props: { label: string; value: number; max: number }) {
  const width = Math.max(12, (props.value / props.max) * 100);
  return (
    <div className="bar-row">
      <div className="bar-row__head">
        <span>{props.label}</span>
        <strong>{props.value}</strong>
      </div>
      <div className="bar-row__track">
        <div className="bar-row__fill" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function ErrorBanner(props: { message: string }) {
  return (
    <div className="error-banner">
      <AlertCircle size={16} />
      <span>{props.message}</span>
    </div>
  );
}

export default App;
