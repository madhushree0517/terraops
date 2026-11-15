from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.utils import config
from app.utils.loaders import TERRAIN_METRICS_COLUMNS


PAGE_PATH = Path(__file__).resolve().parents[1] / "app" / "pages" / "3_Terrain_Comparison.py"
GRAVITY = (
    "Results show relative terrain difficulty under normal Earth gravity, not absolute "
    "passability on Mars."
)


def _row(site_id, metric_name, value, unit="", tier="B", note=""):
    row = {column: float("nan") for column in TERRAIN_METRICS_COLUMNS}
    row.update(
        {
            "schema_version": "1.0",
            "site_id": site_id,
            "metric_name": metric_name,
            "value": value,
            "metric_unit": unit,
            "tier": tier,
            "baseline_m": 30,
            "dem_source": "Copernicus GLO30",
            "native_resolution_m": 29.5,
            "computed_at_baseline": False,
            "availability_note": note,
            "source_file": "large/terrain/test.tif",
            "crs": "EPSG:32719",
            "resolution_x": 29.5,
            "resolution_y": 29.5,
            "resolution_unit": "metre",
            "statistics_scope": "whole supplied raster extent",
        }
    )
    return row


@pytest.fixture
def terrain_app(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    processed_dir = data_root / "processed"
    processed_dir.mkdir(parents=True)
    (data_root / "sample").mkdir()
    rows = [
        _row("atacama", "slope_p90_deg", 17.119352340698242),
        _row("atacama", "pct_area_slope_gt10", 20.26, "%"),
        _row("atacama", "pct_area_slope_gt17", 10.12, "%"),
        _row("atacama", "pct_area_slope_gt24", 4.61, "%"),
        _row("atacama", "roughness", 14.05),
        _row("ladakh", "slope_p90_deg", 42.86),
        _row("ladakh", "pct_area_slope_gt24", 62.73, "%"),
        _row("ladakh", "roughness", 50.12),
        _row(
            "jezero", "pct_area_slope_gt24", float("nan"), "%", "",
            "Terrain metrics pending: no Jezero terrain raster is present.",
        ),
        _row(
            "askja", "pct_area_slope_gt24", float("nan"), "%", "",
            "Terrain metrics pending CRS review: Askja CRS is outside area of use.",
        ),
        _row(
            "atacama", "rock_cover_cfa_pct", float("nan"), "%", "",
            "No supplied source for rock_cover_cfa_pct; value remains missing.",
        ),
        _row("atacama", "pct_area_step_gt20cm", float("nan"), "%", "", "No supplied source."),
        _row("atacama", "material_class", float("nan"), "", "", "No supplied source."),
    ]
    pd.DataFrame(rows, columns=TERRAIN_METRICS_COLUMNS).to_csv(
        processed_dir / "terrain_metrics.csv", index=False
    )
    pd.DataFrame(
        [
            {"site_id": "atacama", "bin_start": 0, "bin_end": 1, "pixel_count": 1, "share": 0.25},
            {"site_id": "atacama", "bin_start": 1, "bin_end": 2, "pixel_count": 3, "share": 0.75},
            {"site_id": "ladakh", "bin_start": 0, "bin_end": 1, "pixel_count": 2, "share": 0.5},
            {"site_id": "ladakh", "bin_start": 1, "bin_end": 2, "pixel_count": 2, "share": 0.5},
        ]
    ).to_csv(processed_dir / "slope_histograms.csv", index=False)
    monkeypatch.setattr(config, "DATA_ROOT", data_root)
    return AppTest.from_file(str(PAGE_PATH)).run()


def _text(app):
    return "\n".join(
        element.value for element in [*app.markdown, *app.warning, *app.info, *app.caption]
    )


def test_page_order_purpose_chart_table_lines_expander(terrain_app):
    app = terrain_app

    assert not app.exception
    kinds = [element.type for element in app.main]
    values = [getattr(element, "value", "") for element in app.main]
    chart = kinds.index("plotly_chart")
    table = next(i for i, v in enumerate(values) if "terrain-matrix" in str(v))
    lines = next(i for i, v in enumerate(values) if str(v).startswith("Atacama:"))
    expanders = [i for i, kind in enumerate(kinds) if kind == "expander"]
    purpose = next(i for i, v in enumerate(values) if str(v).startswith("How steep"))
    assert purpose < chart < table < lines < expanders[-1]
    assert app.get("expander")[-1].label == "About these results"
    assert app.get("expander")[-1].proto.expanded is False


def test_only_metrics_and_sites_with_values_are_table_rows_and_columns(terrain_app):
    app = terrain_app
    table_html = next(m.value for m in app.markdown if "terrain-matrix" in m.value)

    for label in ("Slope P90", "Area with slope &gt;10 degrees", "Area with slope &gt;24 degrees", "Roughness"):
        assert label in table_html
    for pending in ("Rock cover", "Area with steps", "Material class"):
        assert pending not in table_html
    assert ">Atacama<" in table_html and ">Ladakh<" in table_html
    assert ">Jezero<" not in table_html and ">Askja<" not in table_html
    assert "data pending" not in table_html
    assert "Tier A" not in table_html and "Tier B" not in table_html
    assert "unit unconfirmed" not in table_html
    assert "no band defined" not in table_html
    assert "4.6%" in table_html and "moderate constraint" in table_html
    assert "td.bg-fff0c2{background-color:#fff0c2" in table_html
    assert "td.bg-f5d6d3{background-color:#f5d6d3" in table_html
    assert "62.7%" in table_html and "high constraint" in table_html


def test_terrain_body_hides_missing_sites_and_measurements(terrain_app):
    text = _text(terrain_app) + "\n" + "\n".join(
        frame.value.to_string() for frame in terrain_app.dataframe
    )
    assert "Not yet included" not in text
    assert "data pending" not in text.casefold()
    assert "not available" not in text.casefold()
    assert "no terrain raster" not in text.casefold()
    assert "unit unconfirmed" not in text.casefold()
    assert not any(expander.label == "What we cannot measure yet" for expander in terrain_app.get("expander"))


def test_plain_language_lines_have_no_ranking_or_score(terrain_app):
    app = terrain_app
    text = _text(app)

    assert "Atacama: 4.6% of the area is steeper than 24 degrees (moderate constraint)." in text
    assert "Ladakh: 62.7% of the area is steeper than 24 degrees (high constraint)." in text
    for forbidden in ("Overall similarity", "Candidate ranking", "Weight sensitivity", "score:", "rank 1"):
        assert forbidden.casefold() not in text.casefold()
    assert "no composite score or ranking is calculated" in "\n".join(
        element.value for element in app.get("expander")[-1].markdown
    )
    assert not app.metric


def test_gravity_statement_and_single_banner(terrain_app):
    app = terrain_app

    assert any(element.value == GRAVITY for element in app.info)
    assert len(app.info) + len(app.warning) == 1


def test_limitations_live_in_the_about_expander(terrain_app):
    app = terrain_app
    about = "\n".join(element.value for element in app.get("expander")[-1].markdown)

    assert "Tier A" in about and "Tier B" in about
    assert "not how suitable a site is" in about
    assert "The slope unit has not been confirmed with the data provider, so the cutoffs are provisional." in about
    assert "not a validated site boundary" in about
    assert "native resolution" in about
    outside = _text(app).replace(about, "")
    assert "Tier A" not in outside
    assert "validated site boundary" not in outside
    assert "The slope unit has not been confirmed" not in outside
    assert "Jezero and Askja are not part of this comparison because no usable terrain data is available for them yet." in about
    resolution = app.get("expander")[-1].dataframe[0].value
    assert list(resolution.columns) == [
        "Site", "Native resolution", "Common baseline", "Terrain source", "Status",
    ]
    assert set(resolution["Site"]) == {"Atacama", "Ladakh"}
    assert "None" not in resolution.to_string()


def test_table_hidden_when_no_values_exist(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    processed_dir = data_root / "processed"
    processed_dir.mkdir(parents=True)
    (data_root / "sample").mkdir()
    pd.DataFrame(
        [_row("jezero", "pct_area_slope_gt24", float("nan"), "%", "", "no raster")],
        columns=TERRAIN_METRICS_COLUMNS,
    ).to_csv(processed_dir / "terrain_metrics.csv", index=False)
    monkeypatch.setattr(config, "DATA_ROOT", data_root)

    app = AppTest.from_file(str(PAGE_PATH)).run()

    assert not app.exception
    assert not any("terrain-matrix" in m.value for m in app.markdown)
    assert "Select at least one site with usable terrain measurements to show a comparison." in _text(app)
    assert len(app.get("plotly_chart")) == 0
