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


def filter_sites_by_body(sites: gpd.GeoDataFrame, body: str) -> gpd.GeoDataFrame:
    """Return a copy containing only sites for the requested planetary body."""
    return sites.loc[sites["body"] == body].copy()


def _sites_with_coordinates(sites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    latitude = pd.to_numeric(sites["lat"], errors="coerce")
    longitude = pd.to_numeric(sites["lon"], errors="coerce")
    return sites.loc[latitude.notna() & longitude.notna()].copy()


def build_site_map(
    sites: gpd.GeoDataFrame,
    *,
    use_earth_basemap: bool = True,
    tile_url: str = "",
    tile_attribution: str = "",
) -> folium.Map:
    """Build a site map with an Earth basemap or an optional configured tile layer."""
    sites_with_coordinates = _sites_with_coordinates(sites)
    if sites_with_coordinates.empty:
        return folium.Map(
            location=[0, 0],
            zoom_start=2,
            control_scale=True,
            tiles="OpenStreetMap" if use_earth_basemap else None,
        )
    center = [
        float(sites_with_coordinates["lat"].mean()),
        float(sites_with_coordinates["lon"].mean()),
    ]
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
    for site in sites_with_coordinates.itertuples():
        folium.Marker(
            location=[site.lat, site.lon],
            tooltip=site.name,
            popup=f"{site.name} ({site.body}) | {site.site_id}",
            icon=folium.Icon(color="red" if site.body == "Mars" else "green"),
        ).add_to(site_map)
    site_map.fit_bounds(
        [
            [float(sites_with_coordinates["lat"].min()), float(sites_with_coordinates["lon"].min())],
            [float(sites_with_coordinates["lat"].max()), float(sites_with_coordinates["lon"].max())],
        ],
            padding=(24, 24),
        max_zoom=5,
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
    sites_with_coordinates = _sites_with_coordinates(sites)
    if not clicked or sites_with_coordinates.empty:
        return None
    latitude = float(clicked["lat"])
    longitude = float(clicked["lng"])
    distances = (sites_with_coordinates["lat"] - latitude) ** 2 + (
        sites_with_coordinates["lon"] - longitude
    ) ** 2
    nearest_index = distances.idxmin()
    if float(distances.loc[nearest_index]) > 0.0004:
        return None
    return str(sites_with_coordinates.loc[nearest_index, "site_id"])