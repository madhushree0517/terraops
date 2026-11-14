"""Transparent terrain similarity heuristic; this is not a success probability."""

import math
from pathlib import Path
import tomllib
from typing import Any

import pandas as pd


SCORING_CONFIG_PATH = Path(__file__).with_name("scoring_config.toml")


def load_scoring_config() -> dict[str, Any]:
    with SCORING_CONFIG_PATH.open("rb") as source:
        return tomllib.load(source)


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    numeric = {key: float(value) for key, value in weights.items()}
    if not numeric or any(not math.isfinite(value) or value < 0 for value in numeric.values()):
        raise ValueError("Weights must be a non-empty mapping of finite non-negative values.")
    total = sum(numeric.values())
    if total <= 0:
        raise ValueError("At least one weight must be greater than zero.")
    return {key: value / total for key, value in numeric.items()}


def score_candidate(
    reference: pd.Series | dict[str, Any],
    candidate: pd.Series | dict[str, Any],
    weights: dict[str, float],
    difference_scales: dict[str, float],
) -> dict[str, Any]:
    """Score available terrain values against a reference using configured scales.

    Each parameter score is max(0, 100 * (1 - abs(candidate-reference)/scale)).
    Overall similarity is the weighted mean over available parameters only;
    remaining weights are renormalized for that candidate.
    """
    normalized_weights = normalize_weights(weights)
    parameter_scores: dict[str, float] = {}
    excluded_parameters = [
        parameter for parameter, weight in normalized_weights.items() if weight == 0
    ]

    for parameter, weight in normalized_weights.items():
        if weight == 0 or parameter == "resolution_m":
            if parameter not in excluded_parameters:
                excluded_parameters.append(parameter)
            continue
        reference_value = pd.to_numeric(reference.get(parameter), errors="coerce")
        candidate_value = pd.to_numeric(candidate.get(parameter), errors="coerce")
        scale = difference_scales.get(parameter)
        if (
            pd.isna(reference_value)
            or pd.isna(candidate_value)
            or scale is None
            or not math.isfinite(float(scale))
            or float(scale) <= 0
        ):
            excluded_parameters.append(parameter)
            continue
        parameter_scores[parameter] = max(
            0.0,
            100.0
            * (1.0 - abs(float(candidate_value) - float(reference_value)) / float(scale)),
        )

    available_weight = sum(normalized_weights[key] for key in parameter_scores)
    overall_score = (
        sum(parameter_scores[key] * normalized_weights[key] for key in parameter_scores)
        / available_weight
        if available_weight > 0
        else float("nan")
    )
    effective_weights = {
        key: normalized_weights[key] / available_weight for key in parameter_scores
    } if available_weight > 0 else {}
    return {
        "score": overall_score,
        "parameter_scores": parameter_scores,
        "weights": effective_weights,
        "excluded_parameters": excluded_parameters,
    }


def resolution_comparability(
    reference_resolution: Any,
    candidate_resolution: Any,
    factor: float = 2.0,
) -> tuple[bool | None, str]:
    """Return whether DEM resolutions are within a symmetric multiplicative factor."""
    reference_value = pd.to_numeric(reference_resolution, errors="coerce")
    candidate_value = pd.to_numeric(candidate_resolution, errors="coerce")
    if pd.isna(reference_value) or pd.isna(candidate_value):
        return None, "Not assessed: missing DEM resolution"
    if reference_value <= 0 or candidate_value <= 0 or factor < 1:
        raise ValueError("Resolutions must be positive and the comparability factor at least 1.")
    ratio = max(reference_value / candidate_value, candidate_value / reference_value)
    if ratio > factor:
        return False, f"Resolution differs by {ratio:.1f}x (limit {factor:.1f}x)"
    return True, f"Within {factor:.1f}x resolution limit"


def rank_candidates(
    reference: pd.Series | dict[str, Any],
    candidates: pd.DataFrame,
    weights: dict[str, float],
    difference_scales: dict[str, float],
) -> pd.DataFrame:
    """Rank candidates by score; metadata fields such as resolution never affect rank."""
    rows = []
    for candidate in candidates.to_dict(orient="records"):
        result = score_candidate(reference, candidate, weights, difference_scales)
        rows.append(
            {
                "site_id": candidate.get("site_id"),
                "score": result["score"],
                "excluded_parameters": result["excluded_parameters"],
            }
        )
    return pd.DataFrame(rows).sort_values(
        "score", ascending=False, na_position="last", ignore_index=True
    )


def rank_sensitivity(
    reference: pd.Series | dict[str, Any],
    candidates: pd.DataFrame,
    weights: dict[str, float],
    difference_scales: dict[str, float],
) -> pd.DataFrame:
    """Compare top-ranked site after changing each positive weight by +/- 50%."""
    baseline = rank_candidates(reference, candidates, weights, difference_scales)
    baseline_top = baseline.iloc[0]["site_id"] if not baseline.empty else None
    rows = []
    for parameter, weight in weights.items():
        if weight <= 0 or parameter == "resolution_m":
            rows.append(
                {
                    "parameter": parameter,
                    "change": "Not applicable",
                    "top_site": baseline_top,
                    "top_changed": False,
                }
            )
            continue
        for label, multiplier in (("-50%", 0.5), ("+50%", 1.5)):
            adjusted = dict(weights)
            adjusted[parameter] = weight * multiplier
            ranking = rank_candidates(reference, candidates, adjusted, difference_scales)
            top_site = ranking.iloc[0]["site_id"] if not ranking.empty else None
            rows.append(
                {
                    "parameter": parameter,
                    "change": label,
                    "top_site": top_site,
                    "top_changed": top_site != baseline_top,
                }
            )
    return pd.DataFrame(rows)