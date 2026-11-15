import json
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from app.utils import config
from app.utils.analogy import format_data_method_note
from app.utils.loaders import CATALOGUE_COLUMNS


ROOT = Path(__file__).resolve().parents[1]


def test_analogy_page_keeps_draft_entries_pending(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    processed_dir = data_root / "processed"
    processed_dir.mkdir(parents=True)
    (data_root / "sample").mkdir()
    gaps = [
        {
            "schema_version": "1.0",
            "factor": "MODIS QA interpretation",
            "can_rehearse_on_earth": None,
            "review_status": "draft, pending engineering review",
            "explanation": "Review product QA semantics.",
        },
        {
            "schema_version": "1.0",
            "factor": "MEDA geometry",
            "can_rehearse_on_earth": None,
            "review_status": "draft, pending engineering review",
            "explanation": "Verify instrument geometry.",
        },
        {
            "schema_version": "1.0",
            "factor": "Martian seasonal reference",
            "can_rehearse_on_earth": None,
            "review_status": "draft, pending engineering review",
            "explanation": "Review Ls coverage.",
        },
        {
            "schema_version": "1.0",
            "factor": "ATS-TIRS time alignment",
            "can_rehearse_on_earth": None,
            "review_status": "draft, pending engineering review",
            "explanation": "The file was not found in the Google Drive search. Verify clock alignment.",
        },
        {
            "schema_version": "1.0",
            "factor": "Temperature threshold",
            "can_rehearse_on_earth": None,
            "review_status": "draft, pending engineering review",
            "explanation": "The previously used 293 K threshold is a chosen screening threshold, not a verified instrument operating limit.",
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
    assert "Mission-relevant analogy gaps" in rendered
    assert "Reduced gravity" in rendered
    assert "Earth gravity is about 2.6 times Mars, so sinkage and traction differ." in rendered
    assert "Thin CO2 atmosphere" in rendered
    assert "Radiation" in rendered
    assert "Regolith and soil properties" in rendered
    assert "Dust adhesion" in rendered
    assert "Thermal environment" in rendered
    assert "Similar temperatures do not mean equivalent thermal conditions." in rendered
    assert "Navigation and communication latency" in rendered
    assert "Status: pending review" in rendered
    assert "Can-rehearse decision" not in rendered
    assert [caption.value for caption in app.caption].count("Status: pending review") == 7
    assert "MODIS QA interpretation" in rendered
    assert "MEDA geometry" in rendered
    assert "Martian seasonal reference" in rendered
    assert "ATS-TIRS time alignment" in rendered
    assert len(app.get("expander")) == 1
    team_notes = app.get("expander")[0]
    assert team_notes.label == "Data and method notes (for the team)"
    assert team_notes.proto.expanded is False
    assert "not absolute passability on Mars" in rendered
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
    assert "citation" in catalogue_table.columns
    assert "licence" in catalogue_table.columns
    assert catalogue_table["spatial_resolution"].iloc[0] == "not documented"
    status_text = " ".join(str(value) for value in status_table.to_numpy().flatten())
    assert "processed (draft, pending review)" in status_text


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
        "Open the app",
        "Select Mars",
        "Select Jezero",
        "Select rover mobility",
        "View the terrain reference",
        "View the Earth candidates",
        "Compare terrain",
        "Read the band matrix",
        "Open When-to-Test",
        "View the temperature bands",
        "Open the Analogy Gap Detector",
        "View the final recommendation and limitations",
    ):
        assert step in rendered
