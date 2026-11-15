import json
from io import BytesIO
from pathlib import Path
from typing import Any

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
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
    selected_site_id: str | None = None,
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
            icon=folium.Icon(
                color=("red" if site.body == "Mars" else "red")
                if str(site.site_id) == str(selected_site_id)
                else ("red" if site.body == "Mars" else "green")
            ),
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
    selected_site_id: str | None = None,
) -> str | None:
    """Render a Folium map and return the site id if a marker was clicked."""
    result = st_folium(
        build_site_map(
            sites,
            use_earth_basemap=use_earth_basemap,
            tile_url=tile_url,
            tile_attribution=tile_attribution,
            selected_site_id=selected_site_id,
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


def build_site_detail_map(
    site: pd.Series,
    extent: gpd.GeoSeries | Any | None,
    *,
    preview_bytes: bytes | None = None,
    preview_bounds: list[list[float]] | None = None,
    opacity: float = 0.6,
) -> folium.Map:
    """Build a focused site map with its supplied footprint and optional georeferenced slope image."""
    latitude, longitude = float(site["lat"]), float(site["lon"])
    detail = folium.Map(location=[latitude, longitude], zoom_start=8, control_scale=True)
    if preview_bytes and preview_bounds:
        image = np.asarray(Image.open(BytesIO(preview_bytes)).convert("RGBA"))
        folium.raster_layers.ImageOverlay(
            image=image,
            bounds=preview_bounds,
            opacity=opacity,
            interactive=False,
            cross_origin=False,
            zindex=2,
            name="Slope preview",
        ).add_to(detail)
    if extent is not None and not extent.is_empty:
        folium.GeoJson(
            extent.__geo_interface__,
            name="Terrain footprint",
            style_function=lambda _: {"color": "#18A999", "weight": 3, "fillOpacity": 0.04},
            tooltip=str(site["name"]),
        ).add_to(detail)
        west, south, east, north = extent.bounds
        detail.fit_bounds([[south, west], [north, east]], padding=(16, 16), max_zoom=12)
    folium.Marker(
        [latitude, longitude],
        tooltip=str(site["name"]),
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(detail)
    return detail


def render_site_detail_map(
    site: pd.Series,
    extent: gpd.GeoSeries | Any | None,
    *,
    preview_bytes: bytes | None = None,
    preview_bounds: list[list[float]] | None = None,
    opacity: float = 0.6,
    height: int = 420,
    key: str = "terraops_site_detail_map",
) -> None:
    detail_map = build_site_detail_map(
        site,
        extent,
        preview_bytes=preview_bytes,
        preview_bounds=preview_bounds,
        opacity=opacity,
    )
    st_folium(
        detail_map,
        height=height,
        use_container_width=True,
        returned_objects=[],
        key=key,
    )
