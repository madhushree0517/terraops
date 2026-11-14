# TERRAOPS Data Contract

The app reads the six files below from `data/processed/` when the complete contract is present. In automatic mode, an incomplete or absent processed contract selects `data/sample/`. `TERRAOPS_DATA_MODE=processed` requires processed data; `TERRAOPS_DATA_MODE=sample` always uses fixtures. CSV headers are exact and case-sensitive. Every file declares `schema_version` as `1.0`; unsupported or missing versions fail validation. Missing numeric observations remain missing (`NaN`); loaders do not replace them with zero.

Measurement values must use the contract's units: geographic coordinates and slope are in degrees, elevations and spatial resolutions are in metres, and temperatures are in Celsius. Unit declarations in `roughness_unit` and `datasets_catalogue.units` accept degree, metre, and Celsius names or common abbreviations only. Convert source values before loading; do not relabel an unconverted value.

## `sites.geojson`

GeoJSON `FeatureCollection`, one point feature per site. Required feature properties:

| Property | Meaning |
| --- | --- |
| `schema_version` | Contract version; currently `1.0`. |
| `site_id` | Stable identifier used to join all files. |
| `name` | Human-readable location name. |
| `body` | `Mars` or `Earth`; Jezero is the Mars reference. |
| `lat` | Latitude in decimal degrees. |
| `lon` | Longitude in decimal degrees, east-positive in the range -180 to 180; GeoJSON point coordinates are ordered `[lon, lat]`. |
| `notes` | Context, caveats, or provenance notes. |

Required sites are Jezero, Atacama, Ladakh, and Iceland; one additional Earth site is optional.

## `terrain_parameters.csv`

| Column | Meaning |
| --- | --- |
| `schema_version` | Contract version; every row is `1.0`. |
| `site_id` | Join key to `sites.geojson`. |
| `elevation_mean_m` | Mean elevation in metres. |
| `elevation_std_m` | Elevation standard deviation in metres. |
| `slope_mean_deg` | Mean slope in degrees. |
| `slope_p95_deg` | 95th-percentile slope in degrees. |
| `roughness_metric` | Roughness value using the declared metric. |
| `roughness_unit` | Unit or definition for the roughness metric. |
| `dem_source` | Digital elevation model source or identifier. |
| `resolution_m` | Spatial resolution in metres. |

## `temperature_monthly.csv`

One record per site, month, and variable type. `month` is 1-12; `variable_type` is `surface_temp` or `air_temp`.

| Column | Meaning |
| --- | --- |
| `schema_version` | Contract version; every row is `1.0`. |
| `site_id` | Join key to `sites.geojson`. |
| `month` | Calendar month number, 1-12. |
| `variable_type` | `surface_temp` or `air_temp`. |
| `temp_min_c` | Minimum temperature in degrees Celsius. |
| `temp_mean_c` | Mean temperature in degrees Celsius. |
| `temp_max_c` | Maximum temperature in degrees Celsius. |
| `pct_in_envelope` | Percent of valid observations in the stated envelope. |
| `n_valid_obs` | Number of valid observations. |
| `n_missing_obs` | Number of missing observations. |
| `source` | Dataset or processing source. |
| `period_start` | Start of the observation period (ISO date or documented label). |
| `period_end` | End of the observation period (ISO date or documented label). |

## `mars_temperature_envelope.json`

JSON object with `schema_version` (`1.0`), `variable_type` (envelope variable), `min_c` and `max_c` (bounds in degrees Celsius), `source` (source identifier), and `notes` (method and caveats).

## `analogy_gaps.json`

JSON list of objects, each with `schema_version` (`1.0`), `factor` (limitation or condition), `can_rehearse_on_earth` (boolean), and `explanation` (scope and caveats). This file records limitations; it does not assert that Earth reproduces Mars.

## `datasets_catalogue.csv`

| Column | Meaning |
| --- | --- |
| `schema_version` | Contract version; every row is `1.0`. |
| `dataset_name` | Dataset title or identifier. |
| `source` | Provider or custodian. |
| `url` | Dataset landing page or access URL. |
| `file_format` | Source or delivered file format. |
| `spatial_resolution` | Spatial resolution and units. |
| `temporal_resolution` | Temporal sampling or aggregation interval. |
| `observation_period` | Time span covered. |
| `units` | Measurement units. |
| `crs` | Coordinate reference system. |
| `limitations` | Known caveats and constraints. |
| `citation` | Recommended citation. |
| `licence` | Licence or usage terms. |

All content in `data/sample/` is placeholder-only, including numeric values. Replace it with reviewed data in `data/processed/`; preserve these headers and document units, methods, periods, and provenance before comparing measurements.