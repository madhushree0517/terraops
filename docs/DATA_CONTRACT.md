# TERRAOPS Data Contract

The app resolves each contract file independently from `data/processed/` when present, otherwise from `data/sample/`. `TERRAOPS_DATA_MODE=processed` requires processed data; `TERRAOPS_DATA_MODE=sample` forces sample files; `auto` uses per-file fallback. CSV headers are exact and case-sensitive. Every file declares `schema_version` as `1.0`; unsupported or missing versions fail validation. Missing numeric observations remain missing (`NaN`); loaders do not replace them with zero.

Measurement values must use documented contract units: geographic coordinates are in degrees, elevations and spatial resolutions are in metres, and temperatures are in Celsius. Slope fields and degree-based thresholds require slope values confirmed to be in degrees. `New_Terrain _metrics.txt` gives no unit for its reprojected slope rasters, so the derived slope P90 and threshold shares are labeled unit unconfirmed until that metadata is supplied. Unit declarations in `roughness_unit` and `datasets_catalogue.units` accept degree, metre, and Celsius names or common abbreviations only. Convert source values before loading; do not relabel an unconverted value.

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

Required sites are Jezero, Askja, Atacama, and Ladakh. Askja, Atacama, and Ladakh coordinates are centroids of the supplied extent footprints; these are not verified field boundaries. Jezero retains an approximate reference coordinate pending confirmation.

## `site_extents.geojson` map artifact

The processed builder writes the supplied Askja, Atacama, and Ladakh extent geometries to `data/processed/site_extents.geojson`, reprojected to EPSG:4326. Each feature retains the site ID, display name, and source extent filename. These are supplied extent footprints, not verified field boundaries; the Earth Candidates page uses them only for map framing and outlines.

## Legacy `terrain_parameters.csv`

This legacy wide format is retained for compatibility with the standalone loader only. Current app pages do not load or display it; use `terrain_metrics.csv` for terrain presentation.

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

## `terrain_metrics.csv`

Long-form mobility metrics. A row represents one site and one metric; `metric_name` identifies the measure and `value` contains its numeric value, except categorical `material_class` values. Required metric names are `slope_p90_deg`, `pct_area_slope_gt10`, `pct_area_slope_gt17`, `pct_area_slope_gt24`, `roughness`, `rock_cover_cfa_pct`, `pct_area_step_gt20cm`, `pct_area_step_gt35cm`, and `material_class`. Additional legacy raster summaries may be retained as separate rows.

Blank values mean missing data and must never be replaced with zero. The tier legend is:

| Tier | Measurement capability |
| --- | --- |
| A | Measurable at rover scale, using about 2 m or finer terrain data. |
| B | Coarse proxy, using about 30 m terrain data; cannot resolve rover-scale features. |
| Blank | No confirmed open data. |

Tiers describe what can be measured, not how suitable a site is. This build marks available coarse raster-derived metrics Tier B; it assigns no Tier A where rover-scale data are absent. The referenced engineering framework deck was not found in the workspace, so the owner should confirm the tier application. `roughness_metric` and `roughness_window` remain blank unless their method and window are documented. Roughness may be shown as numeric rank order only, not assigned a threshold band.

All raster values describe the whole supplied raster extent unless `statistics_scope` documents another method. An extent polygon is not assumed to be a validated site boundary. `baseline_m` is the common analysis baseline; `native_resolution_m` records the source pixel size in metres, and `computed_at_baseline` states whether values were actually resampled/computed at the baseline. A native-resolution value must not be presented as baseline-normalized. `dem_source` is blank when unverified. Units may be missing when source documentation does not define them.

## Derived slope artifacts

`slope_histograms.csv` contains one row per site and 1-unit slope-value bin (`site_id`, `bin_start`, `bin_end`, `pixel_count`, `share`). The builder reads raster blocks and excludes nodata and non-finite pixels; shares are fractions of valid pixels per site and sum to 1. Slope units remain unconfirmed, so bins are numerical value intervals and are not asserted to be degrees.

Slope preview images are written under `data/processed/previews/` only for sites that pass the builder's existing CRS and extent checks. `slope_preview_metadata.csv` records the source file, source CRS, full raster extent, native pixel size/unit, preview dimensions, and preview bounds (`bounds_west`, `bounds_south`, `bounds_east`, `bounds_north`) in EPSG:4326. Preview pixels are downsampled and reprojected for map overlay; they are for visual context only, not a validated site boundary or analysis result.

| Column | Meaning |
| --- | --- |
| `schema_version` | Contract version; every row is `1.0`. |
| `site_id` | Canonical join key. |
| `metric_name` | Mobility measure name, including the supported names listed above. |
| `value` | Numeric metric value or categorical `material_class`; blank when unavailable. |
| `value_mean`, `value_std`, `value_min`, `value_max` | Optional raster summary statistics over the stated scope; missing values remain blank/NaN. |
| `n_valid_pixels` | Count of included non-nodata pixels. |
| `metric_unit` | Source-defined unit; blank if not established. |
| `tier` | `A`, `B`, or blank when unavailable at a tier. |
| `baseline_m` | Common comparison baseline in metres; currently 30 m. |
| `dem_source` | Documented source DEM name; blank if unknown. |
| `native_resolution_m` | Source raster pixel size in metres; blank if unavailable. |
| `computed_at_baseline` | Boolean indicating whether the value was computed at `baseline_m`; blank if not assessable. |
| `roughness_metric`, `roughness_window` | Roughness definition and window; blank until documented. |
| `availability_note` | Reason a requested value is pending, when known. |
| `source_file` | Relative path to the raw raster. |
| `crs` | Raster CRS. |
| `resolution_x`, `resolution_y` | Raster pixel dimensions in source CRS units. |
| `resolution_unit` | Coordinate unit derived from CRS metadata; not assumed to be metres. |
| `statistics_scope` | Method/scope, such as raster extent or a documented polygon zone. |

## `temperature_monthly.csv`

One record per site, month, variable type, and period of day. `month` is 1-12; `variable_type` is `surface_temp` or `air_temp`. Daytime and nighttime surface temperatures remain separate; they are not averaged together.

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
| `source_label` | Original site label from the source row, retained when a confirmed alias maps to a canonical `site_id` (for example `Iceland` to `askja`). |
| `period_of_day` | `daily` for daily air-temperature summaries, or `day` / `night` for separate surface-temperature summaries. Older contract rows without this field load as `daily`; no aggregation is inferred. |

## `mars_temperature_envelope.json`

JSON object with `schema_version` (`1.0`), `variable_type` (`surface_temp` or `air_temp`), `source` and `notes`. A single-envelope object uses numeric `min_c` and `max_c` in Celsius. If only season-specific thresholds are supported, `min_c` and `max_c` remain null and `seasonal_envelopes` contains objects with `season`, `min_c`, and `max_c` from the cited source. Do not collapse season-specific ranges into a single range without an approved interpretation.

The optional `solar_longitude_mapping` object records ATS `coverage_percent`, `mapped_ats_sols`, `total_ats_sols`, and the source handoff. This describes coverage of solar-longitude mapping only; it is not the share of temperature observations analysed.

## `earth_surface_temperature_matches.csv`

Optional builder output derived from `data/raw/package/Earth_temperature_daily_analysis.csv`, the processed Earth site crosswalk, and the processed Mars seasonal bands. Each row is one Earth site, day/night period, and Mars season. A daily value is valid only when its mean and valid-pixel count are present and the count is positive. The share is the percentage of valid daily surface means within the inclusive Mars band bounds. If a comparison has no valid days, its share, matching-day count, and valid-day count remain missing; missing is not zero.

| Column | Meaning |
| --- | --- |
| `site_id` | Canonical Earth site identifier. |
| `period_of_day` | `day` or `night`; periods are not combined. |
| `season` | Mars seasonal band label from the processed envelope. |
| `earth_variable`, `mars_variable` | Measurement descriptions carried into the comparison. |
| `share_in_band_pct` | Share of valid Earth daily means inside the selected Mars band's inclusive bounds. |
| `n_matching_days` | Number of valid daily means inside the band. |
| `n_valid_days` | Number of daily means with a positive valid-pixel count. |
| `source` | Relative path of the source daily file. |

## `analogy_gaps.json`

JSON list of objects. Every object must retain `schema_version` (`1.0`), `factor`, `can_rehearse_on_earth` (boolean or null), and `explanation`. Additional source fields, including `limits` if present, must be preserved rather than discarded. Explicit `true` and `false` decisions are reviewed decisions; `null` is pending review. A true decision applies only to the named aspect and does not assert that Earth reproduces Mars. The processed build uses the reviewed `data/sample/analogy_gaps.json` when present, preserving each entry's exact field values and wording.

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

Files in `data/sample/` are marked as sample by the app. The sample site locations mirror the documented approximate Jezero reference and supplied Earth extent centroids; sample terrain and temperature measurements remain illustrative placeholders. The app's processed files take precedence per file when present. Preserve these headers and document units, methods, periods, and provenance before comparing measurements.
