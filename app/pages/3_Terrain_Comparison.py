# Streamlit's script runner may omit the repository root from sys.path.
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import html

import pandas as pd
import streamlit as st

from app.components.chart_helpers import terrain_slope_distribution_chart
from app.components.site_profile import render_next_step, render_page_banner, render_team_wordmark
from app.utils.config import get_data_file_source
from app.utils.loaders import load_slope_histograms, load_terrain_metrics
from app.utils.terrain import (
    MATRIX_HEADER_BACKGROUND,
    MATRIX_HEADER_TEXT,
    MATRIX_ROW_HEADER_BACKGROUND,
    MATRIX_TEXT_COLOR,
    TERRAIN_SITES,
    band_text,
    build_resolution_panel,
    build_terrain_matrix,
    display_cell_value,
    load_terrain_band_config,
    site_summary_lines,
    split_matrix,
)


GRAVITY_STATEMENT = (
    "Results show relative terrain difficulty under normal Earth gravity, not absolute "
    "passability on Mars."
)

st.set_page_config(page_title="Terrain Comparison | TERRAOPS", layout="wide")
render_team_wordmark()
st.title("Terrain Comparison")
st.caption(
    "How to use this page: choose sites with available terrain data, then switch between their slope distributions and the share above a slope value. "
    "Use the table to inspect each measure; missing inputs remain unavailable."
)
source = get_data_file_source("terrain_metrics.csv")
render_page_banner(GRAVITY_STATEMENT, {"terrain_metrics.csv": source})
st.write(
    "How steep and rough the terrain of each candidate Earth site is, "
    "measured from open terrain data."
)


def _plain(text: str) -> str:
    return text.replace(" (unit unconfirmed)", "")


def _table_html(rows: list[dict], site_ids: list[str]) -> str:
    """Colours use CSS classes because Streamlit strips inline style attributes."""
    labels = dict(TERRAIN_SITES)
    headers = "".join(
        f"<th scope='col' class='terrain-head'>{html.escape(labels[site_id])}</th>"
        for site_id in site_ids
    )
    colors: set[str] = set()
    body = []
    for metric in rows:
        cells = [f"<th scope='row' class='terrain-rowhead'>{html.escape(_plain(metric['label']))}</th>"]
        for site_id in site_ids:
            cell = metric["cells"][site_id]
            colors.add(cell["color"])
            color_class = f"bg-{cell['color'].removeprefix('#')}"
            if cell["tier"] == "not available":
                cells.append(f"<td class='{color_class}'>—</td>")
                continue
            value = html.escape(display_cell_value(metric["metric_name"], cell))
            band = html.escape(band_text(cell))
            band_html = f"<div class='terrain-band'>{band}</div>" if band else ""
            cells.append(
                f"<td class='{color_class}'><div class='terrain-value'>{value}</div>{band_html}</td>"
            )
        body.append("<tr>" + "".join(cells) + "</tr>")
    color_rules = "".join(
        f".terrain-matrix td.bg-{color.removeprefix('#')}"
        f"{{background-color:{color} !important;color:{MATRIX_TEXT_COLOR} !important;}}"
        for color in sorted(colors)
    )
    return (
        "<style>"
        ".terrain-matrix-wrap{overflow-x:auto;width:100%;}"
        ".terrain-matrix{border-collapse:collapse;width:100%;}"
        ".terrain-matrix th,.terrain-matrix td{border:1px solid #73818a;padding:10px;"
        "text-align:left;vertical-align:top;}"
        ".terrain-matrix thead th{font-weight:700;}"
        f".terrain-matrix th.terrain-head{{background-color:{MATRIX_HEADER_BACKGROUND} !important;"
        f"color:{MATRIX_HEADER_TEXT} !important;}}"
        f".terrain-matrix th.terrain-rowhead{{background-color:{MATRIX_ROW_HEADER_BACKGROUND} !important;"
        f"color:{MATRIX_TEXT_COLOR} !important;}}"
        ".terrain-value{font-size:1rem;font-weight:650;margin-bottom:3px;}"
        ".terrain-band{font-weight:500;}"
        f"{color_rules}"
        "</style>"
        "<div class='terrain-matrix-wrap'><table class='terrain-matrix'>"
        f"<thead><tr><th scope='col' class='terrain-head'>Measure</th>{headers}</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )


def _draft_band_descriptions(band_config: dict) -> list[str]:
    definition = band_config.get("metrics", {}).get("pct_area_slope_gt24", {})
    unit = str(definition.get("unit", ""))
    descriptions = []
    for band in definition.get("bands", []):
        label = str(band.get("label", "")).capitalize()
        lower = band.get("lower")
        upper = band.get("upper")
        lower_symbol = "≥" if band.get("lower_inclusive", True) else ">"
        if lower is None and upper is not None:
            expression = f"< {upper:g}{unit}"
        elif lower is not None and upper is None:
            expression = f"{lower_symbol} {lower:g}{unit}"
        elif lower is not None and upper is not None:
            expression = f"{lower:g}–{upper:g}{unit}"
        else:
            expression = "threshold unavailable"
        if label:
            descriptions.append(f"{label}: {expression}")
    return descriptions


if source == "missing":
    st.info("Terrain comparison cannot be shown yet.")
    st.stop()

try:
    terrain = load_terrain_metrics()
    band_config = load_terrain_band_config()
    full_matrix = build_terrain_matrix(terrain, band_config)
    site_labels = dict(TERRAIN_SITES)
    histograms = load_slope_histograms()
    available_histogram_sites = set(histograms["site_id"].astype(str)) if not histograms.empty else set()
    valued_metrics = terrain["value"].notna() & terrain["tier"].astype("string").fillna("").str.strip().ne("")
    available_metric_sites = set(terrain.loc[valued_metrics, "site_id"].astype(str))
    site_options = [
        site_id for site_id, _ in TERRAIN_SITES
        if site_id in available_histogram_sites and site_id in available_metric_sites
    ]
    usable_site_ids = set(site_options)
    selected_sites = st.multiselect(
        "Sites to compare",
        options=site_options,
        default=site_options,
        format_func=lambda site_id: site_labels[site_id],
        help="Only sites with usable terrain measurements are listed.",
    )
    matrix = [
        {**metric, "cells": {site_id: metric["cells"][site_id] for site_id in selected_sites}}
        for metric in full_matrix
    ]
    visible_rows, _, site_ids = split_matrix(matrix)
except Exception as error:
    st.error(f"Could not build the terrain comparison: {error}")
    st.stop()

histograms = histograms.loc[histograms["site_id"].astype(str).isin(selected_sites)]
if not histograms.empty:
    st.subheader("Slope distribution")
    chart_mode = st.radio(
        "Slope chart",
        options=("Distribution", "Share steeper than"),
        horizontal=True,
        label_visibility="collapsed",
    )
    figure = terrain_slope_distribution_chart(histograms, mode=chart_mode)
    st.plotly_chart(figure, width="stretch")
    st.caption(
        "Distribution shows the share of valid pixels in each slope bin; Share steeper than accumulates bins at or above each x value. "
        "Vertical markers label the 10, 17, and 24 slope-value cutoffs."
    )
    maximum_bin = pd.to_numeric(histograms["bin_end"], errors="coerce").max()
    if pd.notna(maximum_bin):
        threshold = st.slider(
            "Slope threshold",
            min_value=0,
            max_value=max(0, int(maximum_bin)),
            value=0,
            step=1,
        )
        threshold_rows = []
        for site_id, group in histograms.groupby("site_id", sort=False):
            share = pd.to_numeric(group["share"], errors="coerce")
            bin_start = pd.to_numeric(group["bin_start"], errors="coerce")
            valid = share.notna() & bin_start.notna()
            if not valid.any():
                threshold_rows.append({"Site": site_labels.get(site_id, str(site_id)), "Share at/above threshold": "not computed"})
                continue
            area_share = float(share.loc[valid & bin_start.ge(threshold)].sum()) * 100
            threshold_rows.append(
                {"Site": site_labels.get(site_id, str(site_id)), "Share at/above threshold": f"{area_share:.2f}%"}
            )
        st.dataframe(pd.DataFrame(threshold_rows), hide_index=True, width="stretch")
        st.caption("Shares are approximate because slopes are grouped in steps of 1.")
elif selected_sites:
    st.info("No slope histogram values are available for the selected sites.")

if visible_rows:
    st.subheader("Comparison")
    st.markdown(_table_html(visible_rows, site_ids), unsafe_allow_html=True)
    csv_rows = []
    for metric in visible_rows:
        record = {"Measure": metric["label"]}
        for site_id in site_ids:
            cell = metric["cells"][site_id]
            if cell["tier"] == "not available" or cell["value"] == "data pending":
                value = None
            elif cell["number"] is not None:
                value = cell["number"]
            else:
                value = cell["value"]
            record[site_labels[site_id]] = value
        csv_rows.append(record)
    csv_table = pd.DataFrame(csv_rows)
    st.download_button(
        "Download comparison table",
        data=csv_table.to_csv(index=False, na_rep=""),
        file_name="terraops_terrain_comparison.csv",
        mime="text/csv",
    )
    st.caption(
        "Each cell reports a measure for that site; a dash marks a missing measurement. Color bands are draft v0.1."
    )
    st.caption(
        f"Bands ({band_config['status']}), based on the configured share of area above the slope cutoff: "
        + "; ".join(_draft_band_descriptions(band_config))
        + ". They describe constraint bands, not site suitability."
    )
else:
    st.write("Select at least one site with usable terrain measurements to show a comparison.")

summary_lines = site_summary_lines(matrix, site_ids)
if summary_lines:
    st.subheader("In plain terms")
    for line in summary_lines:
        st.write(line)

tiers_shown = ", ".join(
    sorted(
        {
            cell["tier"]
            for metric in visible_rows
            for cell in metric["cells"].values()
            if cell["tier"] != "not available"
        }
    )
) or "none"

with st.expander("About these results"):
    st.markdown(
        "**What the values cover.** Earth gravity is about 2.6 times Mars. Values summarize the "
        "whole terrain footprint, not a validated site boundary. This is a comparison aid, "
        "not a prediction of mission success; no composite score or ranking is calculated."
    )
    st.markdown(
        f"**Draft bands.** {band_config['status']}. For the configured share of area above the slope cutoff: "
        + "; ".join(_draft_band_descriptions(band_config))
        + ". These are comparison bands, not a site ranking."
    )
    st.markdown(
        "**Tiers.** Tier A: measurable at rover scale (about 2 m or finer terrain data). "
        "Tier B: coarse proxy (about 30 m terrain data; cannot resolve rover-scale features). "
        "Tiers describe what can be measured, not how suitable a site is. "
        f"Tier of the values shown: {tiers_shown}."
    )
    st.markdown(
        "The slope unit has not been confirmed with the data provider, so the cutoffs are provisional."
    )
    st.markdown(
        "**Bands.** Colour bands exist only for measures with a draft threshold; other cells show "
        "the value alone. Roughness has no thresholds, so its values are for ordering only. "
        "Missing measurements remain blank."
    )
    excluded_sites = [
        label for site_id, label in TERRAIN_SITES
        if site_id not in usable_site_ids
    ]
    if excluded_sites:
        excluded_text = " and ".join(excluded_sites)
        st.markdown(
            f"{excluded_text} are not part of this comparison because no usable terrain data is available for them yet."
        )
    roughness_rows = terrain.loc[
        (terrain["metric_name"] == "roughness") & terrain["value"].notna()
    ]
    for _, row in roughness_rows.iterrows():
        method = row.get("roughness_metric")
        window = row.get("roughness_window")
        st.markdown(
            f"- {str(row['site_id']).title()}: method "
            f"{'not documented' if pd.isna(method) else method}, window "
            f"{'not documented' if pd.isna(window) else window}"
        )
    site_labels = {label for site_id, label in TERRAIN_SITES if site_id in site_ids}
    resolution_rows = [
        row
        for row in build_resolution_panel(terrain, float(band_config["baseline_m"]))
        if row["site_id"] in site_labels
    ]
    if resolution_rows:
        st.markdown("**Resolution and common baseline**")
        resolution = pd.DataFrame(resolution_rows).rename(
            columns={
                "site_id": "Site",
                "native_resolution_m": "Native resolution",
                "baseline_m": "Common baseline",
                "dem_source": "Terrain source",
                "status": "Status",
            }
        )
        st.dataframe(resolution, hide_index=True, width="stretch")
        st.caption("This table shows map resolution and whether its values were adjusted to the common baseline.")
        st.markdown(
            "Raster values were computed at native resolution, not resampled to the "
            f"{band_config['baseline_m']:g} m common baseline, so they are not "
            "baseline-normalized comparisons."
        )

render_next_step("pages/4_When_to_Test.py", "Next step: When to Test")
