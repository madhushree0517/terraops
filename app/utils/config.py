import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"
CONTRACT_FILES = (
    "sites.geojson",
    "terrain_parameters.csv",
    "temperature_monthly.csv",
    "mars_temperature_envelope.json",
    "analogy_gaps.json",
    "datasets_catalogue.csv",
)


def get_data_source() -> str:
    """Return the active data source, honoring TERRAOPS_DATA_MODE."""
    mode = os.getenv("TERRAOPS_DATA_MODE", "auto").strip().lower()
    if mode not in {"auto", "processed", "sample"}:
        raise ValueError(
            "TERRAOPS_DATA_MODE must be one of: auto, processed, sample; "
            f"received {mode!r}."
        )
    if mode != "auto":
        return mode
    processed_dir = DATA_ROOT / "processed"
    if all((processed_dir / filename).is_file() for filename in CONTRACT_FILES):
        return "processed"
    return "sample"


def get_data_dir() -> Path:
    """Resolve the active data folder, preferring a complete processed contract."""
    return DATA_ROOT / get_data_source()