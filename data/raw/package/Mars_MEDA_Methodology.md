# Mars MEDA Data Methodology

## Source
NASA Mars 2020 MEDA calibrated environmental archive.

## Instruments
- ATS: Air Temperature Sensor dataset.
- TIRS: Thermal Infrared Sensor dataset.

## Processing
Source observations were downloaded, processed in batches,
converted to Parquet and consolidated into separate ATS
and TIRS master datasets.

## Coverage
ATS: 1,754 sols.
TIRS: 1,751 sols.
Mission range: Sol 1 to Sol 1859.

## Validation
The workflow examined sol-wise coverage, missing values,
temperature distributions, measurement uncertainty and
engineering flag patterns.

Statistical screening thresholds are not official
instrument operating limits.

SCLK-minute matching remains provisional until the clock
definition and time correlation are verified.
