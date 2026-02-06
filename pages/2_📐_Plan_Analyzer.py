"""
Plan Analyzer - Building rights, compliance, and optional upload analysis.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.application.dtos import BuildingRightsQuery
from src.infrastructure.factory import get_factory


st.set_page_config(page_title="Plan Analyzer", page_icon="📐", layout="wide")


@st.cache_resource
def get_services():
    factory = get_factory()
    return {
        "factory": factory,
        "rights": factory.get_building_rights_service(),
        "upload": factory.get_plan_upload_service(),  # may be None if no vision key
    }


def _zone_options() -> list[tuple[str, str]]:
    # (label, zone_code) - zone_code feeds BuildingRightsCalculator.
    return [
        ("R1 - Low Density Residential", "R1"),
        ("R2 - Medium Density Residential", "R2"),
        ("R3 - High Density Residential", "R3"),
        ("C1 - Commercial", "C1"),
        ("M1 - Mixed Use", "MIXED"),
        ("TAMA 35 - Urban Renewal", "TAMA35"),
    ]


def _coverage_figure(plot_size_sqm: float, coverage_percent: float) -> go.Figure:
    side = max(plot_size_sqm, 1.0) ** 0.5
    building_area = max(plot_size_sqm, 1.0) * (coverage_percent / 100.0)
    building_side = max(building_area, 1.0) ** 0.5

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, side, side, 0, 0],
            y=[0, 0, side, side, 0],
            fill="toself",
            fillcolor="rgba(200,200,200,0.6)",
            line=dict(color="black", width=2),
            name="Plot",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0, building_side, building_side, 0, 0],
            y=[0, 0, building_side, building_side, 0],
            fill="toself",
            fillcolor="rgba(46, 134, 171, 0.55)",
            line=dict(color="#2E86AB", width=2),
            name="Building footprint",
        )
    )
    fig.update_layout(
        height=360,
        showlegend=True,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=10, r=10, t=40, b=10),
        title="Coverage (Top View, Not To Scale)",
    )
    return fig


def main() -> None:
    st.markdown("# 📐 Plan Analyzer")
    st.markdown("### Building rights, compliance checks, and optional upload analysis")

    services = get_services()
    rights_service = services["rights"]
    upload_service = services["upload"]

    with st.sidebar:
        st.markdown("## Project Inputs")
        project_name = st.text_input("Project name", "My Building Project")
        location = st.text_input("Location", "Tel Aviv")

        st.markdown("### Plot")
        plot_size = st.number_input("Plot size (sqm)", min_value=50, max_value=200_000, value=500, step=50)

        st.markdown("### Zoning")
        zone_label_to_code = dict(_zone_options())
        zone_label = st.selectbox("Zone type", list(zone_label_to_code.keys()), index=1)
        zone_code = zone_label_to_code[zone_label]

        st.markdown("### Proposed Building")
        proposed_floors = st.slider("Floors", 1, 60, 4)
        proposed_coverage_pct = st.slider("Coverage (%)", 5, 95, 40)

    query = BuildingRightsQuery(plot_size_sqm=float(plot_size), zone_type=zone_code, location=location)
    rights_result = rights_service.calculate_building_rights(query, include_regulations=False)
    rights = rights_result.building_rights
    regs_key = "plan_analyzer_applicable_regs"
    regs_state = st.session_state.get(regs_key)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Analysis", "📈 Comparison", "✅ Compliance", "📄 Report", "📤 Upload & Analyze"]
    )

    with tab1:
        st.markdown("## Building Rights")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Allowed (Calculated)")
            st.metric("Max floors", rights.max_floors)
            st.metric("Max height (m)", f"{rights.max_height_meters}")
            st.metric("Max coverage (%)", f"{rights.max_coverage_percent}")
            st.metric("Max coverage (sqm)", f"{rights.max_coverage_sqm:.0f}")
            st.metric("FAR", f"{rights.floor_area_ratio}")
            st.metric("Max building area (sqm)", f"{rights.max_building_area_sqm:.0f}")
            st.metric("Parking (typical)", rights.parking_spaces_required)

        with col2:
            st.markdown("### Proposed vs Allowed")
            proposed_floor_area = plot_size * (proposed_coverage_pct / 100.0) * proposed_floors

            floors_ok = proposed_floors <= rights.max_floors
            cov_ok = (plot_size * (proposed_coverage_pct / 100.0)) <= float(rights.max_coverage_sqm)
            area_ok = proposed_floor_area <= float(rights.max_building_area_sqm)

            st.metric("Proposed floors", proposed_floors, delta="OK" if floors_ok else "Over limit")
            st.metric("Proposed coverage (%)", proposed_coverage_pct, delta="OK" if cov_ok else "Over limit")
            st.metric("Proposed floor area (sqm)", f"{proposed_floor_area:,.0f}", delta="OK" if area_ok else "Over limit")

            st.plotly_chart(_coverage_figure(float(plot_size), float(proposed_coverage_pct)), use_container_width=True)

        st.markdown("---")
        st.markdown("### Applicable Regulations (from Vector DB)")
        col_a, col_b = st.columns([1, 2])
        with col_a:
            if st.button("Fetch Applicable Regulations", use_container_width=True):
                with st.spinner("Searching vector DB..."):
                    full = rights_service.calculate_building_rights(query, include_regulations=True)
                st.session_state[regs_key] = full.applicable_regulations
                st.rerun()
        with col_b:
            st.caption("This is optional because it can be slower than the pure calculation step.")

        regs = regs_state or []
        if regs:
            for reg in regs:
                with st.expander(reg.title):
                    st.caption(f"type={reg.type.value} jurisdiction={reg.jurisdiction}")
                    st.write((reg.summary or reg.content)[:800] + ("..." if len((reg.summary or reg.content)) > 800 else ""))
        else:
            st.info("Not fetched yet.")

    with tab2:
        st.markdown("## Scenario Comparison")
        proposed_floor_area = plot_size * (proposed_coverage_pct / 100.0) * proposed_floors
        max_floor_area = float(rights.max_building_area_sqm)

        scenarios = pd.DataFrame(
            [
                {"Scenario": "Proposed", "Floors": proposed_floors, "Coverage (%)": proposed_coverage_pct, "Floor Area (sqm)": proposed_floor_area},
                {"Scenario": "Max Allowed", "Floors": rights.max_floors, "Coverage (%)": float(rights.max_coverage_percent), "Floor Area (sqm)": max_floor_area},
            ]
        )

        fig = px.bar(
            scenarios,
            x="Scenario",
            y="Floor Area (sqm)",
            color="Floors",
            title="Floor Area by Scenario",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(scenarios, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("## Compliance Checks")
        proposed_floor_area = plot_size * (proposed_coverage_pct / 100.0) * proposed_floors
        proposed_coverage_sqm = plot_size * (proposed_coverage_pct / 100.0)

        rows = [
            {
                "Check": "Floors",
                "Required": f"<= {rights.max_floors}",
                "Proposed": str(proposed_floors),
                "Status": "✅" if proposed_floors <= rights.max_floors else "❌",
            },
            {
                "Check": "Coverage (sqm)",
                "Required": f"<= {float(rights.max_coverage_sqm):.0f}",
                "Proposed": f"{proposed_coverage_sqm:.0f}",
                "Status": "✅" if proposed_coverage_sqm <= float(rights.max_coverage_sqm) else "❌",
            },
            {
                "Check": "Total building area (sqm)",
                "Required": f"<= {float(rights.max_building_area_sqm):.0f}",
                "Proposed": f"{proposed_floor_area:.0f}",
                "Status": "✅" if proposed_floor_area <= float(rights.max_building_area_sqm) else "❌",
            },
            {
                "Check": "Setbacks (front/side/rear, m)",
                "Required": f"{rights.front_setback_meters}/{rights.side_setback_meters}/{rights.rear_setback_meters}",
                "Proposed": "TBD",
                "Status": "⏳",
            },
            {
                "Check": "Parking (typical)",
                "Required": str(rights.parking_spaces_required),
                "Proposed": "TBD",
                "Status": "⏳",
            },
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        compliant = sum(1 for r in rows if r["Status"] == "✅")
        total = sum(1 for r in rows if r["Status"] in {"✅", "❌"})
        score = (compliant / total) * 100 if total else 0.0

        st.markdown("### Overall Score (based on computed checks)")
        st.progress(int(score))
        st.caption(f"{score:.0f}% compliant (computed checks only)")

    with tab4:
        st.markdown("## Report")
        proposed_floor_area = plot_size * (proposed_coverage_pct / 100.0) * proposed_floors

        report = f"""
# Building Analysis Report

**Project:** {project_name}
**Location:** {location}
**Date:** {datetime.now().strftime("%Y-%m-%d")}

## Inputs
- Plot size: {plot_size} sqm
- Zone: {zone_label} ({zone_code})
- Proposed floors: {proposed_floors}
- Proposed coverage: {proposed_coverage_pct}%

## Calculated Rights (Typical)
- Max floors: {rights.max_floors}
- Max height: {rights.max_height_meters} m
- Max coverage: {rights.max_coverage_percent}% ({rights.max_coverage_sqm:.0f} sqm)
- FAR: {rights.floor_area_ratio}
- Max building area: {rights.max_building_area_sqm:.0f} sqm
- Parking (typical): {rights.parking_spaces_required}

## Proposed Totals
- Proposed floor area: {proposed_floor_area:.0f} sqm
        """.strip()

        st.markdown(report)

        st.download_button(
            "Download report (Markdown)",
            data=report.encode("utf-8"),
            file_name=f"building_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with tab5:
        st.markdown("## Upload & Analyze Plan (Vision)")
        if upload_service is None:
            st.warning("Vision analysis is disabled. Configure `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) and restart.")
            return

        uploaded = st.file_uploader("Upload PDF/Image", type=["pdf", "jpg", "jpeg", "png", "tiff"])
        if uploaded is None:
            st.info("Upload a document to run vision analysis and semantic search.")
            return

        st.success(f"Uploaded: {uploaded.name} ({uploaded.size / 1024:.1f} KB)")

        if uploaded.type.startswith("image/"):
            st.image(uploaded, caption="Preview", use_container_width=True)

        if st.button("Analyze", type="primary"):
            with st.spinner("Analyzing..."):
                uploaded.seek(0)
                analysis = upload_service.analyze_uploaded_plan(uploaded, uploaded.name, max_results=5)
            if not analysis:
                st.error("Analysis failed. Check logs and API key configuration.")
                return
            st.session_state["upload_analysis"] = analysis
            st.rerun()

        if "upload_analysis" in st.session_state:
            analysis = st.session_state["upload_analysis"]
            st.markdown("### Results")
            with st.expander("Plan Description", expanded=True):
                st.write(analysis.vision_analysis.description or "No description")

            if analysis.extracted_text:
                with st.expander("Extracted Text (preview)"):
                    st.text(analysis.extracted_text[:800] + ("..." if len(analysis.extracted_text) > 800 else ""))

            if analysis.identified_zones:
                st.write("**Zones:** " + ", ".join(analysis.identified_zones))

            st.markdown("### Matching Regulations")
            if analysis.matching_regulations:
                for reg, score in zip(analysis.matching_regulations, analysis.similarity_scores):
                    with st.expander(f"{reg.title} (similarity {score:.2%})"):
                        st.caption(f"type={reg.type.value} jurisdiction={reg.jurisdiction}")
                        st.write((reg.summary or reg.content)[:900] + ("..." if len((reg.summary or reg.content)) > 900 else ""))
            else:
                st.info("No matching regulations found")

            if st.button("Clear results"):
                del st.session_state["upload_analysis"]
                st.rerun()


main()
