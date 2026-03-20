import { useEffect, useMemo, useState } from "react";
import { FileSearch, Map as MapIcon, ShieldAlert, Waypoints } from "lucide-react";
import { Link } from "react-router-dom";
import { MapContainer, Marker, Polygon, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";

import { searchData } from "../../lib/api";
import type { DataFeature, DataSearchResponse } from "../../types";
import {
  buildConstraintSignals,
  formatArea,
  getPlanCity,
  getPlanDistrict,
  getPlanLocation,
  getPlanNumber,
  getPlanStatus,
  getPlanTitle,
  getPlanUrl,
  normalizeErrorMessage,
} from "../model";
import { trackUiEvent } from "../tracking";
import {
  DetailItem,
  ErrorBanner,
  PlanListCard,
  StateSurface,
} from "../components";

const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

type InvestigationPageProps = {
  currentPlan: DataFeature | null;
  setCurrentPlan: (plan: DataFeature | null, source?: string) => void;
};

export function InvestigationPage(props: InvestigationPageProps) {
  const [filters, setFilters] = useState({ district: "", city: "", status: "", text: "" });
  const [response, setResponse] = useState<DataSearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (props.currentPlan && !filters.city) {
      setFilters((current) => ({ ...current, city: getPlanCity(props.currentPlan) }));
    }
  }, [filters.city, props.currentPlan]);

  useEffect(() => {
    setLoading(true);
    searchData(filters)
      .then((payload) => {
        setResponse(payload);
      })
      .catch((err) => {
        const message = normalizeErrorMessage(err.message);
        setError(message);
        trackUiEvent("investigation_error_state_seen", {
          route: "/map",
          status: "error",
          context: { message },
        });
      })
      .finally(() => setLoading(false));
  }, [filters]);

  const features = response?.items ?? [];
  const selectedPlan =
    features.find((item) => getPlanNumber(item) === getPlanNumber(props.currentPlan)) ||
    props.currentPlan ||
    null;
  const center = useMemo(() => {
    const centroid = selectedPlan?.geometry_wgs84?.centroid;
    return centroid
      ? ([centroid.lat, centroid.lon] as [number, number])
      : ([31.7683, 35.2137] as [number, number]);
  }, [selectedPlan]);

  return (
    <section className="page-grid page-grid--investigation">
      <div className="panel panel--wide investigation-header">
        <div className="compact-stack">
          <div className="panel-head panel-head--tight">
            <div>
              <p className="eyebrow">Investigation mode</p>
              <h3>Inspect the site, geometry, and evidence in one place.</h3>
            </div>
            <Waypoints size={18} />
          </div>
          <p className="lede">
            The map is the dominant surface here. Facts, source links, and next actions stay pinned
            to the selected site instead of competing with three equal columns.
          </p>
        </div>
        {selectedPlan ? (
          <div className="button-row">
            <Link className="btn btn--primary" to="/analyzer">
              Analyze this plan
            </Link>
            {getPlanUrl(selectedPlan) ? (
              <a className="btn btn--ghost" href={getPlanUrl(selectedPlan)} target="_blank" rel="noreferrer">
                Open source file
              </a>
            ) : null}
          </div>
        ) : (
          <StateSurface
            tone="warning"
            title="No selected site"
            message="Choose a plan from the queue below before treating the map as evidence for the current project."
          />
        )}
      </div>

      <div className="panel investigation-map">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Map context</p>
            <h4>Selected site on the planning canvas</h4>
          </div>
          <MapIcon size={18} />
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
              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
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
                        pathOptions={{
                          color: isSelected ? "#b75633" : "#3f786e",
                          weight: isSelected ? 3 : 2,
                          fillOpacity: isSelected ? 0.24 : 0.12,
                        }}
                        eventHandlers={{
                          click: () => props.setCurrentPlan(feature, "investigation_map"),
                        }}
                      >
                        <Popup>
                          <strong>{getPlanNumber(feature)}</strong>
                          <p>{getPlanTitle(feature)}</p>
                        </Popup>
                      </Polygon>
                    ))}
                    {geometry?.centroid ? (
                      <Marker
                        position={[geometry.centroid.lat, geometry.centroid.lon]}
                        icon={markerIcon}
                        eventHandlers={{
                          click: () => props.setCurrentPlan(feature, "investigation_map"),
                        }}
                      >
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

      <div className="panel investigation-details compact-stack">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Selected site</p>
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
              <DetailItem label="Approval state" value={getPlanStatus(selectedPlan)} />
              <DetailItem label="Area" value={formatArea(selectedPlan)} />
              <DetailItem label="Geometry" value={selectedPlan.has_geometry ? "Available" : "Missing"} />
            </dl>
            <div className="compact-stack">
              <p className="eyebrow">Constraint cues</p>
              <ul className="action-list">
                {buildConstraintSignals(selectedPlan).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <StateSurface
              tone={selectedPlan.has_geometry ? "info" : "warning"}
              title={selectedPlan.has_geometry ? "Geometry is present" : "Geometry is missing"}
              message={
                selectedPlan.has_geometry
                  ? "Use the map to inspect adjacency and parcel context before moving into feasibility."
                  : "Proceed carefully. This project needs manual parcel confirmation before map-heavy conclusions."
              }
            />
          </>
        ) : (
          <StateSurface
            tone="info"
            title="Choose a plan from the list below"
            message="The investigation rail stays concise until a selected site is driving the map and evidence cues."
          />
        )}
      </div>

      <div className="panel panel--wide investigation-results">
        <div className="panel-head panel-head--tight">
          <div>
            <p className="eyebrow">Matching plans</p>
            <h4>{response?.total ?? 0} local plans</h4>
          </div>
          <FileSearch size={18} />
        </div>
        <div className="results-grid">
          {features.map((feature) => (
            <PlanListCard
              key={getPlanNumber(feature)}
              feature={feature}
              active={getPlanNumber(feature) === getPlanNumber(selectedPlan)}
              onClick={() => props.setCurrentPlan(feature, "investigation_list")}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
