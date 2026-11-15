# TERRAOPS

TERRAOPS organizes Mars rover-mobility evidence and Earth field-rehearsal comparisons for a Jezero Crater reference. It does not certify site suitability, calculate a composite score, or rank Earth sites.

## Run locally

Use Python 3.11. The app was checked with Python 3.11.8.

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app/Home.py
```

Streamlit's multipage navigation is available in the sidebar. In `auto` data mode, the app uses each matching item in `data/processed/` first and falls back to `data/sample/`. Sample content is illustrative and is identified with a placeholder banner. Set `TERRAOPS_DATA_MODE=processed` to require processed inputs, or `TERRAOPS_DATA_MODE=sample` to use the sample set.

## Deploy on Streamlit Community Cloud

Create a Community Cloud app with these settings:

- **Repository:** `madhushree0517/terraops`
- **Branch:** `main`
- **Main file path:** `app/Home.py`
- **Python version:** `3.11` (tested locally with Python 3.11.8)

The runtime dependencies are in `requirements.txt`. The deployed app uses the committed processed outputs and does not need `data/raw/large/`, raster `.tif` files, or Parquet inputs.
The When to Test page also reads the small method note at `data/raw/package/TERRAOPS_TEMPERATURE_ANALYSIS_FINAL_DOCUMENTATION.md` to report the stated local-time basis.

## What is real data and what is still pending

The committed processed outputs contain source-derived Earth terrain measurements for Atacama and Ladakh, separate Earth daytime and nighttime surface-temperature summaries, Earth air-temperature summaries, and Mars seasonal temperature bands. The Mars reference image is also included. These measurements are evidence for comparison, not proof that a location is suitable for a mission.

Askja terrain measurements remain out of the comparison while its coordinate reference needs review. Jezero terrain measurements have not been supplied. Earth temperature summaries currently cover July 2024 only, so they do not support a best-season recommendation. MODIS surface-temperature extraction over the agreed terrain footprints is pending. The optional Mars temperature detail tables, full-year Earth temperature coverage, and some source citations and metadata are also pending.

The reviewed analogy decisions are preserved as provided. Items marked pending remain undecided. Files under `data/sample/` are illustrative placeholders, not real measurements.

## Rebuild data from raw

The app does not need the large raw rasters, but rebuilding processed data does. Place the original package in `data/raw/`, including the required terrain sources under `data/raw/large/`, then install the pipeline dependencies and run the builder:

```powershell
python -m pip install -r requirements-pipeline.txt
python -m scripts.build_processed
```

The builder reads the raw package and writes derived outputs under `data/processed/`. It does not replace the source data.

For test development, install pytest separately and run:

```powershell
python -m pip install "pytest>=8,<9"
python -m pytest
```
