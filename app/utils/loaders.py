import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from app.utils.config import get_data_file_path, get_data_file_source
from app.utils.validation import (
    DataContractError,
    check_temperature_variable_types,
    require_columns,
    require_json_keys,
    validate_coordinates_degrees,
    validate_months,
    validate_numeric_columns,
    validate_schema_version,
    validate_unit_values,
    validate_variable_types,
)


SITE_COLUMNS = ("schema_version", "site_id", "name", "body", "lat", "lon", "notes")
TERRAIN_COLUMNS = (
    "schema_version",
    "site_id",
    "elevation_mean_m",
    "elevation_std_m",
    "slope_mean_deg",
    "slope_p95_deg",
    "roughness_metric",
    "roughness_unit",
    "dem_source",
    "resolution_m",
)
TERRAIN_METRICS_COLUMNS = (
    "schema_version",
    "site_id",
    "metric_name",
    "value",
    "value_mean",
    "value_std",
    "value_min",
    "value_max",
    "n_valid_pixels",
    "metric_unit",
    "tier",
    "baseline_m",
    "dem_source",
    "native_resolution_m",
    "computed_at_baseline",
    "roughness_metric",
    "roughness_window",
    "availability_note",
    "source_file",
    "crs",
    "resolution_x",
    "resolution_y",
    "resolution_unit",
    "statistics_scope",
)
TEMPERATURE_COLUMNS = (
    "schema_version",
    "site_id",
    "month",
    "variable_type",
    "temp_min_c",
    "temp_mean_c",
    "temp_max_c",
    "pct_in_envelope",
    "n_valid_obs",
    "n_missing_obs",
    "source",
    "period_start",
    "period_end",
    "source_label",
    "period_of_day",
)
ENVELOPE_KEYS = ("schema_version", "variable_type", "min_c", "max_c", "source", "notes")
CATALOGUE_COLUMNS = (
    "schema_version",
    "dataset_name",
    "source",
    "url",
    "file_format",
    "spatial_resolution",
    "temporal_resolution",
    "observation_period",
    "units",
    "crs",
    "limitations",
    "citation",
    "licence",
)


def _data_file(filename: str, data_dir: str | Path | None) -> Path:
    if data_dir is None:
        return get_data_file_path(filename)
    folder = Path(data_dir)
    path = folder / filename
    if not path.is_file():
        raise FileNotFoundError(f"Required data file not found: {path}")
    return path


def _read_csv(filename: str, required: tuple[str, ...], data_dir: str | Path | None) -> pd.DataFrame:
    path = _data_file(filename, data_dir)
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as error:
        raise DataContractError(f"Could not read {path}: {error}") from error
    require_columns(frame, required, filename)
    validate_schema_version(frame["schema_version"], filename)
    return frame


def _read_json(filename: str, data_dir: str | Path | None):
    path = _data_file(filename, data_dir)
    try:
        with path.open(encoding="utf-8") as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError) as error:
        raise DataContractError(f"Could not read valid JSON from {path}: {error}") from error


def load_sites(data_dir: str | Path | None = None) -> gpd.GeoDataFrame:
    filename = "sites.geojson"
    path = _data_file(filename, data_dir)
    try:
        sites = gpd.read_file(path)
    except Exception as error:
        raise DataContractError(f"Could not read {path} as GeoJSON: {error}") from error
    require_columns(sites, SITE_COLUMNS, filename)
    validate_schema_version(sites["schema_version"], filename)
    validate_coordinates_degrees(sites, filename)
    invalid_body = sites["body"].notna() & ~sites["body"].isin({"Mars", "Earth"})
    if invalid_body.any():
        raise DataContractError(f"{filename} body values must be Mars or Earth.")
    return sites


def load_terrain_parameters(data_dir: str | Path | None = None) -> pd.DataFrame:
    filename = "terrain_parameters.csv"
    frame = _read_csv(filename, TERRAIN_COLUMNS, data_dir)
    validate_numeric_columns(
        frame,
        (
            "elevation_mean_m",
            "elevation_std_m",
            "slope_mean_deg",
            "slope_p95_deg",
            "roughness_metric",
            "resolution_m",
        ),
        filename,
    )
    validate_unit_values(frame["roughness_unit"], filename, "roughness_unit")
    return frame


def load_terrain_metrics(data_dir: str | Path | None = None) -> pd.DataFrame:
    filename = "terrain_metrics.csv"
    frame = _read_csv(filename, TERRAIN_METRICS_COLUMNS, data_dir)
    validate_numeric_columns(
        frame,
        (
            "value_mean",
            "value_std",
            "value_min",
            "value_max",
            "n_valid_pixels",
            "baseline_m",
            "native_resolution_m",
            "resolution_x",
            "resolution_y",
        ),
        filename,
    )
    numeric_metrics = frame.loc[frame["metric_name"] != "material_class"]
    validate_numeric_columns(numeric_metrics, ("value",), filename)
    for column in ("baseline_m", "native_resolution_m"):
        invalid = frame[column].notna() & frame[column].le(0)
        if invalid.any():
            raise DataContractError(f"{filename} column {column!r} must be positive when present.")
    tiers = frame["tier"].dropna().astype(str).str.strip()
    invalid_tiers = sorted(set(tiers) - {"A", "B"})
    if invalid_tiers:
        raise DataContractError(
            f"{filename} tier must be A, B, or blank; found {', '.join(invalid_tiers)}."
        )
    valued = frame["value"].notna()
    tiered = frame["tier"].notna() & frame["tier"].astype(str).str.strip().ne("")
    if (tiered & ~valued).any():
        raise DataContractError(f"{filename} cannot assign a tier to a missing metric value.")
    invalid_computed_flags = frame["computed_at_baseline"].notna() & ~frame[
        "computed_at_baseline"
    ].astype(str).str.casefold().isin({"true", "false"})
    if invalid_computed_flags.any():
        raise DataContractError(f"{filename} computed_at_baseline must be true, false, or blank.")
    duplicates = frame.duplicated(["site_id", "metric_name"], keep=False)
    if duplicates.any():
        duplicate_keys = frame.loc[duplicates, ["site_id", "metric_name"]].drop_duplicates()
        rendered = ", ".join(
            f"{row.site_id}/{row.metric_name}" for row in duplicate_keys.itertuples(index=False)
        )
        raise DataContractError(f"{filename} contains duplicate site/metric rows: {rendered}.")
    material_values = frame.loc[
        (frame["metric_name"] == "material_class") & frame["value"].notna(), "value"
    ].astype(str).str.strip()
    if material_values.eq("").any():
        raise DataContractError(f"{filename} material_class values cannot be blank strings.")
    return frame


def load_slope_histograms(data_dir: str | Path | None = None) -> pd.DataFrame:
    columns = ("site_id", "bin_start", "bin_end", "pixel_count", "share")
    if data_dir is None:
        try:
            artifact_dir = get_data_file_path("terrain_metrics.csv").parent
        except FileNotFoundError:
            return pd.DataFrame(columns=columns)
    else:
        artifact_dir = Path(data_dir)
    path = artifact_dir / "slope_histograms.csv"
    if not path.is_file():
        return pd.DataFrame(columns=columns)
    try:
        frame = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as error:
        raise DataContractError(f"Could not read {path}: {error}") from error
    require_columns(frame, columns, "slope_histograms.csv")
    validate_numeric_columns(frame, ("bin_start", "bin_end", "pixel_count", "share"), "slope_histograms.csv")
    if frame["bin_end"].sub(frame["bin_start"]).ne(1).any():
        raise DataContractError("slope_histograms.csv bins must be exactly one value unit wide.")
    invalid_counts = frame["pixel_count"].lt(0) | frame["pixel_count"].mod(1).ne(0)
    if invalid_counts.any():
        raise DataContractError("slope_histograms.csv pixel_count must be a non-negative integer.")
    if frame["share"].lt(0).any() or frame["share"].gt(1).any():
        raise DataContractError("slope_histograms.csv share must be in [0, 1].")
    for site_id, group in frame.groupby("site_id"):
        if not pd.Series([group["share"].sum()]).between(0.999999, 1.000001).all():
            raise DataContractError(f"slope_histograms.csv shares for {site_id} do not sum to 1.")
        if group["pixel_count"].sum() <= 0:
            raise DataContractError(f"slope_histograms.csv has no valid pixels for {site_id}.")
    return frame


def load_slope_preview(site_id: str, data_dir: str | Path | None = None) -> dict | None:
    columns = (
        "site_id", "image_path", "source_file", "crs", "extent_left", "extent_bottom",
        "extent_right", "extent_top", "pixel_size_x", "pixel_size_y", "pixel_size_unit",
        "preview_width", "preview_height", "bounds_west", "bounds_south", "bounds_east",
        "bounds_north", "slope_min", "slope_max",
    )
    if data_dir is None:
        try:
            artifact_dir = get_data_file_path("terrain_metrics.csv").parent
        except FileNotFoundError:
            return None
    else:
        artifact_dir = Path(data_dir)
    metadata_path = artifact_dir / "slope_preview_metadata.csv"
    if not metadata_path.is_file():
        return None
    metadata_frame = pd.read_csv(metadata_path)
    require_columns(metadata_frame, columns, "slope_preview_metadata.csv")
    rows = metadata_frame.loc[metadata_frame["site_id"].astype(str).str.casefold() == site_id.casefold()]
    if rows.empty:
        return None
    metadata = rows.iloc[0].to_dict()
    image_path = (artifact_dir / str(metadata["image_path"])).resolve()
    preview_root = (artifact_dir / "previews").resolve()
    if preview_root not in image_path.parents or not image_path.is_file():
        return None
    metadata["image_path"] = image_path.name
    metadata["image_bytes"] = image_path.read_bytes()
    return metadata


def load_site_extents(data_dir: str | Path | None = None) -> gpd.GeoDataFrame:
    """Read the builder-produced Earth footprint layer, if present."""
    from app.utils.config import DATA_ROOT

    artifact_dir = Path(data_dir) if data_dir is not None else DATA_ROOT / "processed"
    path = artifact_dir / "site_extents.geojson"
    if not path.is_file():
        return gpd.GeoDataFrame(
            columns=("site_id", "name", "source_file", "notes", "geometry"),
            geometry="geometry",
            crs="EPSG:4326",
        )
    extents = gpd.read_file(path)
    if extents.crs is not None and extents.crs.to_string() != "EPSG:4326":
        extents = extents.to_crs("EPSG:4326")
    return extents


def load_temperature_monthly(data_dir: str | Path | None = None) -> pd.DataFrame:
    filename = "temperature_monthly.csv"
    frame = _read_csv(filename, TEMPERATURE_COLUMNS[:13], data_dir)
    if "source_label" not in frame:
        frame["source_label"] = ""
    if "period_of_day" not in frame:
        frame["period_of_day"] = "daily"
    frame["source_label"] = frame["source_label"].fillna("").astype(str)
    frame["period_of_day"] = frame["period_of_day"].fillna("daily").astype(str)
    invalid_periods = sorted(set(frame["period_of_day"]) - {"daily", "day", "night"})
    if invalid_periods:
        raise DataContractError(
            f"{filename} period_of_day must be daily, day, or night; "
            f"found {', '.join(invalid_periods)}."
        )
    validate_months(frame, filename)
    validate_variable_types(frame, filename)
    validate_numeric_columns(
        frame,
        (
            "temp_min_c",
            "temp_mean_c",
            "temp_max_c",
            "pct_in_envelope",
            "n_valid_obs",
            "n_missing_obs",
        ),
        filename,
    )
    return frame


def load_daily_surface_temperature_matches(
    data_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Load optional builder output; an absent artifact means no daily match was computed."""
    columns = (
        "site_id", "period_of_day", "season", "earth_variable", "mars_variable",
        "share_in_band_pct", "n_matching_days", "n_valid_days", "source",
    )
    if data_dir is None:
        from app.utils.config import DATA_ROOT

        artifact_dir = DATA_ROOT / "processed"
    else:
        artifact_dir = Path(data_dir)
    path = artifact_dir / "earth_surface_temperature_matches.csv"
    if not path.is_file():
        return pd.DataFrame(columns=columns)
    frame = pd.read_csv(path)
    require_columns(frame, columns, path.name)
    validate_numeric_columns(
        frame,
        ("share_in_band_pct", "n_matching_days", "n_valid_days"),
        path.name,
    )
    numeric_share = pd.to_numeric(frame["share_in_band_pct"], errors="coerce")
    if (numeric_share.dropna().lt(0) | numeric_share.dropna().gt(100)).any():
        raise DataContractError(f"{path.name} share_in_band_pct must be in [0, 100].")
    if not frame["period_of_day"].isin({"day", "night"}).all():
        raise DataContractError(f"{path.name} period_of_day must be day or night.")
    return frame


def load_mars_temperature_envelope(data_dir: str | Path | None = None) -> dict:
    filename = "mars_temperature_envelope.json"
    data = _read_json(filename, data_dir)
    if not isinstance(data, dict):
        raise DataContractError(f"{filename} must contain a JSON object.")
    require_json_keys(data, ENVELOPE_KEYS, filename)
    validate_schema_version(data["schema_version"], filename)
    validate_numeric_columns(pd.DataFrame([data]), ("min_c", "max_c"), filename)
    seasonal = data.get("seasonal_envelopes", [])
    if not isinstance(seasonal, list):
        raise DataContractError(f"{filename} seasonal_envelopes must be a JSON list.")
    if pd.isna(pd.to_numeric(data["min_c"], errors="coerce")) or pd.isna(
        pd.to_numeric(data["max_c"], errors="coerce")
    ):
        if not seasonal:
            raise DataContractError(
                f"{filename} requires numeric min_c/max_c or explicit seasonal_envelopes."
            )
    for index, item in enumerate(seasonal):
        if not isinstance(item, dict):
            raise DataContractError(f"{filename} seasonal_envelopes[{index}] must be an object.")
        require_json_keys(item, ("season", "min_c", "max_c"), f"{filename} seasonal_envelopes[{index}]")
        validate_numeric_columns(pd.DataFrame([item]), ("min_c", "max_c"), f"{filename} seasonal_envelopes[{index}]")
    ls_mapping = data.get("solar_longitude_mapping")
    if ls_mapping is not None:
        if not isinstance(ls_mapping, dict):
            raise DataContractError(f"{filename} solar_longitude_mapping must be an object.")
        require_json_keys(
            ls_mapping,
            ("coverage_percent", "mapped_ats_sols", "total_ats_sols", "source"),
            f"{filename} solar_longitude_mapping",
        )
        validate_numeric_columns(
            pd.DataFrame([ls_mapping]),
            ("coverage_percent", "mapped_ats_sols", "total_ats_sols"),
            f"{filename} solar_longitude_mapping",
        )
        if not 0 <= float(ls_mapping["coverage_percent"]) <= 100:
            raise DataContractError(f"{filename} solar longitude coverage must be in [0, 100].")
        if (
            float(ls_mapping["mapped_ats_sols"]) < 0
            or float(ls_mapping["total_ats_sols"]) <= 0
            or float(ls_mapping["mapped_ats_sols"]) > float(ls_mapping["total_ats_sols"])
        ):
            raise DataContractError(f"{filename} solar longitude sol counts are invalid.")
    return data


def load_analogy_gaps(data_dir: str | Path | None = None) -> list[dict]:
    filename = "analogy_gaps.json"
    data = _read_json(filename, data_dir)
    if not isinstance(data, list):
        raise DataContractError(f"{filename} must contain a JSON list.")
    required = (
        "schema_version",
        "factor",
        "explanation",
    )
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise DataContractError(f"{filename} item {index} must be a JSON object.")
        require_json_keys(item, required, f"{filename} item {index}")
        validate_schema_version(item["schema_version"], f"{filename} item {index}")
        if "can_rehearse_on_earth" not in item:
            raise DataContractError(
                f"{filename} item {index} is missing required key(s): can_rehearse_on_earth."
            )
        if item["can_rehearse_on_earth"] is not None and not isinstance(
            item["can_rehearse_on_earth"], bool
        ):
            raise DataContractError(
                f"{filename} item {index} can_rehearse_on_earth must be boolean or null."
            )
    return data


def load_datasets_catalogue(data_dir: str | Path | None = None) -> pd.DataFrame:
    filename = "datasets_catalogue.csv"
    frame = _read_csv(filename, CATALOGUE_COLUMNS, data_dir)
    validate_unit_values(frame["units"], filename, "units")
    return frame


def get_data_quality_summary(data_dir: str | Path | None = None) -> pd.DataFrame:
    """Return missing-value counts for each available contract file and column."""
    sources = (
        ("sites.geojson", load_sites),
        ("terrain_metrics.csv", load_terrain_metrics),
        ("temperature_monthly.csv", load_temperature_monthly),
        ("mars_temperature_envelope.json", load_mars_temperature_envelope),
        ("analogy_gaps.json", load_analogy_gaps),
        ("datasets_catalogue.csv", load_datasets_catalogue),
    )
    records = []
    for filename, loader in sources:
        if data_dir is not None:
            if not (Path(data_dir) / filename).is_file():
                continue
            data = loader(data_dir)
        else:
            if get_data_file_source(filename) == "missing":
                continue
            data = loader()
        if isinstance(data, dict):
            frame = pd.DataFrame([data])
        elif isinstance(data, list):
            frame = pd.DataFrame(data)
        else:
            frame = data
        for column in frame.columns:
            records.append(
                {
                    "file": filename,
                    "column": str(column),
                    "missing_count": int(frame[column].isna().sum()),
                    "row_count": len(frame),
                }
            )
    return pd.DataFrame(
        records, columns=("file", "column", "missing_count", "row_count")
    )
