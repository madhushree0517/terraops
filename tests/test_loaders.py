import pandas as pd
import pytest

from app.utils import config
from app.utils.loaders import (
    get_data_quality_summary,
    load_slope_histograms,
    load_terrain_metrics,
    load_terrain_parameters,
)
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


def _write_terrain_metrics_file(folder, *, metric_name="slope_p90_deg", value=12.5, tier="B"):
    pd.DataFrame(
        [
            {
                "schema_version": "1.0",
                "site_id": "atacama",
                "metric_name": metric_name,
                "value": value,
                "value_mean": float("nan"),
                "value_std": float("nan"),
                "value_min": float("nan"),
                "value_max": float("nan"),
                "n_valid_pixels": 100,
                "metric_unit": "degrees",
                "tier": tier,
                "baseline_m": 30,
                "dem_source": "Copernicus GLO30",
                "native_resolution_m": 29.5,
                "computed_at_baseline": False,
                "roughness_metric": "",
                "roughness_window": "",
                "availability_note": "",
                "source_file": "large/terrain/test.tif",
                "crs": "EPSG:32719",
                "resolution_x": 29.5,
                "resolution_y": 29.5,
                "resolution_unit": "metre",
                "statistics_scope": "whole supplied raster extent",
            }
        ]
    ).to_csv(folder / "terrain_metrics.csv", index=False)


def test_terrain_metrics_loader_preserves_missing_and_categorical_values(tmp_path):
    _write_terrain_metrics_file(tmp_path, value=float("nan"), tier="")

    metrics = load_terrain_metrics(tmp_path)

    assert pd.isna(metrics.loc[0, "value"])
    assert pd.isna(metrics.loc[0, "tier"])

    _write_terrain_metrics_file(tmp_path, metric_name="material_class", value="basalt", tier="B")
    metrics = load_terrain_metrics(tmp_path)
    assert metrics.loc[0, "value"] == "basalt"


def test_terrain_metrics_loader_rejects_tier_for_missing_value(tmp_path):
    _write_terrain_metrics_file(tmp_path, value=float("nan"), tier="B")

    with pytest.raises(DataContractError, match="tier to a missing metric value"):
        load_terrain_metrics(tmp_path)


def test_terrain_metrics_loader_rejects_unknown_tier(tmp_path):
    _write_terrain_metrics_file(tmp_path, tier="C")

    with pytest.raises(DataContractError, match="tier must be A, B, or blank"):
        load_terrain_metrics(tmp_path)


def test_slope_histogram_loader_checks_totals_and_share_normalization(tmp_path):
    pd.DataFrame(
        [
            {"site_id": "atacama", "bin_start": 0, "bin_end": 1, "pixel_count": 2, "share": 0.5},
            {"site_id": "atacama", "bin_start": 1, "bin_end": 2, "pixel_count": 2, "share": 0.5},
        ]
    ).to_csv(tmp_path / "slope_histograms.csv", index=False)

    histogram = load_slope_histograms(tmp_path)

    assert histogram["pixel_count"].sum() == 4
    assert histogram["share"].sum() == 1


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
    _write_terrain_metrics_file(tmp_path, value=float("nan"), tier="")

    summary = get_data_quality_summary(tmp_path)
    row = summary.loc[
        (summary["file"] == "terrain_metrics.csv")
        & (summary["column"] == "value")
    ].iloc[0]

    assert row["missing_count"] == 1
    assert row["row_count"] == 1


def test_data_quality_summary_accepts_draft_analogy_decisions(tmp_path):
    (tmp_path / "analogy_gaps.json").write_text(
        '[{"schema_version":"1.0","factor":"Pending review",'
        '"can_rehearse_on_earth":null,"explanation":"Needs review",'
        '"review_status":"draft, pending engineering review"}]',
        encoding="utf-8",
    )

    summary = get_data_quality_summary(tmp_path)
    decision = summary.loc[
        (summary["file"] == "analogy_gaps.json")
        & (summary["column"] == "can_rehearse_on_earth")
    ].iloc[0]

    assert decision["missing_count"] == 1
    assert decision["row_count"] == 1


def test_per_file_source_prefers_processed_then_falls_back_to_sample(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    sample = tmp_path / "sample"
    processed.mkdir()
    sample.mkdir()
    (processed / "terrain_parameters.csv").write_text("real", encoding="utf-8")
    (sample / "sites.geojson").write_text("sample", encoding="utf-8")
    monkeypatch.setattr(config, "DATA_ROOT", tmp_path)
    monkeypatch.delenv("TERRAOPS_DATA_MODE", raising=False)

    assert config.get_data_file_source("terrain_parameters.csv") == "processed"
    assert config.get_data_file_source("sites.geojson") == "sample"
    assert config.get_data_file_source("temperature_monthly.csv") == "missing"


def test_explicit_processed_mode_does_not_fall_back(tmp_path, monkeypatch):
    (tmp_path / "processed").mkdir()
    (tmp_path / "sample").mkdir()
    (tmp_path / "sample" / "terrain_parameters.csv").write_text("sample", encoding="utf-8")
    monkeypatch.setattr(config, "DATA_ROOT", tmp_path)
    monkeypatch.setenv("TERRAOPS_DATA_MODE", "processed")

    with pytest.raises(FileNotFoundError, match="terrain_parameters.csv"):
        config.get_data_file_path("terrain_parameters.csv")


def test_contract_statuses_report_mixed_file_origins(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    sample = tmp_path / "sample"
    processed.mkdir()
    sample.mkdir()
    (processed / "temperature_monthly.csv").write_text("real", encoding="utf-8")
    (sample / "sites.geojson").write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr(config, "DATA_ROOT", tmp_path)
    monkeypatch.delenv("TERRAOPS_DATA_MODE", raising=False)

    statuses = config.get_contract_file_statuses()

    assert statuses["temperature_monthly.csv"] == "processed"
    assert statuses["sites.geojson"] == "sample"
    assert statuses["terrain_metrics.csv"] == "missing"
    assert "terrain_parameters.csv" not in statuses