"""FastAPI application exposing GISArchAgent services."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.api.serializers import serialize_data_feature, to_jsonable
from src.application.dtos import (
    BuildingRightsQuery,
    PlanSearchQuery,
    PlanSearchResult,
    RegulationQuery,
)
from src.data_management import DataFetcherFactory, DataStore
from src.infrastructure.factory import ApplicationFactory
from src.config import settings
from src.telemetry import emit_observability_event, persist_ui_event
from src.vectorstore.management_service import VectorDBManagementService


logger = logging.getLogger(__name__)
LIVE_PLAN_SEARCH_TIMEOUT_SECONDS = 10


class RegulationQueryRequest(BaseModel):
    query_text: str
    location: Optional[str] = None
    regulation_type: Optional[str] = None
    max_results: int = Field(default=5, ge=1, le=25)


class BuildingRightsRequest(BaseModel):
    plot_size_sqm: float = Field(ge=1)
    zone_type: str
    location: str
    include_regulations: bool = True


class VectorDbSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=50)
    filters: Optional[dict[str, Any]] = None


class AddRegulationRequest(BaseModel):
    title: str
    content: str
    reg_type: str = "local"
    jurisdiction: str = "national"
    summary: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataFetchRequest(BaseModel):
    source: str = "iplan"
    service_name: str = "xplan"
    max_plans: int = Field(default=100, ge=1, le=5000)
    where: str = "1=1"
    timeout_seconds: int = Field(default=45, ge=5, le=180)


class UiEventRequest(BaseModel):
    event_name: str = Field(min_length=1, max_length=120)
    route: Optional[str] = Field(default=None, max_length=120)
    plan_number: Optional[str] = Field(default=None, max_length=120)
    status: str = Field(default="success", max_length=40)
    context: dict[str, Any] = Field(default_factory=dict)


class AppContext:
    """Shared application state for API handlers."""

    def __init__(self) -> None:
        vectorstore_dir = os.getenv(
            "GISARCHAGENT_VECTORSTORE_DIR", settings.chroma_persist_directory
        )
        cache_dir = os.getenv("GISARCHAGENT_CACHE_DIR", "data/cache")
        data_file = os.getenv("GISARCHAGENT_DATA_FILE", "data/raw/iplan_layers.json")

        self.factory = ApplicationFactory(
            openai_api_key=settings.openai_api_key,
            chroma_persist_dir=vectorstore_dir,
            cache_dir=cache_dir,
        )
        self.data_store = DataStore(data_file=data_file)
        self.vectordb = VectorDBManagementService(
            self.factory.get_regulation_repository()
        )
        self.fetcher_probe_ttl = timedelta(minutes=15)
        self.fetcher_probe_cache: dict[str, dict[str, Any]] = {}


ctx = AppContext()


def create_app() -> FastAPI:
    app = FastAPI(title="GISArchAgent API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        provider_status = ctx.factory.get_provider_status()
        fetcher_status = _fetcher_status_summary(source="iplan", service_name="xplan")
        overall_status = "ok"
        if (
            not provider_status["text"]["healthy"]
            or fetcher_status.get("status") != "ready"
        ):
            overall_status = "degraded"
        return {
            "status": overall_status,
            "provider": provider_status,
            "scraping": fetcher_status,
        }

    @app.get("/api/system/status")
    def system_status() -> dict[str, Any]:
        reg_repo = ctx.factory.get_regulation_repository()
        cache = ctx.factory.get_cache_service().get_stats()
        vectordb = ctx.factory.get_vectordb_status()
        return {
            "provider": to_jsonable(ctx.factory.get_provider_status()),
            "scraping": to_jsonable(
                _fetcher_status_summary(source="iplan", service_name="xplan")
            ),
            "vector_db": to_jsonable(vectordb),
            "cache": to_jsonable(cache),
            "regulation_repository": to_jsonable(reg_repo.get_statistics()),
            "data_store": to_jsonable(ctx.data_store.get_statistics()),
        }

    @app.get("/api/workspace/overview")
    def workspace_overview(plan_number: Optional[str] = None) -> dict[str, Any]:
        feature = _resolve_plan_feature(plan_number)
        return _build_workspace_overview(feature)

    @app.get("/api/operations/overview")
    def operations_overview() -> dict[str, Any]:
        return _build_operations_overview()

    @app.post("/api/ui/events")
    def ui_events(request: UiEventRequest) -> dict[str, Any]:
        payload = persist_ui_event(
            logger,
            event_name=request.event_name,
            route=request.route,
            plan_number=request.plan_number,
            status=request.status,
            context=request.context,
        )
        return {
            "ok": True,
            "event_id": payload["event_id"],
            "received_at": payload["timestamp"],
        }

    @app.post("/api/regulations/query")
    def query_regulations(request: RegulationQueryRequest) -> dict[str, Any]:
        result = ctx.factory.get_regulation_query_service().query(
            RegulationQuery(**request.model_dump())
        )
        return to_jsonable(result)

    @app.post("/api/building-rights/calculate")
    def calculate_building_rights(request: BuildingRightsRequest) -> dict[str, Any]:
        result = ctx.factory.get_building_rights_service().calculate_building_rights(
            BuildingRightsQuery(
                plot_size_sqm=request.plot_size_sqm,
                zone_type=request.zone_type,
                location=request.location,
            ),
            include_regulations=request.include_regulations,
        )
        return to_jsonable(result)

    @app.get("/api/plans/search")
    def search_live_plans(
        plan_id: Optional[str] = None,
        location: Optional[str] = None,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        include_vision_analysis: bool = False,
        max_results: int = Query(default=3, ge=1, le=10),
    ) -> dict[str, Any]:
        result = _execute_plan_search(
            PlanSearchQuery(
                plan_id=plan_id,
                location=location,
                keyword=keyword,
                status=status,
                include_vision_analysis=include_vision_analysis,
                max_results=max_results,
            ),
            timeout_seconds=LIVE_PLAN_SEARCH_TIMEOUT_SECONDS,
        )
        return to_jsonable(result)

    @app.post("/api/uploads/analyze")
    async def analyze_upload(file: UploadFile = File(...)) -> dict[str, Any]:
        upload_service = ctx.factory.get_plan_upload_service()
        if upload_service is None:
            raise HTTPException(
                status_code=503,
                detail="Vision service is unavailable. Check OpenAI-compatible provider configuration.",
            )
        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        result = upload_service.analyze_uploaded_plan(
            file_data=_BytesUpload(payload),
            filename=file.filename or "upload.bin",
            max_results=5,
        )
        if result is None:
            raise HTTPException(status_code=502, detail="Upload analysis failed")
        return to_jsonable(result)

    @app.get("/api/data/status")
    def data_status() -> dict[str, Any]:
        return to_jsonable(ctx.data_store.get_statistics())

    @app.get("/api/data/search")
    def data_search(
        district: Optional[str] = None,
        city: Optional[str] = None,
        status: Optional[str] = None,
        text: Optional[str] = None,
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> dict[str, Any]:
        features = ctx.data_store.search_features(
            district=district,
            city=city,
            status=status,
            text=text,
        )
        serialized = [serialize_data_feature(item) for item in features[:limit]]
        return {
            "total": len(features),
            "items": serialized,
            "filters": {
                "district": district,
                "city": city,
                "status": status,
                "text": text,
            },
        }

    @app.post("/api/data/import")
    async def data_import(file: UploadFile = File(...)) -> dict[str, Any]:
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="File is empty")
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

        if isinstance(parsed, dict) and "features" in parsed:
            features = parsed["features"]
        elif isinstance(parsed, list):
            features = parsed
        else:
            features = [parsed]
        added = ctx.data_store.add_features(features, avoid_duplicates=True)
        ctx.data_store.save(backup=True)
        return {"imported": len(features), "added": added}

    @app.post("/api/data/fetch")
    def data_fetch(request: DataFetchRequest) -> dict[str, Any]:
        result = _execute_fetch(
            source=request.source,
            service_name=request.service_name,
            max_plans=request.max_plans,
            where=request.where,
            timeout_seconds=request.timeout_seconds,
        )
        metadata = result.get("metadata") or {}
        features = result.get("features") or []
        added = 0
        if metadata.get("status") == "success" and features:
            added = ctx.data_store.add_features(features, avoid_duplicates=True)
            ctx.data_store.save(backup=True)
        return {
            "fetch": to_jsonable(metadata),
            "fetched_count": len(features),
            "added_count": added,
        }

    @app.get("/api/data/fetcher-health")
    def data_fetcher_health(
        source: str = "iplan",
        service_name: str = "xplan",
        probe_limit: int = Query(default=1, ge=1, le=5),
        timeout_seconds: int = Query(default=20, ge=5, le=60),
    ) -> dict[str, Any]:
        return _probe_fetcher(
            source=source,
            service_name=service_name,
            max_plans=probe_limit,
            timeout_seconds=timeout_seconds,
        )

    @app.get("/api/vectordb/status")
    def vectordb_status() -> dict[str, Any]:
        return to_jsonable(ctx.vectordb.get_status())

    @app.post("/api/vectordb/initialize")
    def vectordb_initialize() -> dict[str, Any]:
        ok = ctx.vectordb.initialize_if_needed()
        return {"ok": ok, "status": to_jsonable(ctx.vectordb.get_status())}

    @app.post("/api/vectordb/rebuild")
    def vectordb_rebuild() -> dict[str, Any]:
        ok = ctx.vectordb.rebuild_database()
        return {"ok": ok, "status": to_jsonable(ctx.vectordb.get_status())}

    @app.post("/api/vectordb/search")
    def vectordb_search(request: VectorDbSearchRequest) -> dict[str, Any]:
        items = ctx.vectordb.search_regulations(
            request.query,
            filters=request.filters,
            limit=request.limit,
        )
        return {"total": len(items), "items": to_jsonable(items)}

    @app.post("/api/vectordb/regulations")
    def vectordb_add_regulation(request: AddRegulationRequest) -> dict[str, Any]:
        from src.domain.entities.regulation import RegulationType

        try:
            reg_type = RegulationType(request.reg_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        ok = ctx.vectordb.add_regulation(
            title=request.title,
            content=request.content,
            reg_type=reg_type,
            jurisdiction=request.jurisdiction,
            summary=request.summary,
            metadata=request.metadata,
        )
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to add regulation")
        return {"ok": True}

    @app.post("/api/vectordb/import")
    async def vectordb_import(file: UploadFile = File(...)) -> dict[str, Any]:
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="File is empty")
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp.write(raw)
            temp_path = tmp.name
        result = ctx.vectordb.import_from_file(temp_path)
        return to_jsonable(result)

    @app.get("/api/vectordb/export")
    def vectordb_export() -> FileResponse:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            temp_path = tmp.name
        ok = ctx.vectordb.export_to_file(temp_path)
        if not ok:
            raise HTTPException(status_code=500, detail="Export failed")
        return FileResponse(
            temp_path,
            media_type="application/json",
            filename="regulations_export.json",
        )

    _mount_frontend(app)
    return app


def _mount_frontend(app: FastAPI) -> None:
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    assets_dir = frontend_dist / "assets"

    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    index_file = frontend_dist / "index.html"
    if not index_file.exists():
        return

    @app.get("/")
    @app.get("/map")
    @app.get("/analyzer")
    @app.get("/data")
    def frontend_shell() -> FileResponse:
        return FileResponse(index_file)

    @app.exception_handler(404)
    async def frontend_404(_, exc: HTTPException) -> JSONResponse | FileResponse:
        if str(exc.detail).startswith("Not Found"):
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"detail": exc.detail})


class _BytesUpload:
    """Binary upload wrapper matching the file-like contract used by the service."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._cursor = 0

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            self._cursor = offset
        elif whence == 1:
            self._cursor += offset
        elif whence == 2:
            self._cursor = len(self._data) + offset
        return self._cursor

    def tell(self) -> int:
        return self._cursor

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            size = len(self._data) - self._cursor
        chunk = self._data[self._cursor : self._cursor + size]
        self._cursor += len(chunk)
        return chunk


app = create_app()


def _fetcher_capabilities(source: str, *, service_name: str) -> dict[str, Any]:
    if source == "iplan":
        try:
            import pydoll  # noqa: F401

            available = True
        except ImportError:
            available = False
        return {
            "source": source,
            "service_name": service_name,
            "label": "iPlan GIS (Pydoll)",
            "available": available,
        }

    fetcher = DataFetcherFactory.get_fetcher(source)
    return {
        "source": source,
        "service_name": service_name,
        "label": fetcher.get_source_name(),
        "available": fetcher.is_available(),
    }


def _fetcher_cache_key(source: str, service_name: str) -> str:
    return f"{source}:{service_name}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_fetcher_payload(
    payload: dict[str, Any],
    *,
    source: str,
    service_name: str,
) -> dict[str, Any]:
    capabilities = _fetcher_capabilities(source, service_name=service_name)
    normalized = {
        **capabilities,
        "status": str(payload.get("status") or "unvalidated"),
        "runtime_ready": bool(payload.get("runtime_ready", False)),
        "detail": payload.get("detail"),
        "fetched_at": payload.get("fetched_at"),
        "count": int(payload.get("count") or 0),
        "probe_limit": int(payload.get("probe_limit") or 0),
        "timeout_seconds": int(payload.get("timeout_seconds") or 0),
        "metadata": dict(payload.get("metadata") or {}),
        "last_probe_at": payload.get("last_probe_at"),
        "last_probe_duration_ms": payload.get("last_probe_duration_ms"),
        "last_probe_count": int(payload.get("last_probe_count") or payload.get("count") or 0),
    }
    if normalized["status"] == "ready":
        normalized["runtime_ready"] = True
    if not normalized["available"]:
        normalized["status"] = "unavailable"
        normalized["runtime_ready"] = False
        normalized["detail"] = (
            normalized["detail"] or "Fetcher dependencies are not installed."
        )
    return normalized


def _get_cached_fetcher_probe(*, source: str, service_name: str) -> dict[str, Any] | None:
    cached = ctx.fetcher_probe_cache.get(_fetcher_cache_key(source, service_name))
    if not cached:
        return None
    last_probe_at = _parse_utc(cached.get("last_probe_at"))
    if last_probe_at is None:
        return None
    age = datetime.now(timezone.utc) - last_probe_at.astimezone(timezone.utc)
    if age > ctx.fetcher_probe_ttl:
        ctx.fetcher_probe_cache.pop(_fetcher_cache_key(source, service_name), None)
        return None
    return _normalize_fetcher_payload(cached, source=source, service_name=service_name)


def _cache_fetcher_probe(
    payload: dict[str, Any], *, source: str, service_name: str
) -> dict[str, Any]:
    normalized = _normalize_fetcher_payload(
        payload, source=source, service_name=service_name
    )
    ctx.fetcher_probe_cache[_fetcher_cache_key(source, service_name)] = dict(normalized)
    return normalized


def _execute_fetch(
    *,
    source: str,
    service_name: str,
    max_plans: int,
    where: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    fetcher = DataFetcherFactory.get_fetcher(source)
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        fetcher.fetch,
        service_name=service_name,
        max_plans=max_plans,
        where=where,
    )
    try:
        result = future.result(timeout=timeout_seconds)
    except FutureTimeoutError:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        if hasattr(fetcher, "close"):
            fetcher.close()
        return {
            "metadata": {
                "source": fetcher.get_source_name(),
                "service_name": service_name,
                "status": "timeout",
                "timeout_seconds": timeout_seconds,
                "fetched_at": None,
                "error": (
                    "Scrape timed out before the provider returned data. "
                    "Check browser automation, source availability, or increase timeout."
                ),
            },
            "features": [],
        }
    finally:
        if future.done():
            executor.shutdown(wait=False, cancel_futures=True)
        if hasattr(fetcher, "close"):
            fetcher.close()

    metadata = dict(result.get("metadata") or {})
    metadata.setdefault("source", fetcher.get_source_name())
    metadata.setdefault("service_name", service_name)
    metadata.setdefault("status", "success" if result.get("features") else "empty")
    result["metadata"] = metadata
    return result


def _execute_plan_search(
    query: PlanSearchQuery,
    *,
    timeout_seconds: int,
) -> PlanSearchResult:
    service = ctx.factory.get_plan_search_service()
    executor = ThreadPoolExecutor(max_workers=1)
    request_id = uuid4().hex
    future = executor.submit(service.search_plans, query)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError:
        future.cancel()
        emit_observability_event(
            logger,
            component="PlanSearchService",
            operation="plan_search",
            request_id=request_id,
            outcome="degraded",
            degraded_reasons=["live_search_timeout"],
            timeout_seconds=timeout_seconds,
            has_plan_id=bool(query.plan_id),
            has_location=bool(query.location),
            has_keyword=bool(query.keyword),
            include_vision_analysis=query.include_vision_analysis,
            max_results=query.max_results,
            latency_ms=timeout_seconds * 1000,
        )
        return PlanSearchResult(
            plans=[],
            query=query,
            total_found=0,
            execution_time_ms=timeout_seconds * 1000,
            warning=(
                "Live iPlan search timed out before the upstream service responded. "
                "Try again later or use the local catalog."
            ),
            warning_code="live_search_timeout",
        )
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _probe_fetcher(
    *,
    source: str,
    service_name: str,
    max_plans: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    if os.getenv("GISARCHAGENT_SKIP_FETCHER_PROBE") == "1":
        return _cache_fetcher_probe(
            {
                "status": "skipped",
                "runtime_ready": False,
                "detail": "Fetcher probe skipped by environment override.",
                "fetched_at": None,
                "count": 0,
                "probe_limit": max_plans,
                "timeout_seconds": timeout_seconds,
                "metadata": {},
                "last_probe_at": _utc_now_iso(),
                "last_probe_duration_ms": 0,
                "last_probe_count": 0,
            },
            source=source,
            service_name=service_name,
        )

    capabilities = _fetcher_capabilities(source, service_name=service_name)
    if not capabilities["available"]:
        return _cache_fetcher_probe(
            {
                "status": "unavailable",
                "runtime_ready": False,
                "detail": "Fetcher dependencies are not installed.",
                "fetched_at": None,
                "count": 0,
                "probe_limit": max_plans,
                "timeout_seconds": timeout_seconds,
                "metadata": {},
                "last_probe_at": _utc_now_iso(),
                "last_probe_duration_ms": 0,
                "last_probe_count": 0,
            },
            source=source,
            service_name=service_name,
        )

    result = _execute_fetch(
        source=source,
        service_name=service_name,
        max_plans=max_plans,
        where="1=1",
        timeout_seconds=timeout_seconds,
    )
    metadata = result.get("metadata") or {}
    raw_status = str(metadata.get("status") or "error")
    if raw_status == "success":
        status = "ready"
        runtime_ready = True
    elif raw_status == "timeout":
        status = "timeout"
        runtime_ready = False
    else:
        status = "error"
        runtime_ready = False
    detail = metadata.get("error")
    if status == "error" and not detail and not result.get("features"):
        detail = "Fetcher probe completed without returning any plan records."
    duration_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)
    return _cache_fetcher_probe(
        {
            "status": status,
            "runtime_ready": runtime_ready,
            "detail": detail,
            "fetched_at": metadata.get("fetched_at"),
            "count": len(result.get("features") or []),
            "probe_limit": max_plans,
            "timeout_seconds": timeout_seconds,
            "metadata": metadata,
            "last_probe_at": _utc_now_iso(),
            "last_probe_duration_ms": duration_ms,
            "last_probe_count": len(result.get("features") or []),
        },
        source=source,
        service_name=service_name,
    )


def _fetcher_status_summary(*, source: str, service_name: str) -> dict[str, Any]:
    cached = _get_cached_fetcher_probe(source=source, service_name=service_name)
    if cached:
        return cached
    capabilities = _fetcher_capabilities(source, service_name=service_name)
    return _normalize_fetcher_payload(
        {
            "status": "unvalidated" if capabilities["available"] else "unavailable",
            "runtime_ready": False,
            "detail": (
                "Run Validate scraper to perform a bounded live probe."
                if capabilities["available"]
                else "Fetcher dependencies are not installed."
            ),
            "fetched_at": None,
            "count": 0,
            "probe_limit": 0,
            "timeout_seconds": 0,
            "metadata": {},
            "last_probe_at": None,
            "last_probe_duration_ms": None,
            "last_probe_count": 0,
        },
        source=source,
        service_name=service_name,
    )


def _resolve_plan_feature(plan_number: str | None) -> dict[str, Any] | None:
    if not plan_number:
        return None
    return ctx.data_store.get_feature_by_plan_number(plan_number)


def _attr(feature: dict[str, Any] | None, key: str, default: str = "") -> str:
    if not feature:
        return default
    return str((feature.get("attributes") or {}).get(key) or default)


def _plan_location(feature: dict[str, Any] | None) -> str:
    city = _attr(feature, "plan_county_name", "Unknown city")
    district = _attr(feature, "district_name", "Unknown district")
    return f"{city}, {district}"


def _plan_area_label(feature: dict[str, Any] | None) -> str:
    try:
        dunam = float((feature or {}).get("attributes", {}).get("pl_area_dunam") or 0)
    except (TypeError, ValueError):
        dunam = 0
    if not dunam:
        return "Unknown"
    return f"{dunam:.2f} dunam"


def _plan_url(feature: dict[str, Any] | None) -> str | None:
    value = _attr(feature, "pl_url", "")
    return value or None


def _build_constraint_signals(feature: dict[str, Any]) -> list[str]:
    attributes = feature.get("attributes") or {}
    signals = [
        f"Approval state: {_attr(feature, 'station_desc', _attr(feature, 'internet_short_status', 'Unknown status'))}.",
        f"Municipality context: {_plan_location(feature)}.",
        "Geometry is available for map review."
        if feature.get("geometry")
        else "Geometry is missing, so parcel context needs manual verification.",
    ]
    objectives = attributes.get("pl_objectives")
    if objectives:
        text = str(objectives)
        signals.append(
            f"Plan objective: {text[:120]}{'...' if len(text) > 120 else ''}"
        )
    return signals


def _build_next_actions(feature: dict[str, Any], health: dict[str, Any]) -> list[str]:
    actions = [
        f"Verify municipality status: {_attr(feature, 'station_desc', _attr(feature, 'internet_short_status', 'Unknown status'))}.",
        f"Run feasibility assumptions for {_attr(feature, 'pl_number', 'selected plan')} before client review.",
        "Open the source plan package and confirm setbacks, parking, and approval notes.",
    ]
    provider_ok = bool(((health.get("provider") or {}).get("text") or {}).get("healthy"))
    provider_configured = bool((health.get("provider") or {}).get("configured"))
    if provider_configured and not provider_ok:
        actions.append(
            "Fix provider configuration before relying on synthesized summaries."
        )
    elif not provider_configured:
        actions.append(
            "Provider configuration is optional; retrieval-only answers remain available until synthesis is enabled."
        )
    if not feature.get("geometry"):
        actions.append(
            "Geometry is missing; confirm parcel boundaries before map-based review."
        )
    return actions


def _build_shareable_brief(
    feature: dict[str, Any] | None,
    *,
    vector_status: str,
    health: dict[str, Any],
) -> str | None:
    if not feature:
        return None
    provider_ok = bool(((health.get("provider") or {}).get("text") or {}).get("healthy"))
    provider_configured = bool((health.get("provider") or {}).get("configured"))
    scraping_status = str((health.get("scraping") or {}).get("status") or "unknown")
    if provider_ok:
        provider_label = "Ready"
    elif provider_configured:
        provider_label = "Blocked"
    else:
        provider_label = "Optional"
    scraper_label = scraping_status.replace("_", " ").title()
    return "\n".join(
        [
            f"Project dossier: {_attr(feature, 'pl_number', 'No plan number')} - {_attr(feature, 'pl_name', 'Untitled plan')}",
            f"Location: {_plan_location(feature)}",
            f"Approval state: {_attr(feature, 'station_desc', _attr(feature, 'internet_short_status', 'Unknown status'))}",
            f"Area: {_plan_area_label(feature)}",
            f"Geometry: {'available' if feature.get('geometry') else 'missing'}",
            f"Vector DB status: {vector_status.replace('_', ' ').title()}",
            f"Provider status: {provider_label}",
            f"Scraper status: {scraper_label}",
            "Next review step: validate feasibility assumptions and confirm source regulations before client output.",
        ]
    )


def _build_workspace_overview(feature: dict[str, Any] | None) -> dict[str, Any]:
    provider_status = ctx.factory.get_provider_status()
    fetcher_status = _fetcher_status_summary(source="iplan", service_name="xplan")
    vector_payload = to_jsonable(ctx.factory.get_vectordb_status())
    data_payload = to_jsonable(ctx.data_store.get_statistics())
    vector_status = str(
        (vector_payload or {}).get("health")
        or (vector_payload or {}).get("status")
        or "unknown"
    )
    selected_plan = serialize_data_feature(feature) if feature else None
    return {
        "selected_plan": selected_plan,
        "brief": {
            "plan_number": _attr(feature, "pl_number", "No plan number"),
            "title": _attr(feature, "pl_name", "No plan selected"),
            "location": _plan_location(feature) if feature else "—",
            "district": _attr(feature, "district_name", "—"),
            "city": _attr(feature, "plan_county_name", "—"),
            "status": _attr(
                feature,
                "station_desc",
                _attr(feature, "internet_short_status", "—"),
            ),
            "area": _plan_area_label(feature),
            "geometry": "Available" if feature and feature.get("geometry") else "Missing",
            "source_url": _plan_url(feature),
        }
        if feature
        else None,
        "summary_metrics": {
            "tracked_plans": int((data_payload or {}).get("total_plans") or 0),
            "vector_status": vector_status,
            "provider_status": "Ready"
            if ((provider_status.get("text") or {}).get("healthy"))
            else (
                "Optional"
                if not provider_status.get("configured")
                else "Attention"
            ),
            "scraper_status": str(fetcher_status.get("status") or "unknown"),
        },
        "constraint_signals": _build_constraint_signals(feature) if feature else [],
        "next_actions": _build_next_actions(
            feature, {"provider": provider_status, "scraping": fetcher_status}
        )
        if feature
        else [],
        "shareable_brief": _build_shareable_brief(
            feature,
            vector_status=vector_status,
            health={"provider": provider_status, "scraping": fetcher_status},
        ),
        "readiness": {
            "has_selected_plan": bool(feature),
            "provider_ready": bool((provider_status.get("text") or {}).get("healthy")),
            "scraper_ready": fetcher_status.get("status") == "ready",
            "vector_status": vector_status,
        },
    }


def _build_operations_overview() -> dict[str, Any]:
    data_status_payload = to_jsonable(ctx.data_store.get_statistics())
    vector_payload = to_jsonable(ctx.vectordb.get_status())
    fetcher_payload = _fetcher_status_summary(source="iplan", service_name="xplan")
    provider_status = ctx.factory.get_provider_status()
    health_payload = {
        "status": "ok"
        if (provider_status.get("text") or {}).get("healthy") and fetcher_payload.get("status") == "ready"
        else "degraded",
        "provider": provider_status,
        "scraping": fetcher_payload,
    }
    metadata = data_status_payload.get("metadata") or {}
    inventory = {
        "total_plans": int(data_status_payload.get("total_plans") or 0),
        "districts": len(data_status_payload.get("by_district") or {}),
        "cities": len(data_status_payload.get("by_city") or {}),
        "statuses": len(data_status_payload.get("by_status") or {}),
    }
    recommended_actions = []
    if not ((health_payload.get("provider") or {}).get("text") or {}).get("healthy"):
        recommended_actions.append(
            "Restore the OpenAI-compatible provider before trusting synthesis-heavy workflows."
        )
    if fetcher_payload.get("status") != "ready":
        recommended_actions.append(
            "Validate the scraper path before running a bounded data refresh."
        )
    if str(vector_payload.get("status") or "") not in {"healthy", "warning"}:
        recommended_actions.append(
            "Initialize or rebuild the vector knowledge base before relying on regulation search."
        )
    if not recommended_actions:
        recommended_actions.append(
            "Runtime looks healthy. Use bounded refresh or regulation authoring only when new source material arrives."
        )

    return {
        "provider": health_payload.get("provider"),
        "scraper": fetcher_payload,
        "data_store": data_status_payload,
        "vector_db": vector_payload,
        "inventory": inventory,
        "freshness": {
            "last_updated": metadata.get("last_updated") or metadata.get("fetched_at"),
            "update_note": metadata.get("update_note"),
            "source": metadata.get("source"),
            "endpoint": metadata.get("endpoint"),
            "fetched_at": metadata.get("fetched_at"),
            "probe_status": fetcher_payload.get("status"),
            "probe_detail": fetcher_payload.get("detail"),
            "last_probe_at": fetcher_payload.get("last_probe_at"),
            "last_probe_duration_ms": fetcher_payload.get("last_probe_duration_ms"),
        },
        "recommended_actions": recommended_actions,
    }
