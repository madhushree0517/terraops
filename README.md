# TERRAOPS

TERRAOPS is a Streamlit app skeleton for helping a Mars exploration team compare Earth locations for rover-mobility field rehearsal under Jezero Crater-like conditions. The initial project is wired to a fixed data contract and clearly marked sample fixtures; scientific scoring and analysis features are intentionally not implemented yet.

## Requirements

- Python 3.11
- Dependencies in `requirements.txt`

## Run

From the project root, create and activate a Python 3.11 environment, install dependencies, then run:

```powershell
python -m pip install -r requirements.txt
streamlit run app/Home.py
```

Streamlit's multipage navigation is available in the sidebar. The app defaults to `TERRAOPS_DATA_MODE=auto`: it reads `data/processed/` only when all contract files are present there, otherwise it reads `data/sample/` and displays a visible `PLACEHOLDER DATA` banner. Set `TERRAOPS_DATA_MODE=processed` to require processed data, or `TERRAOPS_DATA_MODE=sample` to force the sample fixtures.

Processed data files must use the exact names and columns documented in [docs/DATA_CONTRACT.md](docs/DATA_CONTRACT.md). Place original source files in `data/raw/`; the app never reads or modifies that directory.

## Tests

```powershell
python -m pytest
```

All data in `data/sample/` is illustrative placeholder content, not scientific evidence or an endorsed site assessment. Never use it to make operational decisions.
