import pandas as pd
import streamlit as st


def render_placeholder_banner(data_source: str) -> None:
    if data_source == "sample":
        st.warning(
            "PLACEHOLDER DATA: values shown by this app are illustrative only.",
            icon="⚠️",
        )


def render_site_profile(
    site: pd.Series,
    terrain: pd.DataFrame,
    temperatures: pd.DataFrame,
    catalogue: pd.DataFrame,
) -> None:
    with st.container(border=True):
        st.subheader(str(site["name"]))
        first, second = st.columns(2)
        first.metric("Latitude", f"{float(site['lat']):.4f}°")
        second.metric("Longitude", f"{float(site['lon']):.4f}°")
        st.caption(f"Body: {site['body']}")
        notes = site.get("notes")
        st.write(str(notes) if pd.notna(notes) and str(notes).strip() else "No site notes provided.")

        site_terrain = terrain.loc[terrain["site_id"] == site["site_id"]]
        st.markdown("**Terrain parameters**")
        if site_terrain.empty:
            st.info("No terrain record is available for this site.")
        else:
            display = site_terrain.drop(
                columns=[column for column in ("schema_version", "site_id") if column in site_terrain]
            )
            st.dataframe(display, hide_index=True, width="stretch")

        sources = []
        if not site_terrain.empty:
            sources.extend(
                str(value)
                for value in site_terrain["dem_source"].dropna().unique()
                if str(value).strip()
            )
        site_temperatures = temperatures.loc[
            temperatures["site_id"] == site["site_id"]
        ]
        if not site_temperatures.empty:
            sources.extend(
                str(value)
                for value in site_temperatures["source"].dropna().unique()
                if str(value).strip()
            )
        st.markdown("**Dataset sources recorded for this site**")
        if sources:
            for source in dict.fromkeys(sources):
                st.write(f"- {source}")
        else:
            st.write("No source identifiers are recorded for this site.")

        if not catalogue.empty:
            st.caption(
                "Catalogue records (not linked to individual sites by the current contract): "
                + ", ".join(catalogue["dataset_name"].dropna().astype(str).unique())
            )