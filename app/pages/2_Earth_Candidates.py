# Streamlit's script runner may omit the repository root from sys.path.
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import html

import pandas as pd
import streamlit as st

from app.components.chart_helpers import slope_histogram_chart
from app.components.map_helpers import (
    filter_sites_by_body,
    render_site_detail_map,
    render_site_map,
)
from app.components.site_profile import load_profile_terrain_metrics, render_next_step, render_page_banner
from app.utils.config import DATA_ROOT, get_data_file_source
from app.utils.loaders import (
    load_site_extents,
    load_sites,
    load_slope_histograms,
    load_slope_preview,
)


st.set_page_config(page_title="Earth Candidates | TERRAOPS", layout="wide")
st.title("Earth Candidates")
st.caption(
    "How to use this page: choose a site from the map or selector, then inspect its footprint and terrain measurements. "
    "Use the comparison selector to view a second candidate beside it."
)
render_page_banner(
    None,
    {
        filename: get_data_file_source(filename)
        for filename in ("sites.geojson", "terrain_metrics.csv", "datasets_catalogue.csv")
    },
)


def _site_reason(site_id: str, terrain: pd.DataFrame) -> tuple[str, str]:
    rows = terrain.loc[terrain["site_id"].astype(str) == site_id]
    notes = (
        rows["availability_note"].dropna().astype(str).str.strip()
        if "availability_note" in rows
        else pd.Series(dtype=str)
    )
    note = next((value for value in notes if value), "Terrain measurements are not available yet.")
    if note.startswith("Terrain metrics pending CRS review:"):
        return "the terrain measurements need coordinate-system review", note
    if note.startswith("Terrain metrics pending:"):
        detail = note.removeprefix("Terrain metrics pending:").strip()
        plain = detail.replace("preferred reprojected raster(s) absent", "required terrain measurements are absent")
        plain = plain.replace("no supplied extent geometry is available", "no mapped site footprint is available")
        return plain, note
    return note, note


def _value(site_terrain: pd.DataFrame, metric_name: str) -> float | None:
    rows = site_terrain.loc[site_terrain["metric_name"] == metric_name]
    if rows.empty:
        return None
    row = rows.iloc[0]
    number = pd.to_numeric(pd.Series([row["value"]]), errors="coerce").iloc[0]
    if pd.isna(number) or pd.isna(row["tier"]) or not str(row["tier"]).strip():
        return None
    return float(number)


def _render_site(site_id, sites, extents, terrain, histogram, show_overlay, opacity, site_names):
    site_rows = sites.loc[sites["site_id"].astype(str) == site_id]
    site = site_rows.iloc[0]
    extent_rows = extents.loc[extents["site_id"].astype(str) == site_id]
    extent = extent_rows.geometry.iloc[0] if not extent_rows.empty else None
    preview = load_slope_preview(site_id, DATA_ROOT / "processed")
    site_terrain = terrain.loc[terrain["site_id"].astype(str) == site_id]

    st.markdown(f"#### {html.escape(str(site['name']))}")
    lat = pd.to_numeric(pd.Series([site["lat"]]), errors="coerce").iloc[0]
    lon = pd.to_numeric(pd.Series([site["lon"]]), errors="coerce").iloc[0]
    if pd.notna(lat) and pd.notna(lon):
        st.write(f"Coordinates: {float(lat):.4f}°, {float(lon):.4f}°")

    preview_bytes = preview["image_bytes"] if preview is not None and show_overlay else None
    preview_bounds = (
        [[float(preview["bounds_south"]), float(preview["bounds_west"])],
         [float(preview["bounds_north"]), float(preview["bounds_east"])]]
        if preview is not None and show_overlay
        else None
    )
    render_site_detail_map(
        site,
        extent,
        preview_bytes=preview_bytes,
        preview_bounds=preview_bounds,
        opacity=opacity,
        height=380,
        key=f"earth_detail_{site_id}",
    )
    st.caption(
        "The outlined box is the area covered by the terrain measurements, not a validated study site."
    )
    if preview is not None and show_overlay:
        st.markdown(
            "<div style='height:12px;border-radius:6px;background:linear-gradient(90deg,#f8fafc,#bee6dc,#52b3a7,#256ea5,#08306b)'></div>",
            unsafe_allow_html=True,
        )
        minimum = pd.to_numeric(pd.Series([preview.get("slope_min")]), errors="coerce").iloc[0]
        maximum = pd.to_numeric(pd.Series([preview.get("slope_max")]), errors="coerce").iloc[0]
        if pd.notna(minimum) and pd.notna(maximum):
            st.caption(
                f"Slope range: {minimum:.2f} to {maximum:.2f}. "
                "Light colors indicate lower values; darker colors indicate higher values."
            )

    has_values = (
        site_terrain["value"].notna()
        & site_terrain["tier"].astype("string").fillna("").str.strip().ne("")
    ).any()
    if not has_values:
        reason, technical_reason = _site_reason(site_id, terrain)
        st.markdown(f"Terrain measurements are not available yet: {reason}.")
        with st.expander("Terrain data details", expanded=False):
            st.write(technical_reason)
        return

    values = (
        ("Slope P90", _value(site_terrain, "slope_p90_deg"), "{:.2f}"),
        ("Area above 24°", _value(site_terrain, "pct_area_slope_gt24"), "{:.2f}%"),
        ("Roughness", _value(site_terrain, "roughness"), "{:.2f}"),
    )
    metric_columns = st.columns(3)
    for column, (label, value, number_format) in zip(metric_columns, values):
        column.metric(label, "Not available" if value is None else number_format.format(value))
    st.caption("Values summarize this site's terrain; slope cutoffs are provisional and roughness has no defined threshold.")
    site_histogram = histogram.loc[histogram["site_id"].astype(str) == site_id]
    if not site_histogram.empty:
        st.plotly_chart(
            slope_histogram_chart(histogram, emphasized_site=site_id),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.caption(
            "Each line shows the share of valid terrain pixels in slope-value bins; the selected site's line is emphasized."
        )
    with st.expander("Preview source details", expanded=False):
        if preview is not None:
            st.write(
                f"Coordinate system: {preview['crs']}; "
                f"preview size: {int(preview['preview_width'])} × {int(preview['preview_height'])} px."
            )
        else:
            st.write("No terrain image is available for this site.")


try:
    sites = load_sites()
    terrain = load_profile_terrain_metrics()
    earth_sites = filter_sites_by_body(sites, "Earth")
    site_ids = earth_sites["site_id"].astype(str).tolist()
    site_names = dict(zip(earth_sites["site_id"].astype(str), earth_sites["name"].astype(str)))
    if not site_ids:
        st.info("No Earth sites are available in the active data source.")
        st.stop()

    terrain_values = terrain["value"].notna() & terrain["tier"].astype("string").fillna("").str.strip().ne("")
    sites_with_terrain = set(terrain.loc[terrain_values, "site_id"].astype(str))
    default_site = next((site_id for site_id in site_ids if site_id in sites_with_terrain), site_ids[0])
    if st.session_state.get("earth_selected_site") not in site_ids:
        st.session_state["earth_selected_site"] = default_site

    st.subheader("Site overview")
    clicked_site = render_site_map(
        earth_sites,
        height=250,
        key=f"earth_overview_{st.session_state['earth_selected_site']}",
        selected_site_id=st.session_state["earth_selected_site"],
    )
    if clicked_site in site_ids:
        st.session_state["earth_selected_site"] = clicked_site
    st.caption("Select a marker or use the selector to focus the site map below.")

    selected_site_id = st.selectbox(
        "Select an Earth site",
        options=site_ids,
        format_func=lambda site_id: f"{site_names[site_id]} ({site_id})",
        key="earth_selected_site",
    )
    comparison_options = [site_id for site_id in site_ids if site_id != selected_site_id]
    compare_site_id = st.selectbox(
        "Compare with another site",
        options=["none", *comparison_options],
        format_func=lambda site_id: "No comparison" if site_id == "none" else site_names[site_id],
        key="earth_compare_site",
    )
    show_overlay = st.checkbox("Show slope overlay", value=True)
    overlay_opacity = st.slider(
        "Slope overlay opacity", min_value=0.1, max_value=1.0, value=0.6, step=0.05,
        disabled=not show_overlay,
    )

    extents = load_site_extents()
    histogram = load_slope_histograms(DATA_ROOT / "processed")
    if compare_site_id == "none":
        left, right = st.columns([1.15, 1])
        with left:
            _render_site(
                selected_site_id, earth_sites, extents, terrain, histogram,
                show_overlay, overlay_opacity, site_names,
            )
        with right:
            st.caption("Choose a second site above to compare its map, terrain values, and slope distribution side by side.")
    else:
        left, right = st.columns(2)
        with left:
            _render_site(
                selected_site_id, earth_sites, extents, terrain, histogram,
                show_overlay, overlay_opacity, site_names,
            )
        with right:
            _render_site(
                compare_site_id, earth_sites, extents, terrain, histogram,
                show_overlay, overlay_opacity, site_names,
            )
except Exception as error:
    st.error(f"Could not load candidate site data: {error}")

render_next_step("pages/3_Terrain_Comparison.py", "Next step: Terrain Comparison")
