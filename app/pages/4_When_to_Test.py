import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.site_profile import render_page_banner
from app.utils.config import get_data_file_source
from app.utils.loaders import (
    load_mars_temperature_envelope,
    load_sites,
    load_temperature_monthly,
)
from app.utils.when_to_test import (
    MONTH_NAMES,
    annotate_low_data,
    months_covered,
    short_coverage_message,
    variable_type_mismatch,
)


VARIABLE_LABELS = {"surface_temp": "surface temperature", "air_temp": "air temperature"}


def _label(variable_type: str) -> str:
    return VARIABLE_LABELS.get(variable_type, variable_type.replace("_", " "))


def _month_label(row: pd.Series) -> str:
    month = pd.to_numeric(row["month"], errors="coerce")
    if pd.isna(month) or not 1 <= int(month) <= 12:
        return "not available"
    year = pd.to_datetime(row.get("period_start"), errors="coerce")
    name = MONTH_NAMES[int(month) - 1]
    return name if pd.isna(year) else f"{name} {year.year}"


def _number(value: object) -> str:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return "not available" if pd.isna(number) else f"{float(number):.1f}"


st.set_page_config(page_title="When to Test | TERRAOPS", layout="wide")
st.title("When to Test")

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
if len(seasonal_envelopes) != 4:
    st.error(f"Expected four seasonal Mars bands; found {len(seasonal_envelopes)}.")

mars_types = {
    str(band.get("variable_type", envelope.get("variable_type", "")))
    for band in seasonal_envelopes
}
st.subheader("Mars seasonal temperature bands")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Season": band.get("season", "not available"),
                "Measurement": band.get("mars_variable", "not specified"),
                "Min (°C)": _number(band.get("min_c")),
                "Max (°C)": _number(band.get("max_c")),
            }
            for band in seasonal_envelopes
        ]
    ),
    hide_index=True,
    width="stretch",
)
band_kind = ", ".join(sorted(_label(kind) for kind in mars_types if kind))
st.caption(f"Mars bands are {band_kind}." if band_kind else "Mars band type is not stated.")
ls_mapping = envelope.get("solar_longitude_mapping")
if isinstance(ls_mapping, dict):
    st.caption(
        "Official Ls mapping covers "
        f"{float(ls_mapping['coverage_percent']):.1f}% "
        f"({int(ls_mapping['mapped_ats_sols']):,} of {int(ls_mapping['total_ats_sols']):,} ATS sols). "
        "This is Ls mapping coverage, not the share of temperature observations analysed."
    )

earth_sites = sites.loc[sites["body"] == "Earth"].copy()
earth_site_ids = earth_sites["site_id"].astype(str).tolist()
site_names = dict(zip(earth_sites["site_id"].astype(str), earth_sites["name"].astype(str)))
selected_site_ids = st.multiselect(
    "Earth sites",
    options=earth_site_ids,
    default=earth_site_ids,
    format_func=lambda site_id: f"{site_names[site_id]} ({site_id})",
)

selected_rows = {
    site_id: temperatures.loc[temperatures["site_id"].astype(str) == site_id].copy()
    for site_id in selected_site_ids
}
sites_with_data = [site_id for site_id, rows in selected_rows.items() if not rows.empty]
sites_without_data = [site_id for site_id, rows in selected_rows.items() if rows.empty]

if sites_with_data:
    st.subheader("Earth temperature observations")
    table_rows = []
    for site_id in sites_with_data:
        flagged = annotate_low_data(selected_rows[site_id])
        for _, row in flagged.iterrows():
            table_rows.append(
                {
                    "Site": site_names.get(site_id, site_id),
                    "Source label": row["source_label"] or site_names.get(site_id, site_id),
                    "Month": _month_label(row),
                    "Period": {
                        "daily": "Daily",
                        "day": "Daytime",
                        "night": "Nighttime",
                    }.get(row["period_of_day"], "Not specified"),
                    "Temperature type": _label(str(row["variable_type"])),
                    "Min (°C)": _number(row["temp_min_c"]),
                    "Mean (°C)": _number(row["temp_mean_c"]),
                    "Max (°C)": _number(row["temp_max_c"]),
                    "Valid observations": row["n_valid_obs"],
                    "Missing observations": row["n_missing_obs"],
                    "Data quality": row["data_flag"] or "ok",
                }
            )
    table = pd.DataFrame(table_rows)
    st.dataframe(table, hide_index=True, width="stretch")
    if (table["Data quality"] == "low data").any():
        st.caption("Low data means fewer than half of the expected observations are valid.")

    coverage: dict[str, list[str]] = {}
    for site_id in sites_with_data:
        message = short_coverage_message(selected_rows[site_id])
        if message:
            coverage.setdefault(message, []).append(site_names.get(site_id, site_id))
    for message, names in coverage.items():
        st.markdown(message if len(coverage) == 1 else f"{', '.join(names)}: {message}")

blocked_messages: dict[str, list[str]] = {}
compatible_site_ids = []
match_percentage_displayed = False
for site_id in sites_with_data:
    site_name = site_names.get(site_id, site_id)
    earth_types = sorted(selected_rows[site_id]["variable_type"].dropna().astype(str).unique())
    messages = []
    for earth_type in earth_types:
        for mars_type in sorted(mars_types):
            message = variable_type_mismatch(site_name, _label(earth_type), _label(mars_type))
            if message and message not in messages:
                messages.append(message)
    if messages:
        blocked_messages[site_id] = messages
    else:
        compatible_site_ids.append(site_id)

eligible_site_ids = []
partial_site_ids = []
for site_id in compatible_site_ids:
    site_rows = selected_rows[site_id]
    full_year = set(months_covered(site_rows)) == set(range(1, 13)) and not (
        site_rows.groupby("month", dropna=False).size().ne(1).any()
    )
    (eligible_site_ids if full_year else partial_site_ids).append(site_id)

if partial_site_ids:
    partial_rows = []
    for site_id in partial_site_ids:
        for _, row in selected_rows[site_id].iterrows():
            share = pd.to_numeric(pd.Series([row["pct_in_envelope"]]), errors="coerce").iloc[0]
            if pd.notna(share):
                match_percentage_displayed = True
                partial_rows.append(
                    {
                        "Site": site_names.get(site_id, site_id),
                        "Month": _month_label(row),
                        "Share of observations in the supplied Mars band (%)": f"{float(share):.1f}",
                    }
                )
    if partial_rows:
        st.subheader("Comparison with Mars bands")
        st.dataframe(pd.DataFrame(partial_rows), hide_index=True, width="stretch")

if eligible_site_ids:
    chart_rows = annotate_low_data(
        temperatures.loc[temperatures["site_id"].astype(str).isin(eligible_site_ids)].copy()
    )
    match_percentage_displayed = match_percentage_displayed or chart_rows["pct_in_envelope"].notna().any()
    st.subheader("Monthly comparison with Mars bands")
    st.caption(
        "Values are the supplied share of observations inside the Mars band, with missing values "
        "left blank. They are not attributed to a specific Mars season because the data has no "
        "season key."
    )

    bar_figure = go.Figure()
    heatmap_values = []
    heatmap_labels = []
    month_labels = list(MONTH_NAMES)
    for site_id in eligible_site_ids:
        site_rows = chart_rows.loc[chart_rows["site_id"].astype(str) == site_id].set_index("month")
        values = []
        custom_data = []
        for month in range(1, 13):
            row = site_rows.loc[month]
            pct = pd.to_numeric(pd.Series([row["pct_in_envelope"]]), errors="coerce").iloc[0]
            values.append(None if pd.isna(pct) else float(pct))
            custom_data.append([row["n_valid_obs"], row["n_missing_obs"], row["data_flag"] or ""])
        bar_figure.add_trace(
            go.Bar(
                x=month_labels,
                y=values,
                name=site_names.get(site_id, site_id),
                customdata=custom_data,
                hovertemplate=(
                    "%{x}<br>Share in band: %{y}%<br>Valid: %{customdata[0]}"
                    "<br>Missing: %{customdata[1]}<br>%{customdata[2]}<extra></extra>"
                ),
            )
        )
        heatmap_values.append(values)
        heatmap_labels.append(site_names.get(site_id, site_id))
    bar_figure.update_layout(
        barmode="group",
        xaxis_title="Earth calendar month",
        yaxis_title="Share of observations in the Mars band (%)",
        yaxis=dict(range=[0, 100]),
        legend_title="Earth site",
    )
    st.plotly_chart(bar_figure, width="stretch")

    heatmap = go.Figure(
        data=go.Heatmap(
            z=heatmap_values,
            x=month_labels,
            y=heatmap_labels,
            zmin=0,
            zmax=100,
            colorscale="YlGnBu",
            colorbar_title="Percent",
            connectgaps=False,
            hoverongaps=False,
        )
    )
    heatmap.update_layout(xaxis_title="Earth calendar month", yaxis_title="Earth site")
    st.plotly_chart(heatmap, width="stretch")

    st.subheader("Best months by supplied percentage")
    for site_id in eligible_site_ids:
        site_rows = chart_rows.loc[chart_rows["site_id"].astype(str) == site_id].copy()
        percentages = pd.to_numeric(site_rows["pct_in_envelope"], errors="coerce")
        available_percentages = percentages.dropna()
        if available_percentages.empty:
            st.write(
                f"{site_names.get(site_id, site_id)}: the supplied share is missing for all "
                "months; no best month can be identified."
            )
            continue
        best_percentage = available_percentages.max()
        for _, row in site_rows.loc[percentages == best_percentage].iterrows():
            month_number = int(row["month"])
            period = f"{row['period_start']} to {row['period_end']}"
            flag = "; low data" if row["data_flag"] == "low data" else ""
            st.write(
                f"{site_names.get(site_id, site_id)}: {MONTH_NAMES[month_number - 1]} "
                f"({period}), {best_percentage:g}% of observations in the supplied Mars band; "
                f"{row['n_valid_obs']} valid observations{flag}. This is a best month, not a "
                "Mars-season recommendation."
            )

if blocked_messages or sites_without_data:
    with st.expander("Why some comparisons are not shown"):
        for site_id, messages in blocked_messages.items():
            st.write(" ".join(messages))
        for site_id in sites_without_data:
            st.write(f"{site_names.get(site_id, site_id)}: no Earth temperature observations are loaded.")
        st.write(
            "Each Mars season is a separate band, and the monthly data has no season key, so a "
            "supplied percentage cannot be assigned to one season."
        )

if match_percentage_displayed:
    st.caption(
        "A high match percentage does not prove thermal equivalence. Mars seasons are defined "
        "by solar longitude (Ls) and are not mapped to Earth calendar months."
    )
