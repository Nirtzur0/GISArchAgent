"""FastAPI application exposing GISArchAgent services."""

from __future__ import annotations

import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.api.serializers import serialize_data_feature, to_jsonable
from src.application.dtos import BuildingRightsQuery, PlanSearchQuery, RegulationQuery
from src.data_management import DataFetcherFactory, DataStore
from src.infrastructure.factory import ApplicationFactory
from src.config import settings
from src.vectorstore.management_service import VectorDBManagementService


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


class AppContext:
    """Shared application state for API handlers."""

    def __init__(self) -> None:
        vectorstore_dir = os.getenv(
            "GISARCHAGENT_VECTORSTORE_DIR", settings.chroma_persist_directory
        )
        cache_dir = os.getenv("GISARCHAGENT_CACHE_DIR", "data/cache")
        data_file = os.getenv("GISARCHAGENT_DATA_FILE", "data/raw/iplan_layers.json")

        self.factory = ApplicationFactory(
            gemini_api_key=settings.openai_api_key,
            chroma_persist_dir=vectorstore_dir,
            cache_dir=cache_dir,
        )
        self.data_store = DataStore(data_file=data_file)
        self.vectordb = VectorDBManagementService(
            self.factory.get_regulation_repository()
        )


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
        fetcher_status = _fetcher_capabilities("iplan", service_name="xplan")
        fetcher_status["status"] = "ready" if fetcher_status["available"] else "unavailable"
        overall_status = "ok"
        if not provider_status["text"]["healthy"] or not fetcher_status["available"]:
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
            "scraping": to_jsonable(_fetcher_capabilities("iplan", service_name="xplan")),
            "vector_db": to_jsonable(vectordb),
            "cache": to_jsonable(cache),
            "regulation_repository": to_jsonable(reg_repo.get_statistics()),
            "data_store": to_jsonable(ctx.data_store.get_statistics()),
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
        result = ctx.factory.get_plan_search_service().search_plans(
            PlanSearchQuery(
                plan_id=plan_id,
                location=location,
                keyword=keyword,
                status=status,
                include_vision_analysis=include_vision_analysis,
                max_results=max_results,
            )
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


def _probe_fetcher(
    *,
    source: str,
    service_name: str,
    max_plans: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    if os.getenv("GISARCHAGENT_SKIP_FETCHER_PROBE") == "1":
        capabilities = _fetcher_capabilities(source, service_name=service_name)
        return {
            **capabilities,
            "status": "skipped",
            "detail": "Fetcher probe skipped by environment override.",
            "fetched_at": None,
            "count": 0,
            "probe_limit": max_plans,
            "timeout_seconds": timeout_seconds,
            "metadata": {},
        }

    capabilities = _fetcher_capabilities(source, service_name=service_name)
    if not capabilities["available"]:
        return {
            **capabilities,
            "status": "unavailable",
            "detail": "Fetcher dependencies are not installed.",
        }

    result = _execute_fetch(
        source=source,
        service_name=service_name,
        max_plans=max_plans,
        where="1=1",
        timeout_seconds=timeout_seconds,
    )
    metadata = result.get("metadata") or {}
    status = metadata.get("status", "unknown")
    return {
        **capabilities,
        "status": "ready" if status == "success" else status,
        "detail": metadata.get("error"),
        "fetched_at": metadata.get("fetched_at"),
        "count": len(result.get("features") or []),
        "probe_limit": max_plans,
        "timeout_seconds": timeout_seconds,
        "metadata": metadata,
    }
