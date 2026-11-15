# TERRAOPS Data Gap Report

## Inventory Evidence

The current inventory found 79 files in `data/raw/`; one JSON manifest was initially routed to the GeoJSON reader, and the inventory script has since been corrected to treat JSON manifests as JSON. No `.crdownload` files were found. There is no `.docx` or `Mobility_Parameter_Definition.pptx` in the workspace/raw package. Preferred handoffs now exist under `package/temperature/documentation/`, Earth/Mars/validation subfolders. Raw files have not been changed.

The site catalogue uses `jezero`, `askja`, `atacama`, and `ladakh`. The team confirmed that the Earth temperature source label `Iceland` is Askja; the processed temperature output maps it to `site_id=askja` and preserves `source_label=Iceland`. The Earth temperature CSVs do not state extraction coordinates, so this mapping is based on the team's identity confirmation and is not independently coordinate-validated. The `site_boundaries.gpkg` layer is empty (0 features); individual `Extent_*.gpkg` files provide rectangular footprints, not validated field boundaries. Jezero's extent is tagged EPSG:4326 but has coordinates x=0..1865 and y=-1495..0, so it is invalid as a geographic site geometry.

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
| `site_id` | Earth summary `site` | `Atacama`→`atacama`, `Iceland`→`askja` (team-confirmed), and `Ladakh`→`ladakh`. Original labels are preserved in `source_label`. |
| `month` | Preferred Earth summary `period_start` / `period_end` | Numeric month is explicitly derived as `7`; period is July 2024. Mars `SOL`/`mars_sol` is not an Earth calendar month. |
| `variable_type` | `POWER_T2M_*`; `MODIS_day_*`, `MODIS_night_*` | POWER maps to `air_temp`; MODIS day and night map to separate `surface_temp` records with `period_of_day=day` or `night`. TIRS AIR_TEMP and GROUND_TEMP are distinct; ATS has five distinct channels. |
| `temp_min_c`, `temp_mean_c`, `temp_max_c` | POWER and MODIS summary fields | Values are copied from their corresponding source fields in Celsius. Day/night MODIS values remain separate; no aggregate is computed. |
| `pct_in_envelope` | Final recalculated MODIS/TIRS surface comparison exists | Not copied into POWER air-temperature rows: they are `air_temp`, while the available envelope is `surface_temp`. No air-temperature envelope is supplied. |
| `n_valid_obs`, `n_missing_obs` | Daily values and their missingness | POWER counts and MODIS counts are retained per series. Askja/Iceland MODIS day and night each have 8 valid of 31 days (23 missing); both are low data. |
| `source` | Dataset/source registry and inventory | POWER source identified; MODIS source identified. |
| `period_start`, `period_end` | Summary/audit | `2024-07-01` to `2024-07-31`. |
| `source_label`, `period_of_day` | Original `site` and MODIS field names | Original site label is retained; `daily`, `day`, and `night` prevent conflating incompatible or separate series. |

**Result:** `temperature_monthly.csv` contains the separate POWER daily air-temperature and MODIS day/night surface-temperature series for the confirmed sites Atacama, Askja, and Ladakh. Missing values remain blank and `pct_in_envelope` remains NaN. Source labels and day/night periods are retained; MODIS day/night are never averaged together.

Only month `7` (July 2024) is present; no records support months `1–6` or `8–12`. The source temperature CSVs contain no latitude/longitude coordinates, so source-series locations cannot be compared to terrain centroids directly. The team-supplied Atacama MODIS analysis coordinate and other note coordinate are therefore listed separately below and neither is selected as canonical.

### Location consistency

Distances use the WGS84 geodesic from each supplied terrain extent centroid. Earth temperature source CSVs do not contain site coordinates. The two Atacama note coordinates below were provided in the team request; those coordinate statements were not found in the Earth temperature CSVs or searched package notes. No coordinate is selected or substituted.

| Site | Location reference | Latitude, longitude | Distance from terrain extent centroid | Finding |
| --- | --- | --- | ---: | --- |
| Atacama | Supplied terrain extent centroid | -22.499861, -68.500139 | Reference | Extent centroid, not a validated field boundary. |
| Atacama | MODIS analysis coordinate (team-supplied) | -24.60, -69.90 | 273.0 km | More than 20 km; keep distinct pending owner confirmation. |
| Atacama | Other note coordinate (team-supplied) | -22.91, -68.20 | 54.9 km | More than 20 km; keep distinct pending owner confirmation. |
| Askja | Supplied terrain extent centroid | 65.500139, -16.500278 | Reference | Earth temperature files do not state the extraction coordinate. |
| Ladakh | Supplied terrain extent centroid | 34.500139, 77.499861 | Reference | Earth temperature files do not state the extraction coordinate. |
| Jezero | Supplied extent | Not usable under its EPSG:4326 label | Not available | Invalid extent; the point in `sites.geojson` is an approximate reference only. |

The two Atacama note coordinates are 255.1 km apart. The MODIS coordinate is 273.0 km from the extent centroid and the other note coordinate is 54.9 km from it; both exceed the 20 km review threshold. The Earth CSVs do not establish which coordinate was used to extract the series, so no choice is made. For Askja, the Iceland-to-Askja identity was confirmed by the team; because the source temperature files have no coordinates, a coordinate-distance check cannot be reported.

### `mars_temperature_envelope.json`

Potential inputs: preferred `temperature/validation/handover/05_EARTH_MARS_FINAL_RECALCULATED_TABLE.csv`; supporting TIRS parquet schema and season documentation.

Preferred source: `temperature/validation/handover/05_EARTH_MARS_FINAL_RECALCULATED_TABLE.csv`. It explicitly labels all rows `SURFACE_TEMPERATURE`, uses `TIRS ground temperature`, and supplies one P05/P95 pair per northern season, repeated identically across Earth sites/day-night records. The builder validates one unique pair for each of the four seasons and preserves those four ranges. It leaves top-level `min_c`/`max_c` null rather than collapsing seasonal thresholds into a fabricated global interval. The older `53_FINAL_MARS_SEASONAL_TEMPERATURE_SUMMARY.csv` contains mean/standard deviation/mean-of-sol extrema, not these recalculated P05/P95 bounds.

**Result:** built as `surface_temp` seasonal envelopes for TIRS GROUND_TEMP. This is not an ATS air-temperature envelope. POWER T2M monthly rows are air temperature, so the app's variable compatibility guard should report the mismatch; it is not physical validation.

### `analogy_gaps.json`

Potential inputs: methodology, comparison-validity and limitations notes.

Source of reviewed decisions: `data/sample/analogy_gaps.json`. Its exact entry keys are `schema_version`, `factor`, `can_rehearse_on_earth`, and `explanation`; the limits are preserved in the explanation text. Explicit booleans are reviewed decisions; null remains pending. The builder copies every field and the exact decision/explanation text without rewriting. The raw limitations register remains a fallback only when the reviewed file is absent.

**Result:** processed output preserves the reviewed file's fields and wording. It does not add a reviewer name or infer a decision for null entries.

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
- **Hitaeshi — MEDA/Mars temperature:** The current official PDS Ls mapping covers 1,526 of 1,754 ATS sols (87.0%). This is Ls mapping coverage, not the share of temperature observations analysed. The earlier 1,179/1,754 (67.2%) figure is superseded; the 1,496 TIRS index count is a different instrument/index stage. Please provide matched-parquet definitions and confirm ATS channel/height, SCLK correlation, flag semantics and uncertainty handling.
- **Mankani — Earth temperature:** Iceland is confirmed as Askja. MODIS day and night remain separate; no aggregation is performed. Please provide the site extraction coordinates/CRS for each temperature series and confirm source-product resolution and the valid-observation denominator for any future `pct_in_envelope` values.
- **Dataset source/licensing owner:** Please provide formal citations/licences and source-product CRS/resolution/format metadata, including whether the local derived rasters can represent source-product metadata.