import geopandas as gpd
from shapely.geometry import Point

from app.components.map_helpers import build_site_map
from app.utils.loaders import load_sites


def test_mars_map_has_marker_without_earth_basemap():
    jezero = gpd.GeoDataFrame(
        {
            "site_id": ["jezero"],
            "name": ["Jezero Crater"],
            "body": ["Mars"],
            "lat": [18.4],
            "lon": [77.6],
        },
        geometry=[Point(77.6, 18.4)],
        crs="EPSG:4326",
    )

    html = build_site_map(jezero, use_earth_basemap=False).get_root().render()

    assert "[18.4, 77.6]" in html
    assert "tile.openstreetmap.org" not in html


def test_configured_mars_tile_url_is_added():
    jezero = gpd.GeoDataFrame(
        {
            "site_id": ["jezero"],
            "name": ["Jezero Crater"],
            "body": ["Mars"],
            "lat": [18.4],
            "lon": [77.6],
        },
        geometry=[Point(77.6, 18.4)],
        crs="EPSG:4326",
    )

    html = build_site_map(
        jezero,
        use_earth_basemap=False,
        tile_url="https://mars.example/{z}/{x}/{y}.png",
        tile_attribution="Mars tiles",
    ).get_root().render()

    assert "https://mars.example/{z}/{x}/{y}.png" in html
    assert "tile.openstreetmap.org" not in html


def test_sample_jezero_coordinates_are_placeholder_reference():
    sites = load_sites()
    jezero = sites.loc[sites["site_id"] == "jezero"].iloc[0]

    assert jezero["lat"] == 18.4
    assert jezero["lon"] == 77.6
    assert "PLACEHOLDER" in jezero["notes"]