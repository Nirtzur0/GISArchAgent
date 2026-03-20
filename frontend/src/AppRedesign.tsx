import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  ClipboardList,
  Database,
  Layers3,
  Map as MapIcon,
  Radar,
} from "lucide-react";
import { Route, Routes, useLocation } from "react-router-dom";

import { getHealth } from "./lib/api";
import type { DataFeature, HealthProbe } from "./types";
import { NavCard, StateSurface, StatusChipRow } from "./redesign/components";
import {
  buildGlobalHealthMessage,
  buildSidebarGuidance,
  getPlanLocation,
  getPlanNumber,
  getPlanTitle,
  readStoredPlan,
  persistStoredPlan,
  ROUTE_META,
} from "./redesign/model";
import { trackUiEvent } from "./redesign/tracking";
import { WorkspacePage } from "./redesign/pages/WorkspacePage";
import { InvestigationPage } from "./redesign/pages/InvestigationPage";
import { FeasibilityPage } from "./redesign/pages/FeasibilityPage";
import { OperationsPage } from "./redesign/pages/OperationsPage";

function AppRedesign() {
  const location = useLocation();
  const routeMeta = ROUTE_META[location.pathname as keyof typeof ROUTE_META] ?? ROUTE_META["/"];
  const [health, setHealth] = useState<HealthProbe | null>(null);
  const [currentPlan, setCurrentPlan] = useState<DataFeature | null>(() => readStoredPlan());
  const [globalError, setGlobalError] = useState<string | null>(null);

  async function refreshShell() {
    try {
      const healthPayload = await getHealth();
      setHealth(healthPayload);
      setGlobalError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setGlobalError(message);
      trackUiEvent("shell_error_state_seen", {
        route: location.pathname,
        status: "error",
        planNumber: currentPlan ? getPlanNumber(currentPlan) : undefined,
        context: { message },
      });
    }
  }

  useEffect(() => {
    refreshShell();
  }, []);

  useEffect(() => {
    persistStoredPlan(currentPlan);
  }, [currentPlan]);

  useEffect(() => {
    trackUiEvent("route_viewed", {
      route: location.pathname,
      planNumber: currentPlan ? getPlanNumber(currentPlan) : undefined,
    });
  }, [currentPlan, location.pathname]);

  useEffect(() => {
    if (health && health.status !== "ok") {
      trackUiEvent("degraded_state_seen", {
        route: location.pathname,
        planNumber: currentPlan ? getPlanNumber(currentPlan) : undefined,
        status: "degraded",
        context: { status: health.status },
      });
    }
  }, [currentPlan, health, location.pathname]);

  function handlePlanSelect(plan: DataFeature | null, source = "route_surface") {
    setCurrentPlan(plan);
    if (plan) {
      trackUiEvent("workspace_plan_selected", {
        route: location.pathname,
        planNumber: getPlanNumber(plan),
        context: { source },
      });
    }
  }

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
          <NavCard
            to="/"
            icon={<ClipboardList size={18} />}
            title="Workspace"
            caption="Plan selection, decision signals, and grounded questions"
          />
          <NavCard
            to="/map"
            icon={<MapIcon size={18} />}
            title="Investigation"
            caption="Map context, site evidence, and source review"
          />
          <NavCard
            to="/analyzer"
            icon={<Radar size={18} />}
            title="Feasibility"
            caption="Scenario stress-testing and supporting regulations"
          />
          <NavCard
            to="/data"
            icon={<Database size={18} />}
            title="Operations"
            caption="Runtime health, data freshness, and vector maintenance"
          />
        </nav>

        <div className="sidebar-section compact-stack">
          <div className="sidebar-section__head">
            <p className="eyebrow">Current project</p>
            <span className="sidebar-tag">{routeMeta.label}</span>
          </div>
          {currentPlan ? (
            <div className="current-plan-card">
              <strong>{getPlanTitle(currentPlan)}</strong>
              <span>{getPlanNumber(currentPlan)}</span>
              <span>{getPlanLocation(currentPlan)}</span>
            </div>
          ) : (
            <StateSurface
              tone="info"
              title="No plan selected yet"
              message="Use the workspace search to select a plan and keep the rest of the product grounded to one project."
            />
          )}
        </div>

        <div className="sidebar-section compact-stack">
          <p className="eyebrow">Session health</p>
          <StatusChipRow health={health} />
          <p className="sidebar-note">
            {buildSidebarGuidance(routeMeta.label, currentPlan, health)}
          </p>
        </div>
      </aside>

      <main className="app-main">
        <header className="topbar">
          <div className="topbar__content">
            <p className="eyebrow">{routeMeta.label}</p>
            <h2>{routeMeta.title}</h2>
            <p className="lede">{routeMeta.description}</p>
            {currentPlan ? (
              <div className="current-plan-pill">
                <span className="current-plan-pill__label">Selected plan</span>
                <strong>{getPlanNumber(currentPlan)}</strong>
                <span>{getPlanLocation(currentPlan)}</span>
              </div>
            ) : null}
          </div>
          <div className="topbar-actions">
            <button className="btn btn--ghost" onClick={refreshShell}>
              Refresh status
            </button>
            <a className="topbar-link" href="/api/health" target="_blank" rel="noreferrer">
              API health
              <ArrowUpRight size={16} />
            </a>
          </div>
        </header>

        {globalError ? (
          <StateSurface
            tone="danger"
            title="Shell status could not refresh"
            message={globalError}
          />
        ) : null}

        {health && health.status !== "ok" ? (
          <StateSurface
            tone="warning"
            title="Some runtime dependencies need attention"
            message={buildGlobalHealthMessage(health)}
          />
        ) : null}

        <Routes>
          <Route
            path="/"
            element={
              <WorkspacePage
                currentPlan={currentPlan}
                health={health}
                setCurrentPlan={handlePlanSelect}
              />
            }
          />
          <Route
            path="/map"
            element={
              <InvestigationPage
                currentPlan={currentPlan}
                setCurrentPlan={handlePlanSelect}
              />
            }
          />
          <Route
            path="/analyzer"
            element={<FeasibilityPage currentPlan={currentPlan} health={health} />}
          />
          <Route
            path="/data"
            element={<OperationsPage health={health} onHealthRefresh={refreshShell} />}
          />
        </Routes>
      </main>
    </div>
  );
}

export default AppRedesign;
