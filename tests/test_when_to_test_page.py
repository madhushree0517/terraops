import json
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from app.utils import config
from app.utils.loaders import load_sites
from app.utils.location import build_location_consistency


PAGE_PATH = Path(__file__).resolve().parents[1] / "app" / "pages" / "4_When_to_Test.py"


def _workspace(tmp_path, monkeypatch, variable_type="surface_temp"):
    root = tmp_path / "data"
    processed = root / "processed"
    sample = root / "sample"
    processed.mkdir(parents=True)
    sample.mkdir()
    features = [{
        "type": "Feature", "geometry": {"type": "Point", "coordinates": [-68.5, -22.5]},
        "properties": {"schema_version": "1.0", "site_id": "atacama", "name": "Atacama",
                       "body": "Earth", "lat": -22.5, "lon": -68.5, "notes": ""},
    }]
    (sample / "sites.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    envelope = {
        "schema_version": "1.0", "variable_type": "surface_temp", "min_c": None, "max_c": None,
        "source": "fixture", "notes": "fixture",
        "seasonal_envelopes": [
            {"season": "Northern Spring", "min_c": -50, "max_c": -40, "mars_variable": "TIRS surface"}
        ],
    }
    (processed / "mars_temperature_envelope.json").write_text(json.dumps(envelope))
    row = {
        "schema_version": "1.0", "site_id": "atacama", "month": 7,
        "variable_type": variable_type, "temp_min_c": 10, "temp_mean_c": 20, "temp_max_c": 30,
        "pct_in_envelope": None, "n_valid_obs": 31, "n_missing_obs": 0,
        "source": "fixture", "period_start": "2024-07-01", "period_end": "2024-07-31",
        "period_of_day": "day",
    }
    pd.DataFrame([row]).to_csv(processed / "temperature_monthly.csv", index=False)
    monkeypatch.setattr(config, "DATA_ROOT", root)
    return processed


def test_surface_ranges_gaps_bands_and_guidance_render(tmp_path, monkeypatch):
    _workspace(tmp_path, monkeypatch)
    app = AppTest.from_file(str(PAGE_PATH)).run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 1
    text = "\n".join(element.value for element in [*app.markdown, *app.caption])
    assert "How to use this page" in text
    assert "Vertical marks show Earth minimum and maximum" in text
    assert "nearest edge" in text
    assert "not stated in the source documentation" in text
    assert any("Gap to nearest band edge" in str(frame.value.columns) for frame in app.dataframe)
    assert not any(expander.label.startswith("Air temperature") for expander in app.get("expander"))


def test_temperature_distance_caption_uses_location_table_value(tmp_path, monkeypatch):
    _workspace(tmp_path, monkeypatch)
    app = AppTest.from_file(str(PAGE_PATH)).run()
    assert not app.exception
    sites = load_sites(tmp_path / "data" / "sample")
    locations = build_location_consistency(sites)
    row = locations.loc[
        locations["Location source"].astype(str).str.startswith("MODIS analysis coordinate")
    ].iloc[0]
    expected_distance = row["Distance from terrain centroid (km)"]
    assert any(
        f"{row['Site']} temperature values come from a point {expected_distance} km from its terrain footprint."
        == caption.value
        for caption in app.caption
    )


def test_air_temperature_stays_out_of_surface_chart(tmp_path, monkeypatch):
    _workspace(tmp_path, monkeypatch, "air_temp")
    app = AppTest.from_file(str(PAGE_PATH)).run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 0
    air = next(expander for expander in app.get("expander") if expander.label.startswith("Air temperature"))
    assert "different measurement types" in " ".join(element.value for element in air.markdown)


def test_loaded_daily_match_rows_display_zero_and_valid_days_without_filling_missing(tmp_path, monkeypatch):
    processed = _workspace(tmp_path, monkeypatch)
    pd.DataFrame([{
        "site_id": "atacama", "period_of_day": "day", "season": "Northern Spring",
        "earth_variable": "surface_temp", "mars_variable": "surface_temp",
        "share_in_band_pct": 0.0, "n_matching_days": 0, "n_valid_days": 31, "source": "fixture",
    }]).to_csv(processed / "earth_surface_temperature_matches.csv", index=False)
    app = AppTest.from_file(str(PAGE_PATH)).run()
    assert not app.exception
    daily = next(frame.value for frame in app.dataframe if "Valid days" in frame.value.columns)
    assert daily.loc[0, "Share inside Mars band"] == "0.0%"
    assert daily.loc[0, "Valid days"] == "31"
    pd.DataFrame([{
        "site_id": "atacama", "period_of_day": "day", "season": "Northern Spring",
        "earth_variable": "surface_temp", "mars_variable": "surface_temp",
        "share_in_band_pct": float("nan"), "n_matching_days": float("nan"),
        "n_valid_days": float("nan"), "source": "fixture",
    }]).to_csv(processed / "earth_surface_temperature_matches.csv", index=False)
    app = AppTest.from_file(str(PAGE_PATH)).run()
    daily = next(frame.value for frame in app.dataframe if "Valid days" in frame.value.columns)
    assert daily.loc[0, "Share inside Mars band"] == "not computed"
