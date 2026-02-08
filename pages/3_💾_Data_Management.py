"""
Data Management Page - Manage planning data sources and vector database.

Streamlit pages execute top-to-bottom on each rerun. Keep heavy initialization
behind st.cache_resource and avoid side effects at import time.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_management import DataStore, DataFetcherFactory
from src.infrastructure.factory import get_factory
from src.vectorstore.management_service import VectorDBManagementService


st.set_page_config(page_title="Data Management", page_icon="💾", layout="wide")


@st.cache_resource
def get_data_store() -> DataStore:
    return DataStore()


@st.cache_resource
def get_vectordb_service() -> VectorDBManagementService:
    factory = get_factory()
    repo = factory.get_regulation_repository()
    return VectorDBManagementService(repo)


def _import_features_from_upload(store: DataStore, uploaded_file) -> None:
    try:
        data = json.loads(uploaded_file.getvalue().decode("utf-8"))
    except Exception as e:
        st.error(f"Failed to read JSON: {e}")
        return

    if isinstance(data, dict) and "features" in data:
        features = data["features"]
    elif isinstance(data, list):
        features = data
    else:
        features = [data]

    st.info(f"File contains {len(features)} features")
    if st.button("Import Features", use_container_width=True, type="primary"):
        added = store.add_features(features, avoid_duplicates=True)
        store.save(backup=True)
        st.success(f"Imported {added} new features")
        st.rerun()


def _render_overview_tab(store: DataStore) -> None:
    st.markdown("## Overview")

    stats = store.get_statistics()
    metadata = stats.get("metadata", {}) or {}

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Plans", stats["total_plans"])
    col2.metric("Districts", len(stats["by_district"]))
    col3.metric("Cities", len(stats["by_city"]))
    col4.metric("Statuses", len(stats["by_status"]))

    st.markdown("---")

    if metadata:
        st.markdown("### Source Info")
        col1, col2 = st.columns(2)
        col1.write(f"**Source:** {metadata.get('source', 'Unknown')}")
        col1.write(f"**Last Updated:** {metadata.get('last_updated', metadata.get('fetched_at', 'Unknown'))}")
        col1.write(f"**Quality:** {metadata.get('data_quality', 'N/A')}")

        if "coverage" in metadata:
            col2.write("**Coverage:**")
            for region in metadata["coverage"]:
                col2.write(f"- {region}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### By District")
        if stats["by_district"]:
            df = pd.DataFrame([{"District": k, "Count": v} for k, v in stats["by_district"].items()])
            df = df.sort_values("Count", ascending=False)
            st.bar_chart(df.set_index("District"))
        else:
            st.info("No data available")

    with col2:
        st.markdown("### By Status")
        if stats["by_status"]:
            df = pd.DataFrame([{"Status": k, "Count": v} for k, v in stats["by_status"].items()])
            df = df.sort_values("Count", ascending=False)
            st.bar_chart(df.set_index("Status"))
        else:
            st.info("No data available")


def _render_browse_tab(store: DataStore) -> None:
    st.markdown("## Browse Plans")

    col1, col2, col3 = st.columns(3)
    with col1:
        districts = ["All"] + store.get_unique_values("district_name")
        selected_district = st.selectbox("District", districts)
    with col2:
        cities = ["All"] + store.get_unique_values("plan_county_name")
        selected_city = st.selectbox("City", cities)
    with col3:
        statuses = ["All"] + store.get_unique_values("station_desc")
        selected_status = st.selectbox("Status", statuses)

    search_text = st.text_input("Search plan name/number", placeholder="e.g., 101-0121850")

    results = store.search_features(
        district=None if selected_district == "All" else selected_district,
        city=None if selected_city == "All" else selected_city,
        status=None if selected_status == "All" else selected_status,
        text=search_text or None,
    )

    st.markdown(f"**Found {len(results)} plans**")

    if not results:
        st.info("No plans match the current filters")
        return

    for feature in results[:50]:
        attrs = feature.get("attributes", {}) or {}
        title = f"{attrs.get('pl_number', 'N/A')} - {str(attrs.get('pl_name', 'Unnamed'))[:80]}"
        with st.expander(f"📋 {title}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Plan Number:** {attrs.get('pl_number', 'N/A')}")
                st.write(f"**Name:** {attrs.get('pl_name', 'N/A')}")
                st.write(f"**District:** {attrs.get('district_name', 'N/A')}")
                st.write(f"**City:** {attrs.get('plan_county_name', 'N/A')}")
                st.write(f"**Area:** {attrs.get('pl_area_dunam', 0)} dunam")
                if attrs.get("pl_objectives"):
                    st.write("**Objectives:**")
                    st.write(str(attrs["pl_objectives"])[:600] + ("..." if len(str(attrs["pl_objectives"])) > 600 else ""))
            with col2:
                st.write(f"**Status:** {attrs.get('station_desc', 'N/A')}")
                st.write(f"**Type:** {attrs.get('entity_subtype_desc', 'N/A')}")
                if attrs.get("pl_url"):
                    st.markdown(f"[View on iPlan]({attrs['pl_url']})")
                has_geometry = bool((feature.get("geometry", {}) or {}).get("rings"))
                st.write(f"**Has Geometry:** {'✅' if has_geometry else '❌'}")

    if len(results) > 50:
        st.info(f"Showing first 50 of {len(results)} results. Refine filters to see more.")


def _render_fetch_tab(store: DataStore) -> None:
    st.markdown("## Fetch Fresh Data")
    st.caption("Fetching via Pydoll uses a local Chrome browser (CDP). Headless mode may be blocked by MAVAT.")

    sources = DataFetcherFactory.list_sources()
    if not sources:
        st.info("No fetchers registered")
        return

    source_name = st.selectbox("Source", sources, index=0)
    fetcher = DataFetcherFactory.get_fetcher(source_name)

    st.write(f"**Selected:** {fetcher.get_source_name()}")
    st.write(f"**Availability:** {'✅ Available' if fetcher.is_available() else '⚠️ Not available in this environment'}")

    if source_name in {"iplan", "iplan_pydoll"}:
        col1, col2 = st.columns(2)
        with col1:
            service_name = st.selectbox("Service", ["xplan", "xplan_full", "tama35", "tama"], index=0)
        with col2:
            max_plans = st.number_input("Max plans", min_value=1, max_value=5000, value=100, step=50)

        where = st.text_input("Where clause", value="1=1", help="ArcGIS SQL where clause (advanced)")

        if st.button("Fetch Now", type="primary"):
            if not fetcher.is_available():
                st.error("Fetcher is not available. Check that Chrome can be launched by Pydoll.")
                return

            with st.spinner("Fetching..."):
                result = fetcher.fetch(service_name=service_name, max_plans=int(max_plans), where=where)
            features = result.get("features", []) or []

            if not features:
                st.warning("No features returned")
                st.json(result.get("metadata", {}))
                return

            added = store.add_features(features, avoid_duplicates=True)
            store.save(backup=True)
            st.success(f"Fetched {len(features)} features, added {added} new plans")
            st.json(result.get("metadata", {}))
            st.rerun()

    else:
        st.info("This fetcher currently supports manual file import via the sidebar.")


def _render_vectordb_tab(vectordb: VectorDBManagementService) -> None:
    st.markdown("## Vector Database Management")

    try:
        status = vectordb.get_status()
    except Exception as e:
        st.error(f"Failed to read vector DB status: {e}")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Regulations", status.get("total_regulations", 0))
    with col2:
        st.write(f"**Status:** {status.get('status', 'unknown')}")
        st.write(f"**Health:** {status.get('health', 'unknown')}")
    with col3:
        st.write(f"**Collection:** {status.get('statistics', {}).get('collection_name', 'N/A')}")
        st.write(f"**Directory:** {status.get('statistics', {}).get('persist_directory', 'N/A')}")

    st.markdown("---")

    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("Check & Initialize", use_container_width=True):
            with st.spinner("Initializing if needed..."):
                ok = vectordb.initialize_if_needed()
            if ok:
                st.success("Vector DB is ready")
            else:
                st.error("Initialization failed")
            st.cache_resource.clear()
            st.rerun()

    with action_col2:
        if st.button("Refresh Status", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()

    with action_col3:
        if st.button("Rebuild (Samples)", use_container_width=True, type="secondary"):
            if st.session_state.get("confirm_vectordb_rebuild"):
                with st.spinner("Rebuilding..."):
                    ok = vectordb.rebuild_database()
                st.session_state["confirm_vectordb_rebuild"] = False
                st.cache_resource.clear()
                if ok:
                    st.success("Rebuilt successfully")
                else:
                    st.error("Rebuild failed")
                st.rerun()
            else:
                st.session_state["confirm_vectordb_rebuild"] = True
                st.warning("This deletes the current collection. Click again to confirm.")

    with st.expander("➕ Add Regulation"):
        title = st.text_input("Title", placeholder="e.g., Parking Space Requirements")
        reg_type = st.selectbox("Type", ["local", "national", "district", "tama", "zoning"], index=0)
        jurisdiction = st.text_input("Jurisdiction", value="national")
        summary = st.text_area("Summary (optional)", placeholder="Short summary")
        content = st.text_area("Content", height=200, placeholder="Full regulation text...")

        if st.button("Add", type="primary"):
            if not title.strip() or not content.strip():
                st.error("Title and content are required")
            else:
                from src.domain.entities.regulation import RegulationType

                ok = vectordb.add_regulation(
                    title=title.strip(),
                    content=content.strip(),
                    reg_type=RegulationType(reg_type),
                    jurisdiction=jurisdiction.strip() or "national",
                    summary=summary.strip() or None,
                )
                if ok:
                    st.success("Added regulation")
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.error("Failed to add regulation")

    with st.expander("🔍 Search Regulations", expanded=True):
        q = st.text_input("Query", placeholder="e.g., parking requirements / תכנית")
        limit = st.slider("Max results", 1, 25, 5)

        if st.button("Search", type="primary"):
            if not q.strip():
                st.warning("Enter a query")
            else:
                results = vectordb.search_regulations(q.strip(), limit=int(limit))
                if not results:
                    st.info("No results")
                else:
                    st.success(f"Found {len(results)} results")
                    for i, reg in enumerate(results, 1):
                        st.markdown(f"**{i}. {reg.title}**")
                        st.caption(f"type={reg.type.value} jurisdiction={reg.jurisdiction}")
                        st.write((reg.summary or reg.content)[:500] + ("..." if len((reg.summary or reg.content)) > 500 else ""))
                        with st.expander("Show content"):
                            st.text(reg.content)

    with st.expander("📥 Import/Export Regulations"):
        uploaded = st.file_uploader("Import JSON", type=["json"])
        if uploaded is not None:
            try:
                with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".json") as tmp:
                    tmp.write(uploaded.getvalue())
                    tmp_path = tmp.name
                if st.button("Import", type="primary"):
                    res = vectordb.import_from_file(tmp_path)
                    if res.get("error"):
                        st.error(res["error"])
                    else:
                        st.success(f"Imported {res.get('success', 0)} regulations (failed: {res.get('failed', 0)})")
                    st.cache_resource.clear()
                    st.rerun()
            finally:
                pass

        export_name = st.text_input("Export filename", value=f"regulations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if st.button("Export All"):
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / export_name
                ok = vectordb.export_to_file(str(out))
                if not ok:
                    st.error("Export failed")
                else:
                    st.download_button(
                        label="Download export",
                        data=out.read_bytes(),
                        file_name=export_name,
                        mime="application/json",
                        use_container_width=True,
                    )


def _render_instructions_tab() -> None:
    st.markdown("## Instructions")
    st.markdown(
        """
### Typical Workflow

1. Use **Overview** to confirm you have plans loaded.
2. Use **Browse** to validate coverage and spot-check plan attributes.
3. Use **Vector DB** to initialize semantic search and verify regulation queries.

### Importing Plans
- Use the sidebar to upload a JSON/GeoJSON file.
- Imports are de-duplicated by `attributes.pl_number` when present.
- A backup is created on save in `data/raw/backups/`.
        """.strip()
    )


def main() -> None:
    st.markdown("# 💾 Data Management")
    st.markdown("### Manage planning data sources, updates, and the vector database")

    store = get_data_store()
    vectordb = get_vectordb_service()

    with st.sidebar:
        st.markdown("## Actions")
        if st.button("Reload Data", use_container_width=True):
            store.reload()
            st.cache_resource.clear()
            st.success("Reloaded")
            st.rerun()

        if st.button("Save Data (Backup)", use_container_width=True):
            store.save(backup=True)
            st.success("Saved")

        st.markdown("---")
        st.markdown("## Import Plans")
        uploaded = st.file_uploader("Upload JSON/GeoJSON", type=["json", "geojson"])
        if uploaded is not None:
            _import_features_from_upload(store, uploaded)

    tab_overview, tab_browse, tab_fetch, tab_vectordb, tab_instructions = st.tabs(
        ["📊 Overview", "🔍 Browse", "📡 Fetch", "🗄️ Vector DB", "📖 Instructions"]
    )

    with tab_overview:
        _render_overview_tab(store)

    with tab_browse:
        _render_browse_tab(store)

    with tab_fetch:
        _render_fetch_tab(store)

    with tab_vectordb:
        _render_vectordb_tab(vectordb)

    with tab_instructions:
        _render_instructions_tab()


main()
