import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.site_profile import render_page_banner
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
    collect_terrain_footnotes,
    display_cell_value,
    load_terrain_band_config,
    not_yet_included_line,
    site_summary_lines,
    split_matrix,
)


GRAVITY_STATEMENT = (
    "Results show relative terrain difficulty under normal Earth gravity, not absolute "
    "passability on Mars."
)

st.set_page_config(page_title="Terrain Comparison | TERRAOPS", layout="wide")
st.title("Terrain Comparison")
source = get_data_file_source("terrain_metrics.csv")
render_page_banner(GRAVITY_STATEMENT, {"terrain_metrics.csv": source})
st.write(
    "How steep and rough the terrain of each candidate Earth site is, "
    "measured from open terrain data."
)


def _plain(text: str) -> str:
    return text.replace(" (unit unconfirmed)", "")


def _slope_chart(histograms: pd.DataFrame) -> go.Figure:
    figure = go.Figure()
    for site_id, site_rows in histograms.groupby("site_id", sort=False):
        figure.add_trace(
            go.Bar(
                x=site_rows["bin_start"],
                y=site_rows["share"],
                width=1,
                name=str(site_id).title(),
                hovertemplate=(
                    "%{x:.0f} to %{customdata:.0f}"
                    "<br>Share of valid pixels: %{y:.2%}<extra>%{fullData.name}</extra>"
                ),
                customdata=site_rows["bin_end"],
            )
        )
    figure.update_layout(
        barmode="overlay",
        xaxis_title="Slope value (unit unconfirmed)",
        yaxis_title="Share of valid slope pixels",
        legend_title="Site",
    )
    for threshold in (10, 17, 24):
        figure.add_vline(
            x=threshold,
            line_dash="dash",
            line_color="#263746",
            annotation_text=str(threshold),
            annotation_position="top",
        )
    return figure


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
                cells.append(f"<td class='{color_class}'>not available</td>")
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


if source == "missing":
    st.info("Terrain data has not been loaded.")
    st.stop()

try:
    terrain = load_terrain_metrics()
    band_config = load_terrain_band_config()
    matrix = build_terrain_matrix(terrain, band_config)
    visible_rows, unmeasured_labels, site_ids = split_matrix(matrix)
    histograms = load_slope_histograms()
    footnotes, _, _ = collect_terrain_footnotes(matrix)
except Exception as error:
    st.error(f"Could not build the terrain comparison: {error}")
    st.stop()

if not histograms.empty:
    st.subheader("Slope distribution")
    st.plotly_chart(_slope_chart(histograms), width="stretch")

if visible_rows:
    st.subheader("Comparison")
    st.markdown(_table_html(visible_rows, site_ids), unsafe_allow_html=True)
    st.caption(
        "Bands are draft v0.1, pending engineering review, and the slope unit is not yet "
        "confirmed, so slope thresholds are provisional."
    )
else:
    st.write("No terrain values are available yet.")

missing_line = not_yet_included_line(terrain, matrix)
if missing_line:
    st.write(missing_line)

if unmeasured_labels:
    with st.expander("What we cannot measure yet"):
        st.write("Needs rover-scale data (about 2 m or finer):")
        for label in unmeasured_labels:
            st.write(f"- {label}")

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
        "whole supplied raster extent, not a validated site boundary. This is a comparison aid, "
        "not a prediction of mission success; no composite score or ranking is calculated."
    )
    st.markdown(
        "**Tiers.** Tier A: measurable at rover scale (about 2 m or finer terrain data). "
        "Tier B: coarse proxy (about 30 m terrain data; cannot resolve rover-scale features). "
        "Tiers describe what can be measured, not how suitable a site is. "
        f"Tier of the values shown: {tiers_shown}."
    )
    st.markdown(
        "**Slope unit.** The source notes give no unit for the slope rasters. The 90th-percentile "
        "values fall between each raster's reported mean and maximum, which is consistent with "
        "those statistics but does not confirm degrees. Degree-based thresholds stay provisional "
        "until the unit is confirmed."
    )
    st.markdown(
        "**Bands.** Colour bands exist only for measures with a draft threshold; other cells show "
        "the value alone. Roughness has no thresholds, so its values are for ordering only. "
        "Missing values are unavailable, not zero."
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
    if footnotes:
        st.markdown("**Source notes**")
        st.markdown("\n".join(f"{index}. {note}" for index, note in enumerate(footnotes, start=1)))
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
        st.markdown(
            "Raster values were computed at native resolution, not resampled to the "
            f"{band_config['baseline_m']:g} m common baseline, so they are not "
            "baseline-normalized comparisons."
        )
