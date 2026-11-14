import pandas as pd
import pytest

from app.utils.loaders import get_data_quality_summary, load_terrain_parameters
from app.utils.validation import (
    DataContractError,
    check_temperature_variable_types,
    validate_coordinates_degrees,
    validate_numeric_columns,
    validate_schema_version,
    validate_unit_values,
    temperature_compatibility_status,
)


TERRAIN_COLUMNS = [
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
]


def _write_terrain_file(folder, columns=TERRAIN_COLUMNS, values=None):
    if values is None:
        values = ["1.0", "test_site", 100, 5, 2, 8, 0.1, "m", "test_dem", 30]
        values = values[: len(columns)]
    pd.DataFrame([values], columns=columns).to_csv(
        folder / "terrain_parameters.csv", index=False
    )


def test_valid_terrain_file_loads(tmp_path):
    _write_terrain_file(tmp_path)

    terrain = load_terrain_parameters(tmp_path)

    assert terrain.loc[0, "site_id"] == "test_site"
    assert terrain.loc[0, "elevation_mean_m"] == 100


def test_missing_column_raises_clear_error(tmp_path):
    _write_terrain_file(tmp_path, columns=TERRAIN_COLUMNS[:-1])

    with pytest.raises(DataContractError, match="resolution_m"):
        load_terrain_parameters(tmp_path)


def test_nan_is_preserved(tmp_path):
    values = ["1.0", "test_site", float("nan"), 5, 2, 8, 0.1, "m", "test_dem", 30]
    _write_terrain_file(tmp_path, values=values)

    terrain = load_terrain_parameters(tmp_path)

    assert pd.isna(terrain.loc[0, "elevation_mean_m"])


def test_missing_schema_version_fails(tmp_path):
    _write_terrain_file(tmp_path, columns=TERRAIN_COLUMNS[1:])

    with pytest.raises(DataContractError, match="schema_version"):
        load_terrain_parameters(tmp_path)


def test_wrong_schema_version_fails():
    with pytest.raises(DataContractError, match="schema_version '1.0'"):
        validate_schema_version("2.0", "example.csv")


def test_unsupported_unit_fails(tmp_path):
    values = ["1.0", "test_site", 100, 5, 2, 8, 0.1, "feet", "test_dem", 30]
    _write_terrain_file(tmp_path, values=values)

    with pytest.raises(DataContractError, match="unsupported unit"):
        load_terrain_parameters(tmp_path)


def test_supported_unit_names_pass():
    validate_unit_values(
        ["degrees", "metres", "Celsius", "deg C"], "example.csv", "units"
    )


def test_non_numeric_measurement_fails():
    frame = pd.DataFrame({"elevation_mean_m": ["unknown"]})

    with pytest.raises(DataContractError, match="numeric values"):
        validate_numeric_columns(frame, ("elevation_mean_m",), "terrain_parameters.csv")


def test_invalid_coordinate_range_fails():
    frame = pd.DataFrame({"lat": [91], "lon": [20]})

    with pytest.raises(DataContractError, match="decimal degrees"):
        validate_coordinates_degrees(frame, "sites.geojson")


def test_temperature_envelope_variable_mismatch_warns():
    temperatures = pd.DataFrame(
        {"site_id": ["test_site"], "variable_type": ["air_temp"]}
    )
    envelope = {"variable_type": "surface_temp"}

    with pytest.warns(RuntimeWarning, match="Do not compare these variables"):
        messages = check_temperature_variable_types(temperatures, envelope)

    assert "test_site: air_temp" in messages[0]
    assert "labels only" in messages[0]
    assert "not a physical validation" in messages[0]


def test_temperature_types_match_when_site_has_envelope_and_other_variable():
    temperatures = pd.DataFrame(
        {
            "site_id": ["test_site", "test_site"],
            "variable_type": ["surface_temp", "air_temp"],
        }
    )
    envelope = {"variable_type": "surface_temp"}

    assert check_temperature_variable_types(temperatures, envelope) == []


def test_temperature_types_warn_when_site_lacks_envelope_variable():
    temperatures = pd.DataFrame(
        {
            "site_id": ["compatible", "incompatible"],
            "variable_type": ["surface_temp", "air_temp"],
        }
    )
    envelope = {"variable_type": "surface_temp"}

    with pytest.warns(RuntimeWarning, match="incompatible: air_temp"):
        messages = check_temperature_variable_types(temperatures, envelope)

    assert len(messages) == 1


def test_sample_matching_labels_use_warning_status():
    level, message = temperature_compatibility_status("sample", [])

    assert level == "warning"
    assert "labels only" in message
    assert "not a physical validation" in message


def test_processed_matching_labels_use_success_status():
    level, message = temperature_compatibility_status("processed", [])

    assert level == "success"
    assert "labels only" in message
    assert "not a physical validation" in message


def test_temperature_mismatch_uses_error_status_and_sites():
    mismatches = ["Incompatible site data: site_a: air_temp"]

    level, message = temperature_compatibility_status("sample", mismatches)

    assert level == "error"
    assert "site_a" in message


def test_data_quality_summary_reports_missing_values(tmp_path):
    values = ["1.0", "test_site", float("nan"), 5, 2, 8, 0.1, "m", "test_dem", 30]
    _write_terrain_file(tmp_path, values=values)

    summary = get_data_quality_summary(tmp_path)
    row = summary.loc[
        (summary["file"] == "terrain_parameters.csv")
        & (summary["column"] == "elevation_mean_m")
    ].iloc[0]

    assert row["missing_count"] == 1
    assert row["row_count"] == 1