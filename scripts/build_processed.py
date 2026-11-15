import json
import math
import re
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS
from rasterio.features import geometry_mask
from rasterio.enums import Resampling

from app.utils.terrain import load_terrain_band_config


SCHEMA_VERSION = "1.0"
TEMPERATURE_COLUMNS = [
    "schema_version", "site_id", "month", "variable_type", "temp_min_c",
    "temp_mean_c", "temp_max_c", "pct_in_envelope", "n_valid_obs",
    "n_missing_obs", "source", "period_start", "period_end", "source_label",
    "period_of_day",
]
TERRAIN_METRICS_COLUMNS = [
    "schema_version", "site_id", "metric_name", "value", "value_mean", "value_std",
    "value_min", "value_max", "n_valid_pixels", "metric_unit", "tier", "baseline_m",
    "dem_source", "native_resolution_m", "computed_at_baseline", "roughness_metric",
    "roughness_window", "availability_note", "source_file", "crs", "resolution_x",
    "resolution_y", "resolution_unit", "statistics_scope",
]
SLOPE_HISTOGRAM_COLUMNS = ["site_id", "bin_start", "bin_end", "pixel_count", "share"]
SLOPE_PREVIEW_METADATA_COLUMNS = [
    "site_id", "image_path", "source_file", "crs", "extent_left", "extent_bottom",
    "extent_right", "extent_top", "pixel_size_x", "pixel_size_y", "pixel_size_unit",
    "preview_width", "preview_height",
]
CATALOGUE_COLUMNS = [
    "schema_version", "dataset_name", "source", "url", "file_format",
    "spatial_resolution", "temporal_resolution", "observation_period", "units",
    "crs", "limitations", "citation", "licence",
]
SITE_IDS = {"atacama": "atacama", "ladakh": "ladakh"}
BOUNDARY_LAYER_TO_SITE = {
    "Extent_Askja — extent": "askja",
    "Extent_Atacama — extent": "atacama",
    "Extent_Ladakh — extent": "ladakh",
    "Extent_Jezero Crater — extent": "jezero",
}
SITE_EXTENT_FILES = {
    "askja": ("Extent_Askja.gpkg", "Askja, Iceland"),
    "atacama": ("Extent_Atacama.gpkg", "Atacama Desert, Chile"),
    "ladakh": ("Extent_Ladakh.gpkg", "Ladakh, India"),
}
TERRAIN_DEM_SOURCES = {
    "askja": "Copernicus GLO30",
    "atacama": "Copernicus GLO30",
    "ladakh": "Copernicus GLO30",
}
TERRAIN_MOBILITY_METRICS = (
    "slope_p90_deg",
    "pct_area_slope_gt10",
    "pct_area_slope_gt17",
    "pct_area_slope_gt24",
    "roughness",
    "rock_cover_cfa_pct",
    "pct_area_step_gt20cm",
    "pct_area_step_gt35cm",
    "material_class",
)


def _log(message: str) -> None:
    print(message)


def _build_temperature_monthly(raw_dir: Path, processed_dir: Path) -> bool:
    source_path = raw_dir / "package" / "temperature" / "earth" / "14_earth_site_temperature_summary.csv"
    if not source_path.is_file():
        _log(f"SKIP temperature_monthly.csv: missing preferred source {source_path.relative_to(raw_dir)}")
        return False
    frame = pd.read_csv(source_path)
    required = {
        "site", "period_start", "period_end", "total_calendar_days", "POWER_valid_days",
        "POWER_T2M_mean_C", "POWER_min_T2M_C", "POWER_max_T2M_C",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_path.name} missing required fields: {', '.join(missing)}")
    site_map = {"atacama": "atacama", "ladakh": "ladakh"}
    output = []
    for row_number, row in enumerate(frame.to_dict(orient="records"), start=2):
        site_label = str(row["site"]).strip()
        site_id = site_map.get(site_label.casefold())
        if site_id is None:
            _log(f"DROP {source_path.name} row {row_number}: site label {site_label!r} has no approved canonical site_id mapping.")
            continue
        start = pd.to_datetime(row["period_start"], errors="coerce")
        end = pd.to_datetime(row["period_end"], errors="coerce")
        if pd.isna(start) or pd.isna(end):
            raise ValueError(f"{source_path.name} row {row_number} has invalid observation period.")
        month_values = {int(start.month), int(end.month)}
        if len(month_values) != 1 or start.year != end.year:
            raise ValueError(f"{source_path.name} row {row_number} spans multiple calendar months/years; monthly output is ambiguous.")
        total_days = int(row["total_calendar_days"])
        valid_days = int(row["POWER_valid_days"])
        if valid_days < 0 or valid_days > total_days:
            raise ValueError(f"{source_path.name} row {row_number} has invalid POWER valid-day count.")
        output.append({
            "schema_version": SCHEMA_VERSION,
            "site_id": site_id,
            "month": next(iter(month_values)),
            "variable_type": "air_temp",
            "temp_min_c": row["POWER_T2M_min_C"],
            "temp_mean_c": row["POWER_T2M_mean_C"],
            "temp_max_c": row["POWER_T2M_max_C"],
            "pct_in_envelope": float("nan"),
            "n_valid_obs": valid_days,
            "n_missing_obs": total_days - valid_days,
            "source": f"NASA POWER T2M; {source_path.relative_to(raw_dir).as_posix()}",
            "period_start": start.date().isoformat(),
            "period_end": end.date().isoformat(),
        })
        _log(f"TRANSFORM {site_label} -> {site_id}: POWER_T2M_C min/mean/max copied to Celsius air_temp; valid={valid_days}, missing={total_days-valid_days}; period={start.date()}..{end.date()}.")
    _log("OMIT MODIS day/night values from temperature_monthly.csv: both map to surface_temp, but contract has no period-of-day key or approved aggregation rule; retain source summaries as provenance.")
    _log("SET pct_in_envelope=NaN: the Earth air_temp rows are not compatible with the TIRS ground-temperature seasonal envelope, and no air-temp envelope is supplied.")
    if not output:
        _log("SKIP temperature_monthly.csv: no unambiguously mapped site records remain.")
        return False
    processed_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(output, columns=TEMPERATURE_COLUMNS).to_csv(processed_dir / "temperature_monthly.csv", index=False, na_rep="")
    _log(f"WROTE temperature_monthly.csv: {len(output)} air_temp row(s), sourced from {source_path.relative_to(raw_dir)}.")
    return True


def _read_site_zones(raw_dir: Path) -> dict[str, Any]:
    path = raw_dir / "large" / "terrain" / "site_boundaries.gpkg.geojson"
    if not path.is_file():
        _log(f"SKIP terrain_metrics.csv: extent geometry file is absent: {path.relative_to(raw_dir)}")
        return {}
    zones = gpd.read_file(path)
    result = {}
    for _, row in zones.iterrows():
        layer_name = str(row.get("layer", ""))
        site_id = BOUNDARY_LAYER_TO_SITE.get(layer_name)
        if site_id is None:
            _log(f"DROP boundary feature: unrecognized layer label {layer_name!r}.")
            continue
        if site_id in result:
            raise ValueError(f"Multiple extent polygons found for site_id={site_id!r}.")
        result[site_id] = row.geometry
        _log(f"MAP boundary layer {layer_name!r} -> site_id={site_id}; source attributes identify an Extent layer (not verified field boundary).")
    return result


def _build_sites(raw_dir: Path, processed_dir: Path) -> bool:
    import geopandas as gpd
    from shapely.geometry import Point, mapping

    features = []
    jezero_point = Point(77.6, 18.4)
    features.append(
        {
            "type": "Feature",
            "geometry": mapping(jezero_point),
            "properties": {
                "schema_version": SCHEMA_VERSION,
                "site_id": "jezero",
                "name": "Jezero Crater",
                "body": "Mars",
                "lat": 18.4,
                "lon": 77.6,
                "notes": "approximate reference coordinate, to be confirmed",
            },
        }
    )

    for site_id, (filename, name) in SITE_EXTENT_FILES.items():
        extent_path = raw_dir / "large" / "terrain" / filename
        latitude = longitude = None
        point_geometry = None
        notes = "centroid of supplied extent footprint"
        if extent_path.is_file():
            extents = gpd.read_file(extent_path)
            if not extents.empty and extents.crs is not None and extents.geometry.notna().any():
                geometry = extents.geometry.dropna().union_all()
                if not geometry.is_empty:
                    centroid = gpd.GeoSeries([geometry], crs=extents.crs).to_crs("EPSG:4326").iloc[0].centroid
                    if -180 <= centroid.x <= 180 and -90 <= centroid.y <= 90:
                        longitude = float(centroid.x)
                        latitude = float(centroid.y)
                        point_geometry = Point(longitude, latitude)
        if point_geometry is None:
            notes += "; coordinate pending because no valid supplied extent centroid is available"
            _log(f"PENDING site_id={site_id}: no valid centroid can be derived from {filename}.")
        else:
            _log(f"DERIVE site_id={site_id}: point is centroid of supplied extent footprint at ({longitude},{latitude}) from {filename}.")
        features.append(
            {
                "type": "Feature",
                "geometry": mapping(point_geometry) if point_geometry is not None else None,
                "properties": {
                    "schema_version": SCHEMA_VERSION,
                    "site_id": site_id,
                    "name": name,
                    "body": "Earth",
                    "lat": latitude,
                    "lon": longitude,
                    "notes": notes,
                },
            }
        )

    processed_dir.mkdir(parents=True, exist_ok=True)
    with (processed_dir / "sites.geojson").open("w", encoding="utf-8") as destination:
        json.dump({"type": "FeatureCollection", "features": features}, destination, indent=2)
        destination.write("\n")
    _log("WROTE sites.geojson: Jezero approximate reference plus three Earth extent centroids; unavailable coordinates remain null.")
    return True


def _windowed_zonal_stats(path: Path, geometry: Any | None) -> dict[str, float | int]:
    count = 0
    total = 0.0
    total_sq = 0.0
    minimum = math.inf
    maximum = -math.inf
    dropped = 0
    with rasterio.open(path) as dataset:
        for _, window in dataset.block_windows(1):
            band = dataset.read(1, window=window, masked=True)
            inside = (
                np.ones(band.shape, dtype=bool)
                if geometry is None
                else geometry_mask(
                    [geometry],
                    out_shape=band.shape,
                    transform=dataset.window_transform(window),
                    invert=True,
                    all_touched=False,
                )
            )
            masked = np.ma.getmaskarray(band)
            valid_mask = inside & ~masked & np.isfinite(band.data)
            values = band.data[valid_mask].astype(np.float64, copy=False)
            dropped += int(band.size - values.size)
            if not values.size:
                continue
            count += int(values.size)
            total += float(values.sum(dtype=np.float64))
            total_sq += float(np.square(values, dtype=np.float64).sum(dtype=np.float64))
            minimum = min(minimum, float(values.min()))
            maximum = max(maximum, float(values.max()))
    if not count:
        return {"count": 0, "mean": float("nan"), "std": float("nan"), "min": float("nan"), "max": float("nan"), "dropped": dropped}
    mean = total / count
    variance = max(0.0, total_sq / count - mean * mean)
    return {"count": count, "mean": mean, "std": math.sqrt(variance), "min": minimum, "max": maximum, "dropped": dropped}


def _read_reprojected_slope_metrics(raw_dir: Path) -> dict[str, dict[str, float | int]]:
    metrics_path = raw_dir / "package" / "New_Terrain _metrics.txt"
    if not metrics_path.is_file():
        _log(f"Preferred QGIS slope metrics note missing: {metrics_path.relative_to(raw_dir)}; slope will use block-window raster stats.")
        return {}
    lines = metrics_path.read_text(encoding="utf-8", errors="replace").splitlines()
    results: dict[str, dict[str, float | int]] = {}
    pending_site_id = None
    for line in lines:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        input_path = payload.get("INPUT")
        if input_path:
            filename = str(input_path).replace("\\", "/").rsplit("/", 1)[-1]
            suffix = "_Reprojected_slope.tif"
            pending_site_id = (
                filename[:-len(suffix)].casefold()
                if filename.endswith(suffix)
                else None
            )
            continue
        if "COUNT" not in payload or pending_site_id is None:
            continue
        results[pending_site_id] = {
            "count": int(payload["COUNT"]),
            "min": float(payload["MIN"]),
            "max": float(payload["MAX"]),
            "mean": float(payload["MEAN"]),
            "std": float(payload["STD_DEV"]),
            "dropped": 0,
        }
        _log(f"USE preferred QGIS slope stats for {pending_site_id} from {metrics_path.relative_to(raw_dir)}: count={payload['COUNT']}, mean={payload['MEAN']}, min={payload['MIN']}, max={payload['MAX']}, std={payload['STD_DEV']}.")
        pending_site_id = None
    return results


def _slope_mobility_stats(path: Path) -> dict[str, float | int]:
    value_blocks = []
    count = 0
    over_threshold = {10: 0, 17: 0, 24: 0}
    with rasterio.open(path) as dataset:
        for _, window in dataset.block_windows(1):
            band = dataset.read(1, window=window, masked=True)
            values = band.compressed()
            values = values[np.isfinite(values)]
            if not values.size:
                continue
            count += int(values.size)
            value_blocks.append(values)
            for threshold in over_threshold:
                over_threshold[threshold] += int(np.count_nonzero(values > threshold))
    if not count:
        return {
            "slope_p90_deg": float("nan"),
            **{f"pct_area_slope_gt{threshold}": float("nan") for threshold in over_threshold},
            "n_valid_pixels": 0,
        }
    values = np.concatenate(value_blocks)
    return {
        "slope_p90_deg": float(np.percentile(values, 90)),
        **{
            f"pct_area_slope_gt{threshold}": 100.0 * over_threshold[threshold] / count
            for threshold in over_threshold
        },
        "n_valid_pixels": count,
    }


def _slope_histogram(path: Path, site_id: str) -> list[dict[str, Any]]:
    """Compute 1-unit bins from raster blocks, excluding masked and non-finite pixels."""
    minimum = math.inf
    maximum = -math.inf
    valid_total = 0
    with rasterio.open(path) as dataset:
        for _, window in dataset.block_windows(1):
            band = dataset.read(1, window=window, masked=True)
            values = band.compressed()
            values = values[np.isfinite(values)]
            if not values.size:
                continue
            valid_total += int(values.size)
            minimum = min(minimum, float(values.min()))
            maximum = max(maximum, float(values.max()))
        if valid_total == 0:
            return []

        first_bin = math.floor(minimum)
        last_bin = math.floor(maximum)
        bin_edges = np.arange(first_bin, last_bin + 2, dtype=np.float64)
        counts = np.zeros(last_bin - first_bin + 1, dtype=np.int64)
        for _, window in dataset.block_windows(1):
            band = dataset.read(1, window=window, masked=True)
            values = band.compressed()
            values = values[np.isfinite(values)]
            if values.size:
                counts += np.histogram(values, bins=bin_edges)[0]

    return [
        {
            "site_id": site_id,
            "bin_start": float(bin_edges[index]),
            "bin_end": float(bin_edges[index + 1]),
            "pixel_count": int(count),
            "share": float(count / valid_total),
        }
        for index, count in enumerate(counts)
    ]


def _write_slope_preview(
    dataset: rasterio.io.DatasetReader,
    raw_dir: Path,
    processed_dir: Path,
    site_id: str,
    source_path: Path,
) -> dict[str, Any]:
    from PIL import Image

    width = min(dataset.width, 800)
    scale = width / dataset.width
    height = max(1, round(dataset.height * scale))
    band = dataset.read(
        1,
        out_shape=(height, width),
        resampling=Resampling.nearest,
        masked=True,
    )
    values = band.compressed()
    pixels = np.full((height, width), 220, dtype=np.uint8)
    if values.size:
        low = float(values.min())
        high = float(values.max())
        if high > low:
            scaled = np.clip((band.filled(low).astype(np.float64) - low) / (high - low), 0, 1)
            pixels = (255 * (1 - scaled)).astype(np.uint8)
            pixels[np.ma.getmaskarray(band)] = 220
        else:
            pixels[~np.ma.getmaskarray(band)] = 128
    preview_dir = processed_dir / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / f"{site_id}_slope.png"
    Image.fromarray(pixels, mode="L").save(preview_path, format="PNG")
    return {
        "site_id": site_id,
        "image_path": preview_path.relative_to(processed_dir).as_posix(),
        "source_file": source_path.relative_to(raw_dir).as_posix(),
        "crs": str(dataset.crs),
        "extent_left": float(dataset.bounds.left),
        "extent_bottom": float(dataset.bounds.bottom),
        "extent_right": float(dataset.bounds.right),
        "extent_top": float(dataset.bounds.top),
        "pixel_size_x": float(abs(dataset.res[0])),
        "pixel_size_y": float(abs(dataset.res[1])),
        "pixel_size_unit": CRS.from_user_input(dataset.crs).axis_info[0].unit_name
        if dataset.crs and CRS.from_user_input(dataset.crs).axis_info
        else "unknown",
        "preview_width": width,
        "preview_height": height,
    }


def _site_crs_is_usable(site_id: str, raster_crs: CRS, geometry_wgs84: Any) -> tuple[bool, str]:
    point = geometry_wgs84.centroid
    epsg = raster_crs.to_epsg()
    area_crs = CRS.from_epsg(epsg) if epsg is not None else raster_crs
    area = area_crs.area_of_use
    if area is not None and not (area.west <= point.x <= area.east and area.south <= point.y <= area.north):
        return False, f"site center ({point.x:.6f},{point.y:.6f}) is outside CRS {raster_crs.to_string()} area of use ({area.west},{area.south},{area.east},{area.north})"
    if not raster_crs.is_projected:
        return False, f"raster CRS {raster_crs.to_string()} is not projected"
    return True, f"CRS {raster_crs.to_string()} area of use contains the site center"


def _build_terrain_metrics(raw_dir: Path, processed_dir: Path) -> bool:
    import geopandas as gpd

    terrain_dir = raw_dir / "large" / "terrain"
    zones = _read_site_zones(raw_dir)
    qgis_slopes = _read_reprojected_slope_metrics(raw_dir)
    band_config = load_terrain_band_config()
    baseline_m = float(band_config["baseline_m"])
    metrics_by_site: dict[str, dict[str, dict[str, Any]]] = {}
    site_metadata: dict[str, dict[str, Any]] = {}
    site_notes: dict[str, str] = {}
    site_paths = {}
    slope_histogram_rows = []
    slope_preview_rows = []

    for site_id, _ in (("jezero", "Jezero"), ("atacama", "Atacama"), ("ladakh", "Ladakh"), ("askja", "Askja")):
        matching = {
            "elevation": terrain_dir / f"{site_id.title()}_Reprojected.tif",
            "slope": terrain_dir / f"{site_id.title()}_Reprojected_slope.tif",
            "roughness": terrain_dir / f"{site_id.title()}_Reprojected_roughness.tif",
        }
        site_paths[site_id] = matching
        metadata_path = next((path for path in matching.values() if path.is_file()), None)
        metadata = {
            "dem_source": TERRAIN_DEM_SOURCES.get(site_id, ""),
            "native_resolution_m": float("nan"),
            "crs": "",
            "resolution_x": float("nan"),
            "resolution_y": float("nan"),
            "resolution_unit": "",
        }
        if metadata_path is not None:
            with rasterio.open(metadata_path) as dataset:
                raster_crs = CRS.from_user_input(dataset.crs)
                resolution_x, resolution_y = map(float, dataset.res)
                unit = raster_crs.axis_info[0].unit_name if raster_crs.axis_info else "unknown"
                metadata.update(
                    {
                        "crs": str(dataset.crs),
                        "resolution_x": resolution_x,
                        "resolution_y": resolution_y,
                        "resolution_unit": unit,
                    }
                )
                if raster_crs.is_projected and unit.casefold() in {"metre", "meter"}:
                    metadata["native_resolution_m"] = (abs(resolution_x) + abs(resolution_y)) / 2
        site_metadata[site_id] = metadata
        site_notes[site_id] = "No usable terrain raster is available for this site."

    for site_id in ("atacama", "ladakh", "askja"):
        zone = zones.get(site_id)
        matching = site_paths[site_id]
        absent = [name for name, path in matching.items() if not path.is_file()]
        if zone is None:
            site_notes[site_id] = "Terrain metrics pending: no supplied extent geometry is available."
            continue
        if absent:
            site_notes[site_id] = f"Terrain metrics pending: preferred reprojected raster(s) absent for {', '.join(absent)}."
            continue
        with rasterio.open(matching["slope"]) as slope_ds:
            raster_crs = CRS.from_user_input(slope_ds.crs)
            usable, reason = _site_crs_is_usable(site_id, raster_crs, zone)
            if not usable:
                site_notes[site_id] = f"Terrain metrics pending CRS review: {reason}."
                _log(f"PENDING terrain site_id={site_id}: {site_notes[site_id]}")
                continue
            zone_in_raster_crs = gpd.GeoSeries([zone], crs="EPSG:4326").to_crs(slope_ds.crs).iloc[0]
            tolerance = max(slope_ds.res) * 2
            if any(abs(a - b) > tolerance for a, b in zip(slope_ds.bounds, zone_in_raster_crs.bounds)):
                site_notes[site_id] = "Terrain metrics pending: supplied extent does not align with raster bounds."
                continue

        slope_path = matching["slope"]
        roughness_path = matching["roughness"]
        slope_histogram_rows.extend(_slope_histogram(slope_path, site_id))
        with rasterio.open(slope_path) as preview_dataset:
            slope_preview_rows.append(
                _write_slope_preview(preview_dataset, raw_dir, processed_dir, site_id, slope_path)
            )
        slope_stats = _slope_mobility_stats(slope_path)
        roughness_stats = _windowed_zonal_stats(roughness_path, None)
        raster_stats = qgis_slopes.get(site_id, {})
        metric_values = {
            "slope_p90_deg": slope_stats["slope_p90_deg"],
            "pct_area_slope_gt10": slope_stats["pct_area_slope_gt10"],
            "pct_area_slope_gt17": slope_stats["pct_area_slope_gt17"],
            "pct_area_slope_gt24": slope_stats["pct_area_slope_gt24"],
            "roughness": roughness_stats["mean"],
        }
        metrics_by_site[site_id] = {
            name: {
                "value": value,
                "stats": roughness_stats if name == "roughness" else raster_stats,
                "source_path": roughness_path if name == "roughness" else slope_path,
                "n_valid_pixels": (
                    roughness_stats["count"] if name == "roughness" else slope_stats["n_valid_pixels"]
                ),
            }
            for name, value in metric_values.items()
        }
        site_notes[site_id] = (
            "Provisional Tier B; computed at native resolution from all valid pixels in the supplied raster extent, "
            "not resampled to the 30 m baseline; extent is not a validated site boundary."
        )
        _log(
            f"TRANSFORM terrain site_id={site_id}: slope P90={slope_stats['slope_p90_deg']}; "
            f"area >10={slope_stats['pct_area_slope_gt10']}; >17={slope_stats['pct_area_slope_gt17']}; "
            f">24={slope_stats['pct_area_slope_gt24']}; roughness mean={roughness_stats['mean']}."
        )

    jezero_files = [path for path in terrain_dir.glob("*") if "jezero" in path.name.casefold() and path.suffix.casefold() in {".tif", ".tiff"}]
    site_notes["jezero"] = (
        "Terrain metrics pending: no Jezero terrain raster is present; its supplied extent is invalid under EPSG:4326."
        if not jezero_files
        else "Terrain metrics pending: Jezero raster georeferencing and extent require review."
    )
    _log(f"Jezero terrain rasters found: {len(jezero_files)}.")

    metric_units = {
        "slope_p90_deg": "",
        "pct_area_slope_gt10": "%",
        "pct_area_slope_gt17": "%",
        "pct_area_slope_gt24": "%",
        "roughness": "",
        "rock_cover_cfa_pct": "%",
        "pct_area_step_gt20cm": "%",
        "pct_area_step_gt35cm": "%",
        "material_class": "",
    }
    source_paths = {
        "slope_p90_deg": "slope",
        "pct_area_slope_gt10": "slope",
        "pct_area_slope_gt17": "slope",
        "pct_area_slope_gt24": "slope",
        "roughness": "roughness",
    }
    output = []
    for site_id in ("jezero", "atacama", "ladakh", "askja"):
        metadata = site_metadata[site_id]
        site_values = metrics_by_site.get(site_id, {})
        for metric_name in TERRAIN_MOBILITY_METRICS:
            metric = site_values.get(metric_name)
            source_key = source_paths.get(metric_name)
            source_path = site_paths[site_id].get(source_key) if source_key else None
            if metric is None:
                missing_note = site_notes[site_id]
                if site_id in metrics_by_site:
                    missing_note = f"No supplied source for {metric_name}; value remains missing."
                value = float("nan")
                stats = {}
                pixel_count = float("nan")
                tier = ""
                scope = missing_note
            else:
                missing_note = site_notes[site_id]
                value = metric["value"]
                stats = metric["stats"]
                pixel_count = metric["n_valid_pixels"]
                tier = "B"
                scope = "all valid pixels in whole supplied raster extent; not a validated site boundary"
                source_path = metric["source_path"]
            output.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "site_id": site_id,
                    "metric_name": metric_name,
                    "value": value,
                    "value_mean": stats.get("mean", float("nan")),
                    "value_std": stats.get("std", float("nan")),
                    "value_min": stats.get("min", float("nan")),
                    "value_max": stats.get("max", float("nan")),
                    "n_valid_pixels": pixel_count,
                    "metric_unit": metric_units[metric_name],
                    "tier": tier,
                    "baseline_m": baseline_m,
                    "dem_source": metadata["dem_source"],
                    "native_resolution_m": metadata["native_resolution_m"],
                    "computed_at_baseline": False if not pd.isna(metadata["native_resolution_m"]) else float("nan"),
                    "roughness_metric": "",
                    "roughness_window": "",
                    "availability_note": missing_note,
                    "source_file": source_path.relative_to(raw_dir).as_posix() if source_path and source_path.is_file() else "",
                    "crs": metadata["crs"],
                    "resolution_x": metadata["resolution_x"],
                    "resolution_y": metadata["resolution_y"],
                    "resolution_unit": metadata["resolution_unit"],
                    "statistics_scope": scope,
                }
            )
    if not output:
        _log("SKIP terrain_metrics.csv: no requested mobility metric records could be represented.")
        return False
    processed_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(output, columns=TERRAIN_METRICS_COLUMNS).to_csv(processed_dir / "terrain_metrics.csv", index=False, na_rep="")
    pd.DataFrame(slope_histogram_rows, columns=SLOPE_HISTOGRAM_COLUMNS).to_csv(
        processed_dir / "slope_histograms.csv", index=False, na_rep=""
    )
    pd.DataFrame(slope_preview_rows, columns=SLOPE_PREVIEW_METADATA_COLUMNS).to_csv(
        processed_dir / "slope_preview_metadata.csv", index=False, na_rep=""
    )
    _log(
        f"WROTE slope_histograms.csv: {len(slope_histogram_rows)} bins across "
        f"{len(slope_preview_rows)} CRS-accepted site(s); wrote matching decimated previews."
    )
    _log(f"WROTE terrain_metrics.csv: {len(output)} site/metric records with missing values left blank.")
    return True


def _build_temperature_monthly(raw_dir: Path, processed_dir: Path) -> bool:
    source_path = raw_dir / "package" / "temperature" / "earth" / "14_earth_site_temperature_summary.csv"
    if not source_path.is_file():
        raise FileNotFoundError(f"Preferred Earth summary is missing: {source_path}")
    frame = pd.read_csv(source_path)
    required = {
        "site", "period_start", "period_end", "total_calendar_days", "POWER_valid_days",
        "POWER_T2M_mean_C", "POWER_T2M_min_C", "POWER_T2M_max_C",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_path.name} missing required column(s): {', '.join(missing)}")
    site_map = {"atacama": "atacama", "iceland": "askja", "ladakh": "ladakh"}
    modis_fields = {
        f"MODIS_{period}_{stat}_C"
        for period in ("day", "night")
        for stat in ("mean", "min", "max")
    } | {f"MODIS_{period}_valid_days" for period in ("day", "night")}
    modis_present = modis_fields & set(frame.columns)
    if modis_present and modis_present != modis_fields:
        missing_modis = sorted(modis_fields - modis_present)
        raise ValueError(
            f"{source_path.name} has an incomplete MODIS day/night summary; "
            f"missing {', '.join(missing_modis)}"
        )
    output = []
    for row_number, source_row in enumerate(frame.to_dict(orient="records"), start=2):
        site_label = str(source_row["site"]).strip()
        site_id = site_map.get(site_label.casefold())
        if site_id is None:
            _log(f"DROP {source_path.name} row {row_number}: site label {site_label!r} has no approved canonical site_id mapping.")
            continue
        start = pd.to_datetime(source_row["period_start"], errors="coerce")
        end = pd.to_datetime(source_row["period_end"], errors="coerce")
        if pd.isna(start) or pd.isna(end) or start.year != end.year or start.month != end.month:
            raise ValueError(f"{source_path.name} row {row_number} has an invalid or multi-month period.")
        total_days = int(source_row["total_calendar_days"])
        valid_days = int(source_row["POWER_valid_days"])
        if not (0 <= valid_days <= total_days):
            raise ValueError(f"{source_path.name} row {row_number} valid count is outside 0..total_calendar_days.")
        common = {
            "schema_version": SCHEMA_VERSION,
            "site_id": site_id,
            "month": int(start.month),
            "pct_in_envelope": float("nan"),
            "period_start": start.date().isoformat(),
            "period_end": end.date().isoformat(),
            "source_label": site_label,
        }
        relative_source = source_path.relative_to(raw_dir).as_posix()
        output.append({
            **common,
            "variable_type": "air_temp",
            "temp_min_c": source_row["POWER_T2M_min_C"],
            "temp_mean_c": source_row["POWER_T2M_mean_C"],
            "temp_max_c": source_row["POWER_T2M_max_C"],
            "n_valid_obs": valid_days,
            "n_missing_obs": total_days - valid_days,
            "source": f"NASA POWER T2M; {relative_source}",
            "period_of_day": "daily",
        })
        if modis_present:
            for period in ("day", "night"):
                modis_valid = int(source_row[f"MODIS_{period}_valid_days"])
                if not 0 <= modis_valid <= total_days:
                    raise ValueError(
                        f"{source_path.name} row {row_number} has invalid MODIS {period} valid-day count."
                    )
                output.append({
                    **common,
                    "variable_type": "surface_temp",
                    "temp_min_c": source_row[f"MODIS_{period}_min_C"],
                    "temp_mean_c": source_row[f"MODIS_{period}_mean_C"],
                    "temp_max_c": source_row[f"MODIS_{period}_max_C"],
                    "n_valid_obs": modis_valid,
                    "n_missing_obs": total_days - modis_valid,
                    "source": f"MODIS LST {period}; {relative_source}",
                    "period_of_day": period,
                })
        _log(
            f"TRANSFORM {site_label!r}->{site_id}: preserved source_label; copied POWER daily "
            f"and separate MODIS day/night values where supplied; POWER valid={valid_days}; "
            f"period={start.date()}..{end.date()}."
        )
    _log("KEEP MODIS day/night measurements separate; no day/night aggregate was computed.")
    _log("KEEP pct_in_envelope as NaN: no single monthly envelope percentage is supplied by this source.")
    if not output:
        _log("SKIP temperature_monthly.csv: no explicitly mapped sites remain.")
        return False
    processed_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(output, columns=TEMPERATURE_COLUMNS).to_csv(processed_dir / "temperature_monthly.csv", index=False, na_rep="")
    _log(f"WROTE temperature_monthly.csv: {len(output)} separate temperature-series rows.")
    return True


def _build_mars_temperature_envelope(raw_dir: Path, processed_dir: Path) -> bool:
    source_path = raw_dir / "package" / "temperature" / "validation" / "handover" / "05_EARTH_MARS_FINAL_RECALCULATED_TABLE.csv"
    if not source_path.is_file():
        raise FileNotFoundError(f"Preferred recalculated comparison is missing: {source_path}")
    frame = pd.read_csv(source_path)
    required = {"mars_variable", "mars_season", "mars_p05_C", "mars_p95_C", "comparison_class"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_path.name} missing required column(s): {', '.join(missing)}")
    classes = set(frame["comparison_class"].dropna().astype(str))
    variables = set(frame["mars_variable"].dropna().astype(str))
    if classes != {"SURFACE_TEMPERATURE"} or variables != {"TIRS ground temperature"}:
        raise ValueError(f"Ambiguous envelope scope: classes={sorted(classes)}, Mars variables={sorted(variables)}")
    envelope_rows = []
    for season, group in frame.groupby("mars_season", sort=False):
        pairs = group[["mars_p05_C", "mars_p95_C"]].drop_duplicates()
        if len(pairs) != 1:
            raise ValueError(f"Season {season!r} has {len(pairs)} different P05/P95 pairs; refusing to choose one.")
        p05 = pd.to_numeric(pairs.iloc[0]["mars_p05_C"], errors="coerce")
        p95 = pd.to_numeric(pairs.iloc[0]["mars_p95_C"], errors="coerce")
        if pd.isna(p05) or pd.isna(p95) or p05 > p95:
            raise ValueError(f"Season {season!r} has invalid explicit P05/P95 thresholds.")
        envelope_rows.append({"season": str(season), "min_c": float(p05), "max_c": float(p95), "mars_variable": "TIRS ground temperature", "comparison_class": "SURFACE_TEMPERATURE"})
        _log(f"MAP envelope season={season}: exact source P05={p05} C, P95={p95} C; no cross-season collapsing.")
    expected_seasons = {"Northern Spring", "Northern Summer", "Northern Autumn", "Northern Winter"}
    if {row["season"] for row in envelope_rows} != expected_seasons:
        raise ValueError(f"Envelope seasons differ from expected explicit four-season set: {[row['season'] for row in envelope_rows]}.")
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "variable_type": "surface_temp",
        "min_c": None,
        "max_c": None,
        "source": source_path.relative_to(raw_dir).as_posix(),
        "notes": "Season-specific TIRS GROUND_TEMP P05-P95 intervals copied from the final recalculated surface-temperature comparison. No single global min/max is asserted; Earth comparisons are exploratory and not a direct matched-site experiment.",
        "seasonal_envelopes": envelope_rows,
    }
    ls_coverage_path = raw_dir / "package" / "temperature" / "documentation" / "66_FINAL_WORKSTREAM_UPDATE.txt"
    if ls_coverage_path.is_file():
        ls_text = ls_coverage_path.read_text(encoding="utf-8", errors="replace")
        coverage_match = re.search(
            r"Ls coverage currently:\s*([0-9.]+)% of the ([0-9,]+)-sol temperature reference\.\s*"
            r"- ([0-9,]+) sols have an Ls reference\.",
            ls_text,
        )
        if coverage_match:
            envelope["solar_longitude_mapping"] = {
                "coverage_percent": float(coverage_match.group(1)),
                "mapped_ats_sols": int(coverage_match.group(3).replace(",", "")),
                "total_ats_sols": int(coverage_match.group(2).replace(",", "")),
                "source": ls_coverage_path.relative_to(raw_dir).as_posix(),
            }
            _log(
                "COPY official ATS Ls mapping coverage: "
                f"{coverage_match.group(1)}%; "
                f"{coverage_match.group(3)} of {coverage_match.group(2)} sols."
            )
    processed_dir.mkdir(parents=True, exist_ok=True)
    with (processed_dir / "mars_temperature_envelope.json").open("w", encoding="utf-8") as destination:
        json.dump(envelope, destination, indent=2, ensure_ascii=False)
        destination.write("\n")
    _log(f"WROTE mars_temperature_envelope.json: {len(envelope_rows)} explicit TIRS ground-temperature seasonal bands; global min_c/max_c remain null.")
    return True


def _build_analogy_gaps(raw_dir: Path, processed_dir: Path) -> bool:
    reviewed_path = raw_dir.parent / "sample" / "analogy_gaps.json"
    if reviewed_path.is_file():
        with reviewed_path.open(encoding="utf-8") as source:
            reviewed_items = json.load(source)
        if not isinstance(reviewed_items, list):
            raise ValueError(f"{reviewed_path.name} must contain a JSON list.")
        processed_dir.mkdir(parents=True, exist_ok=True)
        with (processed_dir / "analogy_gaps.json").open("w", encoding="utf-8") as destination:
            json.dump(reviewed_items, destination, indent=2, ensure_ascii=False)
            destination.write("\n")
        _log(
            f"WROTE analogy_gaps.json: copied {len(reviewed_items)} reviewed entries "
            "without dropping fields or changing decisions/text."
        )
        return True

    source_path = raw_dir / "package" / "temperature" / "validation" / "FINAL_REVISED_SCIENTIFIC_LIMITATIONS_REGISTER.csv"
    if not source_path.is_file():
        _log(f"SKIP analogy_gaps.json: limitations register not found at {source_path.relative_to(raw_dir)}.")
        return False
    frame = pd.read_csv(source_path)
    required = {"topic", "status", "finding", "next_action"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_path.name} missing columns: {', '.join(missing)}")
    items = []
    for row_number, source_row in enumerate(frame.to_dict(orient="records"), start=2):
        factor = str(source_row["topic"]).strip()
        if not factor:
            _log(f"DROP {source_path.name} row {row_number}: empty topic.")
            continue
        items.append({
            "schema_version": SCHEMA_VERSION,
            "factor": factor,
            "can_rehearse_on_earth": None,
            "explanation": f"{source_row['finding']} Next action: {source_row['next_action']}",
            "review_status": "draft, pending engineering review",
            "source": source_path.relative_to(raw_dir).as_posix(),
        })
        _log(f"TRANSFORM limitations row {row_number}: copy topic/status finding into draft gap; decision remains null pending engineering review.")
    processed_dir.mkdir(parents=True, exist_ok=True)
    with (processed_dir / "analogy_gaps.json").open("w", encoding="utf-8") as destination:
        json.dump(items, destination, indent=2, ensure_ascii=False)
        destination.write("\n")
    _log(f"WROTE analogy_gaps.json: {len(items)} draft limitation item(s), all pending engineering review.")
    return True


def _build_catalogue(raw_dir: Path, processed_dir: Path) -> bool:
    sources_path = raw_dir / "package" / "TERRAOPS_Data_Sources.csv"
    inventory_path = raw_dir / "package" / "MASTER_TEMPERATURE_DATASET_INVENTORY.csv"
    if not sources_path.is_file() or not inventory_path.is_file():
        _log("SKIP datasets_catalogue.csv: source registry or dataset inventory is absent.")
        return False
    sources = pd.read_csv(sources_path)
    inventory = pd.read_csv(inventory_path)
    known = {
        "NASA POWER": ("CSV", "Daily", "2024-07-01 to 2024-07-31", "Celsius", "2 m gridded near-surface air temperature; July 2024 only."),
        "MODIS LST": ("CSV", "Daily day/night summaries", "2024-07-01 to 2024-07-31", "Celsius", "Surface skin temperature; not air temperature; coverage varies and exact local-time match is unavailable."),
        "Mars MEDA TIRS": ("Parquet", "Per observation; local solar time fields supplied", "Sol 1 to 1859; 1,751 sols stated", "Celsius", "AIR_TEMP and GROUND_TEMP are in Celsius; uncertainty is in K and irradiance units require source verification. Flag semantics and dynamic geometry require verification."),
        "Mars MEDA ATS": ("Parquet", "Per observation; local solar time fields supplied", "Sol 1 to 1859; 1,754 sols stated", "Celsius", "Five sensor channels remain separate; values are converted to Celsius. Geometry and time matching limitations apply."),
    }
    inv = inventory.set_index("dataset", drop=False)
    rows = []
    for source_row in sources.to_dict(orient="records"):
        registry_name = str(source_row["dataset"])
        names = {"Mars MEDA ATS and TIRS": ["Mars MEDA TIRS", "Mars MEDA ATS"], "MODIS": ["MODIS LST"]}.get(registry_name, [registry_name])
        for name in names:
            values = known.get(name)
            invrow = inv.loc[name].to_dict() if name in inv.index else {}
            if isinstance(invrow, pd.DataFrame):
                raise ValueError(f"Multiple inventory definitions found for {name}.")
            if values is None:
                file_format = temporal = period = units = limitations = float("nan")
            else:
                file_format, temporal, period, units, limitations = values
            if pd.isna(period):
                period = invrow.get("coverage", float("nan"))
            if pd.isna(limitations):
                limitations = invrow.get("notes", float("nan"))
            record = {
                "schema_version": SCHEMA_VERSION,
                "dataset_name": name,
                "source": source_row.get("source"),
                "url": source_row.get("url"),
                "file_format": file_format,
                "spatial_resolution": float("nan"),
                "temporal_resolution": temporal,
                "observation_period": period,
                "units": units,
                "crs": float("nan"),
                "limitations": limitations,
                "citation": source_row.get("citation", float("nan")),
                "licence": source_row.get("licence", float("nan")),
            }
            for provenance_field in ("citation", "licence"):
                provenance_value = record[provenance_field]
                if pd.isna(provenance_value) or not str(provenance_value).strip():
                    record[provenance_field] = float("nan")
            rows.append(record)
            _log(f"TRANSFORM catalogue {name}: copy registry name/provider/URL and explicitly documented inventory fields; unresolved spatial resolution/CRS/citation/licence stay NaN.")
    processed_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=CATALOGUE_COLUMNS).to_csv(processed_dir / "datasets_catalogue.csv", index=False, na_rep="")
    _log(f"WROTE datasets_catalogue.csv: {len(rows)} records.")
    return bool(rows)


def build_processed(raw_dir: str | Path | None = None, processed_dir: str | Path | None = None) -> dict[str, str]:
    project_root = Path(__file__).resolve().parents[1]
    raw_root = Path(raw_dir) if raw_dir is not None else project_root / "data" / "raw"
    output_root = Path(processed_dir) if processed_dir is not None else project_root / "data" / "processed"
    if not raw_root.is_dir():
        raise FileNotFoundError(f"Raw data directory does not exist: {raw_root}")

    results = {
        "sites.geojson": "built" if _build_sites(raw_root, output_root) else "skipped",
        "terrain_metrics.csv": "built" if _build_terrain_metrics(raw_root, output_root) else "skipped",
        "temperature_monthly.csv": "built" if _build_temperature_monthly(raw_root, output_root) else "skipped",
        "mars_temperature_envelope.json": "built" if _build_mars_temperature_envelope(raw_root, output_root) else "skipped",
        "analogy_gaps.json": "built" if _build_analogy_gaps(raw_root, output_root) else "skipped",
        "datasets_catalogue.csv": "built" if _build_catalogue(raw_root, output_root) else "skipped",
    }
    _log("Raw source files were read only; data/raw/ was not modified.")
    return results


def main() -> None:
    build_processed()


if __name__ == "__main__":
    main()
