# TERRAOPS Data Quality and Limitations

## Earth-Mars comparison
MODIS measures land-surface temperature.
NASA POWER provides gridded near-surface air temperature.
MEDA ATS and TIRS have distinct instrument measurement
definitions and geometries.

These should not be treated as interchangeable measurements.

## Temporal coverage
The current Earth summary covers July 2024.
Mars MEDA data spans Sol 1 to Sol 1859.
Sampling frequency and temporal coverage differ.

## Missing data
Some Mars sols are absent from ATS and TIRS.
Missing sols are different from missing values within rows.

## Temperature extremes
Statistical outlier thresholds are diagnostic screens.
They do not establish that a measurement is invalid.

## Clock matching
SCLK-minute matching is provisional until SCLK units and
time correlation are verified from authoritative PDS sources.

## Engineering flags
Flag meanings must be obtained from official instrument
documentation, not inferred from zero/one patterns.
