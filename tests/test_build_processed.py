import json
import pandas as pd
import geopandas as gpd
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin
from shapely.geometry import Polygon, mapping

from scripts.build_processed import _build_sites, build_processed
from app.utils.loaders import (
    load_analogy_gaps,
    load_mars_temperature_envelope,
    load_sites,
    load_terrain_metrics,
    load_temperature_monthly,
)


def _write_projected_site_rasters(raw_root, site_id, lon, lat, epsg):
    terrain_dir = raw_root / "large" / "terrain"
    terrain_dir.mkdir(parents=True, exist_ok=True)
    forward = Transformer.from_crs("EPSG:4326", epsg, always_xy=True)
    reverse = Transformer.from_crs(epsg, "EPSG:4326", always_xy=True)
    center_x, center_y = forward.transform(lon, lat)
    left, right = center_x - 60, center_x + 60
    bottom, top = center_y - 60, center_y + 60
    corners = [
        reverse.transform(left, bottom),
        reverse.transform(right, bottom),
        reverse.transform(right, top),
        reverse.transform(left, top),
        reverse.transform(left, bottom),
    ]
    polygon = Polygon(corners)
    return terrain_dir, polygon, from_origin(left, top, 30, 30)


def test_build_processed_creates_only_clear_outputs_and_preserves_missing(tmp_path, capsys):
    raw_dir = tmp_path / "raw"
    package = raw_dir / "package"
    package.mkdir(parents=True)
    temp_earth = package / "temperature" / "earth"
    temp_earth.mkdir(parents=True)
    processed_dir = tmp_path / "processed"

    pd.DataFrame(
        {
            "site": ["Atacama", "Unmapped candidate", " Ladakh"],
            "period_start": ["2024-07-01"] * 3,
            "period_end": ["2024-07-31"] * 3,
            "total_calendar_days": [31] * 3,
            "POWER_valid_days": [31, 31, 30],
            "POWER_T2M_mean_C": [12.0, 4.0, 10.0],
            "POWER_T2M_min_C": [4.0, 1.0, 7.0],
            "POWER_T2M_max_C": [17.0, 6.0, 15.0],
        }
    ).to_csv(temp_earth / "14_earth_site_temperature_summary.csv", index=False)

    # Extent geometries are supplied; create small, reproducible projected fixture rasters.
    features = []
    expected_centroids = {}
    for site_id, lon, lat, epsg in (
        ("atacama", -68.5, -22.5, "EPSG:32719"),
        ("ladakh", 77.5, 34.5, "EPSG:32643"),
        ("askja", -16.5, 65.5, "EPSG:32727"),
    ):
        terrain_dir, polygon, transform = _write_projected_site_rasters(
            raw_dir, site_id, lon, lat, epsg
        )
        gpd.GeoDataFrame(
            {"geometry": [polygon]}, geometry="geometry", crs="EPSG:4326"
        ).to_file(
            terrain_dir / f"Extent_{site_id.title()}.gpkg",
            layer="extent",
            driver="GPKG",
        )
        expected_centroids[site_id] = (polygon.centroid.x, polygon.centroid.y)
        label = f"Extent_{site_id.title()} — extent"
        features.append(
            {
                "type": "Feature",
                "geometry": mapping(polygon),
                "properties": {"layer": label},
            }
        )
        for suffix, values in (
            ("Reprojected", np.arange(16, dtype=np.float32).reshape(4, 4) + 10),
            (
                "Reprojected_slope",
                np.array(
                    [[-9999, 4, 4, 4], [4, 4, 4, 4], [4, 4, 4, 4], [4, 4, 4, 4]],
                    dtype=np.float32,
                )
                if site_id == "atacama"
                else np.ones((4, 4), dtype=np.float32) * 4,
            ),
            ("Reprojected_roughness", np.ones((4, 4), dtype=np.float32) * 0.25),
        ):
            raster_path = terrain_dir / f"{site_id.title()}_{suffix}.tif"
            with rasterio.open(
                raster_path,
                "w",
                driver="GTiff",
                height=4,
                width=4,
                count=1,
                dtype="float32",
                crs=epsg,
                transform=transform,
                nodata=-9999,
            ) as dataset:
                dataset.write(values, 1)
    qgis_metrics = []
    for site_id, mean, minimum, maximum, std in (
        ("Atacama", 5.25, 0.0, 8.0, 1.5),
        ("Ladakh", 4.5, 1.0, 9.0, 2.0),
    ):
        qgis_metrics.extend(
            [
                json.dumps(
                    {
                        "BAND": 1,
                        "INPUT": f"C:/nested/source/path/{site_id}_Reprojected_slope.tif",
                    }
                ),
                json.dumps(
                    {
                        "COUNT": 16,
                        "MIN": minimum,
                        "MAX": maximum,
                        "MEAN": mean,
                        "STD_DEV": std,
                    }
                ),
            ]
        )
    (package / "New_Terrain _metrics.txt").write_text(
        "\n".join(qgis_metrics), encoding="utf-8"
    )
    (raw_dir / "large" / "terrain" / "site_boundaries.gpkg.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )

    pd.DataFrame(
        [
            {
                "dataset": "NASA POWER",
                "source": "NASA",
                "url": "https://power.example",
                "citation": "Explicit NASA POWER citation",
                "licence": "Explicit NASA terms",
            },
            {"dataset": "MODIS", "source": "NASA", "url": "https://modis.example"},
            {"dataset": "Mars MEDA ATS and TIRS", "source": "PDS", "url": "https://pds.example"},
            {"dataset": "Copernicus DEM", "source": "Copernicus", "url": "https://dem.example"},
        ]
    ).to_csv(package / "TERRAOPS_Data_Sources.csv", index=False)
    pd.DataFrame(
        [
            {"dataset": "NASA POWER", "coverage": "July 2024", "notes": "T2M Celsius"},
            {"dataset": "MODIS LST", "coverage": "July 2024", "notes": "Day/night LST Celsius"},
            {"dataset": "Mars MEDA TIRS", "coverage": "Sol 1 to 1859", "notes": "Air and ground temperatures"},
            {"dataset": "Mars MEDA ATS", "coverage": "Sol 1 to 1859", "notes": "Five channels; Celsius after conversion"},
        ]
    ).to_csv(package / "MASTER_TEMPERATURE_DATASET_INVENTORY.csv", index=False)
    seasonal_rows = []
    seasonal_bounds = {
        "Northern Spring": (-54.2, -40.0),
        "Northern Summer": (-50.0, -36.5),
        "Northern Autumn": (-66.0, -39.0),
        "Northern Winter": (-64.5, -44.9),
    }
    for season, (p05, p95) in seasonal_bounds.items():
        for earth_site in ("Atacama", "Ladakh"):
            seasonal_rows.append(
                {
                    "earth_site": earth_site,
                    "earth_variable": "MODIS daytime LST",
                    "mars_variable": "TIRS ground temperature",
                    "mars_season": season,
                    "mars_p05_C": p05,
                    "mars_p95_C": p95,
                    "comparison_class": "SURFACE_TEMPERATURE",
                }
            )
    recalculated_path = package / "temperature" / "validation" / "handover" / "05_EARTH_MARS_FINAL_RECALCULATED_TABLE.csv"
    recalculated_path.parent.mkdir(parents=True)
    pd.DataFrame(seasonal_rows).to_csv(recalculated_path, index=False)
    limitations_path = package / "temperature" / "validation" / "FINAL_REVISED_SCIENTIFIC_LIMITATIONS_REGISTER.csv"
    limitations_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"topic": "Earth coverage", "status": "Limited", "finding": "July only", "next_action": "Extend coverage"},
            {"topic": "Geometry", "status": "Pending", "finding": "Not verified", "next_action": "Review product geometry"},
        ]
    ).to_csv(limitations_path, index=False)

    results = build_processed(raw_dir, processed_dir)
    log = capsys.readouterr().out
    temperatures = pd.read_csv(processed_dir / "temperature_monthly.csv")
    catalogue = pd.read_csv(processed_dir / "datasets_catalogue.csv")
    sites = load_sites(processed_dir)
    terrain_metrics = load_terrain_metrics(processed_dir)
    histograms = pd.read_csv(processed_dir / "slope_histograms.csv")
    preview_metadata = pd.read_csv(processed_dir / "slope_preview_metadata.csv")
    envelope = load_mars_temperature_envelope(processed_dir)
    analogy_gaps = load_analogy_gaps(processed_dir)

    atacama = temperatures.loc[temperatures["site_id"] == "atacama"].iloc[0]
    ladakh = temperatures.loc[temperatures["site_id"] == "ladakh"].iloc[0]
    assert atacama["variable_type"] == "air_temp"
    assert atacama["temp_min_c"] == 4.0
    assert atacama["temp_mean_c"] == 12.0
    assert atacama["temp_max_c"] == 17.0
    assert atacama["n_valid_obs"] == 31
    assert atacama["n_missing_obs"] == 0
    assert pd.isna(atacama["pct_in_envelope"])
    assert ladakh["site_id"] == "ladakh"
    assert set(catalogue["dataset_name"]) == {
        "NASA POWER", "MODIS LST", "Mars MEDA TIRS", "Mars MEDA ATS", "Copernicus DEM"
    }
    assert pd.to_numeric(catalogue["schema_version"]).eq(1.0).all()
    assert pd.isna(catalogue.loc[catalogue["dataset_name"] == "Copernicus DEM", "spatial_resolution"]).all()
    power_catalogue = catalogue.loc[catalogue["dataset_name"] == "NASA POWER"].iloc[0]
    modis_catalogue = catalogue.loc[catalogue["dataset_name"] == "MODIS LST"].iloc[0]
    assert power_catalogue["citation"] == "Explicit NASA POWER citation"
    assert power_catalogue["licence"] == "Explicit NASA terms"
    assert pd.isna(modis_catalogue["citation"])
    assert pd.isna(modis_catalogue["licence"])
    assert "Unmapped candidate" in log and "no approved canonical site_id mapping" in log
    assert "OMIT MODIS day/night" in log
    assert set(terrain_metrics["site_id"]) == {"jezero", "atacama", "ladakh", "askja"}
    expected_metrics = {
        "slope_p90_deg",
        "pct_area_slope_gt10",
        "pct_area_slope_gt17",
        "pct_area_slope_gt24",
        "roughness",
        "rock_cover_cfa_pct",
        "pct_area_step_gt20cm",
        "pct_area_step_gt35cm",
        "material_class",
    }
    assert set(terrain_metrics["metric_name"]) == expected_metrics
    assert len(terrain_metrics) == 36
    assert pd.to_numeric(terrain_metrics["baseline_m"]).eq(30).all()
    atacama_slope = terrain_metrics.loc[
        (terrain_metrics["site_id"] == "atacama")
        & (terrain_metrics["metric_name"] == "slope_p90_deg")
    ].iloc[0]
    atacama_gt24 = terrain_metrics.loc[
        (terrain_metrics["site_id"] == "atacama")
        & (terrain_metrics["metric_name"] == "pct_area_slope_gt24")
    ].iloc[0]
    ladakh_slope = terrain_metrics.loc[
        (terrain_metrics["site_id"] == "ladakh")
        & (terrain_metrics["metric_name"] == "slope_p90_deg")
    ].iloc[0]
    assert atacama_slope["value"] == 4.0
    assert atacama_slope["value_mean"] == 5.25
    assert atacama_slope["tier"] == "B"
    assert pd.isna(atacama_slope["metric_unit"])
    assert atacama_slope["native_resolution_m"] == 30
    assert not atacama_slope["computed_at_baseline"]
    assert atacama_gt24["value"] == 0.0
    assert atacama_gt24["tier"] == "B"
    assert ladakh_slope["value"] == 4.0
    unavailable = terrain_metrics.loc[
        terrain_metrics["metric_name"].isin(
            {"rock_cover_cfa_pct", "pct_area_step_gt20cm", "pct_area_step_gt35cm", "material_class"}
        )
    ]
    assert unavailable["value"].isna().all()
    assert unavailable["tier"].isna().all()
    askja_slope = terrain_metrics.loc[
        (terrain_metrics["site_id"] == "askja")
        & (terrain_metrics["metric_name"] == "slope_p90_deg")
    ].iloc[0]
    jezero_slope = terrain_metrics.loc[
        (terrain_metrics["site_id"] == "jezero")
        & (terrain_metrics["metric_name"] == "slope_p90_deg")
    ].iloc[0]
    assert pd.isna(askja_slope["value"])
    assert askja_slope["native_resolution_m"] == 30
    assert "CRS review" in askja_slope["availability_note"]
    assert pd.isna(jezero_slope["value"])
    assert pd.isna(jezero_slope["native_resolution_m"])
    assert len(envelope["seasonal_envelopes"]) == 4
    assert envelope["variable_type"] == "surface_temp"
    assert envelope["seasonal_envelopes"][0]["mars_variable"] == "TIRS ground temperature"
    assert all(item["can_rehearse_on_earth"] is None for item in analogy_gaps)
    assert all(item["review_status"] == "draft, pending engineering review" for item in analogy_gaps)
    assert results["temperature_monthly.csv"] == "built"
    assert results["sites.geojson"] == "built"
    assert results["datasets_catalogue.csv"] == "built"
    assert results["terrain_metrics.csv"] == "built"
    assert results["mars_temperature_envelope.json"] == "built"
    assert results["analogy_gaps.json"] == "built"
    assert set(histograms["site_id"]) == {"atacama", "ladakh"}
    assert histograms["bin_end"].sub(histograms["bin_start"]).eq(1).all()
    for site_id, expected_valid in (("atacama", 15), ("ladakh", 16)):
        site_histogram = histograms.loc[histograms["site_id"] == site_id]
        assert site_histogram["pixel_count"].sum() == expected_valid
        assert np.isclose(site_histogram["share"].sum(), 1.0)
    assert set(preview_metadata["site_id"]) == {"atacama", "ladakh"}
    assert preview_metadata["preview_width"].le(800).all()
    for image_path in (processed_dir / preview_metadata["image_path"]).tolist():
        assert image_path.is_file()
    assert set(sites["site_id"]) == {"jezero", "askja", "atacama", "ladakh"}
    assert sites.loc[sites["site_id"] == "askja", "name"].iloc[0] == "Askja, Iceland"
    assert sites.loc[sites["site_id"] == "atacama", "name"].iloc[0] == "Atacama Desert, Chile"
    assert sites.loc[sites["site_id"] == "ladakh", "name"].iloc[0] == "Ladakh, India"
    assert sites.loc[sites["site_id"] == "jezero", "notes"].iloc[0] == (
        "approximate reference coordinate, to be confirmed"
    )
    assert sites.loc[sites["site_id"] == "askja", "notes"].iloc[0] == (
        "centroid of supplied extent footprint"
    )
    for site_id in ("askja", "atacama", "ladakh"):
        site = sites.loc[sites["site_id"] == site_id].iloc[0]
        expected_lon, expected_lat = expected_centroids[site_id]
        assert site["lon"] == expected_lon
        assert site["lat"] == expected_lat
    assert "terrain_parameters.csv" not in results
    assert "CRS" in log and "outside CRS" in log


def test_processed_builder_requires_raw_directory(tmp_path):
    try:
        build_processed(tmp_path / "not-raw", tmp_path / "processed")
    except FileNotFoundError as error:
        assert "Raw data directory" in str(error)
    else:
        raise AssertionError("Expected a missing raw directory to fail clearly")


def test_site_builder_leaves_coordinates_pending_when_extent_sources_are_absent(tmp_path):
    raw_dir = tmp_path / "raw"
    (raw_dir / "large" / "terrain").mkdir(parents=True)
    processed_dir = tmp_path / "processed"

    assert _build_sites(raw_dir, processed_dir)
    sites = load_sites(processed_dir)
    earth_sites = sites.loc[sites["body"] == "Earth"]

    assert set(earth_sites["site_id"]) == {"askja", "atacama", "ladakh"}
    assert earth_sites["lat"].isna().all()
    assert earth_sites["lon"].isna().all()
    assert earth_sites.geometry.isna().all()
    jezero = sites.loc[sites["site_id"] == "jezero"].iloc[0]
    assert jezero["lat"] == 18.4
    assert jezero["lon"] == 77.6
