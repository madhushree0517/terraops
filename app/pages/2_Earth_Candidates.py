import streamlit as st

from app.components.map_helpers import filter_sites_by_body, render_site_map
from app.components.site_profile import (
    load_profile_terrain_metrics,
    render_page_banner,
    render_site_card,
)
from app.utils.config import get_data_file_source
from app.utils.loaders import (
    load_slope_preview,
    load_sites,
    load_temperature_monthly,
)


st.set_page_config(page_title="Earth Candidates | TERRAOPS", layout="wide")
st.title("Earth Candidates")
render_page_banner(None, {
    filename: get_data_file_source(filename)
    for filename in (
        "sites.geojson", "terrain_metrics.csv", "temperature_monthly.csv",
        "datasets_catalogue.csv",
    )
})

try:
    sites = load_sites()
    terrain_metrics = load_profile_terrain_metrics()
    temperatures = load_temperature_monthly()
    earth_sites = filter_sites_by_body(sites, "Earth")
    site_ids = earth_sites["site_id"].astype(str).tolist()
    site_names = dict(zip(earth_sites["site_id"].astype(str), earth_sites["name"].astype(str)))
    if not site_ids:
        st.info("No sites are available in the active data source.")
    else:
        if "earth_selected_site" not in st.session_state or st.session_state["earth_selected_site"] not in site_ids:
            st.session_state["earth_selected_site"] = site_ids[0]
        clicked_site = render_site_map(
            earth_sites,
            height=420,
            key=f"earth_candidates_map_{st.session_state['earth_selected_site']}",
        )
        if clicked_site in site_ids:
            st.session_state["earth_selected_site"] = clicked_site
        selected_site_id = st.selectbox(
            "Select an Earth site",
            options=site_ids,
            format_func=lambda site_id: f"{site_names[site_id]} ({site_id})",
            key="earth_selected_site",
        )
        selected_site = earth_sites.loc[earth_sites["site_id"] == selected_site_id].iloc[0]
        render_site_card(selected_site, terrain_metrics, temperatures)
        slope_preview = load_slope_preview(selected_site_id)
        if slope_preview is not None:
            st.image(slope_preview["image_bytes"], width="stretch")
            st.caption(
                "Preview of the supplied raster extent, downsampled; not a validated site boundary."
            )
            with st.expander("Preview details"):
                st.write(
                    f"Extent ({slope_preview['crs']}): left {slope_preview['extent_left']}, "
                    f"bottom {slope_preview['extent_bottom']}, right {slope_preview['extent_right']}, "
                    f"top {slope_preview['extent_top']}. Native pixel size "
                    f"{slope_preview['pixel_size_x']} x {slope_preview['pixel_size_y']} "
                    f"{slope_preview['pixel_size_unit']}; preview "
                    f"{slope_preview['preview_width']} x {slope_preview['preview_height']} px."
                )
except Exception as error:
    st.error(f"Could not load candidate site data: {error}")