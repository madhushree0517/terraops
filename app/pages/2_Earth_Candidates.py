import streamlit as st

from app.components.map_helpers import render_site_map
from app.components.site_profile import render_placeholder_banner, render_site_profile
from app.utils.config import get_data_source
from app.utils.loaders import (
    load_datasets_catalogue,
    load_sites,
    load_temperature_monthly,
    load_terrain_parameters,
)


st.set_page_config(page_title="Earth Candidates | TERRAOPS", layout="wide")
st.title("Earth Candidates")
render_placeholder_banner(get_data_source())

try:
    sites = load_sites()
    terrain = load_terrain_parameters()
    temperatures = load_temperature_monthly()
    catalogue = load_datasets_catalogue()
    site_ids = sites["site_id"].astype(str).tolist()
    site_names = dict(zip(sites["site_id"].astype(str), sites["name"].astype(str)))
    if not site_ids:
        st.info("No sites are available in the active data source.")
    else:
        if "earth_selected_site" not in st.session_state or st.session_state["earth_selected_site"] not in site_ids:
            st.session_state["earth_selected_site"] = site_ids[0]
        map_column, profile_column = st.columns([1.2, 1])
        with map_column:
            clicked_site = render_site_map(
                sites,
                key=f"earth_candidates_map_{st.session_state['earth_selected_site']}",
            )
        if clicked_site in site_ids:
            st.session_state["earth_selected_site"] = clicked_site
        with profile_column:
            selected_site_id = st.selectbox(
                "Select a site",
                options=site_ids,
                format_func=lambda site_id: f"{site_names[site_id]} ({site_id})",
                key="earth_selected_site",
            )
            selected_site = sites.loc[sites["site_id"] == selected_site_id].iloc[0]
            render_site_profile(selected_site, terrain, temperatures, catalogue)
except Exception as error:
    st.error(f"Could not load candidate site data: {error}")