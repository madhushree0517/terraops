from collections.abc import Iterable
import re
import warnings

import pandas as pd


SCHEMA_VERSION = "1.0"


class DataContractError(ValueError):
    """Raised when a data file does not satisfy the TERRAOPS contract."""


def require_columns(
    frame: pd.DataFrame, required: Iterable[str], filename: str
) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise DataContractError(
            f"{filename} is missing required column(s): {', '.join(missing)}."
        )


def require_json_keys(data: dict, required: Iterable[str], filename: str) -> None:
    missing = [key for key in required if key not in data]
    if missing:
        raise DataContractError(
            f"{filename} is missing required key(s): {', '.join(missing)}."
        )


def validate_schema_version(value, filename: str) -> None:
    if isinstance(value, pd.Series):
        invalid = value.isna().any() or set(value.dropna().astype(str)) != {SCHEMA_VERSION}
    else:
        invalid = str(value) != SCHEMA_VERSION
    if invalid:
        raise DataContractError(
            f"{filename} must declare schema_version {SCHEMA_VERSION!r}."
        )


_UNIT_ALIASES = {
    "m": "metres",
    "meter": "metres",
    "meters": "metres",
    "metre": "metres",
    "metres": "metres",
    "deg": "degrees",
    "degree": "degrees",
    "degrees": "degrees",
    "decimal degree": "degrees",
    "decimal degrees": "degrees",
    "c": "Celsius",
    "deg c": "Celsius",
    "degree c": "Celsius",
    "degrees c": "Celsius",
    "degree celsius": "Celsius",
    "degrees celsius": "Celsius",
    "deg celsius": "Celsius",
    "celsius": "Celsius",
}


def validate_unit_values(values: Iterable, filename: str, column: str) -> None:
    unsupported = set()
    for value in values:
        if pd.isna(value):
            continue
        tokens = [token.strip().lower().replace("°", "deg ") for token in re.split(r"[,;|/]", str(value))]
        unsupported.update(token for token in tokens if token not in _UNIT_ALIASES)
    if unsupported:
        labels = ", ".join(sorted(repr(value) for value in unsupported))
        raise DataContractError(
            f"{filename} column {column!r} contains unsupported unit(s): {labels}. "
            "Use degrees, metres, or Celsius."
        )


def validate_numeric_columns(frame: pd.DataFrame, columns: Iterable[str], filename: str) -> None:
    for column in columns:
        invalid = frame[column].notna() & pd.to_numeric(
            frame[column], errors="coerce"
        ).isna()
        if invalid.any():
            raise DataContractError(
                f"{filename} column {column!r} must contain numeric values or missing values."
            )


def validate_coordinates_degrees(frame: pd.DataFrame, filename: str) -> None:
    validate_numeric_columns(frame, ("lat", "lon"), filename)
    invalid_lat = frame["lat"].notna() & ~frame["lat"].between(-90, 90)
    invalid_lon = frame["lon"].notna() & ~frame["lon"].between(-180, 180)
    if invalid_lat.any() or invalid_lon.any():
        raise DataContractError(
            f"{filename} latitude/longitude must be expressed in decimal degrees "
            "within valid coordinate ranges."
        )


def check_temperature_variable_types(
    temperatures: pd.DataFrame, envelope: dict
) -> list[str]:
    envelope_type = envelope["variable_type"]
    site_types = temperatures.groupby("site_id", dropna=False)["variable_type"].agg(
        lambda values: set(values.dropna().astype(str))
    )
    mismatched = site_types.loc[
        site_types.map(lambda variable_types: envelope_type not in variable_types)
    ]
    if mismatched.empty:
        return []
    details = sorted(
        f"{site_id}: {', '.join(sorted(variable_types)) or 'no variable_type'}"
        for site_id, variable_types in mismatched.items()
    )
    message = (
        f"Temperature/envelope variable_type mismatch: Mars envelope is "
        f"{envelope_type!r}; sites without matching data: {', '.join(details)}. "
        "This check compares variable_type labels only; it is not a physical validation. "
        "Do not compare these variables."
    )
    warnings.warn(message, RuntimeWarning, stacklevel=2)
    return [message]


def temperature_compatibility_status(
    data_source: str, mismatches: list[str]
) -> tuple[str, str]:
    """Return the UI level and caveated message for label-only compatibility."""
    if mismatches:
        return "error", " ".join(mismatches)
    caveat = "This check compares variable_type labels only; it is not a physical validation."
    if data_source == "sample":
        return "warning", f"Temperature variable_type labels match the Mars envelope. {caveat}"
    return "success", f"Processed-data variable_type labels match the Mars envelope. {caveat}"


def validate_months(frame: pd.DataFrame, filename: str) -> None:
    invalid = frame["month"].notna() & ~frame["month"].between(1, 12)
    if invalid.any():
        raise DataContractError(f"{filename} contains month values outside 1-12.")


def validate_variable_types(frame: pd.DataFrame, filename: str) -> None:
    allowed = {"surface_temp", "air_temp"}
    present = set(frame["variable_type"].dropna().astype(str))
    invalid = sorted(present - allowed)
    if invalid:
        raise DataContractError(
            f"{filename} has unsupported variable_type value(s): {', '.join(invalid)}."
        )