import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"
CONTRACT_FILES = (
    "sites.geojson",
    "terrain_metrics.csv",
    "temperature_monthly.csv",
    "mars_temperature_envelope.json",
    "analogy_gaps.json",
    "datasets_catalogue.csv",
)


def get_data_source() -> str:
    """Return processed only when every contract file is processed; otherwise sample."""
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


def get_data_file_source(filename: str) -> str:
    """Resolve one contract file independently, preferring processed data in auto mode."""
    mode = os.getenv("TERRAOPS_DATA_MODE", "auto").strip().lower()
    if mode not in {"auto", "processed", "sample"}:
        raise ValueError(
            "TERRAOPS_DATA_MODE must be one of: auto, processed, sample; "
            f"received {mode!r}."
        )
    if mode != "auto":
        return mode
    if (DATA_ROOT / "processed" / filename).is_file():
        return "processed"
    if (DATA_ROOT / "sample" / filename).is_file():
        return "sample"
    return "missing"


def get_data_file_path(filename: str) -> Path:
    source = get_data_file_source(filename)
    if source == "missing":
        raise FileNotFoundError(
            f"Required data file {filename!r} is missing from data/processed/ and data/sample/."
        )
    path = DATA_ROOT / source / filename
    if not path.is_file():
        raise FileNotFoundError(f"Required data file not found: {path}")
    return path


def get_contract_file_statuses() -> dict[str, str]:
    """Return each contract filename's active source for the Data Sources UI."""
    return {filename: get_data_file_source(filename) for filename in CONTRACT_FILES}


def get_data_dir() -> Path:
    """Resolve the active data folder, preferring a complete processed contract."""
    return DATA_ROOT / get_data_source()