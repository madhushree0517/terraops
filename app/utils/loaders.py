import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from app.utils.config import get_data_dir
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
    folder = Path(data_dir) if data_dir is not None else get_data_dir()
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


def load_temperature_monthly(data_dir: str | Path | None = None) -> pd.DataFrame:
    filename = "temperature_monthly.csv"
    frame = _read_csv(filename, TEMPERATURE_COLUMNS, data_dir)
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


def load_mars_temperature_envelope(data_dir: str | Path | None = None) -> dict:
    filename = "mars_temperature_envelope.json"
    data = _read_json(filename, data_dir)
    if not isinstance(data, dict):
        raise DataContractError(f"{filename} must contain a JSON object.")
    require_json_keys(data, ENVELOPE_KEYS, filename)
    validate_schema_version(data["schema_version"], filename)
    validate_numeric_columns(pd.DataFrame([data]), ("min_c", "max_c"), filename)
    return data


def load_analogy_gaps(data_dir: str | Path | None = None) -> list[dict]:
    filename = "analogy_gaps.json"
    data = _read_json(filename, data_dir)
    if not isinstance(data, list):
        raise DataContractError(f"{filename} must contain a JSON list.")
    required = (
        "schema_version",
        "factor",
        "can_rehearse_on_earth",
        "explanation",
    )
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise DataContractError(f"{filename} item {index} must be a JSON object.")
        require_json_keys(item, required, f"{filename} item {index}")
        validate_schema_version(item["schema_version"], f"{filename} item {index}")
        if not isinstance(item["can_rehearse_on_earth"], bool):
            raise DataContractError(
                f"{filename} item {index} can_rehearse_on_earth must be boolean."
            )
    return data


def load_datasets_catalogue(data_dir: str | Path | None = None) -> pd.DataFrame:
    filename = "datasets_catalogue.csv"
    frame = _read_csv(filename, CATALOGUE_COLUMNS, data_dir)
    validate_unit_values(frame["units"], filename, "units")
    return frame


def get_data_quality_summary(data_dir: str | Path | None = None) -> pd.DataFrame:
    """Return missing-value counts for each available contract file and column."""
    folder = Path(data_dir) if data_dir is not None else get_data_dir()
    sources = (
        ("sites.geojson", load_sites),
        ("terrain_parameters.csv", load_terrain_parameters),
        ("temperature_monthly.csv", load_temperature_monthly),
        ("mars_temperature_envelope.json", load_mars_temperature_envelope),
        ("analogy_gaps.json", load_analogy_gaps),
        ("datasets_catalogue.csv", load_datasets_catalogue),
    )
    records = []
    for filename, loader in sources:
        if not (folder / filename).is_file():
            continue
        data = loader(folder)
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