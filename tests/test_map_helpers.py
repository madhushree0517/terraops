import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from streamlit.testing.v1 import AppTest
from shapely.geometry import Point

from app.components.map_helpers import build_site_map, filter_sites_by_body
from app.components.site_profile import build_terrain_profile_table
from app.utils import config
from app.utils.loaders import TERRAIN_METRICS_COLUMNS, load_sites, load_slope_preview


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


def test_site_without_coordinates_remains_pending_and_does_not_break_map():
    pending = gpd.GeoDataFrame(
        {
            "site_id": ["askja"],
            "name": ["Askja, Iceland"],
            "body": ["Earth"],
            "lat": [float("nan")],
            "lon": [float("nan")],
        },
        geometry=[None],
        crs="EPSG:4326",
    )

    html = build_site_map(pending).get_root().render()

    assert "OpenStreetMap" in html
    assert "Askja, Iceland" not in html


def test_earth_candidate_page_shows_downsampled_slope_preview(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    processed = data_root / "processed"
    sample = data_root / "sample"
    processed.mkdir(parents=True)
    sample.mkdir(parents=True)
    terrain_row = {column: float("nan") for column in TERRAIN_METRICS_COLUMNS}
    terrain_row.update(
        {
            "schema_version": "1.0",
            "site_id": "atacama",
            "metric_name": "slope_p90_deg",
            "value": float("nan"),
            "tier": "",
            "availability_note": "Terrain values pending",
        }
    )
    pd.DataFrame([terrain_row], columns=TERRAIN_METRICS_COLUMNS).to_csv(
        processed / "terrain_metrics.csv", index=False
    )
    pd.DataFrame(
        [{
            "schema_version": "1.0", "site_id": "atacama", "month": 7,
            "variable_type": "air_temp", "temp_min_c": 0, "temp_mean_c": 1,
            "temp_max_c": 2, "pct_in_envelope": float("nan"), "n_valid_obs": 31,
            "n_missing_obs": 0, "source": "fixture", "period_start": "2024-07-01",
            "period_end": "2024-07-31",
        }]
    ).to_csv(processed / "temperature_monthly.csv", index=False)
    pd.DataFrame(
        [{
            "schema_version": "1.0", "dataset_name": "Test dataset", "source": "Test",
            "url": "", "file_format": "CSV", "spatial_resolution": "",
            "temporal_resolution": "Daily", "observation_period": "July 2024",
            "units": "Celsius", "crs": "", "limitations": "",
            "citation": "", "licence": "",
        }]
    ).to_csv(processed / "datasets_catalogue.csv", index=False)
    site = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-68.5, -22.5]},
            "properties": {
                "schema_version": "1.0", "site_id": "atacama", "name": "Atacama Desert, Chile",
                "body": "Earth", "lat": -22.5, "lon": -68.5,
                "notes": "centroid of supplied extent footprint",
            },
        }],
    }
    (processed / "sites.geojson").write_text(json.dumps(site), encoding="utf-8")
    metadata_row = {
        "site_id": "atacama", "image_path": "previews/atacama_slope.png",
        "source_file": "large/terrain/Atacama_Reprojected_slope.tif", "crs": "EPSG:32719",
        "extent_left": 1, "extent_bottom": 2, "extent_right": 3, "extent_top": 4,
        "pixel_size_x": 30, "pixel_size_y": 30, "pixel_size_unit": "metre",
        "preview_width": 2, "preview_height": 2,
    }
    pd.DataFrame([metadata_row]).to_csv(processed / "slope_preview_metadata.csv", index=False)
    preview_dir = processed / "previews"
    preview_dir.mkdir()
    raster = preview_dir / "atacama_slope.png"
    with rasterio.open(
        raster, "w", driver="PNG", height=2, width=2, count=1, dtype="uint8",
        transform=from_origin(0, 2, 1, 1),
    ) as dataset:
        dataset.write(np.array([[0, 255], [128, 64]], dtype=np.uint8), 1)
    monkeypatch.setattr(config, "DATA_ROOT", data_root)

    page = Path(__file__).resolve().parents[1] / "app" / "pages" / "2_Earth_Candidates.py"
    app = AppTest.from_file(str(page)).run()

    assert not app.exception
    preview = load_slope_preview("atacama", processed)
    assert preview is not None
    assert preview["preview_width"] <= 800
    assert preview["image_bytes"].startswith(b"\x89PNG")
    assert any(
        "Preview of the supplied raster extent, downsampled; not a validated site boundary." in caption.value
        for caption in app.caption
    )
    assert not app.dataframe
    assert not app.metric
    page_text = "\n".join(
        element.value for element in [*app.markdown, *app.caption, *app.subheader, *app.info, *app.warning]
    )
    assert "Atacama Desert, Chile" in page_text
    assert "Coordinates: -22.5000\u00b0, -68.5000\u00b0" in page_text
    assert "Data sources: fixture" in page_text
    assert "data pending" not in page_text and "None" not in page_text
    assert len(app.warning) + len(app.info) == 0


def test_earth_candidates_default_to_first_site_with_terrain_and_explain_missing_site(
    tmp_path, monkeypatch
):
    data_root = tmp_path / "data"
    processed = data_root / "processed"
    sample = data_root / "sample"
    processed.mkdir(parents=True)
    sample.mkdir(parents=True)
    features = []
    for site_id, name, latitude, longitude in (
        ("askja", "Askja, Iceland", 65.5, -16.5),
        ("atacama", "Atacama Desert, Chile", -22.5, -68.5),
    ):
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "properties": {
                    "schema_version": "1.0", "site_id": site_id, "name": name,
                    "body": "Earth", "lat": latitude, "lon": longitude, "notes": "",
                },
            }
        )
    (processed / "sites.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
    )
    rows = []
    for metric_name, value, unit in (
        ("pct_area_slope_gt24", 4.61, "%"),
        ("pct_area_slope_gt17", 10.12, "%"),
        ("slope_p90_deg", 17.12, ""),
    ):
        row = {column: float("nan") for column in TERRAIN_METRICS_COLUMNS}
        row.update(
            {
                "schema_version": "1.0", "site_id": "atacama", "metric_name": metric_name,
                "value": value, "metric_unit": unit, "tier": "B", "dem_source": "Test DEM",
                "availability_note": "",
            }
        )
        rows.append(row)
    missing = {column: float("nan") for column in TERRAIN_METRICS_COLUMNS}
    missing.update(
        {
            "schema_version": "1.0", "site_id": "askja", "metric_name": "slope_p90_deg",
            "value": float("nan"), "metric_unit": "", "tier": "",
            "availability_note": "Terrain metrics pending CRS review: fixture CRS review.",
        }
    )
    rows.append(missing)
    pd.DataFrame(rows, columns=TERRAIN_METRICS_COLUMNS).to_csv(
        processed / "terrain_metrics.csv", index=False
    )
    temperature_rows = []
    for variable_type, period, valid, minimum, mean, maximum in (
        ("air_temp", "daily", 31, 0, 1, 2),
        ("surface_temp", "day", 8, 6.5, 14.8, 26.7),
        ("surface_temp", "night", 8, -0.03, 2.4, 5.6),
    ):
        temperature_rows.append(
            {
                "schema_version": "1.0", "site_id": "askja", "month": 7,
                "variable_type": variable_type, "temp_min_c": minimum,
                "temp_mean_c": mean, "temp_max_c": maximum,
                "pct_in_envelope": float("nan"), "n_valid_obs": valid,
                "n_missing_obs": 31 - valid, "source": "fixture",
                "period_start": "2024-07-01", "period_end": "2024-07-31",
                "source_label": "Iceland", "period_of_day": period,
            }
        )
    pd.DataFrame(temperature_rows).to_csv(processed / "temperature_monthly.csv", index=False)
    monkeypatch.setattr(config, "DATA_ROOT", data_root)
    page = Path(__file__).resolve().parents[1] / "app" / "pages" / "2_Earth_Candidates.py"

    app = AppTest.from_file(str(page)).run()

    assert not app.exception
    assert not app.error, [element.value for element in app.error]
    assert app.selectbox[0].value == "atacama"
    assert {metric.label for metric in app.metric} == {
        "Area steeper than 24 degrees", "Area steeper than 17 degrees", "Slope P90",
    }
    app.selectbox[0].select("askja").run()
    assert not app.exception
    assert any(
        markdown.value == "Terrain data not yet included: fixture CRS review."
        for markdown in app.markdown
    )
    assert not app.metric
    low_data_captions = [caption.value for caption in app.caption if "Low data: MODIS" in caption.value]
    assert low_data_captions == [
        "Low data: MODIS daytime, 8 of 31 valid July days.",
        "Low data: MODIS nighttime, 8 of 31 valid July days.",
    ]


def test_mars_reference_page_is_one_card_and_one_sentence_without_imagery():
    page = Path(__file__).resolve().parents[1] / "app" / "pages" / "1_Mars_Reference.py"
    assets = page.parents[1].parent / "assets" / "mars"
    has_images = assets.is_dir() and any(
        path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"} for path in assets.glob("*")
    )

    app = AppTest.from_file(str(page)).run()

    assert not app.exception
    text = "\n".join(element.value for element in [*app.markdown, *app.caption, *app.subheader])
    assert "Jezero" in text
    assert "Coordinates: 18.4000\u00b0, 77.6000\u00b0" in text
    assert not app.dataframe
    assert "data pending" not in text
    if not has_images:
        assert "No Mars imagery or basemap is included yet" in text
        assert "Imagery and MEDA measurements" not in text


def test_jezero_coordinates_are_labeled_approximate_reference():
    sites = load_sites()
    jezero = sites.loc[sites["site_id"] == "jezero"].iloc[0]

    assert jezero["lat"] == 18.4
    assert jezero["lon"] == 77.6
    assert jezero["notes"] == "approximate reference coordinate, to be confirmed"


def test_earth_candidate_map_excludes_mars_marker_and_bounds():
    sites = load_sites()
    earth_sites = filter_sites_by_body(sites, "Earth")

    html = build_site_map(earth_sites).get_root().render()

    assert set(earth_sites["body"]) == {"Earth"}
    assert "Jezero Crater" not in html
    assert "[18.4, 77.6]" not in html
    assert "Atacama Desert, Chile" in html
    assert "Ladakh" in html
    assert "Askja, Iceland" in html
    assert "maxBounds" not in html
    assert "fitBounds" in html


def test_site_marker_tooltips_contain_site_names():
    earth_sites = filter_sites_by_body(load_sites(), "Earth")

    html = build_site_map(earth_sites).get_root().render()

    assert html.count("bindTooltip(") == 3
    assert "Atacama Desert, Chile" in html
    assert "Ladakh" in html
    assert "Askja, Iceland" in html


def test_site_profile_terrain_table_is_vertical_and_unit_labelled():
    atacama = pd.DataFrame(
        [
            {
                "metric_name": "slope_p90_deg",
                "value": 17.119352340698242,
                "tier": "B",
                "metric_unit": "",
            },
            {
                "metric_name": "rock_cover_cfa_pct",
                "value": float("nan"),
                "tier": "",
                "metric_unit": "%",
            },
        ]
    )

    profile = build_terrain_profile_table(atacama)

    assert profile.columns.tolist() == ["Parameter", "Value", "Tier"]
    assert "Slope P90 (unit unconfirmed)" in profile["Parameter"].tolist()
    assert "Rock cover CFA" in profile["Parameter"].tolist()
    assert profile.loc[profile["Parameter"] == "Slope P90 (unit unconfirmed)", "Value"].iloc[0] == (
        "17.12 (unit unconfirmed)"
    )
    assert profile.loc[profile["Parameter"] == "Rock cover CFA", "Value"].iloc[0] == "data pending"
    assert profile.loc[profile["Parameter"] == "Rock cover CFA", "Tier"].iloc[0] == "not available"
    assert "-2500" not in profile.to_string()