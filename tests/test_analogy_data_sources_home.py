import json
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from app.utils import config
from app.utils.analogy import format_data_method_note
from app.utils.loaders import CATALOGUE_COLUMNS


ROOT = Path(__file__).resolve().parents[1]


def test_reviewed_analogy_source_has_exact_four_keys_and_no_synthetic_reviewer():
    source = json.loads((ROOT / "data" / "sample" / "analogy_gaps.json").read_text(encoding="utf-8"))

    expected_keys = {
        "schema_version", "factor", "can_rehearse_on_earth", "explanation",
    }
    assert source
    assert all(set(entry) == expected_keys for entry in source)
    assert all(isinstance(entry["can_rehearse_on_earth"], bool) for entry in source)
    assert all("reviewer" not in entry for entry in source)


def test_analogy_page_groups_decisions_and_preserves_explanations_and_limits(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    processed_dir = data_root / "processed"
    processed_dir.mkdir(parents=True)
    (data_root / "sample").mkdir()
    gaps = [
        {
            "schema_version": "1.0",
            "factor": "Terrain mobility",
            "can_rehearse_on_earth": True,
            "explanation": "Relative difficulty only; the 30 m DEM cannot resolve small hazards.",
            "limits": "Not absolute passability.",
        },
        {
            "schema_version": "1.0",
            "factor": "Wheel sinkage",
            "can_rehearse_on_earth": False,
            "explanation": "Needs an offload rig because normal load differs.",
            "limits": "Earth-gravity measurements do not transfer.",
        },
        {
            "schema_version": "1.0",
            "factor": "Dust adhesion",
            "can_rehearse_on_earth": None,
            "explanation": "Review required; no decision recorded.",
            "limits": "Mars dust behavior is not represented.",
        },
    ]
    (processed_dir / "analogy_gaps.json").write_text(json.dumps(gaps), encoding="utf-8")
    monkeypatch.setattr(config, "DATA_ROOT", data_root)

    app = AppTest.from_file(str(ROOT / "app" / "pages" / "5_Analogy_Gap_Detector.py")).run()

    assert not app.exception
    rendered = "\n".join(
        element.value
        for element in [*app.markdown, *app.subheader, *app.info, *app.caption]
    )
    assert [element.value for element in app.subheader] == [
        "Can be rehearsed on Earth",
        "Needs simulation or other testing",
        "Pending review",
    ]
    assert "Relative difficulty only; the 30 m DEM cannot resolve small hazards." in rendered
    assert "Not absolute passability." in rendered
    assert "Needs an offload rig because normal load differs." in rendered
    assert "Earth-gravity measurements do not transfer." in rendered
    assert "Review required; no decision recorded." in rendered
    assert "Mars dust behavior is not represented." in rendered
    assert "does not mean Earth reproduces Mars" in rendered
    assert "reviewer" not in rendered.casefold()
    assert not app.get("expander")
    assert not app.warning


def test_data_method_note_wording_is_normalized():
    assert format_data_method_note(
        "Matched Parquet artifact availability",
        "Not found in the Google Drive or MyDrive search.",
    ) == "File not included in the delivered package; status unconfirmed"
    assert format_data_method_note(
        "Temperature threshold",
        "The previously used 293 K threshold is a chosen screening threshold.",
    ).startswith("293 K is a screening threshold, not an instrument limit.")


def test_data_sources_catalogue_filter_and_per_file_status(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    processed_dir = data_root / "processed"
    processed_dir.mkdir(parents=True)
    (data_root / "sample").mkdir()
    rows = [
        {
            "schema_version": "1.0",
            "dataset_name": "Mars MEDA TIRS",
            "source": "NASA PDS",
            "url": "https://example.test/mars",
            "file_format": "Parquet",
            "spatial_resolution": "",
            "temporal_resolution": "Per observation",
            "observation_period": "Sol 1 to 1859",
            "units": "Celsius",
            "crs": "",
            "limitations": "Thermal channels are distinct.",
            "citation": "",
            "licence": "",
        },
        {
            "schema_version": "1.0",
            "dataset_name": "NASA POWER",
            "source": "NASA",
            "url": "https://example.test/earth",
            "file_format": "CSV",
            "spatial_resolution": "",
            "temporal_resolution": "Daily",
            "observation_period": "July 2024",
            "units": "Celsius",
            "crs": "",
            "limitations": "Air temperature only.",
            "citation": "",
            "licence": "",
        },
    ]
    pd.DataFrame(rows, columns=CATALOGUE_COLUMNS).to_csv(
        processed_dir / "datasets_catalogue.csv", index=False
    )
    (processed_dir / "analogy_gaps.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(config, "DATA_ROOT", data_root)

    app = AppTest.from_file(str(ROOT / "app" / "pages" / "6_Data_Sources.py")).run()

    assert not app.exception
    assert len(app.selectbox) == 1
    assert app.selectbox[0].value == "All"
    status_table = app.dataframe[0].value
    assert "Active source" in status_table.columns
    assert "Missing" in set(status_table["Active source"])
    app.selectbox[0].select("Mars").run()
    assert not app.exception
    catalogue_table = app.dataframe[1].value
    assert set(catalogue_table["dataset_name"]) == {"Mars MEDA TIRS"}
    assert "url" in catalogue_table.columns
    assert "https://example.test/mars" in catalogue_table["url"].tolist()
    assert "citation" in catalogue_table.columns
    assert "licence" in catalogue_table.columns
    assert "limitations" not in catalogue_table.columns
    assert catalogue_table["spatial_resolution"].iloc[0] == "not documented"
    limitation_expander = next(
        expander for expander in app.get("expander") if expander.label == "Mars MEDA TIRS"
    )
    assert limitation_expander.proto.expanded is False
    assert "Thermal channels are distinct." in "\n".join(
        element.value for element in limitation_expander.markdown
    )
    status_text = " ".join(str(value) for value in status_table.to_numpy().flatten())
    assert "processed (reviewed decisions)" in status_text


def test_data_sources_location_consistency_shows_distances_without_selecting_coordinate(
    tmp_path, monkeypatch
):
    data_root = tmp_path / "data"
    processed_dir = data_root / "processed"
    sample_dir = data_root / "sample"
    processed_dir.mkdir(parents=True)
    sample_dir.mkdir()
    sites = []
    for site_id, name, body, latitude, longitude in (
        ("jezero", "Jezero Crater", "Mars", 18.4, 77.6),
        ("askja", "Askja, Iceland", "Earth", 65.500138889, -16.500277778),
        ("atacama", "Atacama Desert, Chile", "Earth", -22.499861111, -68.500138889),
        ("ladakh", "Ladakh, India", "Earth", 34.500138889, 77.499861111),
    ):
        sites.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "properties": {
                    "schema_version": "1.0", "site_id": site_id, "name": name,
                    "body": body, "lat": latitude, "lon": longitude, "notes": "",
                },
            }
        )
    (processed_dir / "sites.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": sites}), encoding="utf-8"
    )
    pd.DataFrame(
        [
            {
                "schema_version": "1.0", "dataset_name": "Test", "source": "Test",
                "url": "", "file_format": "CSV", "spatial_resolution": "",
                "temporal_resolution": "Monthly", "observation_period": "July 2024",
                "units": "Celsius", "crs": "", "limitations": "",
                "citation": "", "licence": "",
            }
        ],
        columns=CATALOGUE_COLUMNS,
    ).to_csv(processed_dir / "datasets_catalogue.csv", index=False)
    (processed_dir / "analogy_gaps.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(config, "DATA_ROOT", data_root)

    app = AppTest.from_file(str(ROOT / "app" / "pages" / "6_Data_Sources.py")).run()

    assert not app.exception
    location_table = next(
        frame.value for frame in app.dataframe if "Location source" in frame.value.columns
    )
    atacama = location_table.loc[
        (location_table["Site"] == "Atacama")
        & location_table["Location source"].str.contains("MODIS analysis")
    ].iloc[0]
    assert atacama["Distance from terrain centroid (km)"] == "273.0"
    assert atacama["Finding"].startswith("Warning:")
    assert location_table["Coordinates (lat, lon)"].eq("Not stated in source files").any()
    warnings = "\n".join(element.value for element in app.warning)
    assert "Atacama" in warnings and "273.0 km" in warnings and "no location has been selected" in warnings


def test_data_sources_sample_compatibility_is_warning(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    processed_dir = data_root / "processed"
    sample_dir = data_root / "sample"
    processed_dir.mkdir(parents=True)
    sample_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "schema_version": "1.0",
                "site_id": "atacama",
                "month": 7,
                "variable_type": "air_temp",
                "temp_min_c": 1,
                "temp_mean_c": 2,
                "temp_max_c": 3,
                "pct_in_envelope": float("nan"),
                "n_valid_obs": 31,
                "n_missing_obs": 0,
                "source": "sample fixture",
                "period_start": "2024-07-01",
                "period_end": "2024-07-31",
            }
        ]
    ).to_csv(sample_dir / "temperature_monthly.csv", index=False)
    envelope = {
        "schema_version": "1.0",
        "variable_type": "surface_temp",
        "min_c": -50,
        "max_c": -40,
        "source": "sample fixture",
        "notes": "sample",
    }
    (sample_dir / "mars_temperature_envelope.json").write_text(
        json.dumps(envelope), encoding="utf-8"
    )
    monkeypatch.setattr(config, "DATA_ROOT", data_root)

    app = AppTest.from_file(str(ROOT / "app" / "pages" / "6_Data_Sources.py")).run()

    assert not app.exception
    warnings = "\n".join(element.value for element in app.warning)
    assert "Known limitation: Earth temperature is currently air temperature; surface comparison pending" in warnings
    assert "Only variable labels are compared" in warnings
    assert warnings.count("not a physical validation") == 1
    assert "not a physical validation" in warnings
    assert "air_temp" in warnings
    assert "surface_temp" in warnings


def test_home_demo_path_contains_all_requested_links():
    app = AppTest.from_file(str(ROOT / "app" / "Home.py")).run()

    assert not app.exception
    intro = app.markdown[0].value
    assert intro.count(".") == 2
    assert len(app.warning) + len(app.info) <= 1
    safeguards = next(element.value for element in app.markdown if "Compare only compatible" in element.value)
    assert safeguards.count("\n- ") + 1 == 3
    rendered = "\n".join(element.label for element in app.get("page_link"))
    for step in (
        "Review the Jezero reference",
        "Explore Earth candidate sites",
        "Compare terrain measures",
        "Review seasonal temperature coverage",
        "Review mission analogy gaps",
        "Check dataset sources and limitations",
    ):
        assert step in rendered
    assert all(text not in rendered for text in ("Select Mars", "Select Jezero", "Select rover mobility"))
    assert len(app.get("page_link")) == 6
    assert "The tool is scoped to Mars rover mobility, with Jezero as the reference." in intro
