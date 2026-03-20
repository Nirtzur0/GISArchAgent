import type { ReactNode } from "react";
import { AlertCircle } from "lucide-react";
import { NavLink } from "react-router-dom";

import type { DataFeature, HealthProbe, Regulation } from "../types";
import type { SurfaceTone } from "./model";
import {
  formatStatusLabel,
  getPlanLocation,
  getPlanNumber,
  getPlanSourceLabel,
  getPlanStatus,
  getPlanTitle,
} from "./model";

export function NavCard(props: {
  to: string;
  icon: ReactNode;
  title: string;
  caption: string;
}) {
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

export function StatTile(props: { label: string; value: string }) {
  return (
    <div className="stat-tile">
      <span>{props.label}</span>
      <strong>{props.value}</strong>
    </div>
  );
}

export function StateSurface(props: { tone: SurfaceTone; title: string; message: string }) {
  return (
    <div className={`state-surface state-surface--${props.tone}`}>
      <strong>{props.title}</strong>
      <p>{props.message}</p>
    </div>
  );
}

export function StatusChipRow(props: { health: HealthProbe | null }) {
  const scraperStatus = props.health?.scraping?.status ?? "unknown";
  const providerConfigured = props.health?.provider?.configured ?? false;
  const providerReady = props.health?.provider?.text?.healthy ?? false;
  const scraperTone =
    scraperStatus === "ready"
      ? "status-chip--ok"
      : scraperStatus === "unvalidated"
        ? "status-chip--neutral"
        : "status-chip--warn";
  const providerTone = providerReady
    ? "status-chip--ok"
    : providerConfigured
      ? "status-chip--warn"
      : "status-chip--neutral";
  const providerLabel = providerReady
    ? "ready"
    : providerConfigured
      ? "blocked"
      : "optional";
  return (
    <div className="status-chip-row">
      <span className={`status-chip ${providerTone}`}>
        Provider {formatStatusLabel(providerLabel)}
      </span>
      <span className={`status-chip ${scraperTone}`}>
        Scraper {formatStatusLabel(scraperStatus)}
      </span>
    </div>
  );
}

export function DetailItem(props: { label: string; value: string }) {
  return (
    <div className="detail-item">
      <dt>{props.label}</dt>
      <dd>{props.value}</dd>
    </div>
  );
}

export function ErrorBanner(props: { message: string }) {
  return (
    <div className="error-banner">
      <AlertCircle size={16} />
      <span>{props.message}</span>
    </div>
  );
}

export function PlanListCard(props: {
  feature: DataFeature;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={`list-card list-card--button${props.active ? " active" : ""}`}
      onClick={props.onClick}
    >
      <div className="list-card__head">
        <strong>{getPlanNumber(props.feature)}</strong>
        <span className="status-chip status-chip--neutral">{getPlanStatus(props.feature)}</span>
      </div>
      <p>{getPlanTitle(props.feature)}</p>
      <span>{getPlanLocation(props.feature)}</span>
      <span className="muted">{getPlanSourceLabel(props.feature)}</span>
    </button>
  );
}

export function SourceCard(props: {
  title: string;
  meta: string;
  body: string;
  footer?: ReactNode;
}) {
  return (
    <article className="source-card">
      <div className="source-card__meta">
        <strong>{props.title}</strong>
        <span>{props.meta}</span>
      </div>
      <p>{props.body}</p>
      {props.footer}
    </article>
  );
}

export function RegulationCard(props: { regulation: Regulation; meta?: string }) {
  return (
    <SourceCard
      title={props.regulation.title}
      meta={props.meta || `${props.regulation.type} · ${props.regulation.jurisdiction}`}
      body={props.regulation.summary || props.regulation.content.slice(0, 220)}
    />
  );
}
