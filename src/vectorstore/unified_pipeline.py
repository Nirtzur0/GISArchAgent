"""
Unified data pipeline for building the vector database.

This orchestrates the complete process:
1. Discover all plans from iPlan (using Pydoll via data_pipeline)
2. Fetch plan documents from Mavat
3. Process documents with vision service
4. Extract regulations and building rights
5. Index everything in vector database

Integrates with existing infrastructure:
- Uses src.data_pipeline for data discovery
- Uses src.infrastructure.services for document/vision processing
- Uses src.vectorstore for indexing
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime
from time import perf_counter
import json
from uuid import uuid4
import os
import re
import resource
import subprocess
import sys

import asyncio
from src.data_management.pydoll_fetcher import IPlanPydollSource
from src.infrastructure.services.document_service import (
    MavatDocumentFetcher,
    DocumentProcessor,
)
from src.infrastructure.services.vision_service import OpenAICompatibleVisionService
from src.domain.entities.regulation import Regulation
from src.domain.entities.regulation import RegulationType
from src.vectorstore.management_service import VectorDBManagementService
from src.telemetry import (
    append_jsonl_record,
    emit_observability_event,
    utc_timestamp,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline."""

    # Data source
    service_name: str = "xplan"  # xplan, xplan_full, tama35, tama
    max_plans: Optional[int] = None  # None = fetch all
    where_clause: str = "1=1"  # SQL filter

    # Document fetching
    fetch_documents: bool = True
    max_documents_per_plan: int = 10

    # Vision processing
    process_documents: bool = True
    vision_model: str = "gpt-4o-mini"

    # Vector DB
    rebuild_vectordb: bool = False  # True = clear and rebuild
    batch_size: int = 100

    # Caching
    use_cache: bool = True
    cache_dir: Path = Path("data/cache")

    # Performance
    # MAVAT appears to block/downgrade headless browsers; default to headed.
    headless: bool = False
    max_workers: int = 4


@dataclass
class PipelineStats:
    """Statistics from pipeline execution."""

    start_time: datetime
    end_time: Optional[datetime] = None

    # Discovery
    plans_discovered: int = 0
    plans_processed: int = 0
    plans_failed: int = 0

    # Documents
    documents_found: int = 0
    documents_downloaded: int = 0
    documents_processed: int = 0
    documents_failed: int = 0

    # Extraction
    regulations_extracted: int = 0
    building_rights_extracted: int = 0

    # Vector DB
    regulations_indexed: int = 0
    indexing_failed: int = 0

    # Cache
    cache_hits: int = 0
    cache_misses: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (
                (self.end_time - self.start_time).total_seconds()
                if self.end_time
                else None
            ),
            "plans_discovered": self.plans_discovered,
            "plans_processed": self.plans_processed,
            "plans_failed": self.plans_failed,
            "documents_found": self.documents_found,
            "documents_downloaded": self.documents_downloaded,
            "documents_processed": self.documents_processed,
            "documents_failed": self.documents_failed,
            "regulations_extracted": self.regulations_extracted,
            "building_rights_extracted": self.building_rights_extracted,
            "regulations_indexed": self.regulations_indexed,
            "indexing_failed": self.indexing_failed,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }

    def save(self, path: Path):
        """Save stats to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class UnifiedDataPipeline:
    """
    Unified pipeline for building the complete vector database.

    This is the single entry point for:
    - Discovering plans from iPlan (using data_pipeline infrastructure)
    - Fetching documents from Mavat
    - Processing with vision AI
    - Indexing in vector database
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        iplan_source: Optional[IPlanPydollSource] = None,
        document_fetcher: Optional[MavatDocumentFetcher] = None,
        document_processor: Optional[DocumentProcessor] = None,
        vision_service: Optional[OpenAICompatibleVisionService] = None,
        vectordb_service: Optional[VectorDBManagementService] = None,
    ):
        """
        Initialize the unified pipeline.

        Args:
            config: Pipeline configuration
            iplan_source: iPlan data source (created if not provided)
            document_fetcher: Document fetcher (created if not provided)
            document_processor: Document processor (created if not provided)
            vision_service: Vision service (created if not provided)
            vectordb_service: Vector DB service (created if not provided)
        """
        self.config = config or PipelineConfig()
        self.stats = PipelineStats(start_time=datetime.now())
        self.run_id = uuid4().hex
        self.metrics_sink = (
            self.config.cache_dir / "observability" / "workflow_metrics.jsonl"
        )

        # Browser-backed data source (Pydoll). Started in run_async().
        self.iplan_source = iplan_source or IPlanPydollSource(
            headless=self.config.headless
        )
        self.document_fetcher = document_fetcher or MavatDocumentFetcher()
        self.document_processor = document_processor or DocumentProcessor()

        # Vision service needs API key from environment
        if vision_service:
            self.vision_service = vision_service
        else:
            # Try to get API key from environment
            import os
            from src.config import settings

            api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
            if settings.openai_base_url:
                self.vision_service = OpenAICompatibleVisionService(
                    api_key=api_key,
                    base_url=settings.openai_base_url,
                    model=settings.openai_vision_model,
                )
            else:
                logger.warning(
                    "No OpenAI-compatible base URL found - vision processing will be disabled"
                )
                self.vision_service = None

        # VectorDB service needs repository
        if vectordb_service:
            self.vectordb_service = vectordb_service
        else:
            from src.infrastructure.repositories.chroma_repository import (
                ChromaRegulationRepository,
            )

            repo = ChromaRegulationRepository(persist_directory="./data/vectorstore")
            self.vectordb_service = VectorDBManagementService(repository=repo)

        # Create directories
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> PipelineStats:
        """
        Run the complete pipeline (sync wrapper around async implementation).

        Returns:
            Pipeline statistics
        """
        return asyncio.run(self.run_async())

    async def run_async(self) -> PipelineStats:
        """Async pipeline runner (Pydoll-native)."""
        started_at = perf_counter()
        logger.info("=" * 80)
        logger.info("Starting Unified Data Pipeline")
        logger.info("=" * 80)
        emit_observability_event(
            logger,
            component="UnifiedDataPipeline",
            operation="build",
            request_id=self.run_id,
            outcome="start",
            service_name=self.config.service_name,
            max_plans=self.config.max_plans,
            rebuild_vectordb=self.config.rebuild_vectordb,
        )

        try:
            await self.iplan_source.__aenter__()

            if self.config.rebuild_vectordb:
                logger.info("\n📦 Phase 0: Clearing vector database...")
                self._clear_vectordb()

            logger.info("\n🔍 Phase 1: Discovering plans from iPlan...")
            plans = await self._discover_plans_async()
            logger.info(f"✅ Discovered {len(plans)} plans")

            logger.info(f"\n🔧 Phase 2: Processing {len(plans)} plans...")
            sem = asyncio.Semaphore(max(1, int(self.config.max_workers or 1)))
            ingest_lock = asyncio.Lock()
            # One Pydoll source owns a single Chrome tab; serialize navigation.
            browser_lock = asyncio.Lock()

            async def _worker(i: int, plan: Dict[str, Any]):
                async with sem:
                    logger.info(f"\n--- Plan {i}/{len(plans)} ---")
                    await self._process_plan_async(
                        plan, ingest_lock=ingest_lock, browser_lock=browser_lock
                    )

            await asyncio.gather(*[_worker(i, p) for i, p in enumerate(plans, 1)])

            logger.info("\n📊 Phase 3: Finalizing...")
            self._finalize()

            logger.info("\n" + "=" * 80)
            logger.info("Pipeline Complete!")
            logger.info("=" * 80)
            self._print_stats()
            saturation_snapshot = self._system_saturation_snapshot()
            emit_observability_event(
                logger,
                component="UnifiedDataPipeline",
                operation="build",
                request_id=self.run_id,
                outcome=self._pipeline_outcome(),
                latency_ms=round((perf_counter() - started_at) * 1000, 2),
                plans_discovered=self.stats.plans_discovered,
                plans_processed=self.stats.plans_processed,
                plans_failed=self.stats.plans_failed,
                regulations_indexed=self.stats.regulations_indexed,
                indexing_failed=self.stats.indexing_failed,
                **saturation_snapshot,
            )

            return self.stats
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            saturation_snapshot = self._system_saturation_snapshot()
            emit_observability_event(
                logger,
                component="UnifiedDataPipeline",
                operation="build",
                request_id=self.run_id,
                outcome="error",
                level=logging.ERROR,
                error_class=type(e).__name__,
                message=str(e),
                latency_ms=round((perf_counter() - started_at) * 1000, 2),
                **saturation_snapshot,
            )
            raise
        finally:
            try:
                await self.iplan_source.__aexit__(None, None, None)
            except Exception:
                pass

    def _clear_vectordb(self):
        """Clear the vector database for rebuild."""
        try:
            logger.info("Clearing existing vector database...")
            self.vectordb_service.clear()
            logger.info("✅ Vector database cleared")
        except Exception as e:
            logger.warning(f"Failed to clear vector database: {e}")

    async def _discover_plans_async(self) -> List[Dict[str, Any]]:
        """Discover plans from iPlan (async)."""
        plans = await self.iplan_source.discover_plans(
            service_name=self.config.service_name,
            max_plans=self.config.max_plans,
            where=self.config.where_clause,
        )
        self.stats.plans_discovered = len(plans)
        return plans

    async def _process_plan_async(
        self,
        plan: Dict[str, Any],
        *,
        ingest_lock: asyncio.Lock,
        browser_lock: asyncio.Lock,
    ):
        """
        Process a single plan: fetch documents, analyze, extract, index.

        Args:
            plan: Plan feature from iPlan
        """
        try:
            attrs = plan.get("attributes", {}) or {}

            # Real ArcGIS payloads often use lowercase keys.
            def _get(*keys: str, default=None):
                for k in keys:
                    if isinstance(attrs, dict):
                        if k in attrs and attrs.get(k) not in (None, ""):
                            return attrs.get(k)
                        lk = k.lower()
                        if lk in attrs and attrs.get(lk) not in (None, ""):
                            return attrs.get(lk)
                        uk = k.upper()
                        if uk in attrs and attrs.get(uk) not in (None, ""):
                            return attrs.get(uk)
                return default

            plan_id = _get("OBJECTID", "objectid")
            plan_number = _get("PL_NUMBER", "pl_number", default="unknown")
            plan_name = _get("PL_NAME", "pl_name", default="") or ""
            pl_url = attrs.get("pl_url", "")

            logger.info(f"Processing plan {plan_number}: {plan_name}")
            logger.info(f"  Plan ID: {plan_id}")
            logger.info(f"  Mavat URL: {pl_url}")

            # Always index at least the plan-level metadata so "ingest" works even
            # when document fetching is unavailable or the plan has no MAVAT URL.
            plan_reg = self._create_plan_regulation(attrs)
            if plan_reg:
                async with ingest_lock:
                    self._upsert_regulations([plan_reg])

            # Skip if no Mavat URL
            if not pl_url or "mavat.iplan.gov.il" not in pl_url:
                logger.warning("  ⚠️ No Mavat URL, skipping documents")
                self.stats.plans_processed += 1
                return

            # Extract MAVAT plan ID from URL.
            # URL format: https://mavat.iplan.gov.il/SV4/1/{plan_id}/310
            from urllib.parse import urlparse

            path_parts = [p for p in urlparse(pl_url).path.split("/") if p]
            mavat_plan_id = None
            try:
                # Expected: ["SV4", "1", "{plan_id}", "310"]
                if (
                    len(path_parts) >= 4
                    and path_parts[0] == "SV4"
                    and path_parts[1] == "1"
                ):
                    mavat_plan_id = path_parts[2]
                else:
                    # Fallback: choose the last numeric path part before the trailing section.
                    numeric = [p for p in path_parts if p.isdigit()]
                    if len(numeric) >= 2:
                        mavat_plan_id = numeric[-2]
            except Exception:
                mavat_plan_id = None

            if not mavat_plan_id:
                logger.warning("  ⚠️ Could not extract MAVAT plan ID")
                self.stats.plans_processed += 1
                return

            # Phase 2.1: Fetch documents
            if self.config.fetch_documents:
                documents = await self._fetch_plan_documents_async(
                    mavat_plan_id, browser_lock=browser_lock
                )
                logger.info(f"  📄 Found {len(documents)} documents")
            else:
                documents = []

            # Phase 2.2: Index document links (and optionally run vision later).
            # Even if vision processing is disabled, document URLs are still useful
            # to ingest into the vector DB for later retrieval.
            regulations = []
            if documents:
                regulations = self._process_documents(
                    documents, attrs, mavat_plan_id=mavat_plan_id
                )
                logger.info(
                    f"  📋 Extracted {len(regulations)} regulations (document-link records)"
                )

            # Phase 2.3: Index regulations in vector DB
            if regulations:
                async with ingest_lock:
                    self._upsert_regulations(regulations)
                logger.info(f"  💾 Indexed {len(regulations)} regulations")

            self.stats.plans_processed += 1
            logger.info(f"  ✅ Plan {plan_number} processed successfully")

        except Exception as e:
            logger.error(f"  ❌ Failed to process plan: {e}")
            self.stats.plans_failed += 1

    async def _fetch_plan_documents_async(
        self, mavat_plan_id: str, *, browser_lock: asyncio.Lock
    ) -> List[Dict[str, str]]:
        """
        Fetch documents for a plan from Mavat.

        Args:
            mavat_plan_id: Mavat plan ID

        Returns:
            List of document metadata
        """
        try:
            async with browser_lock:
                documents = await self.iplan_source.fetch_plan_documents(mavat_plan_id)
            self.stats.documents_found += len(documents)

            # Download documents
            downloaded = []
            for doc in documents[: self.config.max_documents_per_plan]:
                try:
                    # Download document
                    # Note: This would need actual download implementation
                    # For now, we just track the URLs
                    downloaded.append(doc)
                    self.stats.documents_downloaded += 1
                except Exception as e:
                    logger.warning(f"    Failed to download {doc.get('title')}: {e}")
                    self.stats.documents_failed += 1

            return downloaded

        except Exception as e:
            logger.error(f"  Failed to fetch documents: {e}")
            return []

    def _process_documents(
        self,
        documents: List[Dict[str, str]],
        plan_attrs: Dict[str, Any],
        mavat_plan_id: str,
    ) -> List[Regulation]:
        """
        Process documents with vision service to extract regulations.

        Args:
            documents: List of document metadata
            plan_attrs: Plan attributes from iPlan

        Returns:
            Extracted regulations
        """
        regulations = []

        for doc in documents:
            try:
                # Here we would:
                # 1. Download the document (PDF/DWG)
                # 2. Convert to images if needed
                # 3. Run vision analysis
                # 4. Extract regulations
                # 5. Parse building rights

                # For now, create placeholder regulation
                # TODO: Implement actual vision processing

                logger.info(f"    Processing document: {doc.get('title')}")

                # Example regulation extraction (placeholder)
                regulation = self._extract_regulation_from_document(
                    doc, plan_attrs, mavat_plan_id=mavat_plan_id
                )
                if regulation:
                    regulations.append(regulation)
                    self.stats.regulations_extracted += 1

                self.stats.documents_processed += 1

            except Exception as e:
                logger.warning(f"    Failed to process document: {e}")
                self.stats.documents_failed += 1

        return regulations

    def _extract_regulation_from_document(
        self, document: Dict[str, str], plan_attrs: Dict[str, Any], mavat_plan_id: str
    ) -> Optional[Regulation]:
        """
        Extract regulation from a document using vision service.

        Args:
            document: Document metadata
            plan_attrs: Plan attributes

        Returns:
            Extracted regulation or None
        """
        # TODO: Implement actual vision-based extraction.
        # For now, index a stable, searchable record with document URL + plan metadata.
        try:
            import hashlib

            def _get(*keys: str, default=None):
                for k in keys:
                    if k in plan_attrs and plan_attrs.get(k) not in (None, ""):
                        return plan_attrs.get(k)
                    lk = k.lower()
                    if lk in plan_attrs and plan_attrs.get(lk) not in (None, ""):
                        return plan_attrs.get(lk)
                    uk = k.upper()
                    if uk in plan_attrs and plan_attrs.get(uk) not in (None, ""):
                        return plan_attrs.get(uk)
                return default

            objectid = str(_get("OBJECTID", "objectid", default="") or "").strip()
            plan_number = str(_get("PL_NUMBER", "pl_number", default="") or "").strip()
            plan_name = (
                str(_get("PL_NAME", "pl_name", default="") or "").strip()
                or plan_number
                or "Untitled Plan"
            )
            municipality = str(
                _get(
                    "MUNICIPALITY_NAME",
                    "municipality_name",
                    "plan_county_name",
                    default="",
                )
                or ""
            ).strip()
            doc_url = str(document.get("url") or "").strip()
            doc_title = str(document.get("title") or "").strip() or "Document"
            artifact_type = str(document.get("artifact_type") or "").strip()

            # Deterministic ID: reruns won't create duplicates.
            url_hash = (
                hashlib.sha1(doc_url.encode("utf-8")).hexdigest()[:12]
                if doc_url
                else "no_url"
            )
            reg_id = (
                f"iplan_{objectid or 'unknown'}_mavat_{mavat_plan_id}_doc_{url_hash}"
            )

            parts = [
                f"{plan_name}",
                f"מספר תכנית: {plan_number}" if plan_number else "",
                f"רשות: {municipality}" if municipality else "",
                f"מסמך: {doc_title}",
                f"סוג קובץ: {artifact_type}" if artifact_type else "",
                f"URL: {doc_url}" if doc_url else "",
                "",
                str(_get("PLAN_TARGETS", "plan_targets", default="") or "").strip(),
                str(_get("MAIN_DETAILS", "main_details", default="") or "").strip(),
            ]
            content = "\n".join([p for p in parts if p]).strip()

            regulation = Regulation(
                id=reg_id,
                type=RegulationType.LOCAL,
                title=f"{plan_number} - {plan_name} - {doc_title}".strip(" -"),
                content=content,
                summary=None,
                jurisdiction=municipality or "national",
                effective_date=None,
                source_document=f"MAVAT {mavat_plan_id}",
                metadata={
                    "source": "UnifiedDataPipeline",
                    "objectid": objectid,
                    "plan_number": plan_number,
                    "municipality_name": municipality,
                    "mavat_plan_id": mavat_plan_id,
                    "document_title": doc_title,
                    "document_url": doc_url,
                    "artifact_type": artifact_type,
                    "full_details": "false",
                },
            )

            return regulation
        except Exception as e:
            logger.error(f"Failed to create regulation: {e}")
            return None

    def _create_plan_regulation(
        self, plan_attrs: Dict[str, Any]
    ) -> Optional[Regulation]:
        """Create a plan-level searchable record (no document required)."""
        try:

            def _get(*keys: str, default=None):
                for k in keys:
                    if k in plan_attrs and plan_attrs.get(k) not in (None, ""):
                        return plan_attrs.get(k)
                    lk = k.lower()
                    if lk in plan_attrs and plan_attrs.get(lk) not in (None, ""):
                        return plan_attrs.get(lk)
                    uk = k.upper()
                    if uk in plan_attrs and plan_attrs.get(uk) not in (None, ""):
                        return plan_attrs.get(uk)
                return default

            objectid = str(_get("OBJECTID", "objectid", default="") or "").strip()
            if not objectid:
                return None

            plan_number = str(_get("PL_NUMBER", "pl_number", default="") or "").strip()
            plan_name = (
                str(_get("PL_NAME", "pl_name", default="") or "").strip()
                or plan_number
                or "Untitled Plan"
            )
            municipality = str(
                _get(
                    "MUNICIPALITY_NAME",
                    "municipality_name",
                    "plan_county_name",
                    default="",
                )
                or ""
            ).strip()
            entity_subtype = str(
                _get("ENTITY_SUBTYPE_DESC", "entity_subtype_desc", default="") or ""
            ).strip()

            parts = [
                plan_name,
                f"מספר תכנית: {plan_number}" if plan_number else "",
                f"רשות: {municipality}" if municipality else "",
                f"סוג: {entity_subtype}" if entity_subtype else "",
                "",
                str(_get("PLAN_TARGETS", "plan_targets", default="") or "").strip(),
                str(_get("MAIN_DETAILS", "main_details", default="") or "").strip(),
            ]
            content = "\n".join([p for p in parts if p]).strip()

            return Regulation(
                id=f"iplan_{objectid}",
                type=RegulationType.LOCAL,
                title=plan_name,
                content=content,
                summary=None,
                jurisdiction=municipality or "national",
                effective_date=None,
                source_document=f"iPlan OBJECTID {objectid}",
                metadata={
                    "source": "UnifiedDataPipeline",
                    "objectid": objectid,
                    "plan_number": plan_number,
                    "entity_subtype": entity_subtype,
                    "municipality_name": municipality,
                    "indexed": "true",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to create plan regulation: {e}")
            return None

    def _upsert_regulations(self, regulations: List[Regulation]):
        """Upsert regulations into Chroma (idempotent continuous ingestion)."""
        try:
            repo = getattr(self.vectordb_service, "repository", None)
            if repo is None:
                raise RuntimeError("VectorDBManagementService has no repository")

            if hasattr(repo, "upsert_regulations_batch"):
                count = repo.upsert_regulations_batch(regulations)
            else:
                count = repo.add_regulations_batch(regulations)

            self.stats.regulations_indexed += int(count or 0)
        except Exception as e:
            logger.error(f"  Failed to index regulations: {e}")
            self.stats.indexing_failed += len(regulations)

    def _finalize(self):
        """Finalize the pipeline and save stats."""
        self.stats.end_time = datetime.now()

        # Save stats to file
        stats_file = self.config.cache_dir / "pipeline_stats.json"
        self.stats.save(stats_file)
        logger.info(f"📊 Stats saved to {stats_file}")

        # Append per-run workflow metrics record for local trend tracking.
        saturation_snapshot = self._system_saturation_snapshot()
        metrics_record = {
            "timestamp": utc_timestamp(),
            "component": "UnifiedDataPipeline",
            "operation": "build",
            "request_id": self.run_id,
            "outcome": self._pipeline_outcome(),
            "duration_seconds": self.stats.to_dict().get("duration_seconds"),
            "max_workers": self.config.max_workers,
            "plans_discovered": self.stats.plans_discovered,
            "plans_processed": self.stats.plans_processed,
            "plans_failed": self.stats.plans_failed,
            "documents_found": self.stats.documents_found,
            "documents_processed": self.stats.documents_processed,
            "documents_failed": self.stats.documents_failed,
            "regulations_indexed": self.stats.regulations_indexed,
            "indexing_failed": self.stats.indexing_failed,
            "cache_hits": self.stats.cache_hits,
            "cache_misses": self.stats.cache_misses,
            **saturation_snapshot,
        }
        append_jsonl_record(self.metrics_sink, metrics_record)
        logger.info(f"📈 Workflow metrics appended to {self.metrics_sink}")

    def _system_saturation_snapshot(self) -> dict[str, Any]:
        """Collect host resource saturation signals for observability."""
        snapshot: dict[str, Any] = {
            "load_1m": None,
            "cpu_count": None,
            "saturation_ratio_1m": None,
            "rss_mb": None,
            "memory_used_ratio": None,
            "memory_used_ratio_source": None,
            "memory_used_ratio_unavailable_reason": None,
            "disk_free_ratio_cache_dir": None,
            "disk_free_mb_cache_dir": None,
        }

        try:
            cpu_count = max(1, int(os.cpu_count() or 1))
            snapshot["cpu_count"] = cpu_count
        except (TypeError, ValueError):
            cpu_count = None

        try:
            load_1m = float(os.getloadavg()[0])
            snapshot["load_1m"] = round(load_1m, 4)
            if cpu_count:
                snapshot["saturation_ratio_1m"] = round(load_1m / cpu_count, 4)
        except (AttributeError, OSError, ValueError):
            pass

        try:
            rss = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            if rss > 0:
                if sys.platform == "darwin":
                    snapshot["rss_mb"] = round(rss / (1024 * 1024), 2)
                else:
                    snapshot["rss_mb"] = round(rss / 1024, 2)
        except Exception:
            pass

        memory_ratio, memory_source, memory_unavailable_reason = (
            self._memory_used_ratio_snapshot()
        )
        snapshot["memory_used_ratio"] = memory_ratio
        snapshot["memory_used_ratio_source"] = memory_source
        snapshot["memory_used_ratio_unavailable_reason"] = memory_unavailable_reason

        try:
            path = (
                self.config.cache_dir if self.config.cache_dir.exists() else Path(".")
            )
            fs = os.statvfs(str(path))
            total_bytes = fs.f_frsize * fs.f_blocks
            free_bytes = fs.f_frsize * fs.f_bavail
            if total_bytes > 0:
                snapshot["disk_free_ratio_cache_dir"] = round(
                    max(0.0, min(1.0, free_bytes / total_bytes)), 4
                )
                snapshot["disk_free_mb_cache_dir"] = round(
                    free_bytes / (1024 * 1024), 2
                )
        except (AttributeError, OSError, ValueError):
            pass

        return snapshot

    def _memory_used_ratio_snapshot(
        self,
    ) -> tuple[float | None, str | None, str | None]:
        """
        Resolve host memory pressure ratio and probe provenance.

        Returns:
            tuple[ratio, source, unavailable_reason]
        """
        ratio = self._memory_used_ratio_from_sysconf()
        if ratio is not None:
            return ratio, "sysconf_sc_avphys_pages", None

        ratio = self._memory_used_ratio_from_memory_pressure()
        if ratio is not None:
            return ratio, "memory_pressure_q", None

        return None, None, "host_memory_probe_unavailable"

    def _memory_used_ratio_from_sysconf(self) -> float | None:
        """Estimate host memory-used ratio from POSIX sysconf page counters."""
        try:
            total_pages = int(os.sysconf("SC_PHYS_PAGES"))
            page_size = int(os.sysconf("SC_PAGE_SIZE"))
            avail_pages = int(os.sysconf("SC_AVPHYS_PAGES"))
            total_bytes = total_pages * page_size
            if total_bytes <= 0:
                return None
            used_ratio = 1.0 - (avail_pages * page_size / total_bytes)
            return round(max(0.0, min(1.0, used_ratio)), 4)
        except (AttributeError, OSError, ValueError):
            return None

    def _memory_used_ratio_from_memory_pressure(self) -> float | None:
        """macOS fallback for memory ratio using `memory_pressure -Q` output."""
        if sys.platform != "darwin":
            return None

        try:
            result = subprocess.run(
                ["memory_pressure", "-Q"],
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            return None

        if result.returncode != 0:
            return None

        free_percent = self._parse_memory_pressure_free_percent(result.stdout)
        if free_percent is None:
            return None

        used_ratio = 1.0 - (free_percent / 100.0)
        return round(max(0.0, min(1.0, used_ratio)), 4)

    @staticmethod
    def _parse_memory_pressure_free_percent(output: str | None) -> float | None:
        """Extract free-memory percentage from `memory_pressure -Q` output."""
        if not output:
            return None

        match = re.search(
            r"System-wide memory free percentage:\s*([0-9]+(?:\.[0-9]+)?)%",
            output,
        )
        if not match:
            return None

        try:
            return float(match.group(1))
        except (TypeError, ValueError):
            return None

    def _system_saturation_ratio(self) -> float | None:
        """Estimate host saturation from 1-minute load average / CPU count."""
        snapshot = self._system_saturation_snapshot()
        value = snapshot.get("saturation_ratio_1m")
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _pipeline_outcome(self) -> str:
        """Classify run outcome for observability events/metrics."""
        if self.stats.indexing_failed > 0:
            return "error"
        if self.stats.plans_failed > 0 or self.stats.documents_failed > 0:
            return "degraded"
        return "success"

    def _print_stats(self):
        """Print pipeline statistics."""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()

        print("\n📊 Pipeline Statistics:")
        print(f"  Duration: {duration:.2f}s")
        print(f"\n  Plans:")
        print(f"    Discovered: {self.stats.plans_discovered}")
        print(f"    Processed:  {self.stats.plans_processed}")
        print(f"    Failed:     {self.stats.plans_failed}")
        print(f"\n  Documents:")
        print(f"    Found:      {self.stats.documents_found}")
        print(f"    Downloaded: {self.stats.documents_downloaded}")
        print(f"    Processed:  {self.stats.documents_processed}")
        print(f"    Failed:     {self.stats.documents_failed}")
        print(f"\n  Extraction:")
        print(f"    Regulations:     {self.stats.regulations_extracted}")
        print(f"    Building Rights: {self.stats.building_rights_extracted}")
        print(f"\n  Vector DB:")
        print(f"    Indexed: {self.stats.regulations_indexed}")
        print(f"    Failed:  {self.stats.indexing_failed}")


def build_vectordb(
    max_plans: Optional[int] = None,
    service_name: str = "xplan",
    rebuild: bool = False,
    headless: bool = True,
) -> PipelineStats:
    """
    Convenience function to build the vector database.

    Args:
        max_plans: Maximum plans to process (None = all)
        service_name: iPlan service to use
        rebuild: Clear and rebuild vector DB
        headless: Run browser in headless mode

    Returns:
        Pipeline statistics
    """
    config = PipelineConfig(
        service_name=service_name,
        max_plans=max_plans,
        rebuild_vectordb=rebuild,
        headless=headless,
    )

    pipeline = UnifiedDataPipeline(config=config)
    return pipeline.run()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("Building vector database from iPlan data...")
    print("This will:")
    print("  1. Discover plans using Pydoll (bypasses WAF)")
    print("  2. Fetch documents from Mavat")
    print("  3. Process with vision AI")
    print("  4. Index in vector database")
    print()

    # Build with first 10 plans for testing
    stats = build_vectordb(
        max_plans=10, service_name="xplan", rebuild=False, headless=True
    )

    print("\n✅ Vector database build complete!")
    print(f"📊 {stats.regulations_indexed} regulations indexed")
