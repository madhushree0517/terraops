import json
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from app.utils import config


PAGE_PATH = Path(__file__).resolve().parents[1] / "app" / "pages" / "4_When_to_Test.py"
SEASONS = (
    ("Northern Spring", -54.2, -40.0),
    ("Northern Summer", -50.0, -36.5),
    ("Northern Autumn", -66.0, -39.0),
    ("Northern Winter", -64.5, -44.9),
)


def _write_sites(path, site_ids=("atacama", "ladakh")):
    names = {"atacama": "Atacama Desert", "ladakh": "Ladakh", "askja": "Askja"}
    features = []
    for index, site_id in enumerate(site_ids):
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-68.5 + index, -22.5 + index]},
                "properties": {
                    "schema_version": "1.0",
                    "site_id": site_id,
                    "name": names[site_id],
                    "body": "Earth",
                    "lat": -22.5 + index,
                    "lon": -68.5 + index,
                    "notes": "test site",
                },
            }
        )
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8")


def _write_envelope(path):
    envelope = {
        "schema_version": "1.0",
        "variable_type": "surface_temp",
        "min_c": None,
        "max_c": None,
        "source": "test recalculated comparison",
        "notes": "season-specific test bands",
        "solar_longitude_mapping": {
            "coverage_percent": 87.001,
            "mapped_ats_sols": 1526,
            "total_ats_sols": 1754,
            "source": "current official Ls mapping handoff",
        },
        "seasonal_envelopes": [
            {
                "season": season,
                "min_c": lower,
                "max_c": upper,
                "mars_variable": "TIRS ground temperature",
                "comparison_class": "SURFACE_TEMPERATURE",
            }
            for season, lower, upper in SEASONS
        ],
    }
    path.write_text(json.dumps(envelope), encoding="utf-8")


def _write_monthly(path, variable_type, months, site_ids=("atacama", "ladakh")):
    rows = []
    for site_id in site_ids:
        for month in months:
            period = pd.Period(f"2024-{month:02d}", freq="M")
            is_low_data = site_id == "atacama" and month == 12
            rows.append(
                {
                    "schema_version": "1.0",
                    "site_id": site_id,
                    "month": month,
                    "variable_type": variable_type,
                    "temp_min_c": -5.0,
                    "temp_mean_c": 3.0,
                    "temp_max_c": 10.0,
                    "pct_in_envelope": float("nan") if variable_type == "air_temp" else (
                        float(month * 5) if site_id == "atacama" else float(100 - month * 5)
                    ),
                    "n_valid_obs": 15 if is_low_data else 31,
                    "n_missing_obs": 16 if is_low_data else 0,
                    "source": "fixture source",
                    "period_start": period.start_time.date().isoformat(),
                    "period_end": period.end_time.date().isoformat(),
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)


def _prepare_workspace(tmp_path, monkeypatch, variable_type, months):
    data_root = tmp_path / "data"
    processed_dir = data_root / "processed"
    sample_dir = data_root / "sample"
    processed_dir.mkdir(parents=True)
    sample_dir.mkdir(parents=True)
    _write_sites(sample_dir / "sites.geojson")
    _write_envelope(processed_dir / "mars_temperature_envelope.json")
    _write_monthly(processed_dir / "temperature_monthly.csv", variable_type, months)
    monkeypatch.setattr(config, "DATA_ROOT", data_root)


def test_one_month_air_temperature_mismatch_shows_error_and_no_charts(tmp_path, monkeypatch):
    _prepare_workspace(tmp_path, monkeypatch, "air_temp", [7])
    monthly_path = tmp_path / "data" / "processed" / "temperature_monthly.csv"
    monthly = pd.read_csv(monthly_path)
    monthly = monthly.loc[monthly["site_id"] != "ladakh"]
    monthly.to_csv(monthly_path, index=False)

    app = AppTest.from_file(str(PAGE_PATH)).run()

    assert not app.exception
    assert not app.error
    expander = next(e for e in app.get("expander") if e.label == "Why some comparisons are not shown")
    assert expander.proto.expanded is False
    reasons = "\n".join(element.value for element in expander.markdown)
    assert reasons.count("Cannot compare Atacama Desert") == 1
    assert "air temperature" in reasons
    assert "surface temperature" in reasons
    assert "air_temp" not in reasons and "surface_temp" not in reasons
    assert "Ladakh: no Earth temperature observations are loaded." in reasons
    visible = "\n".join(element.value for element in [*app.markdown, *app.caption])
    assert "Only July 2024 available, so no best-season recommendation can be made." in visible
    assert len(app.warning) == 1
    assert "PLACEHOLDER DATA" in app.warning[0].value
    assert "Cannot compare" not in "\n".join(
        element.value for element in [*app.warning, *app.info, *app.error]
    )
    assert len(app.get("plotly_chart")) == 0
    assert "A high match percentage does not prove thermal equivalence." not in visible
    observations = app.dataframe[1].value
    assert list(observations["Site"]) == ["Atacama Desert"]
    assert observations.loc[0, "Month"] == "July 2024"
    assert observations.loc[0, "Temperature type"] == "air temperature"
    assert "None" not in observations.to_string()


def test_compatible_full_year_shows_charts_and_low_data_best_month(tmp_path, monkeypatch):
    _prepare_workspace(tmp_path, monkeypatch, "surface_temp", range(1, 13))

    app = AppTest.from_file(str(PAGE_PATH)).run()

    assert not app.exception
    season_table = app.dataframe[0].value
    assert season_table.loc[0, "Min (°C)"] == "-54.2"
    assert season_table.loc[0, "Max (°C)"] == "-40.0"
    assert len(app.get("plotly_chart")) == 2
    assert not app.get("expander")
    rendered = "\n".join(
        element.value
        for element in [*app.markdown, *app.caption, *app.subheader, *app.info]
    )
    assert "Monthly comparison with Mars bands" in rendered
    assert "Official Ls mapping covers 87.0% (1,526 of 1,754 ATS sols)." in rendered
    assert "not the share of temperature observations analysed" in rendered
    assert "A high match percentage does not prove thermal equivalence." in rendered
    assert "no season key" in rendered
    assert "pct_in_envelope" not in rendered
    assert "Atacama Desert: December (2024-12-01 to 2024-12-31), 60%" in rendered
    assert "15 valid observations; low data" in rendered


def test_missing_percentages_do_not_become_zero_or_best_month(tmp_path, monkeypatch):
    _prepare_workspace(tmp_path, monkeypatch, "surface_temp", range(1, 13))
    monthly_path = tmp_path / "data" / "processed" / "temperature_monthly.csv"
    monthly = pd.read_csv(monthly_path)
    monthly["pct_in_envelope"] = float("nan")
    monthly.to_csv(monthly_path, index=False)

    app = AppTest.from_file(str(PAGE_PATH)).run()

    assert not app.exception
    assert len(app.get("plotly_chart")) == 2
    rendered = "\n".join(
        element.value
        for element in [*app.markdown, *app.info, *app.subheader]
    )
    assert "the supplied share is missing for all months; no best month can be identified" in rendered
    assert "A high match percentage does not prove thermal equivalence." not in rendered


def test_compatible_single_month_shows_supplied_share_and_no_blocked_expander(tmp_path, monkeypatch):
    _prepare_workspace(tmp_path, monkeypatch, "surface_temp", [7])

    app = AppTest.from_file(str(PAGE_PATH)).run()

    assert not app.exception
    assert not app.get("expander")
    assert len(app.get("plotly_chart")) == 0
    shares = app.dataframe[2].value
    assert set(shares["Site"]) == {"Atacama Desert", "Ladakh"}
    assert "Only July 2024 available, so no best-season recommendation can be made." in "\n".join(
        element.value for element in app.markdown
    )
    rendered = "\n".join(element.value for element in [*app.markdown, *app.caption])
    assert "A high match percentage does not prove thermal equivalence." in rendered


def test_askja_modis_day_and_night_rows_are_flagged_low_data(tmp_path, monkeypatch):
    _prepare_workspace(tmp_path, monkeypatch, "surface_temp", [7])
    sample_sites = tmp_path / "data" / "sample" / "sites.geojson"
    _write_sites(sample_sites, site_ids=("askja",))
    askja_rows = []
    for period, mean in (("day", 14.8217414655), ("night", 2.3817085287)):
        askja_rows.append(
            {
                "schema_version": "1.0", "site_id": "askja", "month": 7,
                "variable_type": "surface_temp", "temp_min_c": 0.0,
                "temp_mean_c": mean, "temp_max_c": 26.0,
                "pct_in_envelope": float("nan"), "n_valid_obs": 8,
                "n_missing_obs": 23, "source": "MODIS fixture",
                "period_start": "2024-07-01", "period_end": "2024-07-31",
                "source_label": "Iceland", "period_of_day": period,
            }
        )
    pd.DataFrame(askja_rows).to_csv(
        tmp_path / "data" / "processed" / "temperature_monthly.csv", index=False
    )

    app = AppTest.from_file(str(PAGE_PATH)).run()

    assert not app.exception
    observations = app.dataframe[1].value
    assert set(observations["Site"]) == {"Askja"}
    assert set(observations["Source label"]) == {"Iceland"}
    assert set(observations["Period"]) == {"Daytime", "Nighttime"}
    assert observations["Data quality"].eq("low data").all()
    assert observations["Valid observations"].eq(8).all()
    rendered = "\n".join(element.value for element in [*app.markdown, *app.caption])
    assert "A high match percentage does not prove thermal equivalence." not in rendered
