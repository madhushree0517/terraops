import json
from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium


def load_mars_map_config() -> dict[str, str]:
    config_path = Path(__file__).resolve().parents[1] / "utils" / "map_config.json"
    with config_path.open(encoding="utf-8") as source:
        return json.load(source)


def build_site_map(
    sites: gpd.GeoDataFrame,
    *,
    use_earth_basemap: bool = True,
    tile_url: str = "",
    tile_attribution: str = "",
) -> folium.Map:
    """Build a site map with an Earth basemap or an optional configured tile layer."""
    if sites.empty:
        return folium.Map(
            location=[0, 0],
            zoom_start=2,
            control_scale=True,
            tiles="OpenStreetMap" if use_earth_basemap else None,
        )
    center = [float(sites["lat"].mean()), float(sites["lon"].mean())]
    site_map = folium.Map(
        location=center,
        zoom_start=2 if len(sites) > 1 else 4,
        control_scale=True,
        tiles="OpenStreetMap" if use_earth_basemap else None,
    )
    if tile_url:
        folium.TileLayer(
            tiles=tile_url,
            attr=tile_attribution,
            name="Mars imagery",
            overlay=False,
            control=True,
        ).add_to(site_map)
    for site in sites.itertuples():
        folium.Marker(
            location=[site.lat, site.lon],
            tooltip=site.name,
            popup=f"{site.name} ({site.body}) | {site.site_id}",
            icon=folium.Icon(color="red" if site.body == "Mars" else "green"),
        ).add_to(site_map)
    if len(sites) > 1:
        site_map.fit_bounds(
            [
                [float(sites["lat"].min()), float(sites["lon"].min())],
                [float(sites["lat"].max()), float(sites["lon"].max())],
            ],
            padding=(24, 24),
        )
    return site_map


def render_site_map(
    sites: gpd.GeoDataFrame,
    height: int = 480,
    key: str = "terraops_site_map",
    *,
    use_earth_basemap: bool = True,
    tile_url: str = "",
    tile_attribution: str = "",
) -> str | None:
    """Render a Folium map and return the site id if a marker was clicked."""
    result = st_folium(
        build_site_map(
            sites,
            use_earth_basemap=use_earth_basemap,
            tile_url=tile_url,
            tile_attribution=tile_attribution,
        ),
        height=height,
        use_container_width=True,
        returned_objects=["last_object_clicked"],
        key=key,
    )
    clicked = result.get("last_object_clicked") if result else None
    if not clicked or not sites.size:
        return None
    latitude = float(clicked["lat"])
    longitude = float(clicked["lng"])
    distances = (sites["lat"] - latitude) ** 2 + (sites["lon"] - longitude) ** 2
    nearest_index = distances.idxmin()
    if float(distances.loc[nearest_index]) > 0.0004:
        return None
    return str(sites.loc[nearest_index, "site_id"])