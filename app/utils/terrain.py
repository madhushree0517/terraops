from pathlib import Path
import re
from typing import Any

import pandas as pd
import yaml


TERRAIN_SITES = (
    ("jezero", "Jezero"),
    ("atacama", "Atacama"),
    ("ladakh", "Ladakh"),
    ("askja", "Askja"),
)
TERRAIN_MATRIX_METRICS = (
    ("slope_p90_deg", "Slope P90 (unit unconfirmed)", "unit unconfirmed"),
    ("pct_area_slope_gt10", "Area with slope >10 degrees", "%"),
    ("pct_area_slope_gt17", "Area with slope >17 degrees", "%"),
    ("pct_area_slope_gt24", "Area with slope >24 degrees", "%"),
    ("roughness", "Roughness", "rank only"),
    ("rock_cover_cfa_pct", "Rock cover CFA", "%"),
    ("pct_area_step_gt20cm", "Area with steps >20 cm", "%"),
    ("pct_area_step_gt35cm", "Area with steps >35 cm", "%"),
    ("material_class", "Material class", "categorical"),
)
NEUTRAL_COLOR = "#e8ecef"
MATRIX_TEXT_COLOR = "#14212b"
MATRIX_HEADER_BACKGROUND = "#263746"
MATRIX_HEADER_TEXT = "#ffffff"
MATRIX_ROW_HEADER_BACKGROUND = "#edf1f3"


def contrast_ratio(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        value = color.removeprefix("#")
        channels = [int(value[index:index + 2], 16) / 255 for index in (0, 2, 4)]
        linear = [
            channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    luminances = sorted((luminance(foreground), luminance(background)))
    return (luminances[1] + 0.05) / (luminances[0] + 0.05)


def load_terrain_band_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[2] / "config" / "bands.yaml"
    with config_path.open(encoding="utf-8") as source:
        config = yaml.safe_load(source)
    if not isinstance(config, dict):
        raise ValueError("config/bands.yaml must contain a mapping.")
    if config.get("status") != "draft v0.1, pending engineering review":
        raise ValueError("Terrain bands must remain marked draft v0.1 pending engineering review.")
    baseline = config.get("baseline_m")
    if not isinstance(baseline, (int, float)) or baseline <= 0:
        raise ValueError("Terrain baseline_m must be a positive number.")
    metrics = config.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("Terrain band metrics must be a mapping.")
    for metric_name, metric in metrics.items():
        if not isinstance(metric, dict) or not isinstance(metric.get("bands"), list):
            raise ValueError(f"Terrain metric {metric_name!r} must define a bands list.")
        for band in metric["bands"]:
            if not isinstance(band, dict) or not isinstance(band.get("label"), str):
                raise ValueError(f"Terrain metric {metric_name!r} contains an invalid band.")
            color = band.get("color", "")
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(color)):
                raise ValueError(f"Terrain metric {metric_name!r} contains an invalid band color.")
    return config


def classify_terrain_band(
    metric_name: str, value: Any, config: dict[str, Any]
) -> dict[str, str] | None:
    if pd.isna(value):
        return None
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{metric_name} must be numeric to classify a band.") from error
    if not pd.notna(numeric_value):
        return None
    metric_config = config.get("metrics", {}).get(metric_name)
    if metric_config is None:
        return None
    for band in metric_config["bands"]:
        lower = band.get("lower")
        upper = band.get("upper")
        above_lower = (
            True
            if lower is None
            else numeric_value >= lower
            if band.get("lower_inclusive", True)
            else numeric_value > lower
        )
        below_upper = (
            True
            if upper is None
            else numeric_value <= upper
            if band.get("upper_inclusive", False)
            else numeric_value < upper
        )
        if above_lower and below_upper:
            return {"label": band["label"], "color": band["color"]}
    return {"label": "outside band definitions", "color": NEUTRAL_COLOR}


def _is_missing(value: Any) -> bool:
    return value is None or pd.isna(value)


def _lookup_metric(terrain: pd.DataFrame, site_id: str, metric_name: str) -> pd.Series | None:
    rows = terrain.loc[
        (terrain["site_id"].astype(str).str.casefold() == site_id)
        & (terrain["metric_name"].astype(str) == metric_name)
    ]
    return None if rows.empty else rows.iloc[0]


def _tier_label(value: Any) -> str:
    if not _is_missing(value) and str(value).strip() in {"A", "B"}:
        return f"Tier {str(value).strip()}"
    return "not available"


def _format_metric_value(metric_name: str, value: Any) -> str:
    if metric_name == "material_class":
        return str(value).strip()
    numeric_value = float(value)
    if metric_name.startswith("pct_area_") or metric_name == "rock_cover_cfa_pct":
        return f"{numeric_value:.2f}%"
    if metric_name == "slope_p90_deg":
        return f"{numeric_value:.2f} (unit unconfirmed)"
    return f"{numeric_value:.2f}"


def build_terrain_matrix(
    terrain: pd.DataFrame, config: dict[str, Any]
) -> list[dict[str, Any]]:
    """Prepare display cells; missing values stay pending and are never coerced to zero."""
    material_reference = _lookup_metric(terrain, "jezero", "material_class")
    reference_value = (
        None
        if material_reference is None or _is_missing(material_reference.get("value"))
        else str(material_reference["value"]).strip()
    )

    roughness_values = {}
    for site_id, _ in TERRAIN_SITES:
        row = _lookup_metric(terrain, site_id, "roughness")
        if row is not None and not _is_missing(row.get("value")) and _tier_label(row.get("tier")) != "not available":
            roughness_values[site_id] = float(row["value"])
    roughness_order = sorted(set(roughness_values.values()))
    roughness_ranks = {value: index + 1 for index, value in enumerate(roughness_order)}

    matrix = []
    for metric_name, label, _ in TERRAIN_MATRIX_METRICS:
        cells = {}
        for site_id, _site_label in TERRAIN_SITES:
            row = _lookup_metric(terrain, site_id, metric_name)
            tier = _tier_label(None if row is None else row.get("tier"))
            value = None if row is None else row.get("value")
            cell = {
                "value": "data pending",
                "band": "",
                "color": NEUTRAL_COLOR,
                "text_color": MATRIX_TEXT_COLOR,
                "tier": "not available",
                "detail": "",
                "note": "",
                "number": None,
            }
            if row is None or _is_missing(value):
                if row is not None and not _is_missing(row.get("availability_note")):
                    cell["note"] = str(row["availability_note"])
                cells[site_id] = cell
                continue
            if tier == "not available":
                cell["value"] = "data pending"
                if not _is_missing(row.get("availability_note")):
                    cell["note"] = str(row["availability_note"])
                cells[site_id] = cell
                continue

            cell["tier"] = tier
            cell["value"] = _format_metric_value(metric_name, value)
            if metric_name != "material_class":
                cell["number"] = float(value)
            if metric_name == "roughness":
                rank = roughness_ranks[float(value)]
                cell["band"] = "rank order only"
                cell["detail"] = f"Rank {rank} of {len(roughness_order)} (ascending numeric value)"
                metric_label = row.get("roughness_metric")
                window = row.get("roughness_window")
                metric_label = "not documented" if _is_missing(metric_label) else str(metric_label)
                window = "not documented" if _is_missing(window) else str(window)
                cell["detail"] += f"; metric: {metric_label}; window: {window}"
                cell["color"] = NEUTRAL_COLOR
            elif metric_name == "material_class":
                if reference_value is None:
                    cell["band"] = "Jezero reference class pending"
                elif str(value).strip().casefold() == reference_value.casefold():
                    cell["band"] = "matches Jezero"
                    cell["color"] = "#dcefe4"
                else:
                    cell["band"] = "differs from Jezero"
                    cell["color"] = "#f5d6d3"
            else:
                band = classify_terrain_band(metric_name, value, config)
                if band is None:
                    cell["band"] = "band not defined"
                else:
                    cell["band"] = band["label"]
                    cell["color"] = band["color"]
            cells[site_id] = cell
        matrix.append({"metric_name": metric_name, "label": label, "cells": cells})
    return matrix


def collect_terrain_footnotes(
    matrix: list[dict[str, Any]],
) -> tuple[list[str], dict[str, int], dict[str, int]]:
    footnotes: list[str] = []
    footnote_numbers: dict[str, int] = {}
    for metric in matrix:
        for site_id, _ in TERRAIN_SITES:
            note = metric["cells"][site_id].get("note", "")
            if note and note not in footnote_numbers:
                footnotes.append(note)
                footnote_numbers[note] = len(footnotes)

    site_note_numbers = {}
    for site_id, _ in TERRAIN_SITES:
        notes = [
            metric["cells"][site_id].get("note", "")
            for metric in matrix
            if metric["cells"][site_id].get("note", "").startswith("Terrain metrics pending")
        ]
        if notes:
            site_note_numbers[site_id] = footnote_numbers[notes[0]]
    return footnotes, footnote_numbers, site_note_numbers


def cell_has_value(cell: dict[str, Any]) -> bool:
    return cell["tier"] in {"Tier A", "Tier B"} and cell["value"] not in {
        "data pending",
        "not available at this tier",
    }


def split_matrix(
    matrix: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Return rows with any value, labels of rows with none, and site ids that have values."""
    visible = [
        metric for metric in matrix if any(cell_has_value(c) for c in metric["cells"].values())
    ]
    unmeasured = [
        metric["label"]
        for metric in matrix
        if not any(cell_has_value(c) for c in metric["cells"].values())
    ]
    site_ids = [
        site_id
        for site_id, _ in TERRAIN_SITES
        if any(cell_has_value(metric["cells"][site_id]) for metric in matrix)
    ]
    return visible, unmeasured, site_ids


def _pending_reason(note: str) -> str:
    if "CRS" in note:
        return "raster coordinate system under review"
    if "georeferencing" in note:
        return "raster georeferencing under review"
    if re.search(r"\bno\b[^.]*raster", note, flags=re.IGNORECASE) or "absent" in note:
        return "no terrain raster supplied"
    if "extent" in note:
        return "raster extent under review"
    return "terrain data not yet available"


def not_yet_included_line(
    terrain: pd.DataFrame, matrix: list[dict[str, Any]]
) -> str | None:
    """Name the sites without terrain values, with a reason taken from the loaded notes."""
    _, _, with_data = split_matrix(matrix)
    items = []
    for site_id, label in TERRAIN_SITES:
        if site_id in with_data:
            continue
        rows = terrain.loc[terrain["site_id"].astype(str).str.casefold() == site_id]
        notes = (
            rows["availability_note"].dropna().astype(str).str.strip()
            if "availability_note" in rows
            else pd.Series(dtype=str)
        )
        notes = notes[notes != ""]
        reason = _pending_reason(notes.iloc[0]) if not notes.empty else "terrain data not yet available"
        items.append(f"{label} ({reason})")
    if not items:
        return None
    joined = items[0] if len(items) == 1 else ", ".join(items[:-1]) + f" and {items[-1]}"
    return f"Not yet included: {joined}."


def band_text(cell: dict[str, Any]) -> str:
    band = cell["band"]
    if band in {"", "band not defined", "rank order only"}:
        return ""
    if band in {"moderate", "high"}:
        return f"{band} constraint"
    return band


def display_number(metric_name: str, number: float) -> str:
    if metric_name.startswith("pct_area_") or metric_name == "rock_cover_cfa_pct":
        return f"{number:.1f}%"
    return f"{number:.1f}"


def display_cell_value(metric_name: str, cell: dict[str, Any]) -> str:
    if cell["number"] is None:
        return cell["value"]
    return display_number(metric_name, cell["number"])


SUMMARY_TEMPLATES = {
    "pct_area_slope_gt24": "{value} of the area is steeper than 24 degrees",
    "rock_cover_cfa_pct": "rock cover (CFA) is {value}",
    "pct_area_step_gt35cm": "{value} of the area has steps taller than 35 cm",
}


def site_summary_lines(matrix: list[dict[str, Any]], site_ids: list[str]) -> list[str]:
    """One plain sentence per site, built only from displayed values and bands."""
    labels = dict(TERRAIN_SITES)
    lines = []
    for site_id in site_ids:
        clauses = []
        for metric in matrix:
            template = SUMMARY_TEMPLATES.get(metric["metric_name"])
            cell = metric["cells"][site_id]
            if template is None or not cell_has_value(cell):
                continue
            clause = template.format(value=display_cell_value(metric["metric_name"], cell))
            if band_text(cell):
                clause += f" ({band_text(cell)})"
            clauses.append(clause)
        if not clauses:
            first = next(
                (m for m in matrix if cell_has_value(m["cells"][site_id])),
                None,
            )
            if first is None:
                continue
            value = display_cell_value(first["metric_name"], first["cells"][site_id])
            clauses.append(f"{first['label'].lower()} is {value}")
        lines.append(f"{labels[site_id]}: {'; '.join(clauses)}.")
    return lines


def build_resolution_panel(terrain: pd.DataFrame, baseline_m: float) -> list[dict[str, Any]]:
    panel = []
    for site_id, site_label in TERRAIN_SITES:
        site_rows = terrain.loc[terrain["site_id"].astype(str).str.casefold() == site_id]
        native_values = pd.to_numeric(site_rows.get("native_resolution_m"), errors="coerce").dropna()
        source_values = site_rows.get("dem_source", pd.Series(dtype=object)).dropna()
        metric_values = site_rows.loc[
            site_rows["metric_name"].isin([metric[0] for metric in TERRAIN_MATRIX_METRICS]), "value"
        ]
        has_metric_data = not metric_values.dropna().empty
        computed_flags = site_rows.get("computed_at_baseline", pd.Series(dtype=object))
        computed_at_baseline = computed_flags.astype(str).str.casefold().eq("true").any()
        native_resolution = float(native_values.iloc[0]) if not native_values.empty else None
        if native_resolution is None:
            status = "data pending"
        elif has_metric_data and not computed_at_baseline:
            status = f"Warning: values computed at native resolution, not the {baseline_m:g} m baseline"
        elif has_metric_data:
            status = f"Computed at the {baseline_m:g} m baseline"
        else:
            note_values = site_rows.get("availability_note", pd.Series(dtype=object)).dropna()
            status = str(note_values.iloc[0]) if not note_values.empty else "Terrain metrics pending"
        panel.append(
            {
                "site_id": site_label,
                "native_resolution_m": (
                    "data pending" if native_resolution is None else f"{native_resolution:.6f} m"
                ),
                "baseline_m": f"{baseline_m:g} m",
                "dem_source": "not documented" if source_values.empty else str(source_values.iloc[0]),
                "status": status,
            }
        )
    return panel
