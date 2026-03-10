import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  ArrowUpRight,
  Bot,
  ClipboardList,
  Database,
  FileSearch,
  Layers3,
  Map as MapIcon,
  Radar,
  Search,
  Server,
  ShieldAlert,
  Sparkles,
  Waypoints
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
  getFetcherHealth,
  getHealth,
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
  HealthProbe,
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

const QUERY_HISTORY_KEY = "gisarchagent-query-history";
const CURRENT_PLAN_KEY = "gisarchagent-current-plan";

function App() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [health, setHealth] = useState<HealthProbe | null>(null);
  const [currentPlan, setCurrentPlan] = useState<DataFeature | null>(() => readStoredPlan());
  const [lastUploadAnalysis, setLastUploadAnalysis] = useState<UploadAnalysis | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);

  async function refreshShell() {
    try {
      const [statusPayload, healthPayload] = await Promise.all([getSystemStatus(), getHealth()]);
      setSystemStatus(statusPayload);
      setHealth(healthPayload);
      setGlobalError(null);
    } catch (err) {
      setGlobalError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    refreshShell();
  }, []);

  useEffect(() => {
    if (currentPlan) {
      localStorage.setItem(CURRENT_PLAN_KEY, JSON.stringify(currentPlan));
    } else {
      localStorage.removeItem(CURRENT_PLAN_KEY);
    }
  }, [currentPlan]);

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="brand-block">
          <div className="brand-mark">
            <Layers3 size={20} />
          </div>
          <div>
            <p className="eyebrow">Planning workspace</p>
            <h1>GISArchAgent</h1>
          </div>
        </div>
        <nav className="nav-list">
          <NavCard to="/" icon={<ClipboardList size={18} />} title="Project Intake" caption="Due diligence, dossier, and grounded research" />
          <NavCard to="/map" icon={<MapIcon size={18} />} title="Site Context" caption="Map-first plan browsing and selected-site review" />
          <NavCard to="/analyzer" icon={<Radar size={18} />} title="Feasibility" caption="Rights, comparison, and upload analysis" />
          <NavCard to="/data" icon={<Database size={18} />} title="Admin Ops" caption="Data refresh, vector DB, and runtime validation" />
        </nav>

        <div className="sidebar-section compact-stack">
          <div>
            <p className="eyebrow">Current project</p>
            {currentPlan ? (
              <div className="current-plan-card">
                <strong>{getPlanTitle(currentPlan)}</strong>
                <span>{getPlanNumber(currentPlan)}</span>
                <span>{getPlanLocation(currentPlan)}</span>
              </div>
            ) : (
              <p className="muted">Select a plan from Project Intake or Site Context.</p>
            )}
          </div>
          <StatusChipRow health={health} />
        </div>
      </aside>

      <main className="app-main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Architecture office mode</p>
            <h2>Project due diligence and planning review</h2>
          </div>
          <div className="topbar-actions">
            <button className="btn btn--ghost" onClick={refreshShell}>Refresh status</button>
            <a className="topbar-link" href="/api/health" target="_blank" rel="noreferrer">
              API health
              <ArrowUpRight size={16} />
            </a>
          </div>
        </header>

        {globalError ? <ErrorBanner message={globalError} /> : null}
        {health && health.status !== "ok" ? (
          <InlineNotice
            tone="warning"
            title="Runtime dependencies need attention"
            message={buildGlobalHealthMessage(health)}
          />
        ) : null}

        <Routes>
          <Route
            path="/"
            element={
              <DashboardPage
                currentPlan={currentPlan}
                health={health}
                systemStatus={systemStatus}
                setCurrentPlan={setCurrentPlan}
              />
            }
          />
          <Route
            path="/map"
            element={
              <MapPage
                currentPlan={currentPlan}
                setCurrentPlan={setCurrentPlan}
              />
            }
          />
          <Route
            path="/analyzer"
            element={
              <AnalyzerPage
                currentPlan={currentPlan}
                health={health}
                lastUploadAnalysis={lastUploadAnalysis}
                setLastUploadAnalysis={setLastUploadAnalysis}
              />
            }
          />
          <Route
            path="/data"
            element={<DataPage health={health} onHealthRefresh={refreshShell} />}
          />
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

function DashboardPage(props: {
  currentPlan: DataFeature | null;
  health: HealthProbe | null;
  systemStatus: SystemStatus | null;
  setCurrentPlan: (plan: DataFeature | null) => void;
}) {
  const [filters, setFilters] = useState({ district: "", city: "", status: "", text: "" });
  const [response, setResponse] = useState<DataSearchResponse | null>(null);
  const [queryText, setQueryText] = useState("Summarize the key zoning constraints and approval risks for this plan.");
  const [result, setResult] = useState<RegulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>(() => readStoredHistory());
  const [copyState, setCopyState] = useState<string | null>(null);

  useEffect(() => {
    setSearchLoading(true);
    searchData(filters)
      .then((payload) => {
        setResponse(payload);
        if (!props.currentPlan && payload.items.length) {
          props.setCurrentPlan(payload.items[0]);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setSearchLoading(false));
  }, [filters]);

  useEffect(() => {
    localStorage.setItem(QUERY_HISTORY_KEY, JSON.stringify(history.slice(0, 10)));
  }, [history]);

  const selectedPlan = useMemo(() => {
    if (!response?.items?.length) return props.currentPlan;
    const currentNumber = getPlanNumber(props.currentPlan);
    return response.items.find((item) => getPlanNumber(item) === currentNumber) || props.currentPlan || response.items[0];
  }, [props.currentPlan, response]);

  const dossierSummary = useMemo(
    () => buildDossierSummary(selectedPlan, props.systemStatus, props.health),
    [selectedPlan, props.systemStatus, props.health]
  );

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const responsePayload = await queryRegulations(queryText, {
        location: selectedPlan ? getPlanLocation(selectedPlan) : undefined,
        maxResults: 6
      });
      setResult(responsePayload);
      setHistory((current) => [queryText, ...current.filter((item) => item !== queryText)].slice(0, 10));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function onCopySummary() {
    try {
      await navigator.clipboard.writeText(dossierSummary);
      setCopyState("Copied summary");
    } catch {
      setCopyState("Clipboard unavailable");
    }
  }

  return (
    <section className="page-grid page-grid--dashboard">
      <div className="panel panel--hero">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Project intake</p>
            <h3>Start from a site or plan, then move into constraints, map review, and feasibility.</h3>
          </div>
          <Sparkles size={18} />
        </div>
        <div className="hero-metrics">
          <StatTile label="Tracked plans" value={String(props.systemStatus?.data_store?.total_plans ?? "—")} />
          <StatTile label="Vector DB" value={String((props.systemStatus?.vector_db as any)?.status ?? "—")} />
          <StatTile label="Provider" value={props.health?.provider?.text?.healthy ? "ready" : "attention"} />
          <StatTile label="Scraper" value={String(props.health?.scraping?.status ?? "—")} />
        </div>
      </div>

      <div className="panel compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Plan search</p>
            <h4>Find the project under review</h4>
          </div>
          <Search size={18} />
        </div>
        <div className="filters-grid">
          <input className="field" placeholder="District" value={filters.district} onChange={(e) => setFilters({ ...filters, district: e.target.value })} />
          <input className="field" placeholder="City / municipality" value={filters.city} onChange={(e) => setFilters({ ...filters, city: e.target.value })} />
          <input className="field" placeholder="Status" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} />
          <input className="field" placeholder="Plan number / text" value={filters.text} onChange={(e) => setFilters({ ...filters, text: e.target.value })} />
        </div>
        <div className="list-stack scroll-panel scroll-panel--short">
          {searchLoading ? <div className="empty-state">Loading local plan inventory...</div> : null}
          {!searchLoading && (response?.items ?? []).slice(0, 8).map((feature) => (
            <button
              key={getPlanNumber(feature)}
              className={`list-card list-card--button${getPlanNumber(feature) === getPlanNumber(selectedPlan) ? " active" : ""}`}
              onClick={() => props.setCurrentPlan(feature)}
            >
              <strong>{getPlanNumber(feature)}</strong>
              <p>{getPlanTitle(feature)}</p>
              <span>{getPlanLocation(feature)} · {getPlanStatus(feature)}</span>
            </button>
          ))}
          {!searchLoading && !(response?.items?.length) ? <p className="muted">No plans matched the current search.</p> : null}
        </div>
      </div>

      <div className="panel compact-stack panel--dossier">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Project dossier</p>
            <h4>{selectedPlan ? getPlanTitle(selectedPlan) : "No plan selected"}</h4>
          </div>
          <ShieldAlert size={18} />
        </div>
        {selectedPlan ? (
          <>
            <dl className="detail-grid">
              <DetailItem label="Plan number" value={getPlanNumber(selectedPlan)} />
              <DetailItem label="Municipality" value={getPlanCity(selectedPlan)} />
              <DetailItem label="District" value={getPlanDistrict(selectedPlan)} />
              <DetailItem label="Status" value={getPlanStatus(selectedPlan)} />
              <DetailItem label="Area" value={formatArea(selectedPlan)} />
              <DetailItem label="Geometry" value={selectedPlan.has_geometry ? "Available" : "Missing"} />
            </dl>
            <div className="compact-stack">
              <p className="eyebrow">Recommended next actions</p>
              <ul className="action-list">
                {buildNextActions(selectedPlan, props.health).map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            <div className="compact-stack">
              <div className="button-row button-row--between">
                <p className="eyebrow">Export-ready summary</p>
                <button className="btn btn--ghost" onClick={onCopySummary}>Copy summary</button>
              </div>
              <pre className="summary-block">{dossierSummary}</pre>
              {copyState ? <p className="muted">{copyState}</p> : null}
            </div>
            <div className="button-row">
              <Link className="btn btn--primary" to="/map">Open site context</Link>
              <Link className="btn btn--ghost" to="/analyzer">Run feasibility</Link>
              {getPlanUrl(selectedPlan) ? (
                <a className="btn btn--ghost" href={getPlanUrl(selectedPlan)} target="_blank" rel="noreferrer">Open source plan</a>
              ) : null}
            </div>
          </>
        ) : (
          <div className="empty-state">Select a plan to generate a dossier.</div>
        )}
      </div>

      <div className="panel panel--wide compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Grounded query assistant</p>
            <h4>Ask about the selected plan, not the corpus in the abstract</h4>
          </div>
          <Bot size={18} />
        </div>
        {selectedPlan ? (
          <p className="muted">Questions will be grounded to {getPlanNumber(selectedPlan)} in {getPlanLocation(selectedPlan)}.</p>
        ) : (
          <p className="muted">Select a plan first so the question can stay tied to a real project dossier.</p>
        )}
        <form onSubmit={onSubmit} className="compact-stack">
          <textarea value={queryText} onChange={(event) => setQueryText(event.target.value)} rows={5} className="field field--textarea" />
          <div className="button-row">
            <button className="btn btn--primary" disabled={loading || !queryText.trim() || !selectedPlan}>{loading ? "Querying..." : "Ask about this project"}</button>
            <button type="button" className="btn btn--ghost" onClick={() => setQueryText("")}>Clear</button>
          </div>
        </form>
        {error ? <ErrorBanner message={error} /> : null}
        {result?.answer_warning ? <InlineNotice tone="warning" title="Synthesis unavailable" message={result.answer_warning} /> : null}
        {result?.answer ? (
          <div className="answer-block">
            <p className="eyebrow">Synthesized answer</p>
            <p>{result.answer}</p>
          </div>
        ) : null}
        <div className="compact-stack">
          <div className="button-row button-row--between">
            <p className="eyebrow">Relevant source regulations</p>
            <span className="muted">{result?.total_found ?? 0} matched</span>
          </div>
          {result?.regulations?.length ? result.regulations.map((regulation) => (
            <article key={regulation.id} className="source-card">
              <div className="source-card__meta">
                <strong>{regulation.title}</strong>
                <span>{regulation.type} · {regulation.jurisdiction}</span>
              </div>
              <p>{regulation.summary || regulation.content.slice(0, 220)}</p>
            </article>
          )) : <p className="muted">Run a query to inspect supporting regulations.</p>}
        </div>
        {history.length ? (
          <div className="history-block">
            <p className="eyebrow">Recent prompts</p>
            <div className="tag-row">
              {history.map((item) => <button key={item} className="history-chip" onClick={() => setQueryText(item)}>{item}</button>)}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function MapPage(props: { currentPlan: DataFeature | null; setCurrentPlan: (plan: DataFeature | null) => void }) {
  const [filters, setFilters] = useState({ district: "", city: "", status: "", text: "" });
  const [response, setResponse] = useState<DataSearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (props.currentPlan && !filters.city) {
      setFilters((current) => ({ ...current, city: getPlanCity(props.currentPlan) }));
    }
  }, [props.currentPlan]);

  useEffect(() => {
    setLoading(true);
    searchData(filters)
      .then((payload) => {
        setResponse(payload);
        if (!props.currentPlan && payload.items.length) {
          props.setCurrentPlan(payload.items[0]);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [filters]);

  const features = response?.items ?? [];
  const selectedPlan = features.find((item) => getPlanNumber(item) === getPlanNumber(props.currentPlan)) || props.currentPlan || features[0] || null;
  const center = useMemo(() => {
    const centroid = selectedPlan?.geometry_wgs84?.centroid;
    return centroid ? [centroid.lat, centroid.lon] as [number, number] : [31.7683, 35.2137] as [number, number];
  }, [selectedPlan]);

  return (
    <section className="page-grid page-grid--map">
      <div className="panel panel--map-shell">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Site context</p>
            <h4>Browse planning geometry with the selected project kept in focus</h4>
          </div>
          <Waypoints size={18} />
        </div>
        <div className="filters-grid">
          <input className="field" placeholder="District" value={filters.district} onChange={(e) => setFilters({ ...filters, district: e.target.value })} />
          <input className="field" placeholder="City" value={filters.city} onChange={(e) => setFilters({ ...filters, city: e.target.value })} />
          <input className="field" placeholder="Status" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} />
          <input className="field" placeholder="Plan number / text" value={filters.text} onChange={(e) => setFilters({ ...filters, text: e.target.value })} />
        </div>
        {error ? <ErrorBanner message={error} /> : null}
        <div className="map-stage">
          {loading ? (
            <div className="empty-state">Loading site context...</div>
          ) : (
            <MapContainer center={center} zoom={10} scrollWheelZoom className="map-canvas">
              <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {features.map((feature, index) => {
                const geometry = feature.geometry_wgs84;
                const key = `${getPlanNumber(feature)}-${index}`;
                const isSelected = getPlanNumber(feature) === getPlanNumber(selectedPlan);
                return (
                  <div key={key}>
                    {geometry?.rings?.map((ring, ringIndex) => (
                      <Polygon
                        key={`${key}-poly-${ringIndex}`}
                        positions={ring.map(([lat, lon]) => [lat, lon])}
                        pathOptions={{ color: isSelected ? "#ff8f5b" : "#4fc3b7", weight: isSelected ? 3 : 2, fillOpacity: isSelected ? 0.22 : 0.1 }}
                        eventHandlers={{ click: () => props.setCurrentPlan(feature) }}
                      >
                        <Popup>
                          <strong>{getPlanNumber(feature)}</strong>
                          <p>{getPlanTitle(feature)}</p>
                        </Popup>
                      </Polygon>
                    ))}
                    {geometry?.centroid ? (
                      <Marker position={[geometry.centroid.lat, geometry.centroid.lon]} icon={markerIcon} eventHandlers={{ click: () => props.setCurrentPlan(feature) }}>
                        <Popup>
                          <strong>{getPlanNumber(feature)}</strong>
                          <p>{getPlanTitle(feature)}</p>
                          <p>{getPlanLocation(feature)}</p>
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

      <div className="panel compact-stack panel--results">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Matching plans</p>
            <h4>{response?.total ?? 0} local plans</h4>
          </div>
          <FileSearch size={18} />
        </div>
        <div className="list-stack scroll-panel">
          {features.map((feature) => (
            <button
              key={getPlanNumber(feature)}
              className={`list-card list-card--button${getPlanNumber(feature) === getPlanNumber(selectedPlan) ? " active" : ""}`}
              onClick={() => props.setCurrentPlan(feature)}
            >
              <strong>{getPlanNumber(feature)}</strong>
              <p>{getPlanTitle(feature)}</p>
              <span>{getPlanLocation(feature)} · {getPlanStatus(feature)}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="panel compact-stack panel--details">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Selected site</p>
            <h4>{selectedPlan ? getPlanTitle(selectedPlan) : "No plan selected"}</h4>
          </div>
          <MapIcon size={18} />
        </div>
        {selectedPlan ? (
          <>
            <dl className="detail-grid">
              <DetailItem label="Plan number" value={getPlanNumber(selectedPlan)} />
              <DetailItem label="Municipality" value={getPlanCity(selectedPlan)} />
              <DetailItem label="District" value={getPlanDistrict(selectedPlan)} />
              <DetailItem label="Approval state" value={getPlanStatus(selectedPlan)} />
              <DetailItem label="Area" value={formatArea(selectedPlan)} />
              <DetailItem label="Geometry" value={selectedPlan.has_geometry ? "Available" : "Missing"} />
            </dl>
            <div className="compact-stack">
              <p className="eyebrow">Constraint cues</p>
              <ul className="action-list">
                {buildConstraintSignals(selectedPlan).map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            <div className="button-row">
              <Link className="btn btn--primary" to="/analyzer">Analyze this plan</Link>
              {getPlanUrl(selectedPlan) ? <a className="btn btn--ghost" href={getPlanUrl(selectedPlan)} target="_blank" rel="noreferrer">Open source file</a> : null}
            </div>
          </>
        ) : (
          <div className="empty-state">Choose a plan from the results list or map.</div>
        )}
      </div>
    </section>
  );
}

function AnalyzerPage(props: {
  currentPlan: DataFeature | null;
  health: HealthProbe | null;
  lastUploadAnalysis: UploadAnalysis | null;
  setLastUploadAnalysis: (analysis: UploadAnalysis | null) => void;
}) {
  const [location, setLocation] = useState(props.currentPlan ? getPlanLocation(props.currentPlan) : "Tel Aviv");
  const [zone, setZone] = useState("R2");
  const [plotSize, setPlotSize] = useState(inferPlotSize(props.currentPlan));
  const [proposedFloors, setProposedFloors] = useState(4);
  const [proposedArea, setProposedArea] = useState(inferPlotSize(props.currentPlan) * 0.9);
  const [proposedParking, setProposedParking] = useState(8);
  const [includeRegs, setIncludeRegs] = useState(true);
  const [result, setResult] = useState<BuildingRightsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (props.currentPlan) {
      const nextLocation = getPlanLocation(props.currentPlan);
      const nextPlotSize = inferPlotSize(props.currentPlan);
      setLocation(nextLocation);
      setPlotSize(nextPlotSize);
      setProposedArea(nextPlotSize * 0.9);
    }
  }, [props.currentPlan]);

  useEffect(() => {
    calculateRights({
      plot_size_sqm: plotSize,
      zone_type: zone,
      location,
      include_regulations: includeRegs
    })
      .then((payload) => {
        setResult(payload);
        setError(null);
      })
      .catch((err) => setError(err.message));
  }, [includeRegs, location, plotSize, zone]);

  async function onUpload(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      props.setLastUploadAnalysis(await analyzeUpload(file));
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
    }
  }

  const rights = result?.building_rights;
  const comparisons = rights ? [
    compareMetric("Floors", proposedFloors, rights.max_floors, "floors"),
    compareMetric("Built area", proposedArea, rights.max_building_area_sqm, "sqm"),
    compareMetric("Parking", proposedParking, rights.parking_spaces_required, "spaces", true)
  ] : [];

  return (
    <section className="page-grid page-grid--analyzer">
      <div className="panel compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Feasibility inputs</p>
            <h4>{props.currentPlan ? `Working on ${getPlanNumber(props.currentPlan)}` : "Set project assumptions"}</h4>
          </div>
          <Radar size={18} />
        </div>
        {props.currentPlan ? <p className="muted">Project context: {getPlanTitle(props.currentPlan)} in {getPlanLocation(props.currentPlan)}.</p> : <InlineNotice tone="warning" title="No selected plan" message="Choose a plan from Project Intake or Site Context so feasibility stays tied to a real dossier." />}
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
          Pull linked regulations from the vector database
        </label>
        {error ? <ErrorBanner message={error} /> : null}
        {rights ? (
          <div className="metric-grid metric-grid--dense">
            <StatTile label="Allowed floors" value={String(rights.max_floors)} />
            <StatTile label="Allowed height" value={`${rights.max_height_meters} m`} />
            <StatTile label="Coverage" value={`${rights.max_coverage_percent}%`} />
            <StatTile label="Buildable area" value={`${Math.round(rights.max_building_area_sqm)} sqm`} />
            <StatTile label="FAR" value={String(rights.floor_area_ratio)} />
            <StatTile label="Required parking" value={String(rights.parking_spaces_required)} />
          </div>
        ) : (
          <div className="empty-state">Calculating building rights...</div>
        )}
        <div className="compact-stack">
          <p className="eyebrow">Proposal comparison</p>
          <div className="comparison-inputs">
            <label><span>Proposed floors</span><input className="field" type="number" min={0} value={proposedFloors} onChange={(e) => setProposedFloors(Number(e.target.value))} /></label>
            <label><span>Proposed built area (sqm)</span><input className="field" type="number" min={0} value={proposedArea} onChange={(e) => setProposedArea(Number(e.target.value))} /></label>
            <label><span>Proposed parking</span><input className="field" type="number" min={0} value={proposedParking} onChange={(e) => setProposedParking(Number(e.target.value))} /></label>
          </div>
          <div className="comparison-grid">
            {comparisons.map((item) => (
              <article key={item.label} className={`comparison-card comparison-card--${item.status}`}>
                <strong>{item.label}</strong>
                <span>{item.proposedLabel} proposed / {item.allowedLabel} allowed</span>
                <p>{item.message}</p>
              </article>
            ))}
          </div>
        </div>
        <div className="compact-stack">
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
          {!result?.applicable_regulations?.length ? <p className="muted">No linked regulations were returned for this scenario.</p> : null}
        </div>
      </div>

      <div className="panel compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Upload analysis</p>
            <h4>Review a drawing or plan package inside the current project context</h4>
          </div>
          <AlertCircle size={18} />
        </div>
        {!props.health?.provider?.vision?.healthy ? (
          <InlineNotice tone="warning" title="MockChat vision unavailable" message={props.health?.provider?.vision?.detail || "The configured provider is not exposing a valid OpenAI-compatible vision endpoint."} />
        ) : null}
        <label className="upload-zone">
          <input type="file" accept=".pdf,.png,.jpg,.jpeg,.tiff" onChange={(e) => onUpload(e.target.files?.[0])} />
          <span>{uploading ? "Analyzing file..." : "Upload drawing, PDF, or scan"}</span>
        </label>
        {uploadError ? <ErrorBanner message={uploadError} /> : null}
        {props.lastUploadAnalysis ? (
          <div className="compact-stack">
            <div className="answer-block">
              <p className="eyebrow">Description</p>
              <p>{props.lastUploadAnalysis.vision_analysis.description}</p>
            </div>
            <div className="tag-row">
              {props.lastUploadAnalysis.identified_zones.map((zoneItem) => <span key={zoneItem} className="history-chip">{zoneItem}</span>)}
            </div>
            <div className="compact-stack">
              {props.lastUploadAnalysis.matching_regulations.map((regulation, index) => (
                <article key={regulation.id} className="source-card">
                  <div className="source-card__meta">
                    <strong>{regulation.title}</strong>
                    <span>{Math.round((props.lastUploadAnalysis?.similarity_scores[index] || 0) * 100)}% similarity</span>
                  </div>
                  <p>{regulation.summary || regulation.content.slice(0, 180)}</p>
                </article>
              ))}
            </div>
          </div>
        ) : (
          <p className="muted">Upload a plan package to run OCR, zoning extraction, and regulation matching.</p>
        )}
      </div>
    </section>
  );
}

function DataPage(props: { health: HealthProbe | null; onHealthRefresh: () => Promise<void> | void }) {
  const [dataStatus, setDataStatus] = useState<any>(null);
  const [vectordbStatus, setVectordbStatus] = useState<VectorDbStatus | null>(null);
  const [fetcherProbe, setFetcherProbe] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState("parking");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const [dataPayload, vectorPayload, probePayload] = await Promise.all([
        getDataStatus(),
        getVectorDbStatus(),
        getFetcherHealth()
      ]);
      setDataStatus(dataPayload);
      setVectordbStatus(vectorPayload);
      setFetcherProbe(probePayload);
      setError(null);
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

  async function onFetchFreshData() {
    try {
      const response = await fetchFreshData({ source: "iplan", service_name: "xplan", max_plans: 10, where: "1=1", timeout_seconds: 30 });
      setMessage(`Fetch status: ${response.fetch.status}. fetched=${response.fetched_count}, added=${response.added_count}`);
      await refresh();
      await props.onHealthRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <section className="page-grid page-grid--data">
      <div className="panel compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Admin operations</p>
            <h4>Runtime dependencies and scrape validation</h4>
          </div>
          <Server size={18} />
        </div>
        <div className="metric-grid metric-grid--dense">
          <StatTile label="Provider" value={props.health?.provider?.text?.healthy ? "ready" : "blocked"} />
          <StatTile label="Scraper" value={String(fetcherProbe?.status ?? "—")} />
          <StatTile label="Last fetch" value={formatTimestamp(dataStatus?.metadata?.fetched_at)} />
          <StatTile label="Stored plans" value={String(dataStatus?.total_plans ?? "—")} />
        </div>
        {props.health?.provider?.text?.healthy ? null : <InlineNotice tone="warning" title="MockChat path is invalid" message={props.health?.provider?.text?.detail || "Update OPENAI_BASE_URL to the actual OpenAI-compatible API endpoint."} />}
        {fetcherProbe?.status !== "ready" ? <InlineNotice tone="warning" title="Scraper needs validation" message={fetcherProbe?.detail || "The iPlan probe did not complete successfully."} /> : null}
        <div className="button-row">
          <button className="btn btn--ghost" onClick={() => getFetcherHealth().then(setFetcherProbe)}>Validate scraper</button>
          <button className="btn btn--primary" onClick={onFetchFreshData}>Run bounded data fetch</button>
          <button className="btn btn--ghost" onClick={() => initializeVectorDb().then(refresh)}>Initialize vector DB</button>
          <button className="btn btn--ghost" onClick={() => rebuildVectorDb().then(refresh)}>Rebuild vector DB</button>
        </div>
        {message ? <div className="status-banner">{message}</div> : null}
        {error ? <ErrorBanner message={error} /> : null}
        <label className="upload-zone upload-zone--compact">
          <input type="file" accept=".json" onChange={(e) => onImportData(e.target.files?.[0])} />
          <span>Import JSON plan data</span>
        </label>
      </div>

      <div className="panel compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Data inventory</p>
            <h4>Local plan inventory</h4>
          </div>
          <Database size={18} />
        </div>
        <div className="metric-grid metric-grid--dense">
          <StatTile label="Plans" value={String(dataStatus?.total_plans ?? "—")} />
          <StatTile label="Districts" value={String(Object.keys(dataStatus?.by_district ?? {}).length)} />
          <StatTile label="Cities" value={String(Object.keys(dataStatus?.by_city ?? {}).length)} />
          <StatTile label="Statuses" value={String(Object.keys(dataStatus?.by_status ?? {}).length)} />
        </div>
        <div className="compact-stack">
          <p className="eyebrow">Latest source metadata</p>
          <dl className="detail-grid">
            <DetailItem label="Fetched at" value={formatTimestamp(dataStatus?.metadata?.fetched_at)} />
            <DetailItem label="Source" value={String(dataStatus?.metadata?.source ?? "—")} />
            <DetailItem label="Endpoint" value={String(dataStatus?.metadata?.endpoint ?? "—")} />
            <DetailItem label="Probe result" value={String(fetcherProbe?.status ?? "—")} />
          </dl>
        </div>
      </div>

      <div className="panel compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Vector DB</p>
            <h4>Search and author regulations</h4>
          </div>
          <FileSearch size={18} />
        </div>
        <div className="metric-grid metric-grid--dense">
          <StatTile label="Status" value={String(vectordbStatus?.status ?? "—")} />
          <StatTile label="Health" value={String(vectordbStatus?.health ?? "—")} />
          <StatTile label="Regulations" value={String(vectordbStatus?.total_regulations ?? "—")} />
        </div>
        <form onSubmit={onVectorSearch} className="compact-stack">
          <input className="field" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
          <button className="btn btn--primary">Search vector DB</button>
        </form>
        <div className="list-stack scroll-panel scroll-panel--short">
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
    <form onSubmit={onSubmit} className="compact-stack inset-form">
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

function StatusChipRow(props: { health: HealthProbe | null }) {
  return (
    <div className="status-chip-row">
      <span className={`status-chip ${props.health?.provider?.text?.healthy ? "status-chip--ok" : "status-chip--warn"}`}>MockChat {props.health?.provider?.text?.healthy ? "ready" : "blocked"}</span>
      <span className={`status-chip ${props.health?.scraping?.status === "ready" ? "status-chip--ok" : "status-chip--warn"}`}>Scraper {props.health?.scraping?.status ?? "unknown"}</span>
    </div>
  );
}

function DetailItem(props: { label: string; value: string }) {
  return (
    <div className="detail-item">
      <dt>{props.label}</dt>
      <dd>{props.value}</dd>
    </div>
  );
}

function InlineNotice(props: { tone: "warning" | "info"; title: string; message: string }) {
  return (
    <div className={`inline-notice inline-notice--${props.tone}`}>
      <strong>{props.title}</strong>
      <span>{props.message}</span>
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

function compareMetric(label: string, proposed: number, allowed: number, unit: string, minimum = false) {
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
        : `Exceeds allowance by ${formatMetric(delta, unit)}.`
  };
}

function formatMetric(value: number, unit: string) {
  const rounded = Math.round(value * 10) / 10;
  return `${rounded} ${unit}`;
}

function readStoredHistory(): string[] {
  try {
    const raw = localStorage.getItem(QUERY_HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function readStoredPlan(): DataFeature | null {
  try {
    const raw = localStorage.getItem(CURRENT_PLAN_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function getAttrs(feature?: DataFeature | null) {
  return feature?.attributes || {};
}

function getPlanNumber(feature?: DataFeature | null) {
  return String(getAttrs(feature).pl_number || "No plan number");
}

function getPlanTitle(feature?: DataFeature | null) {
  return String(getAttrs(feature).pl_name || "Untitled plan");
}

function getPlanCity(feature?: DataFeature | null) {
  return String(getAttrs(feature).plan_county_name || "Unknown city");
}

function getPlanDistrict(feature?: DataFeature | null) {
  return String(getAttrs(feature).district_name || "Unknown district");
}

function getPlanStatus(feature?: DataFeature | null) {
  return String(getAttrs(feature).station_desc || getAttrs(feature).internet_short_status || "Unknown status");
}

function getPlanLocation(feature?: DataFeature | null) {
  return `${getPlanCity(feature)}, ${getPlanDistrict(feature)}`;
}

function getPlanUrl(feature?: DataFeature | null) {
  const value = getAttrs(feature).pl_url;
  return value ? String(value) : "";
}

function formatArea(feature?: DataFeature | null) {
  const raw = Number(getAttrs(feature).pl_area_dunam || 0);
  if (!raw) return "Unknown";
  return `${raw.toFixed(2)} dunam`;
}

function inferPlotSize(feature?: DataFeature | null) {
  const dunam = Number(getAttrs(feature).pl_area_dunam || 0);
  if (!dunam) return 500;
  return Math.max(250, Math.round(dunam * 1000));
}

function buildNextActions(feature: DataFeature, health: HealthProbe | null): string[] {
  const actions = [
    `Verify municipality status: ${getPlanStatus(feature)}.`,
    `Run feasibility assumptions for ${getPlanNumber(feature)} before client review.`,
    `Open the source plan package and confirm setbacks, parking, and approval notes.`
  ];
  if (!health?.provider?.text?.healthy) {
    actions.push("Fix MockChat configuration before relying on synthesized summaries.");
  }
  if (!feature.has_geometry) {
    actions.push("Geometry is missing; confirm parcel boundaries before map-based review.");
  }
  return actions;
}

function buildConstraintSignals(feature: DataFeature): string[] {
  const signals = [
    `Approval state: ${getPlanStatus(feature)}.`,
    `Municipality context: ${getPlanLocation(feature)}.`,
    feature.has_geometry ? "Geometry is available for map review." : "Geometry is missing, so parcel context needs manual verification."
  ];
  const objectives = getAttrs(feature).pl_objectives;
  if (objectives) {
    signals.push(`Plan objective: ${String(objectives).slice(0, 120)}${String(objectives).length > 120 ? "..." : ""}`);
  }
  return signals;
}

function buildDossierSummary(feature: DataFeature | null, status: SystemStatus | null, health: HealthProbe | null) {
  if (!feature) {
    return "No plan selected.";
  }
  return [
    `Project dossier: ${getPlanNumber(feature)} - ${getPlanTitle(feature)}`,
    `Location: ${getPlanLocation(feature)}`,
    `Approval state: ${getPlanStatus(feature)}`,
    `Area: ${formatArea(feature)}`,
    `Geometry: ${feature.has_geometry ? "available" : "missing"}`,
    `Vector DB status: ${String((status?.vector_db as any)?.status ?? "unknown")}`,
    `MockChat status: ${health?.provider?.text?.healthy ? "ready" : "blocked"}`,
    `Scraper status: ${String(health?.scraping?.status ?? "unknown")}`,
    `Next review step: validate feasibility assumptions and confirm source regulations before client output.`
  ].join("\n");
}

function buildGlobalHealthMessage(health: HealthProbe) {
  const parts: string[] = [];
  if (!health.provider?.text?.healthy) {
    parts.push(health.provider?.text?.detail || "MockChat text provider is not healthy.");
  }
  if (health.scraping?.status !== "ready") {
    parts.push(health.scraping?.detail || `Scraper probe status: ${health.scraping?.status}.`);
  }
  return parts.join(" ");
}

function formatTimestamp(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default App;
