import pandas as pd
import streamlit as st
from collections.abc import Mapping

from app.utils.loaders import load_terrain_metrics
from app.utils.terrain import TERRAIN_MATRIX_METRICS


def render_team_wordmark() -> None:
    """Add a pinned team wordmark above Streamlit's sidebar page navigation."""
    st.markdown(
        """<style>
        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"]::before {
            content: "COSMIC CATALYSTS";
            display: block;
            position: sticky;
            top: 0;
            z-index: 1000;
            padding: 1.1rem 0.8rem 1.2rem;
            margin-bottom: 0.35rem;
            background: #0E1117;
            border-bottom: 1px solid rgba(115, 221, 208, 0.24);
            color: #73ddd0;
            font-family: "Trebuchet MS", Arial, sans-serif;
            font-size: 0.76rem;
            font-weight: 600;
            letter-spacing: 0.18em;
            white-space: nowrap;
        }
        </style>""",
        unsafe_allow_html=True,
    )


def load_profile_terrain_metrics() -> pd.DataFrame:
    try:
        return load_terrain_metrics()
    except FileNotFoundError:
        return pd.DataFrame(
            columns=("site_id", "metric_name", "value", "tier", "metric_unit", "dem_source")
        )


def build_terrain_profile_table(site_terrain: pd.DataFrame) -> pd.DataFrame:
    records = []
    for metric_name, label, _ in TERRAIN_MATRIX_METRICS:
        rows = site_terrain.loc[site_terrain["metric_name"] == metric_name]
        row = rows.iloc[0] if not rows.empty else None
        value = None if row is None else row.get("value")
        tier = None if row is None else row.get("tier")
        unit = "" if row is None or pd.isna(row.get("metric_unit")) else str(row.get("metric_unit")).strip()
        if value is None or pd.isna(value) or tier is None or pd.isna(tier) or not str(tier).strip():
            display_value = "data pending"
            display_tier = "not available"
        elif metric_name == "material_class":
            display_value = str(value)
            display_tier = f"Tier {tier}"
        elif metric_name == "slope_p90_deg":
            display_value = f"{float(value):.2f}"
            display_tier = f"Tier {tier}"
        elif unit == "%":
            display_value = f"{float(value):.2f}%"
            display_tier = f"Tier {tier}"
        else:
            display_value = f"{float(value):.2f}{f' {unit}' if unit else ''}"
            display_tier = f"Tier {tier}"
        records.append({"Parameter": label, "Value": display_value, "Tier": display_tier})
    return pd.DataFrame(records, columns=("Parameter", "Value", "Tier"))


def render_page_banner(
    message: str | None = None, data_sources: str | Mapping[str, str] | None = None
) -> None:
    """Render at most one banner: sample-data warning (with the message) or the message alone."""
    if data_sources is None:
        sample_files = []
    elif isinstance(data_sources, str):
        sample_files = ["active data files"] if data_sources == "sample" else []
    else:
        sample_files = [name for name, source in data_sources.items() if source == "sample"]
    if sample_files:
        text = "PLACEHOLDER DATA: illustrative sample values are in use."
        st.warning(f"{text} {message}" if message else text, icon="\u26a0\ufe0f")
    elif message:
        st.info(message)


def render_next_step(page: str, label: str) -> None:
    """Use Streamlit navigation in the running app and remain renderable in isolated AppTests."""
    try:
        st.page_link(page, label=label, icon="➡️")
    except st.errors.StreamlitPageNotFoundError:
        st.markdown(f"[{label}](/{page})")


def _key_metrics(site_terrain: pd.DataFrame) -> list[tuple[str, str]]:
    metrics = []
    for metric_name, label, formatted in (
        ("pct_area_slope_gt24", "Area steeper than 24 degrees", "{:.1f}%"),
        ("pct_area_slope_gt17", "Area steeper than 17 degrees", "{:.1f}%"),
        ("slope_p90_deg", "Slope P90", "{:.1f}"),
    ):
        rows = site_terrain.loc[site_terrain["metric_name"] == metric_name]
        if rows.empty:
            continue
        value = pd.to_numeric(rows.iloc[0].get("value"), errors="coerce")
        tier = rows.iloc[0].get("tier")
        if pd.isna(value) or pd.isna(tier) or not str(tier).strip():
            continue
        metrics.append((label, formatted.format(float(value))))
    return metrics


def render_site_card(
    site: pd.Series,
    terrain_metrics: pd.DataFrame,
    temperatures: pd.DataFrame,
) -> None:
    """Short card: name, coordinates, up to three key metrics, data sources."""
    with st.container(border=True):
        st.subheader(str(site["name"]))
        latitude = pd.to_numeric(pd.Series([site.get("lat")]), errors="coerce").iloc[0]
        longitude = pd.to_numeric(pd.Series([site.get("lon")]), errors="coerce").iloc[0]
        if pd.notna(latitude) and pd.notna(longitude):
            st.write(f"Coordinates: {float(latitude):.4f}\u00b0, {float(longitude):.4f}\u00b0")
        else:
            st.write("Coordinates are not available.")
        notes = site.get("notes")
        if pd.notna(notes) and str(notes).strip():
            note_text = str(notes).strip()
            st.caption(note_text[0].upper() + note_text[1:])

        site_terrain = terrain_metrics.loc[terrain_metrics["site_id"] == site["site_id"]]
        valued_terrain = site_terrain.loc[
            site_terrain["value"].notna()
            & site_terrain["tier"].astype("string").fillna("").str.strip().ne("")
        ]
        if valued_terrain.empty:
            notes = (
                site_terrain["availability_note"].dropna().astype(str).str.strip()
                if "availability_note" in site_terrain
                else pd.Series(dtype=str)
            )
            reason = notes[notes.ne("")].iloc[0] if not notes[notes.ne("")].empty else "source data is unavailable"
            for prefix in ("Terrain metrics pending CRS review:", "Terrain metrics pending:"):
                reason = reason.removeprefix(prefix).strip()
            st.write(f"Terrain measurements are not available yet: {reason}")

        key_metrics = _key_metrics(site_terrain)
        if key_metrics:
            for column, (label, value) in zip(st.columns(len(key_metrics)), key_metrics):
                column.metric(label, value)
            st.caption("Slope cutoffs are provisional because the measurement unit is not yet confirmed.")

        sources = []
        if not valued_terrain.empty:
            sources.extend(
                str(value) for value in valued_terrain["dem_source"].dropna().unique() if str(value).strip()
            )
        site_temperatures = temperatures.loc[temperatures["site_id"] == site["site_id"]]
        if not site_temperatures.empty:
            sources.extend(
                str(value) for value in site_temperatures["source"].dropna().unique() if str(value).strip()
            )
        if sources:
            names = [source.rsplit("/", 1)[-1] for source in sources]
            st.caption("Data sources: " + "; ".join(dict.fromkeys(names)))
        low_modis_rows = site_temperatures.loc[
            (site_temperatures["variable_type"] == "surface_temp")
            & site_temperatures["period_of_day"].isin({"day", "night"})
        ]
        for _, row in low_modis_rows.iterrows():
            valid = pd.to_numeric(pd.Series([row["n_valid_obs"]]), errors="coerce").iloc[0]
            missing = pd.to_numeric(pd.Series([row["n_missing_obs"]]), errors="coerce").iloc[0]
            expected = valid + missing
            if pd.notna(expected) and expected > 0 and valid < expected / 2:
                period = "daytime" if row["period_of_day"] == "day" else "nighttime"
                st.caption(
                    f"Low data: MODIS {period}, {int(valid)} of {int(expected)} valid July days."
                )
