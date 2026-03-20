import { useEffect, useMemo, useState } from "react";
import { AlertCircle, Clock3, Radar } from "lucide-react";

import { analyzeUpload, calculateRights } from "../../lib/api";
import type { BuildingRightsResult, DataFeature, HealthProbe, UploadAnalysis } from "../../types";
import {
  compareMetric,
  getPlanLocation,
  getPlanNumber,
  getPlanTitle,
  inferPlotSize,
  normalizeErrorMessage,
} from "../model";
import { trackUiEvent } from "../tracking";
import { ErrorBanner, RegulationCard, StateSurface, StatTile } from "../components";

type FeasibilityPageProps = {
  currentPlan: DataFeature | null;
  health: HealthProbe | null;
};

export function FeasibilityPage(props: FeasibilityPageProps) {
  const [location, setLocation] = useState(
    props.currentPlan ? getPlanLocation(props.currentPlan) : "Tel Aviv",
  );
  const [zone, setZone] = useState("R2");
  const [plotSize, setPlotSize] = useState(inferPlotSize(props.currentPlan));
  const [proposedFloors, setProposedFloors] = useState(4);
  const [proposedArea, setProposedArea] = useState(inferPlotSize(props.currentPlan) * 0.9);
  const [proposedParking, setProposedParking] = useState(8);
  const [includeRegs, setIncludeRegs] = useState(true);
  const [result, setResult] = useState<BuildingRightsResult | null>(null);
  const [analysis, setAnalysis] = useState<UploadAnalysis | null>(null);
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
      include_regulations: includeRegs,
    })
      .then((payload) => {
        setResult(payload);
        setError(null);
        trackUiEvent("feasibility_calculation_run", {
          route: "/analyzer",
          planNumber: props.currentPlan ? getPlanNumber(props.currentPlan) : undefined,
          context: { zone, plot_size_sqm: plotSize, include_regulations: includeRegs },
        });
      })
      .catch((err) => {
        const message = normalizeErrorMessage(err.message);
        setError(message);
        trackUiEvent("feasibility_error_state_seen", {
          route: "/analyzer",
          planNumber: props.currentPlan ? getPlanNumber(props.currentPlan) : undefined,
          status: "error",
          context: { message },
        });
      });
  }, [includeRegs, location, plotSize, props.currentPlan, zone]);

  async function onUpload(file: File | undefined) {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const payload = await analyzeUpload(file);
      setAnalysis(payload);
      trackUiEvent("feasibility_upload_analyzed", {
        route: "/analyzer",
        planNumber: props.currentPlan ? getPlanNumber(props.currentPlan) : undefined,
        context: { file_name: file.name, zones: payload.identified_zones.length },
      });
    } catch (err) {
      const message = normalizeErrorMessage(err instanceof Error ? err.message : String(err));
      setUploadError(message);
      trackUiEvent("feasibility_upload_error_seen", {
        route: "/analyzer",
        planNumber: props.currentPlan ? getPlanNumber(props.currentPlan) : undefined,
        status: "error",
        context: { message, file_name: file.name },
      });
    } finally {
      setUploading(false);
    }
  }

  const rights = result?.building_rights;
  const comparisons = useMemo(
    () =>
      rights
        ? [
            compareMetric("Floors", proposedFloors, rights.max_floors, "floors"),
            compareMetric("Built area", proposedArea, rights.max_building_area_sqm, "sqm"),
            compareMetric(
              "Parking",
              proposedParking,
              rights.parking_spaces_required,
              "spaces",
              true,
            ),
          ]
        : [],
    [proposedArea, proposedFloors, proposedParking, rights],
  );
  const hasRisk = comparisons.some((item) => item.status === "risk");

  return (
    <section className="page-grid page-grid--feasibility">
      <div className="panel panel--wide feasibility-hero">
        <div className="compact-stack">
          <div className="panel-head panel-head--tight">
            <div>
              <p className="eyebrow">Feasibility mode</p>
              <h3>Stress-test the scheme before client review.</h3>
            </div>
            <Radar size={18} />
          </div>
          <p className="lede">
            Pull the current project into a scenario, compare the proposal against a heuristic
            envelope, and keep supporting evidence visible instead of buried in a long secondary
            list.
          </p>
        </div>
        <StateSurface
          tone={rights ? (hasRisk ? "warning" : "info") : "info"}
          title={
            rights
              ? hasRisk
                ? "The current scenario needs review"
                : "The current scenario fits inside the heuristic envelope"
              : "Calculating rights and supporting evidence"
          }
          message={
            rights
              ? hasRisk
                ? "At least one proposal metric exceeds the current allowance or falls short of a minimum requirement."
                : "The current proposal stays inside the computed envelope, so the next step is evidence review."
              : "Rights, comparisons, and linked regulations will appear here as soon as the calculation returns."
          }
        />
      </div>

      <div className="panel feasibility-inputs compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Feasibility inputs</p>
            <h4>
              {props.currentPlan
                ? `Working on ${getPlanNumber(props.currentPlan)}`
                : "Set project assumptions"}
            </h4>
          </div>
          <Clock3 size={18} />
        </div>
        {props.currentPlan ? (
          <p className="muted">
            Project context: {getPlanTitle(props.currentPlan)} in {getPlanLocation(props.currentPlan)}.
          </p>
        ) : (
          <StateSurface
            tone="warning"
            title="No selected plan"
            message="Choose a plan from Workspace or Investigation so the scenario stays attached to a real dossier."
          />
        )}
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
          <input
            className="field"
            type="number"
            min={50}
            value={plotSize}
            onChange={(e) => setPlotSize(Number(e.target.value))}
          />
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
      </div>

      <div className="panel feasibility-upload compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Upload analysis</p>
            <h4>Review a drawing or plan package inside the current project context</h4>
          </div>
          <AlertCircle size={18} />
        </div>
        {!props.health?.provider?.vision?.healthy ? (
          <StateSurface
            tone="warning"
            title="Vision analysis is unavailable"
            message={
              props.health?.provider?.vision?.detail ||
              "The configured provider is not exposing a valid OpenAI-compatible vision endpoint."
            }
          />
        ) : null}
        <label className="upload-zone">
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tiff"
            onChange={(e) => onUpload(e.target.files?.[0])}
          />
          <span>{uploading ? "Analyzing file..." : "Upload drawing, PDF, or scan"}</span>
        </label>
        {uploadError ? <ErrorBanner message={uploadError} /> : null}
        {analysis ? (
          <div className="compact-stack">
            <div className="answer-block">
              <div className="answer-block__head">
                <p className="eyebrow">Description</p>
                <span className="status-chip status-chip--neutral">
                  {analysis.identified_zones.length} zones
                </span>
              </div>
              <p>{analysis.vision_analysis.description}</p>
            </div>
            <div className="tag-row">
              {analysis.identified_zones.map((zoneItem) => (
                <span key={zoneItem} className="history-chip">
                  {zoneItem}
                </span>
              ))}
            </div>
            <div className="compact-stack">
              {analysis.matching_regulations.map((regulation, index) => (
                <RegulationCard
                  key={regulation.id}
                  regulation={regulation}
                  meta={`${Math.round((analysis.similarity_scores[index] || 0) * 100)}% similarity`}
                />
              ))}
            </div>
          </div>
        ) : (
          <StateSurface
            tone="info"
            title="Upload evidence stays contextual"
            message="When a document is analyzed, the description and matched regulations appear here instead of interrupting the scenario workspace."
          />
        )}
      </div>

      <div className="panel panel--wide feasibility-review compact-stack">
        <div className="compact-stack">
          <p className="eyebrow">Proposal comparison</p>
          <div className="comparison-inputs">
            <label>
              <span>Proposed floors</span>
              <input className="field" type="number" min={0} value={proposedFloors} onChange={(e) => setProposedFloors(Number(e.target.value))} />
            </label>
            <label>
              <span>Proposed built area (sqm)</span>
              <input className="field" type="number" min={0} value={proposedArea} onChange={(e) => setProposedArea(Number(e.target.value))} />
            </label>
            <label>
              <span>Proposed parking</span>
              <input className="field" type="number" min={0} value={proposedParking} onChange={(e) => setProposedParking(Number(e.target.value))} />
            </label>
          </div>
          <div className="comparison-grid">
            {comparisons.map((item) => (
              <article key={item.label} className={`comparison-card comparison-card--${item.status}`}>
                <strong>{item.label}</strong>
                <span>
                  {item.proposedLabel} proposed / {item.allowedLabel} allowed
                </span>
                <p>{item.message}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="compact-stack">
          <p className="eyebrow">Applicable regulations</p>
          {(result?.applicable_regulations ?? []).slice(0, 5).map((regulation) => (
            <RegulationCard key={regulation.id} regulation={regulation} meta={regulation.type} />
          ))}
          {!result?.applicable_regulations?.length ? (
            <StateSurface
              tone="info"
              title="No linked regulations returned"
              message="This stays explicit instead of leaving a blank gap, so it is obvious when the scenario lacks supporting evidence."
            />
          ) : null}
        </div>
      </div>
    </section>
  );
}
