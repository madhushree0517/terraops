import pandas as pd

from app.utils.when_to_test import (
    annotate_low_data,
    months_covered,
    short_coverage_message,
    variable_type_mismatch,
)


def test_variable_mismatch_names_site_and_both_types():
    message = variable_type_mismatch("Atacama", "air_temp", "surface_temp")

    assert message == (
        "Cannot compare Atacama: Earth variable type 'air_temp' does not match "
        "Mars band variable type 'surface_temp'. No match percentage is shown."
    )


def test_single_month_has_no_recommendation_message():
    monthly = pd.DataFrame(
        {
            "month": [7],
            "period_start": ["2024-07-01"],
            "period_end": ["2024-07-31"],
        }
    )

    assert months_covered(monthly) == [7]
    assert short_coverage_message(monthly) == (
        "Only July 2024 available, so no best-season recommendation can be made."
    )


def test_empty_site_has_specific_no_observations_message():
    assert short_coverage_message(pd.DataFrame()) == "No Earth observations loaded yet"


def test_missing_observations_and_percentages_remain_missing():
    monthly = pd.DataFrame(
        {
            "n_valid_obs": [pd.NA, 4],
            "n_missing_obs": [pd.NA, 27],
            "pct_in_envelope": [pd.NA, pd.NA],
        }
    )

    flagged = annotate_low_data(monthly)

    assert flagged.loc[0, "data_flag"] == "not assessed"
    assert flagged.loc[1, "data_flag"] == "low data"
    assert pd.isna(flagged.loc[0, "n_valid_obs"])
    assert flagged["pct_in_envelope"].isna().all()