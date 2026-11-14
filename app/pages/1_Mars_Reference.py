import streamlit as st

from app.components.map_helpers import load_mars_map_config, render_site_map
from app.components.site_profile import render_placeholder_banner, render_site_profile
from app.utils.config import get_data_source
from app.utils.loaders import (
    load_datasets_catalogue,
    load_sites,
    load_temperature_monthly,
    load_terrain_parameters,
)

st.set_page_config(page_title="Mars Reference | TERRAOPS", layout="wide")
st.title("Mars Reference")
data_source = get_data_source()
render_placeholder_banner(data_source)

try:
    sites = load_sites()
    jezero = sites.loc[sites["site_id"] == "jezero"]
    if jezero.empty:
        st.error("The sites dataset does not contain the required Jezero reference.")
    else:
        site = jezero.iloc[0]
        terrain = load_terrain_parameters()
        temperatures = load_temperature_monthly()
        catalogue = load_datasets_catalogue()
        map_column, profile_column = st.columns([1.2, 1])
        with map_column:
            map_config = load_mars_map_config()
            render_site_map(
                jezero,
                key="mars_reference_map",
                use_earth_basemap=False,
                tile_url=map_config.get("mars_tiles_url", ""),
                tile_attribution=map_config.get("mars_tiles_attribution", ""),
            )
        with profile_column:
            render_site_profile(site, terrain, temperatures, catalogue)
        st.subheader("Imagery and MEDA measurements")
        st.info("Imagery and MEDA measurements will be added when validated data is supplied")
except Exception as error:
    st.error(f"Could not load the Jezero reference data: {error}")