import numpy as np
import pandas as pd
import pytest

from app.utils.terrain import (
    MATRIX_HEADER_BACKGROUND,
    MATRIX_HEADER_TEXT,
    MATRIX_ROW_HEADER_BACKGROUND,
    MATRIX_TEXT_COLOR,
    NEUTRAL_COLOR,
    build_resolution_panel,
    build_terrain_matrix,
    classify_terrain_band,
    collect_terrain_footnotes,
    contrast_ratio,
    load_terrain_band_config,
)
from app.components.site_profile import build_terrain_profile_table


@pytest.fixture
def band_config():
    return load_terrain_band_config()


@pytest.mark.parametrize(
    ("metric_name", "value", "expected"),
    [
        ("pct_area_slope_gt24", 1.99, "low constraint"),
        ("pct_area_slope_gt24", 2.0, "moderate"),
        ("pct_area_slope_gt24", 10.0, "moderate"),
        ("pct_area_slope_gt24", 10.0001, "high"),
        ("rock_cover_cfa_pct", 6.99, "low constraint"),
        ("rock_cover_cfa_pct", 7.0, "moderate"),
        ("rock_cover_cfa_pct", 15.0, "moderate"),
        ("rock_cover_cfa_pct", 15.0001, "high"),
        ("pct_area_step_gt35cm", 4.99, "low constraint"),
        ("pct_area_step_gt35cm", 5.0, "moderate"),
        ("pct_area_step_gt35cm", 15.0, "moderate"),
        ("pct_area_step_gt35cm", 15.0001, "high"),
    ],
)
def test_draft_band_boundaries(band_config, metric_name, value, expected):
    band = classify_terrain_band(metric_name, value, band_config)

    assert band["label"] == expected


def test_missing_value_has_no_band(band_config):
    assert classify_terrain_band("pct_area_slope_gt24", np.nan, band_config) is None


def test_terrain_band_and_header_colors_meet_wcag_aa_contrast(band_config):
    backgrounds = {
        NEUTRAL_COLOR,
        "#ffffff",
        MATRIX_ROW_HEADER_BACKGROUND,
        *(
            band["color"]
            for metric in band_config["metrics"].values()
            for band in metric["bands"]
        ),
        "#f5d6d3",
        "#dcefe4",
    }

    for background in backgrounds:
        assert contrast_ratio(MATRIX_TEXT_COLOR, background) >= 4.5

    assert contrast_ratio(MATRIX_HEADER_TEXT, MATRIX_HEADER_BACKGROUND) >= 4.5

    empty_terrain = pd.DataFrame(columns=("site_id", "metric_name", "value", "tier"))
    matrix = build_terrain_matrix(empty_terrain, band_config)
    for row in matrix:
        for cell in row["cells"].values():
            assert contrast_ratio(cell["text_color"], cell["color"]) >= 4.5


def test_site_profile_shows_pending_mobility_values_without_legacy_sample_numbers():
    profile = build_terrain_profile_table(
        pd.DataFrame(columns=("metric_name", "value", "tier", "metric_unit"))
    )

    assert profile["Value"].eq("data pending").all()
    assert profile["Tier"].eq("not available").all()
    assert "-2500" not in profile.to_string()


def test_terrain_matrix_notes_are_deduplicated_and_numbered():
    config = load_terrain_band_config()
    terrain = pd.DataFrame(
        [
            {
                "site_id": "jezero",
                "metric_name": "slope_p90_deg",
                "value": np.nan,
                "tier": "",
                "availability_note": "Terrain metrics pending: no Jezero raster.",
            },
            {
                "site_id": "jezero",
                "metric_name": "pct_area_slope_gt24",
                "value": np.nan,
                "tier": "",
                "availability_note": "Terrain metrics pending: no Jezero raster.",
            },
            {
                "site_id": "askja",
                "metric_name": "slope_p90_deg",
                "value": np.nan,
                "tier": "",
                "availability_note": "Terrain metrics pending CRS review: Askja.",
            },
            {
                "site_id": "atacama",
                "metric_name": "rock_cover_cfa_pct",
                "value": np.nan,
                "tier": "",
                "availability_note": "No supplied source for rock cover.",
            },
        ]
    )

    matrix = build_terrain_matrix(terrain, config)
    notes, note_numbers, site_note_numbers = collect_terrain_footnotes(matrix)

    assert notes == [
        "Terrain metrics pending: no Jezero raster.",
        "Terrain metrics pending CRS review: Askja.",
        "No supplied source for rock cover.",
    ]
    assert note_numbers[notes[0]] == 1
    assert note_numbers[notes[1]] == 2
    assert site_note_numbers == {"jezero": 1, "askja": 2}


def test_matrix_keeps_missing_separate_from_real_zero(band_config):
    terrain = pd.DataFrame(
        [
            {
                "site_id": "jezero",
                "metric_name": "pct_area_slope_gt24",
                "value": np.nan,
                "tier": "",
                "availability_note": "No Jezero raster is available.",
            },
            {
                "site_id": "atacama",
                "metric_name": "pct_area_slope_gt24",
                "value": 0.0,
                "tier": "B",
                "availability_note": "",
            },
        ]
    )

    rows = build_terrain_matrix(terrain, band_config)
    cells = next(row["cells"] for row in rows if row["metric_name"] == "pct_area_slope_gt24")

    assert cells["jezero"]["value"] == "data pending"
    assert cells["jezero"]["tier"] == "not available"
    assert cells["atacama"]["value"] == "0.00%"
    assert cells["atacama"]["band"] == "low constraint"
    assert cells["atacama"]["tier"] == "Tier B"


def test_roughness_uses_rank_only_and_material_matches_jezero(band_config):
    terrain = pd.DataFrame(
        [
            {"site_id": "jezero", "metric_name": "material_class", "value": "basalt", "tier": "B"},
            {"site_id": "jezero", "metric_name": "roughness", "value": 4.0, "tier": "B"},
            {"site_id": "atacama", "metric_name": "material_class", "value": "basalt", "tier": "B"},
            {"site_id": "atacama", "metric_name": "roughness", "value": 8.0, "tier": "B"},
        ]
    )

    rows = build_terrain_matrix(terrain, band_config)
    roughness = next(row["cells"] for row in rows if row["metric_name"] == "roughness")
    material = next(row["cells"] for row in rows if row["metric_name"] == "material_class")

    assert roughness["jezero"]["band"] == "rank order only"
    assert "Rank 1 of 2" in roughness["jezero"]["detail"]
    assert "Rank 2 of 2" in roughness["atacama"]["detail"]
    assert material["atacama"]["band"] == "matches Jezero"
    assert material["atacama"]["tier"] == "Tier B"


def test_resolution_panel_warns_when_native_values_are_not_at_baseline():
    terrain = pd.DataFrame(
        [
            {
                "site_id": "atacama",
                "metric_name": "slope_p90_deg",
                "value": 12.0,
                "tier": "B",
                "native_resolution_m": 29.68,
                "baseline_m": 30.0,
                "computed_at_baseline": False,
                "dem_source": "Copernicus GLO30",
                "availability_note": "",
            }
        ]
    )

    panel = build_resolution_panel(terrain, 30)
    sites = {row["site_id"]: row for row in panel}

    assert sites["Atacama"]["native_resolution_m"] == "29.680000 m"
    assert "not the 30 m baseline" in sites["Atacama"]["status"]
    assert sites["Jezero"]["native_resolution_m"] == "data pending"


def test_split_matrix_and_not_yet_included_are_built_from_data(band_config):
    from app.utils.terrain import not_yet_included_line, site_summary_lines, split_matrix

    terrain = pd.DataFrame(
        [
            {"site_id": "atacama", "metric_name": "pct_area_slope_gt24", "value": 4.61, "tier": "B"},
            {"site_id": "atacama", "metric_name": "rock_cover_cfa_pct", "value": np.nan, "tier": ""},
            {
                "site_id": "jezero", "metric_name": "pct_area_slope_gt24", "value": np.nan,
                "tier": "", "availability_note": "Terrain metrics pending: no Jezero terrain raster.",
            },
            {
                "site_id": "askja", "metric_name": "pct_area_slope_gt24", "value": np.nan,
                "tier": "", "availability_note": "Terrain metrics pending CRS review: outside area of use.",
            },
        ]
    )
    matrix = build_terrain_matrix(terrain, band_config)

    visible, unmeasured, site_ids = split_matrix(matrix)

    assert [row["metric_name"] for row in visible] == ["pct_area_slope_gt24"]
    assert "Rock cover CFA" in unmeasured and "Material class" in unmeasured
    assert site_ids == ["atacama"]
    assert not_yet_included_line(terrain, matrix) == (
        "Not yet included: Jezero (no terrain raster supplied), Ladakh (terrain data not yet available) "
        "and Askja (raster coordinate system under review)."
    )
    assert site_summary_lines(matrix, site_ids) == [
        "Atacama: 4.6% of the area is steeper than 24 degrees (moderate constraint)."
    ]


def test_not_yet_included_is_none_when_every_site_has_values(band_config):
    from app.utils.terrain import not_yet_included_line

    terrain = pd.DataFrame(
        [
            {"site_id": site_id, "metric_name": "pct_area_slope_gt24", "value": 1.0, "tier": "B"}
            for site_id in ("jezero", "atacama", "ladakh", "askja")
        ]
    )

    assert not_yet_included_line(terrain, build_terrain_matrix(terrain, band_config)) is None
