import pandas as pd
import pytest

from app.utils.scoring import (
    load_scoring_config,
    normalize_weights,
    rank_candidates,
    resolution_comparability,
    score_candidate,
)


def test_identical_values_have_maximum_similarity():
    config = load_scoring_config()
    values = pd.Series(
        {parameter: 10.0 for parameter in config["weights"]}
    )

    result = score_candidate(
        values,
        values,
        config["weights"],
        config["difference_scales"],
    )

    assert result["score"] == pytest.approx(100.0)
    assert all(score == pytest.approx(100.0) for score in result["parameter_scores"].values())


def test_missing_values_are_excluded_not_zero_filled():
    config = load_scoring_config()
    parameter = next(iter(config["weights"]))
    reference = pd.Series({parameter: 10.0})
    candidate = pd.Series({parameter: float("nan")})

    result = score_candidate(
        reference,
        candidate,
        {parameter: 1.0},
        config["difference_scales"],
    )

    assert pd.isna(result["score"])
    assert result["parameter_scores"] == {}
    assert result["excluded_parameters"] == [parameter]


def test_normalized_weights_sum_to_one():
    config = load_scoring_config()

    normalized = normalize_weights(config["weights"])

    assert sum(normalized.values()) == pytest.approx(1.0)


def test_resolution_metadata_does_not_change_candidate_ranking():
    config = load_scoring_config()
    reference = {
        "elevation_std_m": 300,
        "slope_mean_deg": 4,
        "slope_p95_deg": 12,
        "roughness_metric": 0.2,
    }
    candidates = pd.DataFrame(
        [
            {"site_id": "near", "elevation_std_m": 310, "slope_mean_deg": 4.2, "slope_p95_deg": 12, "roughness_metric": 0.2, "resolution_m": 30},
            {"site_id": "far", "elevation_std_m": 500, "slope_mean_deg": 8, "slope_p95_deg": 20, "roughness_metric": 0.5, "resolution_m": 60},
        ]
    )
    changed_resolution = candidates.copy()
    changed_resolution["resolution_m"] = [1000, 0.01]

    original_ranking = rank_candidates(
        reference, candidates, config["weights"], config["difference_scales"]
    )
    changed_ranking = rank_candidates(
        reference,
        changed_resolution,
        config["weights"],
        config["difference_scales"],
    )

    assert original_ranking["site_id"].tolist() == changed_ranking["site_id"].tolist()
    assert original_ranking["score"].tolist() == pytest.approx(changed_ranking["score"].tolist())


def test_zero_elevation_mean_weight_excludes_it_from_score():
    config = load_scoring_config()
    reference = {
        "elevation_mean_m": -2500,
        "elevation_std_m": 300,
        "slope_mean_deg": 4,
        "slope_p95_deg": 12,
        "roughness_metric": 0.2,
    }
    candidate = {
        "elevation_mean_m": 100000,
        "elevation_std_m": 300,
        "slope_mean_deg": 4,
        "slope_p95_deg": 12,
        "roughness_metric": 0.2,
    }

    result = score_candidate(
        reference, candidate, config["weights"], config["difference_scales"]
    )

    assert result["score"] == pytest.approx(100.0)
    assert "elevation_mean_m" not in result["parameter_scores"]
    assert "elevation_mean_m" in result["excluded_parameters"]


def test_resolution_comparability_uses_configurable_factor():
    assert resolution_comparability(30, 60, factor=2.0)[0] is True
    comparable, flag = resolution_comparability(30, 61, factor=2.0)
    assert comparable is False
    assert "site" not in flag
    assert "2.0x" in flag