import pandas as pd


MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def variable_type_mismatch(
    site_name: str, earth_variable_type: str | None, mars_variable_type: str | None
) -> str | None:
    if not earth_variable_type or not mars_variable_type:
        return (
            f"Cannot compare {site_name}: Earth variable type "
            f"{earth_variable_type or 'unavailable'} and Mars band variable type "
            f"{mars_variable_type or 'unavailable'} are not both confirmed."
        )
    if earth_variable_type != mars_variable_type:
        return (
            f"Cannot compare {site_name}: Earth variable type '{earth_variable_type}' "
            f"does not match Mars band variable type '{mars_variable_type}'. "
            "No match percentage is shown."
        )
    return None


def months_covered(frame: pd.DataFrame) -> list[int]:
    if frame.empty or "month" not in frame:
        return []
    values = pd.to_numeric(frame["month"], errors="coerce").dropna().astype(int)
    return sorted(set(values) & set(range(1, 13)))


def months_covered_label(frame: pd.DataFrame) -> str:
    months = months_covered(frame)
    if not months:
        return "0 months"
    labels = []
    for month in months:
        month_rows = frame.loc[pd.to_numeric(frame["month"], errors="coerce") == month]
        years = pd.to_datetime(month_rows.get("period_start"), errors="coerce").dt.year.dropna().unique()
        if len(years) == 1:
            labels.append(f"{MONTH_NAMES[month - 1]} {int(years[0])}")
        else:
            labels.append(MONTH_NAMES[month - 1])
    return ", ".join(labels)


def short_coverage_message(frame: pd.DataFrame) -> str | None:
    if frame.empty:
        return "No Earth observations loaded yet"
    if len(months_covered(frame)) == 12:
        return None
    return (
        f"Only {months_covered_label(frame)} available, so no best-season recommendation "
        "can be made."
    )


def annotate_low_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Flag rows with fewer than half of expected observations; preserve NaNs."""
    result = frame.copy()
    valid = pd.to_numeric(result["n_valid_obs"], errors="coerce")
    missing = pd.to_numeric(result["n_missing_obs"], errors="coerce")
    expected = valid + missing
    flags = []
    for valid_count, expected_count in zip(valid, expected):
        if pd.isna(valid_count) or pd.isna(expected_count) or expected_count <= 0:
            flags.append("not assessed")
        elif valid_count < expected_count / 2:
            flags.append("low data")
        else:
            flags.append("")
    result["data_flag"] = flags
    return result