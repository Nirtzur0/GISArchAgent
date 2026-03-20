import { FormEvent, useEffect, useMemo, useState } from "react";
import { Bot, Search, ShieldAlert, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { getWorkspaceOverview, queryRegulations, searchData, searchLivePlans } from "../../lib/api";
import type {
  DataFeature,
  DataSearchResponse,
  HealthProbe,
  LivePlanAnalysis,
  LivePlanSearchResponse,
  RegulationResult,
  WorkspaceOverview,
} from "../../types";
import {
  buildConstraintSignals,
  buildNextActions,
  buildShareableBrief,
  formatArea,
  formatStatusLabel,
  getPlanLocation,
  getPlanNumber,
  getPlanSource,
  normalizeErrorMessage,
  readStoredHistory,
  writeStoredHistory,
} from "../model";
import { trackUiEvent } from "../tracking";
import {
  DetailItem,
  ErrorBanner,
  PlanListCard,
  RegulationCard,
  StateSurface,
  StatTile,
} from "../components";

type WorkspacePageProps = {
  currentPlan: DataFeature | null;
  health: HealthProbe | null;
  setCurrentPlan: (plan: DataFeature | null, source?: string) => void;
};

type SearchSource = "local" | "live";
type LiveSearchMode = "location" | "keyword";

function toLivePlanFeature(item: LivePlanAnalysis): DataFeature {
  const city = item.plan.location || "Unknown city";
  return {
    attributes: {
      pl_number: item.plan.id,
      pl_name: item.plan.name,
      plan_county_name: city,
      district_name: item.plan.region || "Live iPlan",
      station_desc: item.plan.status,
      pl_url: item.plan.document_url || item.plan.image_url || "",
      plan_source: "live_iplan",
      zone_type: item.plan.zone_type,
    },
    geometry_wgs84: null,
    has_geometry: false,
  };
}

export function WorkspacePage(props: WorkspacePageProps) {
  const [searchSource, setSearchSource] = useState<SearchSource>("local");
  const [filters, setFilters] = useState({ district: "", city: "", status: "", text: "" });
  const [liveSearchMode, setLiveSearchMode] = useState<LiveSearchMode>("location");
  const [liveFilters, setLiveFilters] = useState({
    query: "",
    status: "",
    includeVisionAnalysis: false,
  });
  const [response, setResponse] = useState<DataSearchResponse | null>(null);
  const [liveResponse, setLiveResponse] = useState<LivePlanSearchResponse | null>(null);
  const [overview, setOverview] = useState<WorkspaceOverview | null>(null);
  const [queryText, setQueryText] = useState(
    "Summarize the key zoning constraints and approval risks for this plan.",
  );
  const [result, setResult] = useState<RegulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(true);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<string[]>(() => readStoredHistory());
  const [copyState, setCopyState] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    setSearchLoading(true);
    searchData(filters)
      .then((payload) => {
        setResponse(payload);
      })
      .catch((err) => {
        const message = normalizeErrorMessage(err.message);
        setError(message);
        trackUiEvent("workspace_error_state_seen", {
          route: "/",
          status: "error",
          context: { message },
        });
      })
      .finally(() => setSearchLoading(false));
  }, [filters]);

  useEffect(() => {
    if (searchSource !== "live") {
      return;
    }
    setError(null);
    setSearchLoading(true);
    searchLivePlans({
      location: liveSearchMode === "location" ? liveFilters.query : undefined,
      keyword: liveSearchMode === "keyword" ? liveFilters.query : undefined,
      status: liveFilters.status || undefined,
      includeVisionAnalysis: liveFilters.includeVisionAnalysis,
      maxResults: 8,
    })
      .then((payload) => {
        setLiveResponse(payload);
      })
      .catch((err) => {
        const message = normalizeErrorMessage(err.message);
        setError(message);
        trackUiEvent("workspace_live_search_error_seen", {
          route: "/",
          status: "error",
          context: { message, mode: liveSearchMode },
        });
      })
      .finally(() => setSearchLoading(false));
  }, [liveFilters, liveSearchMode, searchSource]);

  useEffect(() => {
    setOverviewLoading(true);
    getWorkspaceOverview(props.currentPlan ? getPlanNumber(props.currentPlan) : undefined)
      .then((payload) => {
        setOverview(payload);
      })
      .catch((err) => {
        const message = normalizeErrorMessage(err.message);
        setError(message);
        trackUiEvent("workspace_overview_error_seen", {
          route: "/",
          status: "error",
          planNumber: props.currentPlan ? getPlanNumber(props.currentPlan) : undefined,
          context: { message },
        });
      })
      .finally(() => setOverviewLoading(false));
  }, [props.currentPlan]);

  useEffect(() => {
    writeStoredHistory(history);
  }, [history]);

  const localQueueItems = useMemo(() => (response?.items ?? []).slice(0, 8), [response?.items]);
  const liveQueueItems = useMemo(
    () => (liveResponse?.plans ?? []).map((item) => toLivePlanFeature(item)),
    [liveResponse?.plans]
  );

  const selectedPlan = useMemo(() => {
    if (!props.currentPlan) return null;
    const currentNumber = getPlanNumber(props.currentPlan);
    return (
      localQueueItems.find((item) => getPlanNumber(item) === currentNumber) ||
      liveQueueItems.find((item) => getPlanNumber(item) === currentNumber) ||
      overview?.selected_plan ||
      props.currentPlan
    );
  }, [liveQueueItems, localQueueItems, overview?.selected_plan, props.currentPlan]);
  const queueItems = searchSource === "live" ? liveQueueItems : localQueueItems;
  const workspaceBrief = overview?.brief
    ? overview.brief
    : selectedPlan
      ? {
          plan_number: getPlanNumber(selectedPlan),
          title: selectedPlan.attributes.pl_name ? String(selectedPlan.attributes.pl_name) : "Selected plan",
          location: getPlanLocation(selectedPlan),
          district: selectedPlan.attributes.district_name
            ? String(selectedPlan.attributes.district_name)
            : "Unknown district",
          city: selectedPlan.attributes.plan_county_name
            ? String(selectedPlan.attributes.plan_county_name)
            : "Unknown city",
          status: selectedPlan.attributes.station_desc
            ? String(selectedPlan.attributes.station_desc)
            : "Unknown status",
          area: formatArea(selectedPlan),
          geometry: selectedPlan.has_geometry ? "Available" : "Missing",
          source_url: selectedPlan.attributes.pl_url
            ? String(selectedPlan.attributes.pl_url)
            : null,
        }
      : null;
  const constraintSignals =
    overview?.brief && overview.constraint_signals.length
      ? overview.constraint_signals
      : selectedPlan
        ? buildConstraintSignals(selectedPlan)
        : [];
  const nextActions =
    overview?.brief && overview.next_actions.length
      ? overview.next_actions
      : selectedPlan
        ? buildNextActions(selectedPlan, props.health)
        : [];
  const shareableBrief =
    overview?.shareable_brief || (selectedPlan ? buildShareableBrief(selectedPlan, props.health) : null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedPlan) return;
    setLoading(true);
    setError(null);
    try {
      trackUiEvent("workspace_grounded_query_submitted", {
        route: "/",
        planNumber: getPlanNumber(selectedPlan),
        context: { query_length: queryText.length },
      });
      const responsePayload = await queryRegulations(queryText, {
        location: getPlanLocation(selectedPlan),
        maxResults: 6,
      });
      setResult(responsePayload);
      setHistory((current) => [queryText, ...current.filter((item) => item !== queryText)].slice(0, 10));
    } catch (err) {
      const message = normalizeErrorMessage(err instanceof Error ? err.message : String(err));
      setError(message);
      trackUiEvent("workspace_grounded_query_error_seen", {
        route: "/",
        planNumber: selectedPlan ? getPlanNumber(selectedPlan) : undefined,
        status: "error",
        context: { message },
      });
    } finally {
      setLoading(false);
    }
  }

  async function onCopySummary() {
    try {
      await navigator.clipboard.writeText(shareableBrief || "");
      setCopyState("Copied summary");
    } catch {
      setCopyState("Clipboard unavailable");
    }
  }

  const answerSummary =
    result?.answer?.split(/(?<=[.!?])\s+/).slice(0, 2).join(" ") || result?.answer || null;
  const heroMetricsLoading = overviewLoading && !overview;
  const heroNextMoveMessage = heroMetricsLoading
    ? "Refreshing project metrics and next-step guidance for the selected plan."
    : selectedPlan
      ? overview?.next_actions?.[0] ||
        "Move into investigation or feasibility from the selected project."
      : "Use the queue below to pick a plan before writing questions or reviewing constraints.";

  return (
    <section className="page-grid page-grid--workspace">
      <div className="panel panel--wide workspace-hero">
        <div className="workspace-hero__copy compact-stack">
          <div className="panel-head panel-head--tight">
            <div>
              <p className="eyebrow">Planner workspace</p>
              <h3>Move from plan selection to a confident planning brief.</h3>
            </div>
            <Sparkles size={18} />
          </div>
          <p className="lede">
            Keep the selected project visible, isolate the blockers that matter now, and move into
            investigation or feasibility without opening three competing surfaces at once.
          </p>
          {selectedPlan ? (
            <div className="project-spotlight">
              <div className="project-spotlight__identity">
                <span className="eyebrow">Selected project</span>
                <strong>{workspaceBrief?.title || "Selected plan"}</strong>
                <span>
                  {workspaceBrief?.plan_number || getPlanNumber(selectedPlan)} ·{" "}
                  {workspaceBrief?.location || getPlanLocation(selectedPlan)}
                </span>
              </div>
              <div className="button-row">
                <Link className="btn btn--primary" to="/map">
                  Open investigation
                </Link>
                <Link className="btn btn--ghost" to="/analyzer">
                  Run feasibility
                </Link>
                {workspaceBrief?.source_url ? (
                  <a
                    className="btn btn--ghost"
                    href={workspaceBrief.source_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Source plan
                  </a>
                ) : null}
              </div>
            </div>
          ) : (
            <StateSurface
              tone="info"
              title="Start by selecting a plan"
              message="The rest of the workspace stays intentionally secondary until a real project is in focus."
            />
          )}
        </div>
        <div className="workspace-hero__signals compact-stack">
          <div className="hero-metrics">
            <StatTile
              label="Tracked plans"
              value={heroMetricsLoading ? "Loading" : String(overview?.summary_metrics.tracked_plans ?? "—")}
            />
            <StatTile
              label="Vector DB"
              value={heroMetricsLoading ? "Loading" : formatStatusLabel(overview?.summary_metrics.vector_status)}
            />
            <StatTile
              label="Provider"
              value={heroMetricsLoading ? "Loading" : formatStatusLabel(overview?.summary_metrics.provider_status)}
            />
            <StatTile
              label="Scraper"
              value={heroMetricsLoading ? "Loading" : formatStatusLabel(overview?.summary_metrics.scraper_status)}
            />
          </div>
          <StateSurface
            tone={selectedPlan ? "info" : "warning"}
            title={heroMetricsLoading ? "Refreshing project view" : selectedPlan ? "Primary next move" : "Current focus"}
            message={heroNextMoveMessage}
          />
        </div>
      </div>

      <div className="panel workspace-search">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Planner queue</p>
            <h4>Find the project under review</h4>
          </div>
          <Search size={18} />
        </div>
        <div className="button-row">
          <button
            className={`btn ${searchSource === "local" ? "btn--primary" : "btn--ghost"}`}
            type="button"
            onClick={() => setSearchSource("local")}
          >
            Local catalog
          </button>
          <button
            className={`btn ${searchSource === "live" ? "btn--primary" : "btn--ghost"}`}
            type="button"
            onClick={() => setSearchSource("live")}
          >
            Live iPlan
          </button>
        </div>
        {searchSource === "local" ? (
          <div className="filters-grid">
            <input className="field" placeholder="District" value={filters.district} onChange={(e) => setFilters({ ...filters, district: e.target.value })} />
            <input className="field" placeholder="City / municipality" value={filters.city} onChange={(e) => setFilters({ ...filters, city: e.target.value })} />
            <input className="field" placeholder="Status" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} />
            <input className="field" placeholder="Plan number / text" value={filters.text} onChange={(e) => setFilters({ ...filters, text: e.target.value })} />
          </div>
        ) : (
          <div className="compact-stack">
            <div className="filters-grid">
              <select
                className="field"
                value={liveSearchMode}
                onChange={(e) => setLiveSearchMode(e.target.value as LiveSearchMode)}
              >
                <option value="location">Search by location</option>
                <option value="keyword">Search by keyword</option>
              </select>
              <input
                className="field"
                placeholder={liveSearchMode === "location" ? "City / municipality" : "Keyword"}
                value={liveFilters.query}
                onChange={(e) => setLiveFilters({ ...liveFilters, query: e.target.value })}
              />
              <input
                className="field"
                placeholder="Status"
                value={liveFilters.status}
                onChange={(e) => setLiveFilters({ ...liveFilters, status: e.target.value })}
              />
            </div>
            <label className="toggle">
              <input
                type="checkbox"
                checked={liveFilters.includeVisionAnalysis}
                onChange={(e) =>
                  setLiveFilters({
                    ...liveFilters,
                    includeVisionAnalysis: e.target.checked,
                  })
                }
              />
              Request vision analysis only when the provider is healthy
            </label>
            <StateSurface
              tone="info"
              title="Live search is explicit and bounded"
              message="Local catalog remains the stable default. Use live iPlan when the current project is missing locally or needs upstream confirmation."
            />
            {liveResponse?.warning ? (
              <StateSurface
                tone="warning"
                title="Live iPlan search is degraded"
                message={liveResponse.warning}
              />
            ) : null}
          </div>
        )}
        {error ? <ErrorBanner message={error} /> : null}
        <div className="list-stack scroll-panel">
          {searchLoading ? (
            <div className="empty-state">
              {searchSource === "live" ? "Searching live iPlan..." : "Loading local plan inventory..."}
            </div>
          ) : null}
          {!searchLoading &&
            queueItems.map((feature) => (
              <PlanListCard
                key={getPlanNumber(feature)}
                feature={feature}
                active={getPlanNumber(feature) === getPlanNumber(selectedPlan)}
                onClick={() =>
                  props.setCurrentPlan(
                    feature,
                    searchSource === "live" ? "workspace_live_search" : "workspace_queue"
                  )
                }
              />
            ))}
          {!searchLoading && !queueItems.length ? (
            <div className="empty-state">
              {searchSource === "live"
                ? "No live plans matched the current search, or the upstream search is currently degraded."
                : "No plans matched the current filters."}
            </div>
          ) : null}
        </div>
      </div>

      <div className="panel workspace-summary compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Project brief</p>
            <h4>{workspaceBrief?.title || "No plan selected"}</h4>
          </div>
          <ShieldAlert size={18} />
        </div>
        {overviewLoading ? (
          <div className="empty-state">Loading project brief...</div>
        ) : workspaceBrief ? (
          <>
            <dl className="detail-grid">
              <DetailItem label="Plan number" value={workspaceBrief.plan_number} />
              <DetailItem label="Municipality" value={workspaceBrief.city} />
              <DetailItem label="District" value={workspaceBrief.district} />
              <DetailItem label="Status" value={workspaceBrief.status} />
              <DetailItem label="Area" value={workspaceBrief.area} />
              <DetailItem label="Geometry" value={workspaceBrief.geometry} />
            </dl>
            <div className="compact-stack">
              <p className="eyebrow">Why this project needs attention</p>
              <ul className="action-list">
                {constraintSignals.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="compact-stack">
              <p className="eyebrow">Recommended next actions</p>
              <ul className="action-list">
                {nextActions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="compact-stack">
              <div className="button-row button-row--between">
                <p className="eyebrow">Shareable brief</p>
                <button className="btn btn--ghost" onClick={onCopySummary}>
                  Copy summary
                </button>
              </div>
              <pre className="summary-block">{shareableBrief}</pre>
              {copyState ? <p className="muted">{copyState}</p> : null}
            </div>
            {selectedPlan && getPlanSource(selectedPlan) === "live_iplan" ? (
              <StateSurface
                tone="warning"
                title="Selected from live iPlan"
                message="This plan is not guaranteed to exist in the local catalog yet. Investigation and feasibility stay available, but geometry and local dossier fields may be incomplete until the plan is imported."
              />
            ) : null}
          </>
        ) : (
          <StateSurface
            tone="info"
            title="No brief yet"
            message="Select a plan to reveal facts, constraints, and next actions. Until then, the workspace stays intentionally quiet."
          />
        )}
      </div>

      <div className="panel panel--wide workspace-query">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Grounded assistant</p>
            <h4>Ask about the selected plan, not the corpus in the abstract</h4>
          </div>
          <Bot size={18} />
        </div>
        <div className="workspace-query__grid">
          <div className="compact-stack">
            {selectedPlan ? (
              <StateSurface
                tone="info"
                title="Question is grounded to the current project"
                message={`${getPlanNumber(selectedPlan)} in ${getPlanLocation(selectedPlan)} stays attached to the answer, evidence, and next steps.`}
              />
            ) : (
              <StateSurface
                tone="warning"
                title="Questioning is disabled until a plan is selected"
                message="This keeps the assistant from pretending a generic answer is useful when the work depends on a real site."
              />
            )}
            <form onSubmit={onSubmit} className="compact-stack">
              <textarea
                value={queryText}
                onChange={(event) => setQueryText(event.target.value)}
                rows={5}
                className="field field--textarea"
              />
              <div className="button-row">
                <button className="btn btn--primary" disabled={loading || !queryText.trim() || !selectedPlan}>
                  {loading ? "Querying..." : "Ask about this project"}
                </button>
                <button type="button" className="btn btn--ghost" onClick={() => setQueryText("")}>
                  Clear
                </button>
              </div>
            </form>
            {history.length ? (
              <div className="history-block">
                <p className="eyebrow">Recent prompts</p>
                <div className="tag-row">
                  {history.map((item) => (
                    <button key={item} className="history-chip" onClick={() => setQueryText(item)}>
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <div className="compact-stack">
            {error ? <ErrorBanner message={error} /> : null}
            {result?.answer_warning ? (
              <StateSurface
                tone="warning"
                title="Synthesis is degraded"
                message={result.answer_warning}
              />
            ) : null}
            {answerSummary ? (
              <div className="answer-block">
                <div className="answer-block__head">
                  <p className="eyebrow">Working answer</p>
                  <span className="status-chip status-chip--neutral">
                    {result?.answer_status ?? "grounded"}
                  </span>
                </div>
                <p>{answerSummary}</p>
              </div>
            ) : (
              <StateSurface
                tone="info"
                title="Answer surface stays compact until you ask"
                message="The evidence panel on the right only expands once a grounded query has been run for the selected project."
              />
            )}

            <div className="compact-stack">
              <div className="button-row button-row--between">
                <p className="eyebrow">Relevant source regulations</p>
                <span className="muted">{result?.total_found ?? 0} matched</span>
              </div>
              {result?.regulations?.length ? (
                result.regulations.map((regulation) => (
                  <RegulationCard key={regulation.id} regulation={regulation} />
                ))
              ) : (
                <StateSurface
                  tone="info"
                  title="No source evidence yet"
                  message="Run a query to populate supporting regulations instead of showing an empty raw list by default."
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
