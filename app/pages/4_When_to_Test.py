# Streamlit's script runner may omit the repository root from sys.path.
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.site_profile import render_next_step, render_page_banner
from app.utils.config import DATA_ROOT, get_data_file_source
from app.utils.loaders import (
    load_daily_surface_temperature_matches,
    load_mars_temperature_envelope,
    load_sites,
    load_temperature_monthly,
)
from app.utils.when_to_test import (
    MONTH_NAMES,
    annotate_low_data,
    months_covered,
    range_gap_to_envelope,
    short_coverage_message,
    variable_type_mismatch,
)
from app.utils.location import build_location_consistency


VARIABLE_LABELS = {"surface_temp": "surface temperature", "air_temp": "air temperature"}


def _label(variable_type: str) -> str:
    return VARIABLE_LABELS.get(variable_type, variable_type.replace("_", " "))


def _number(value: object) -> str:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return "not available" if pd.isna(number) else f"{float(number):.1f}"


def _local_time_basis() -> str:
    source_path = DATA_ROOT / "raw" / "package" / "TERRAOPS_TEMPERATURE_ANALYSIS_FINAL_DOCUMENTATION.md"
    if not source_path.is_file():
        return "not stated in the source documentation"
    lines = source_path.read_text(encoding="utf-8").splitlines()
    statements = [line.strip() for line in lines if "local-time observations are grouped" in line.casefold()]
    return " ".join(statements) if statements else "not stated in the source documentation"


def _temperature_coordinate_caption(sites: pd.DataFrame, selected_site_ids: list[str]) -> str | None:
    locations = build_location_consistency(sites)
    labels_by_site = {
        str(site_id): str(name).split(",", maxsplit=1)[0].casefold()
        for site_id, name in zip(sites["site_id"], sites["name"])
    }
    for _, row in locations.loc[
        locations["Location source"].astype(str).str.startswith("MODIS analysis coordinate")
    ].iterrows():
        site_id = next(
            (key for key, label in labels_by_site.items()
             if label == str(row["Site"]).casefold() and key in selected_site_ids),
            None,
        )
        distance = pd.to_numeric(
            pd.Series([row["Distance from terrain centroid (km)"]]), errors="coerce"
        ).iloc[0]
        threshold = re.search(
            r"(?:more than|within)\s+([\d.]+)\s*km",
            str(row["Finding"]),
            flags=re.IGNORECASE,
        )
        if site_id and pd.notna(distance) and threshold and float(distance) > float(threshold.group(1)):
            return (
                f"{row['Site']} temperature values come from a point "
                f"{float(distance):.1f} km from its terrain footprint."
            )
    return None


st.set_page_config(page_title="When to Test | TERRAOPS", layout="wide")
st.title("When to Test")
st.caption(
    "How to use this page: select a Mars season and Earth day or night surface readings. "
    "Compare the Earth temperature ranges with the Mars bands and review the daily match counts."
)
input_sources = {
    filename: get_data_file_source(filename)
    for filename in ("sites.geojson", "temperature_monthly.csv", "mars_temperature_envelope.json")
}
render_page_banner(None, input_sources)

try:
    sites = load_sites()
    temperatures = load_temperature_monthly()
    envelope = load_mars_temperature_envelope()
except Exception as error:
    st.error(f"Could not load temperature-window data: {error}")
    st.stop()

seasonal_envelopes = envelope.get("seasonal_envelopes", [])
st.subheader("Mars seasonal surface-temperature bands")
bands_table = pd.DataFrame(
    [
        {
            "Season": band.get("season", "not available"),
            "Measurement": band.get("mars_variable", "not specified"),
            "Minimum (°C)": _number(band.get("min_c")),
            "Maximum (°C)": _number(band.get("max_c")),
        }
        for band in seasonal_envelopes
    ]
)
st.dataframe(bands_table, hide_index=True, width="stretch")
st.caption("Each row is a separate Mars seasonal reference range; these bands are not collapsed into one annual range.")
st.caption(f"Local-time basis: {_local_time_basis()}")

ls_mapping = envelope.get("solar_longitude_mapping")
if isinstance(ls_mapping, dict):
    st.caption(
        "Official Ls mapping covers "
        f"{float(ls_mapping['coverage_percent']):.1f}% "
        f"({int(ls_mapping['mapped_ats_sols']):,} of {int(ls_mapping['total_ats_sols']):,} ATS sols). "
        "This is Ls mapping coverage, not the share of temperature observations analysed."
    )

earth_sites = sites.loc[sites["body"] == "Earth"].copy()
site_names = dict(zip(earth_sites["site_id"].astype(str), earth_sites["name"].astype(str)))
surface_rows = temperatures.loc[temperatures["variable_type"].astype(str) == "surface_temp"].copy()
air_rows = temperatures.loc[temperatures["variable_type"].astype(str) == "air_temp"].copy()
surface_site_ids = [
    site_id for site_id in earth_sites["site_id"].astype(str).tolist()
    if (surface_rows["site_id"].astype(str) == site_id).any()
]
selected_site_ids = st.multiselect(
    "Earth sites",
    options=surface_site_ids,
    default=surface_site_ids,
    format_func=lambda site_id: f"{site_names[site_id]} ({site_id})",
)
season_options = ["All", *[str(band.get("season", "")) for band in seasonal_envelopes]]
season_selection = st.radio("Mars season", season_options, horizontal=True)
period_selection = st.radio(
    "Earth surface period", ("Both", "Daytime", "Nighttime"), horizontal=True
)
period_lookup = {"Daytime": "day", "Nighttime": "night"}
allowed_periods = {period_lookup[period_selection]} if period_selection in period_lookup else {"day", "night"}
selected_bands = (
    seasonal_envelopes
    if season_selection == "All"
    else [band for band in seasonal_envelopes if str(band.get("season")) == season_selection]
)

selected_surface = surface_rows.loc[
    surface_rows["site_id"].astype(str).isin(selected_site_ids)
    & surface_rows["period_of_day"].astype(str).isin(allowed_periods)
].copy()
selected_surface = annotate_low_data(selected_surface)

coverage_messages: dict[str, list[str]] = {}
for site_id in selected_site_ids:
    site_rows = surface_rows.loc[surface_rows["site_id"].astype(str) == site_id]
    message = short_coverage_message(site_rows)
    if message:
        coverage_messages.setdefault(message, []).append(site_names.get(site_id, site_id))
for message, names in coverage_messages.items():
    st.info(message if len(coverage_messages) == 1 else f"{', '.join(names)}: {message}")

mars_types = {
    str(band.get("variable_type", envelope.get("variable_type", "surface_temp")))
    for band in seasonal_envelopes
}
if selected_surface.empty:
    st.info("No Earth surface-temperature values are available for the selected filters.")
else:
    figure = go.Figure()
    band_colors = ("rgba(59,130,246,0.12)", "rgba(245,158,11,0.13)", "rgba(168,85,247,0.12)", "rgba(20,184,166,0.12)")
    for index, band in enumerate(selected_bands):
        low = pd.to_numeric(pd.Series([band.get("min_c")]), errors="coerce").iloc[0]
        high = pd.to_numeric(pd.Series([band.get("max_c")]), errors="coerce").iloc[0]
        if pd.notna(low) and pd.notna(high):
            figure.add_hrect(
                y0=float(low), y1=float(high),
                fillcolor=band_colors[index % len(band_colors)],
                line_width=0,
                annotation_text=str(band.get("season", "")),
                annotation_position="top left",
                layer="below",
            )
            figure.add_trace(
                go.Scatter(
                    x=[None], y=[None], mode="lines",
                    line={"color": band_colors[index % len(band_colors)].replace("0.12)", "0.8)").replace("0.13)", "0.8)")},
                    name=str(band.get("season", "Mars band")),
                )
            )

    range_records = []
    for row in selected_surface.itertuples(index=False):
        low = pd.to_numeric(pd.Series([row.temp_min_c]), errors="coerce").iloc[0]
        mean = pd.to_numeric(pd.Series([row.temp_mean_c]), errors="coerce").iloc[0]
        high = pd.to_numeric(pd.Series([row.temp_max_c]), errors="coerce").iloc[0]
        if pd.isna(low) or pd.isna(high):
            continue
        site_id = str(row.site_id)
        period = str(row.period_of_day)
        category = f"{site_names.get(site_id, site_id)} · {period}"
        color = "#c2410c" if period == "day" else "#0369a1"
        custom = [site_names.get(site_id, site_id), period, row.n_valid_obs]
        figure.add_trace(
            go.Scatter(
                x=[category, category], y=[float(low), float(high)], mode="lines+markers",
                line={"color": color, "width": 4}, marker={"size": 8, "color": color},
                name=f"{site_names.get(site_id, site_id)} {period}", showlegend=False,
                customdata=[custom, custom],
                hovertemplate="%{customdata[0]} · %{customdata[1]}<br>Range endpoint: %{y:.1f} °C<br>Valid observations: %{customdata[2]}<extra></extra>",
            )
        )
        if pd.notna(mean):
            figure.add_trace(
                go.Scatter(
                    x=[category], y=[float(mean)], mode="markers",
                    marker={"color": color, "symbol": "diamond", "size": 11},
                    name=f"{site_names.get(site_id, site_id)} {period} mean",
                    customdata=[custom],
                    hovertemplate="%{customdata[0]} · %{customdata[1]}<br>Mean: %{y:.1f} °C<br>Valid observations: %{customdata[2]}<extra></extra>",
                )
            )
        range_records.append(row._asdict())

    figure.update_layout(
        height=500,
        xaxis_title="Earth site and period",
        yaxis_title="Surface temperature (°C)",
        legend_title="Mars seasonal band / Earth range",
        hovermode="closest",
        margin={"t": 55, "b": 100},
    )
    figure.update_xaxes(tickangle=-25)
    st.plotly_chart(figure, width="stretch")
    st.caption("Vertical marks show Earth minimum and maximum; diamonds mark the mean. Shaded horizontal bands show the selected Mars seasonal temperature ranges.")
    coordinate_caption = _temperature_coordinate_caption(sites, selected_site_ids)
    if coordinate_caption:
        st.caption(coordinate_caption)

    gap_rows = []
    for row in range_records:
        for band in selected_bands:
            earth_kind = "surface_temp"
            mars_kind = str(band.get("variable_type", envelope.get("variable_type", "surface_temp")))
            mismatch = variable_type_mismatch(
                site_names.get(str(row["site_id"]), str(row["site_id"])),
                earth_kind if earth_kind in mars_types else None,
                mars_kind,
            )
            if mismatch:
                gap, overlaps = None, None
            else:
                gap, overlaps = range_gap_to_envelope(
                    row["temp_min_c"], row["temp_max_c"], band.get("min_c"), band.get("max_c")
                )
            gap_rows.append(
                {
                    "Site": site_names.get(str(row["site_id"]), str(row["site_id"])),
                    "Period": "Daytime" if row["period_of_day"] == "day" else "Nighttime",
                    "Mars season": band.get("season", ""),
                    "Gap to nearest band edge (°C)": "not computed" if gap is None else f"{gap:.1f}",
                    "Overlap": "not assessed" if overlaps is None else "Yes" if overlaps else "No",
                }
            )
    gap_table = pd.DataFrame(gap_rows)
    if not gap_table.empty:
        st.dataframe(gap_table, hide_index=True, width="stretch")
        st.caption("The gap is the temperature distance from the Earth range to the nearest edge of that Mars band; zero means the ranges overlap.")

daily_matches = load_daily_surface_temperature_matches(DATA_ROOT / "processed")
if not daily_matches.empty:
    daily_visible = daily_matches.loc[
        daily_matches["site_id"].astype(str).isin(selected_site_ids)
        & daily_matches["period_of_day"].astype(str).isin(allowed_periods)
    ].copy()
    if season_selection != "All":
        daily_visible = daily_visible.loc[daily_visible["season"].astype(str) == season_selection]
    if not daily_visible.empty:
        daily_visible["Site"] = daily_visible["site_id"].map(site_names).fillna(daily_visible["site_id"])
        daily_visible["Period"] = daily_visible["period_of_day"].map({"day": "Daytime", "night": "Nighttime"})
        daily_visible["Share inside Mars band"] = daily_visible["share_in_band_pct"].map(
            lambda value: "not computed" if pd.isna(value) else f"{float(value):.1f}%"
        )
        daily_visible["Matching days"] = daily_visible["n_matching_days"].map(
            lambda value: "not computed" if pd.isna(value) else str(int(value))
        )
        daily_visible["Valid days"] = daily_visible["n_valid_days"].map(
            lambda value: "not computed" if pd.isna(value) else str(int(value))
        )
        display_daily = daily_visible[["Site", "Period", "season", "Share inside Mars band", "Matching days", "Valid days"]].rename(
            columns={"season": "Mars season"}
        )
        st.subheader("Daily Earth surface observations inside each Mars band")
        st.dataframe(display_daily, hide_index=True, width="stretch")
        st.caption("Shares use only valid daily MODIS surface values; zero percent is shown with its valid-day count, while missing calculations say not computed.")

visible_surface = selected_surface.copy()
if not visible_surface.empty:
    visible_surface["Period"] = visible_surface["period_of_day"].map({"day": "Daytime", "night": "Nighttime"})
    visible_surface["Quality"] = visible_surface["data_flag"].replace({"": "ok"})
    with st.expander("Surface temperature observations", expanded=False):
        surface_display = visible_surface[[
            "site_id", "Period", "temp_min_c", "temp_mean_c", "temp_max_c",
            "n_valid_obs", "n_missing_obs", "Quality",
        ]].rename(columns={
            "site_id": "Site ID", "temp_min_c": "Minimum (°C)", "temp_mean_c": "Mean (°C)",
            "temp_max_c": "Maximum (°C)", "n_valid_obs": "Valid observations",
            "n_missing_obs": "Missing observations",
        })
        st.dataframe(surface_display, hide_index=True, width="stretch")
        st.caption("These rows show each site's day/night temperature range and observation counts.")

if not air_rows.empty:
    with st.expander("Air temperature (not compared with Mars surface temperature)", expanded=False):
        st.write("Air temperature and surface temperature are different measurement types, so these rows are not compared with the Mars surface bands.")
        visible_air = air_rows.loc[air_rows["site_id"].astype(str).isin(selected_site_ids)].copy()
        visible_air = visible_air.drop(
            columns=[column for column in ("source", "source_label") if column in visible_air]
        )
        st.dataframe(visible_air, hide_index=True, width="stretch")
        st.caption("These Earth air-temperature measurements are kept separate from surface temperatures.")

if not selected_surface.empty and selected_surface["data_flag"].eq("low data").any():
    st.caption("Low data means fewer than half of the expected observations are valid.")

render_next_step("pages/5_Analogy_Gap_Detector.py", "Next step: Analogy Gap Detector")
