# TERRAOPS: Earth and Mars Dataset Handoff

This folder contains processed Earth and Mars datasets for the
TERRAOPS Earth-Mars analog research project.

## Folder structure

- Earth: processed Earth temperature datasets.
- Mars: full MEDA ATS and TIRS master datasets.
- Validation: quality-control reports and figures.
- Documentation: methodology, sources, data dictionary and limitations.

## Earth datasets

The processed Earth analysis covers:
- Atacama
- Ladakh
- Iceland

The current temperature summary covers July 2024.

The Earth workflow includes MODIS land-surface temperature,
NASA POWER near-surface air-temperature data, daily analysis,
day/night coverage checks and MODIS quality-flag diagnostics.

MODIS land-surface temperature is not equivalent to air temperature.

## Mars datasets

The Mars folder contains:
- Mars_ATS_FULL_MASTER.parquet
- Mars_TIRS_FULL_MASTER.parquet

These datasets were derived from the NASA Mars 2020 MEDA
calibrated environmental archive.

ATS contains observations across 1,754 sols.
TIRS contains observations across 1,751 sols.
The processed mission range is Sol 1 through Sol 1859.

ATS and TIRS are separate instruments and their measurements
must be interpreted according to their respective definitions.

## Important limitations

- Some mission sols are missing from one or both instruments.
- Statistical outlier thresholds are diagnostic screens,
  not verified instrument validity limits.
- Engineering flag meanings require official PDS documentation.
- SCLK-minute matching remains provisional pending verification
  of the clock definition and time correlation.
- Earth surface temperature, gridded air temperature and
  Mars instrument readings are not directly interchangeable.

See the methodology and limitations documents for details.
