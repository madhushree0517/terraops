from pathlib import Path

import streamlit as st

from app.components.map_helpers import load_mars_map_config, render_site_map
from app.components.site_profile import (
    load_profile_terrain_metrics,
    render_page_banner,
    render_site_card,
)
from app.utils.config import get_data_file_source
from app.utils.loaders import (
    load_sites,
    load_temperature_monthly,
)

st.set_page_config(page_title="Mars Reference | TERRAOPS", layout="wide")
st.title("Mars Reference")
render_page_banner(None, {
    filename: get_data_file_source(filename)
    for filename in (
        "sites.geojson", "terrain_metrics.csv", "temperature_monthly.csv",
        "datasets_catalogue.csv",
    )
})

try:
    sites = load_sites()
    jezero = sites.loc[sites["site_id"] == "jezero"]
    if jezero.empty:
        st.error("The sites dataset does not contain the required Jezero reference.")
    else:
        site = jezero.iloc[0]
        terrain_metrics = load_profile_terrain_metrics()
        temperatures = load_temperature_monthly()
        map_column, profile_column = st.columns([1.2, 1])
        with map_column:
            map_config = load_mars_map_config()
            tile_url = str(map_config.get("mars_tiles_url", "")).strip()
            render_site_map(
                jezero,
                key="mars_reference_map",
                use_earth_basemap=False,
                tile_url=tile_url,
                tile_attribution=map_config.get("mars_tiles_attribution", ""),
            )
        with profile_column:
            render_site_card(site, terrain_metrics, temperatures)
        mars_assets = Path(__file__).resolve().parents[2] / "assets" / "mars"
        image_paths = sorted(
            path
            for path in mars_assets.glob("*")
            if path.is_file() and path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}
        ) if mars_assets.is_dir() else []
        if image_paths:
            st.subheader("Imagery and MEDA measurements")
            credits_path = mars_assets / "CREDITS.txt"
            credits = credits_path.read_text(encoding="utf-8").strip() if credits_path.is_file() else "Credit not documented."
            for image_path in image_paths:
                st.image(str(image_path), caption=credits, width="stretch")
        elif not tile_url:
            st.caption(
                "No Mars imagery or basemap is included yet; the marker shows the approximate "
                "reference coordinate only."
            )
except Exception as error:
    st.error(f"Could not load the Jezero reference data: {error}")