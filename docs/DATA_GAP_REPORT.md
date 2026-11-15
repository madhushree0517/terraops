# TERRAOPS Data Gap Report

## Inventory Evidence

The current inventory found 79 files in `data/raw/`; one JSON manifest was initially routed to the GeoJSON reader, and the inventory script has since been corrected to treat JSON manifests as JSON. No `.crdownload` files were found. There is no `.docx` or `Mobility_Parameter_Definition.pptx` in the workspace/raw package. Preferred handoffs now exist under `package/temperature/documentation/`, Earth/Mars/validation subfolders. Raw files have not been changed.

The site catalogue uses `jezero`, `askja`, `atacama`, and `ladakh`. An unmatched Earth temperature source label is excluded rather than mapped to a terrain site. The `site_boundaries.gpkg` layer is empty (0 features); individual `Extent_*.gpkg` files provide rectangular footprints, not validated field boundaries. Jezero's extent is tagged EPSG:4326 but has coordinates x=0..1865 and y=-1495..0, so it is invalid as a geographic site geometry.

## Contract Mapping

### `sites.geojson`

Potential inputs: `large/terrain/site_boundaries.gpkg`, `site_boundaries.gpkg.geojson`, and individual `Extent_*.gpkg` files.

| Contract field | Candidate source | Gap / qualification |
| --- | --- | --- |
| `schema_version` | Build constant `1.0` | Can be set by the converter. |
| `site_id` | Extent filenames | `jezero`, `askja`, `atacama`, and `ladakh`. |
| `name` | Extent filenames and requested canonical labels | `Jezero Crater`, `Askja, Iceland`, `Atacama Desert, Chile`, and `Ladakh, India`. |
| `body` | No raw column | Mars/Earth classification is not recorded on the geometry attributes. |
| `lat`, `lon`, geometry | Supplied Earth `Extent_*.gpkg` polygon centroids; existing Jezero reference | Earth points are the centroids of the supplied footprints. Jezero uses the approximate reference point `(77.6, 18.4)` because its extent coordinates are incompatible with EPSG:4326. |
| `notes` | Source footprint and coordinate provenance | Earth: `centroid of supplied extent footprint`; Jezero: `approximate reference coordinate, to be confirmed`. |

**Result:** built as processed `sites.geojson`. Earth points are explicitly labeled extent-footprint centroids, not validated site locations; Jezero remains explicitly approximate and pending confirmation.

### `terrain_parameters.csv` (legacy wide contract)

Potential inputs: `Terrain_metrics.txt`; Askja, Atacama and Ladakh slope/roughness TIFFs; `Extent_*.gpkg`; source/dictionary CSVs.

| Contract field | Candidate source | Gap / qualification |
| --- | --- | --- |
| `schema_version` | Build constant `1.0` | Can be set by the converter. |
| `site_id` | Raster filenames and extent filenames | Earth rows suggest `askja`, `atacama`, `ladakh`; no Jezero terrain files. |
| `elevation_mean_m`, `elevation_std_m` | Preferred `*_Reprojected.tif` base rasters; older QGIS stats in `Terrain_metrics.txt` | Current builder computes raster-extent statistics by block windows for accepted CRS; vertical units/datum remain undocumented. |
| `slope_mean_deg` | Preferred `*_Reprojected_slope.tif`; exact QGIS values from `New_Terrain _metrics.txt` | Reprojected CRSs are UTM (Askja EPSG:32727, Atacama EPSG:32719, Ladakh EPSG:32643); value-unit/method definition remains undocumented. Askja CRS area of use excludes its northern site position. |
| `slope_p95_deg` | Could be computed from slope TIFFs | No p95 supplied; no approved site boundary polygon, so a valid site zone is unavailable. |
| `roughness_metric` | Preferred `*_Reprojected_roughness.tif`; older QGIS stats in `Terrain_metrics.txt` | Builder computes block-window whole-raster valid-pixel statistics for Atacama/Ladakh; Askja is skipped by CRS area-of-use check. Metric algorithm and window size are not defined. |
| `roughness_unit` | No explicit unit/definition | Unresolved; do not label it as metres or an index without confirmation. |
| `dem_source` | `Terrain_metrics.txt` input paths | Names Copernicus GLO30 for Askja, Atacama, Ladakh. The actual DEM TIFFs are not included. |
| `resolution_m` | Preferred reprojected base raster geotransform | Atacama pixel size is 29.680407648073597 × 29.680407671745545 m; Ladakh is 28.294190637152262 × 28.294190652337008 m. Askja declares about 30 m pixels but its CRS is suspect and is excluded. No Jezero raster resolution is present. |

**Result:** legacy only and not loaded by app pages. The mapping lacks Jezero terrain, slope p95 semantics, documented slope/roughness value units and roughness definition/window.

**Resolution comparison:** Atacama and Ladakh projected pixel sizes are known from preferred derivative rasters. Askja's approximate pixel size is recorded but not accepted because EPSG:32727's declared area of use excludes the site. No Jezero terrain raster/resolution exists; a Jezero-versus-Earth resolution comparison cannot be computed. Legacy non-reprojected derivatives use angular-degree pixel sizes and are superseded by the requested preferred reprojected files.

### `terrain_metrics.csv` (new long-form terrain contract)

Raw sources: `*_Reprojected.tif`, `*_Reprojected_slope.tif`, `*_Reprojected_roughness.tif`, `site_boundaries.gpkg.geojson`, and `New_Terrain _metrics.txt`.

The builder creates the nine mobility rows for Jezero, Atacama, Ladakh and Askja. For Atacama and Ladakh, it derives `slope_p90_deg` and the share of valid raster values above 10, 17 and 24 from the preferred reprojected slope rasters. `New_Terrain _metrics.txt` does not state a unit for any of the three slope rasters. Ladakh P90 42.85955810546875 is between the note's mean 26.551391952664954 and max 89.53579711914063; Atacama P90 17.119352340698242 is between mean 6.412182581141583 and max 89.41896057128906. These comparisons are numerically consistent with each raster's reported statistics but do not confirm degrees. The slope >24 shares remain 4.60555412101043% for Atacama and 62.72936087957937% for Ladakh; all values are whole-raster-extent statistics. The page labels slope units unconfirmed, and the degree-based thresholds remain provisional. The existing roughness raster mean is retained for rank order only; its metric definition/window remain blank. Rock-cover CFA, step-height shares and material class remain missing because no supporting data were found.

Askja retains source-resolution metadata, but its mobility values remain pending because EPSG:32727's declared area of use excludes Askja at approximately 65°N. Jezero has no terrain raster and its extent coordinates are invalid under the EPSG:4326 label. `baseline_m` is 30 m; available values were computed at native resolution, not resampled to that baseline. Derived coarse raster records are Tier B under the supplied legend; no rover-scale Tier A inputs were found. The referenced engineering framework deck remains absent from the workspace. The wide legacy terrain file is not loaded by app pages.

### `temperature_monthly.csv`

Preferred source: `package/temperature/earth/14_earth_site_temperature_summary.csv`. The final recalculated surface comparison is kept as a separate source for the Mars seasonal envelope, not collapsed into monthly rows.

| Contract field | Candidate source | Gap / qualification |
| --- | --- | --- |
| `schema_version` | Build constant `1.0` | Set by the converter. |
| `site_id` | Daily CSV `site` | `Atacama`→`atacama` and `Ladakh`→`ladakh` are direct. The unmatched source label is excluded because no canonical site mapping is documented. |
| `month` | Preferred Earth summary `period_start` / `period_end` | Numeric month is explicitly derived as `7`; period is July 2024. Mars `SOL`/`mars_sol` is not an Earth calendar month. |
| `variable_type` | `T2M_C`; MODIS `day_mean_C`, `night_mean_C`; TIRS/ATS fields | `T2M_C` maps to `air_temp`; MODIS day/night maps to surface conditions but aggregation into the one monthly `surface_temp` row is not defined. TIRS AIR_TEMP and GROUND_TEMP are distinct; ATS has five distinct channels. |
| `temp_min_c`, `temp_mean_c`, `temp_max_c` | `POWER_T2M_min_C`, `POWER_T2M_mean_C`, `POWER_T2M_max_C` | Explicit 2 m near-surface air temperature in Celsius; day/night MODIS values remain separate and are not collapsed. |
| `pct_in_envelope` | Final recalculated MODIS/TIRS surface comparison exists | Not copied into POWER air-temperature rows: they are `air_temp`, while the available envelope is `surface_temp`. No air-temperature envelope is supplied. |
| `n_valid_obs`, `n_missing_obs` | Daily values and their missingness | Derivable per variable/month; POWER has 31 valid days for each raw label. MODIS valid days are Atacama day/night 24/28, Iceland 8/8, Ladakh 25/23; corresponding missing days out of 31 are 7/3, 23/23, and 6/8. |
| `source` | Dataset/source registry and inventory | POWER source identified; MODIS source identified. |
| `period_start`, `period_end` | Summary/audit | `2024-07-01` to `2024-07-31`. |

**Result:** `temperature_monthly.csv` is built only for `air_temp`, Atacama and Ladakh from the preferred temperature-folder summary. It preserves missing values and leaves `pct_in_envelope` NaN. The unmatched source label is logged as dropped. MODIS day/night and Mars rows are not aggregated into calendar-month rows.

Only month `7` (July 2024) is present; no records support months `1–6` or `8–12`. The builder emits `n_valid_obs=31`, `n_missing_obs=0` for Atacama and Ladakh POWER T2M. It drops 31 unmatched source-label rows pending identity confirmation. MODIS valid-day counts remain in the source audit but are not emitted as contract temperature observation counts because the contract's single monthly surface-temperature aggregation rule is unspecified.

### `mars_temperature_envelope.json`

Potential inputs: preferred `temperature/validation/handover/05_EARTH_MARS_FINAL_RECALCULATED_TABLE.csv`; supporting TIRS parquet schema and season documentation.

Preferred source: `temperature/validation/handover/05_EARTH_MARS_FINAL_RECALCULATED_TABLE.csv`. It explicitly labels all rows `SURFACE_TEMPERATURE`, uses `TIRS ground temperature`, and supplies one P05/P95 pair per northern season, repeated identically across Earth sites/day-night records. The builder validates one unique pair for each of the four seasons and preserves those four ranges. It leaves top-level `min_c`/`max_c` null rather than collapsing seasonal thresholds into a fabricated global interval. The older `53_FINAL_MARS_SEASONAL_TEMPERATURE_SUMMARY.csv` contains mean/standard deviation/mean-of-sol extrema, not these recalculated P05/P95 bounds.

**Result:** built as `surface_temp` seasonal envelopes for TIRS GROUND_TEMP. This is not an ATS air-temperature envelope. POWER T2M monthly rows are air temperature, so the app's variable compatibility guard should report the mismatch; it is not physical validation.

### `analogy_gaps.json`

Potential inputs: methodology, comparison-validity and limitations notes.

Source: `temperature/validation/FINAL_REVISED_SCIENTIFIC_LIMITATIONS_REGISTER.csv`. Each register row becomes a draft factor/explanation; the boolean remains null because the register does not make rehearsal decisions.

**Result:** built with `review_status: "draft, pending engineering review"`; the loader accepts null decisions only under this draft state.

### `datasets_catalogue.csv`

Potential inputs: `TERRAOPS_Data_Sources.csv`, `MASTER_TEMPERATURE_DATASET_INVENTORY.csv`, local file formats and methodology notes.

| Contract field | Candidate source | Gap / qualification |
| --- | --- | --- |
| `schema_version` | Build constant `1.0` | Set by converter. |
| `dataset_name`, `source`, `url` | Source registry | Direct mapping; combined Mars ATS/TIRS source is split only because the inventory lists ATS and TIRS separately. |
| `file_format` | Local derived Earth CSV and Mars parquet artifacts | Describes the available local artifact, not necessarily the original provider download format; Copernicus source DEM file is absent. |
| `spatial_resolution`, `crs` | No catalogue metadata | Left NaN; derivative TIFF CRS does not establish original-source metadata. |
| `temporal_resolution`, `observation_period`, `units`, `limitations` | Dataset inventory and method notes | Explicit temperature units are normalized to `Celsius`; TIRS uncertainty remains `K` and irradiance units remain unverified in `limitations`, since the contract's `units` field accepts only supported canonical units. Other unresolved fields remain NaN. |
| `citation`, `licence` | No source fields | Left NaN. |

**Result:** partial catalogue built from the explicit source registry; unknown fields remain NaN.

## Active Processed Outputs

The builder creates processed `sites.geojson`, `terrain_metrics.csv`, `temperature_monthly.csv`, `mars_temperature_envelope.json`, `analogy_gaps.json`, and the partially populated `datasets_catalogue.csv` where mapped. App pages use the long-form terrain file; the legacy wide terrain file is not included in active app status or page rendering.

## Questions for owners

- **Arya — terrain/GIS files:** Are the supplied `Extent_*.gpkg` rectangles approved site analysis areas or raster crops only? EPSG:32727's declared area excludes Askja near 65°N; is that CRS assignment intentional? What are the slope value units/algorithm, roughness definition/window/unit, vertical datum and DEM source resolution? Can you provide Jezero geographic geometry and Jezero slope/roughness rasters? Why is Jezero's extent tagged EPSG:4326 while its coordinates are 0..1865 and -1495..0?
- **Hitaeshi — MEDA/Mars temperature:** Confirm the recalculated seasonal P05/P95 table is the approved `surface_temp` envelope for TIRS GROUND_TEMP. Is an ATS/TIRS AIR_TEMP seasonal envelope available for comparison with POWER T2M? Which Ls coverage is authoritative (66 update: 1,526/1,754; handoff includes 1,179/1,754 and TIRS index 1,496)? Please provide matched-parquet definitions and confirm ATS channel/height, SCLK correlation, flag semantics and uncertainty handling.
- **Mankani — Earth temperature:** Is Iceland the same field site as Askja, or are they distinct? What rule should aggregate MODIS day and night to monthly surface temperature, if any? Confirm the valid-observation denominator for `pct_in_envelope`, Earth site coordinates/CRS and source-product resolution. Is July-only monthly output intended for the app?
- **Dataset source/licensing owner:** Please provide formal citations/licences and source-product CRS/resolution/format metadata, including whether the local derived rasters can represent source-product metadata.