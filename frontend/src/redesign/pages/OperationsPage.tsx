import { FormEvent, useEffect, useState } from "react";
import { AlertCircle, ArrowRight, Database, FileSearch, Server } from "lucide-react";

import {
  addVectorDbRegulation,
  fetchFreshData,
  getFetcherHealth,
  getOperationsOverview,
  importData,
  initializeVectorDb,
  rebuildVectorDb,
  searchVectorDb,
} from "../../lib/api";
import type { HealthProbe, OperationsOverview } from "../../types";
import { formatStatusLabel, formatTimestamp, normalizeErrorMessage } from "../model";
import { trackUiEvent } from "../tracking";
import { DetailItem, ErrorBanner, SourceCard, StateSurface, StatTile } from "../components";

type OperationsPageProps = {
  health: HealthProbe | null;
  onHealthRefresh: () => Promise<void> | void;
};

export function OperationsPage(props: OperationsPageProps) {
  const [overview, setOverview] = useState<OperationsOverview | null>(null);
  const [searchTerm, setSearchTerm] = useState("parking");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function buildScraperSurface(scraper: OperationsOverview["scraper"] | null | undefined) {
    const status = scraper?.status || "unknown";
    if (status === "ready") {
      return {
        tone: "info" as const,
        title: "Scraper probe is ready",
        message:
          scraper?.detail ||
          "A bounded live probe succeeded. You can validate or refresh planning data from this screen.",
      };
    }
    if (status === "unvalidated") {
      return {
        tone: "warning" as const,
        title: "Scraper has not been validated",
        message:
          scraper?.detail ||
          "Run Validate scraper to execute a bounded live probe before relying on fresh upstream data.",
      };
    }
    if (status === "timeout") {
      return {
        tone: "warning" as const,
        title: "Scraper probe timed out",
        message:
          scraper?.detail ||
          "The bounded live probe timed out before the provider returned data.",
      };
    }
    return {
      tone: "warning" as const,
      title: "Scraper needs attention",
      message:
        scraper?.detail || `The latest scraper probe reported status ${status}.`,
    };
  }

  async function refreshOverview() {
    try {
      const payload = await getOperationsOverview();
      setOverview(payload);
      setError(null);
    } catch (err) {
      const message = normalizeErrorMessage(err instanceof Error ? err.message : String(err));
      setError(message);
      trackUiEvent("operations_error_state_seen", {
        route: "/data",
        status: "error",
        context: { message },
      });
    }
  }

  useEffect(() => {
    refreshOverview();
  }, []);

  async function validateScraper() {
    try {
      setError(null);
      const probe = await getFetcherHealth();
      await refreshOverview();
      await props.onHealthRefresh();
      const suffix = probe.detail ? ` ${probe.detail}` : "";
      setMessage(`Scraper validation status: ${probe.status}.${suffix}`.trim());
      trackUiEvent("operations_scraper_validated", {
        route: "/data",
        context: {
          scraper_status: probe.status,
          runtime_ready: probe.runtime_ready ?? false,
          last_probe_count: probe.last_probe_count ?? probe.count ?? 0,
        },
      });
    } catch (err) {
      const message = normalizeErrorMessage(err instanceof Error ? err.message : String(err));
      setError(message);
      trackUiEvent("operations_scraper_validation_error_seen", {
        route: "/data",
        status: "error",
        context: { message },
      });
    }
  }

  async function onVectorSearch(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const response = await searchVectorDb(searchTerm);
      setSearchResults(response.items || []);
      trackUiEvent("operations_vector_search_used", {
        route: "/data",
        context: { query: searchTerm, result_count: (response.items || []).length },
      });
    } catch (err) {
      const message = normalizeErrorMessage(err instanceof Error ? err.message : String(err));
      setError(message);
      trackUiEvent("operations_vector_search_error_seen", {
        route: "/data",
        status: "error",
        context: { message, query: searchTerm },
      });
    }
  }

  async function onImportData(file: File | undefined) {
    if (!file) return;
    try {
      const response = await importData(file);
      setMessage(`Imported ${response.imported} features, added ${response.added}.`);
      await refreshOverview();
      trackUiEvent("operations_data_imported", {
        route: "/data",
        context: { imported: response.imported, added: response.added },
      });
    } catch (err) {
      const message = normalizeErrorMessage(err instanceof Error ? err.message : String(err));
      setError(message);
      trackUiEvent("operations_data_import_error_seen", {
        route: "/data",
        status: "error",
        context: { message },
      });
    }
  }

  async function onFetchFreshData() {
    try {
      const response = await fetchFreshData({
        source: "iplan",
        service_name: "xplan",
        max_plans: 10,
        where: "1=1",
        timeout_seconds: 30,
      });
      setMessage(
        `Fetch status: ${response.fetch.status}. fetched=${response.fetched_count}, added=${response.added_count}`,
      );
      await refreshOverview();
      await props.onHealthRefresh();
      trackUiEvent("operations_bounded_fetch_run", {
        route: "/data",
        context: {
          fetch_status: response.fetch.status,
          fetched_count: response.fetched_count,
          added_count: response.added_count,
        },
      });
    } catch (err) {
      const message = normalizeErrorMessage(err instanceof Error ? err.message : String(err));
      setError(message);
      trackUiEvent("operations_bounded_fetch_error_seen", {
        route: "/data",
        status: "error",
        context: { message },
      });
    }
  }

  async function onInitializeVectorDb() {
    try {
      await initializeVectorDb();
      await refreshOverview();
      trackUiEvent("operations_vector_initialize_run", { route: "/data" });
    } catch (err) {
      setError(normalizeErrorMessage(err instanceof Error ? err.message : String(err)));
    }
  }

  async function onRebuildVectorDb() {
    try {
      await rebuildVectorDb();
      await refreshOverview();
      trackUiEvent("operations_vector_rebuild_run", { route: "/data" });
    } catch (err) {
      setError(normalizeErrorMessage(err instanceof Error ? err.message : String(err)));
    }
  }

  return (
    <section className="page-grid page-grid--operations">
      <div className="panel panel--wide operations-hero compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Operations health</p>
            <h3>Keep data, provider health, and regulations trustworthy.</h3>
          </div>
          <Server size={18} />
        </div>
        <p className="lede">
          Operational work is still visible, but it now reads as a calm maintenance surface rather
          than bleeding raw backend failure text into the planner flow.
        </p>
        <div className="hero-metrics">
          <StatTile
            label="Provider"
            value={
              props.health?.provider?.text?.healthy
                ? "Ready"
                : props.health?.provider?.configured
                  ? "Blocked"
                  : "Optional"
            }
          />
          <StatTile label="Scraper" value={formatStatusLabel(overview?.scraper?.status)} />
          <StatTile label="Stored plans" value={String(overview?.inventory.total_plans ?? "—")} />
          <StatTile
            label="Vector health"
            value={formatStatusLabel(overview?.vector_db.health ?? overview?.vector_db.status)}
          />
        </div>
        <div className="button-row">
          <button className="btn btn--ghost" onClick={validateScraper}>
            Validate scraper
          </button>
          <button className="btn btn--primary" onClick={onFetchFreshData}>
            Run bounded data fetch
          </button>
          <button className="btn btn--ghost" onClick={onInitializeVectorDb}>
            Initialize vector DB
          </button>
          <button className="btn btn--ghost" onClick={onRebuildVectorDb}>
            Rebuild vector DB
          </button>
        </div>
        {overview?.recommended_actions?.length ? (
          <StateSurface
            tone="info"
            title="Recommended maintenance focus"
            message={overview.recommended_actions[0]}
          />
        ) : null}
        {message ? <StateSurface tone="info" title="Latest operation update" message={message} /> : null}
        {error ? <StateSurface tone="danger" title="Operational request failed" message={error} /> : null}
      </div>

      <div className="panel operations-runtime compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Runtime health</p>
            <h4>Provider, scraper, and import actions</h4>
          </div>
          <AlertCircle size={18} />
        </div>
        {props.health?.provider?.text?.healthy ? (
          <StateSurface
            tone="info"
            title="Provider path looks healthy"
            message="OpenAI-compatible text requests are currently available to the product."
          />
        ) : !props.health?.provider?.configured ? (
          <StateSurface
            tone="info"
            title="Provider path is optional and currently unconfigured"
            message="Retrieval-only answers and local workflows remain available. Configure OPENAI_BASE_URL only when you want synthesis or upload analysis."
          />
        ) : (
          <StateSurface
            tone="warning"
            title="Provider path is blocked"
            message={
              props.health?.provider?.text?.detail ||
              "Update OPENAI_BASE_URL to the actual OpenAI-compatible API endpoint."
            }
          />
        )}
        <StateSurface {...buildScraperSurface(overview?.scraper)} />
        <label className="upload-zone upload-zone--compact">
          <input type="file" accept=".json" onChange={(e) => onImportData(e.target.files?.[0])} />
          <span>Import JSON plan data</span>
        </label>
      </div>

      <div className="panel operations-data compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Data inventory</p>
            <h4>Local plan inventory</h4>
          </div>
          <Database size={18} />
        </div>
        <div className="metric-grid metric-grid--dense">
          <StatTile label="Plans" value={String(overview?.inventory.total_plans ?? "—")} />
          <StatTile label="Districts" value={String(overview?.inventory.districts ?? "—")} />
          <StatTile label="Cities" value={String(overview?.inventory.cities ?? "—")} />
          <StatTile label="Statuses" value={String(overview?.inventory.statuses ?? "—")} />
        </div>
        <div className="compact-stack">
          <p className="eyebrow">Latest source metadata</p>
          <dl className="detail-grid">
            <DetailItem label="Updated" value={formatTimestamp(overview?.freshness.last_updated)} />
            <DetailItem label="Source" value={String(overview?.freshness.source ?? "—")} />
            <DetailItem label="Endpoint" value={String(overview?.freshness.endpoint ?? "—")} />
            <DetailItem
              label="Probe result"
              value={formatStatusLabel(overview?.freshness.probe_status)}
            />
            <DetailItem label="Validated" value={formatTimestamp(overview?.freshness.last_probe_at)} />
            <DetailItem
              label="Probe duration"
              value={
                overview?.freshness.last_probe_duration_ms != null
                  ? `${overview.freshness.last_probe_duration_ms} ms`
                  : "—"
              }
            />
          </dl>
        </div>
      </div>

      <div className="panel operations-vdb compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Vector knowledge base</p>
            <h4>Search and author regulations</h4>
          </div>
          <FileSearch size={18} />
        </div>
        <div className="metric-grid metric-grid--dense">
          <StatTile label="Status" value={formatStatusLabel(overview?.vector_db.status)} />
          <StatTile label="Health" value={formatStatusLabel(overview?.vector_db.health)} />
          <StatTile label="Regulations" value={String(overview?.vector_db.total_regulations ?? "—")} />
        </div>
        <form onSubmit={onVectorSearch} className="compact-stack">
          <input className="field" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
          <button className="btn btn--primary">Search vector DB</button>
        </form>
        <div className="list-stack scroll-panel scroll-panel--short">
          {searchResults.length ? (
            searchResults.map((item) => (
              <SourceCard
                key={item.id}
                title={item.title}
                meta={item.type}
                body={item.summary || item.content?.slice(0, 180)}
              />
            ))
          ) : (
            <StateSurface
              tone="info"
              title="Search results appear here"
              message="The first search keeps the area compact instead of leaving a large empty admin gap."
            />
          )}
        </div>
        <QuickRegulationForm
          onSuccess={async () => {
            await refreshOverview();
            trackUiEvent("operations_regulation_added", { route: "/data" });
          }}
          onError={(value) => setError(normalizeErrorMessage(value))}
        />
      </div>
    </section>
  );
}

function QuickRegulationForm(props: { onSuccess: () => void | Promise<void>; onError: (value: string) => void }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await addVectorDbRegulation({
        title,
        content,
        reg_type: "local",
        jurisdiction: "national",
      });
      setTitle("");
      setContent("");
      await props.onSuccess();
    } catch (err) {
      props.onError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <form onSubmit={onSubmit} className="compact-stack inset-form">
      <div className="panel-head panel-head--tight">
        <div>
          <p className="eyebrow">Add regulation</p>
          <h4>Author a quick local rule entry</h4>
        </div>
        <ArrowRight size={16} />
      </div>
      <input className="field" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
      <textarea
        className="field field--textarea"
        placeholder="Content"
        rows={4}
        value={content}
        onChange={(e) => setContent(e.target.value)}
      />
      <button className="btn btn--primary" disabled={!title.trim() || !content.trim()}>
        Add regulation
      </button>
    </form>
  );
}
