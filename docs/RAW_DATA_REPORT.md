# Raw Data Report

Generated from `data/raw/` by `python -m scripts.inventory_raw_data`. No raw source file is modified.

Inventory file count: **79**. Incomplete `.crdownload` files: **0**. Inventory read errors: **0**.

## Documentation Findings

The package includes `README_TERRAOPS.md`, `Earth_Data_Methodology.md`, `Mars_MEDA_Methodology.md`, `Data_Quality_and_Limitations.md`, `TERRAOPS_TEMPERATURE_ANALYSIS_FINAL_DOCUMENTATION.md`, and `ASHWARYA_TEMPERATURE_ANALYSIS_UPDATE.txt`. The requested final files are in `package/temperature/documentation/` and `package/temperature/validation/`; there are no `.docx` files.

### Final handoff and status notes

`66_FINAL_WORKSTREAM_UPDATE.txt` states ATS 88,656,007 observations/1,754 sols; TIRS 80,882,439 observations/1,751 sols; and current official Ls mapping for 1,526 of 1,754 ATS sols (87.0%), with 228 unresolved. This is coverage of Ls mapping, not the share of temperature observations analysed. `TERRAOPS_FINAL_RESEARCH_HANDOFF.txt` contains an earlier, superseded figure of 1,179/1,754 (67.2%); later embedded verification and final consolidated sections report the current 1,526 ATS Ls records. The separate 1,496 TIRS index count is a different instrument/index stage and is not the ATS coverage denominator.

Both copies of `FINAL_HANDOVER_SUMMARY.txt` have the same SHA-256 `CC61ECD68763F05DC6BCAC337AA85B2E985AA119635ADE8F937B9721B4ED67CB`; they are identical. That handover reports 113 SPICE kernels loaded, 52 text-declared frame IDs recognized, 84 CK files and 15 CK object IDs, but explicitly says MEDA/TIRS-specific frames/time coverage were not established. `FINAL_THREE_STREAM_CLOSURE_REPORT.md` instead marks all three closure streams `Scientific pass: NO`, flags MEDA polarity for context review, Earth–Mars comparison as exploratory scope-limited, and SPICE geometry `ERROR_OR_DOWNLOAD_BLOCKED` with `SpiceTYPEMISMATCH()`.

The revised limitations register says the 293 K threshold is a chosen screening threshold, not an instrument operating limit; the matched Parquet artifacts were not located in its Drive search even though matched Parquet files are present in this local raw tree. These are different statements and both are retained.

`FINAL_TEMPERATURE_ANALYSIS_INTERPRETATION.txt` says the main ATS/TIRS and Earth descriptive processing is complete, but seasonal Ls coverage is partial, flag interpretation requires PDS definitions, dynamic geometry remains unverified, and no habitat-suitability ranking is claimed. It specifically distinguishes MODIS surface skin temperature from POWER near-surface air temperature and MEDA channel roles.

`FINAL_THREE_STREAM_CLOSURE_REPORT.md` retains 24 recalculated rows, all classified `SURFACE_TEMPERATURE`, and states the comparison is exploratory, not a simultaneous matched-site experiment or causal climatic-equivalence claim. The recalculated file uses MODIS LST versus TIRS ground temperature. This differs in scope from the older air-to-air POWER T2M/TIRS AIR_TEMP pairing; both measurement classes must remain separate.

### Terrain

`New_Terrain _metrics.txt` records whole-raster QGIS slope statistics for the preferred Askja/Atacama/Ladakh reprojected slope files. The older `Terrain_metrics.txt` records superseded slope/roughness and Copernicus GLO30 DEM statistics. The newer package has preferred reprojected slope and roughness TIFFs for Askja, Atacama and Ladakh; no Jezero slope or roughness TIFF exists. Statistics describe whole raster extents, not a separately validated field boundary. The aggregate `site_boundaries.gpkg` has zero features. The individual `Extent_*.gpkg` files are rectangular raster extents. The Jezero extent has coordinates 0..1865 and -1495..0 despite an EPSG:4326 label, so it is not usable as a geographic boundary. No Jezero slope/roughness TIFF or DEM statistics are supplied.

New_Terrain _metrics slope values are quoted exactly from its raw QGIS output:

| Site | Metric | Count | Min | Max | Mean | Std dev |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Askja | Reprojected slope | 6880248 | 0.0 | 87.40215301513672 | 3.676787553963025 | 7.0877596636742535 |
| Atacama | Reprojected slope | 12996764 | 0.0 | 89.41896057128906 | 6.412182581141583 | 7.9977308509604566 |
| Ladakh | Reprojected slope | 13360659 | 0.0 | 89.53579711914063 | 26.551391952664954 | 14.788001085014608 |

| Site | DEM source evidence | Projected base-raster pixel size | CRS status |
| --- | --- | ---: | --- |
| Askja | Copernicus GLO30 named in older Terrain_metrics input; reprojected base TIFF present | 29.99818936288092 × 29.998189339968448 map units | EPSG:32727 area of use excludes Askja at about 65°N; suspect and skipped by builder |
| Atacama | Copernicus GLO30 named in older Terrain_metrics input; reprojected base TIFF present | 29.680407648073597 × 29.680407671745545 m | EPSG:32719; CRS area of use contains site |
| Ladakh | Copernicus GLO30 named in older Terrain_metrics input; reprojected base TIFF present | 28.294190637152262 × 28.294190652337008 m | EPSG:32643; CRS area of use contains site |
| Iceland | No separate Iceland terrain/DEM raster; the Earth temperature source label is confirmed as Askja | Not available | Not available |
| Jezero | No DEM/slope/roughness raster; Jezero extent is invalid under EPSG:4326 | Not available | Not valid geographic extent |

The preferred reprojected TIFF rows below are inventory samples from a top-left 1024×1024 window (or overview where present), not whole-raster or extent statistics:

The raw notes do not define the roughness algorithm/window size or explicit units for the slope/roughness rasters. TIFF metadata gives CRS, pixel size and nodata below. The DEM inputs named in Terrain_metrics are not themselves included as TIFFs, so an exact per-site DEM pixel size cannot be read from this package.

### Temperature Definitions and Periods

The final documentation and scientific comparison matrix identify NASA POWER T2M (2-m near-surface air temperature) versus MEDA TIRS AIR_TEMP as the air-to-air pairing. MODIS daytime/nighttime LST is surface temperature and pairs only with MEDA TIRS GROUND_TEMP, with caveats. ATS is a distinct air-temperature instrument with five separate channels; the documentation says to keep channels separate unless measurement geometry supports aggregation.

Earth data cover **2024-07-01 through 2024-07-31** (31 daily rows per site). TIRS coverage is documented as 1,751 sols over Sol 1–1859; ATS as 1,754 sols over Sol 1–1859. Official Ls mapping is documented for 1,496 of 1,751 TIRS sols. Four northern Mars seasons and 48 half-hour LTST bins per season are documented; the minimum contributing-sol rule is 10 per bin. The newer recalculated surface comparison explicitly supplies seasonal TIRS GROUND_TEMP P05–P95 bounds:

| Northern season | TIRS GROUND_TEMP P05 (°C) | TIRS GROUND_TEMP P95 (°C) |
| --- | ---: | ---: |
| Spring | -54.20122205756504 | -40.00628837476505 |
| Summer | -50.0903358755237 | -36.58036623135518 |
| Autumn | -66.0541884160499 | -39.297407287068815 |
| Winter | -64.59924723051415 | -44.98437532637752 |

These are season-specific surface-temperature bounds, not air-temperature thresholds. No single global envelope was stated; the report does not collapse these seasonal values into one range.

| Earth site label | MODIS day valid / 31 | Day coverage | MODIS night valid / 31 | Night coverage | POWER valid / 31 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Atacama | 24 | 77.42% | 28 | 90.32% | 31 |
| Iceland | 8 | 25.81% | 8 | 25.81% | 31 |
| Ladakh | 25 | 80.65% | 23 | 74.19% | 31 |

MODIS valid-pixel coverage varies by site/day. Earth daily local-time matching is not established. MEDA flag fractions are descriptive only; official flag semantics, SCLK units/time correlation, solar/rover geometry and irradiance definitions remain unverified. Statistical outlier thresholds are diagnostic, not instrument limits. Sol 367 is retained and no temperature interpolation is performed across its gap. The current Earth data do not support a validated annual testing calendar.

## File-by-File Inventory

### Preferred reprojected TIFF inventory samples

| File | CRS | Pixel size | Sample method | Valid sample pixels | Min | Max | Mean | Std dev |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `large/terrain/Askja_Reprojected.tif` | EPSG:32727 | `[29.99818936288092, 29.998189339968448]` | top_left_window_max_1024x1024 | 1048576 | 0.0 | 879.9260864257812 | 321.845703125 | 159.4658966064453 |
| `large/terrain/Askja_Reprojected_roughness.tif` | EPSG:32727 | `[29.99818936288092, 29.998189339968448]` | top_left_window_max_1024x1024 | 1046529 | 0.0 | 405.094482421875 | 5.80748176574707 | 17.42037010192871 |
| `large/terrain/Askja_Reprojected_slope.tif` | EPSG:32727 | `[29.99818936288092, 29.998189339968448]` | top_left_window_max_1024x1024 | 1046529 | 0.0 | 82.37259674072266 | 3.738919258117676 | 6.604355812072754 |
| `large/terrain/Atacama_Reprojected.tif` | EPSG:32719 | `[29.680407648073597, 29.680407671745545]` | top_left_window_max_1024x1024 | 1048576 | 0.0 | 4582.439453125 | 3178.93310546875 | 377.6178894042969 |
| `large/terrain/Atacama_Reprojected_roughness.tif` | EPSG:32719 | `[29.680407648073597, 29.680407671745545]` | top_left_window_max_1024x1024 | 1046529 | 0.0 | 3823.69189453125 | 12.355607986450195 | 61.13019943237305 |
| `large/terrain/Atacama_Reprojected_slope.tif` | EPSG:32719 | `[29.680407648073597, 29.680407671745545]` | top_left_window_max_1024x1024 | 1046529 | 0.0 | 89.1095199584961 | 8.108246803283691 | 7.470362663269043 |
| `large/terrain/Ladakh_Reprojected.tif` | EPSG:32643 | `[28.294190637152262, 28.294190652337008]` | top_left_window_max_1024x1024 | 1048576 | 0.0 | 6566.47705078125 | 4393.044921875 | 1444.5233154296875 |
| `large/terrain/Ladakh_Reprojected_roughness.tif` | EPSG:32643 | `[28.294190637152262, 28.294190652337008]` | top_left_window_max_1024x1024 | 1046529 | 0.0 | 6109.5908203125 | 65.11235809326172 | 316.0396423339844 |
| `large/terrain/Ladakh_Reprojected_slope.tif` | EPSG:32643 | `[28.294190637152262, 28.294190652337008]` | top_left_window_max_1024x1024 | 1046529 | 0.0 | 89.5184326171875 | 29.814498901367188 | 16.232036590576172 |

### `large/temperature/Mars_ATS_FULL_MASTER.parquet`

Extension: `.parquet`; size: 2724.922509 MB.
Rows: 88656007; columns: `["SCLK", "LMST", "LTST", "ATS_LOCAL_TEMP1", "ATS_LOCAL_TEMP2", "ATS_LOCAL_TEMP3", "ATS_LOCAL_TEMP4", "ATS_LOCAL_TEMP5", "SOURCE_FILE", "PRODUCT", "SOL", "ATS_LOCAL_TEMP1_K", "ATS_LOCAL_TEMP1_C", "ATS_LOCAL_TEMP2_K", "ATS_LOCAL_TEMP2_C", "ATS_LOCAL_TEMP3_K", "ATS_LOCAL_TEMP3_C", "ATS_LOCAL_TEMP4_K", "ATS_LOCAL_TEMP4_C", "ATS_LOCAL_TEMP5_K", "ATS_LOCAL_TEMP5_C"]`; dtypes: `{"SCLK": "double", "LMST": "string", "LTST": "string", "ATS_LOCAL_TEMP1": "double", "ATS_LOCAL_TEMP2": "double", "ATS_LOCAL_TEMP3": "double", "ATS_LOCAL_TEMP4": "double", "ATS_LOCAL_TEMP5": "double", "SOURCE_FILE": "string", "PRODUCT": "string", "SOL": "int64", "ATS_LOCAL_TEMP1_K": "double", "ATS_LOCAL_TEMP1_C": "double", "ATS_LOCAL_TEMP2_K": "double", "ATS_LOCAL_TEMP2_C": "double", "ATS_LOCAL_TEMP3_K": "double", "ATS_LOCAL_TEMP3_C": "double", "ATS_LOCAL_TEMP4_K": "double", "ATS_LOCAL_TEMP4_C": "double", "ATS_LOCAL_TEMP5_K": "double", "ATS_LOCAL_TEMP5_C": "double"}`.
Schema:
```text
SCLK: double
LMST: string
LTST: string
ATS_LOCAL_TEMP1: double
ATS_LOCAL_TEMP2: double
ATS_LOCAL_TEMP3: double
ATS_LOCAL_TEMP4: double
ATS_LOCAL_TEMP5: double
SOURCE_FILE: string
PRODUCT: string
SOL: int64
ATS_LOCAL_TEMP1_K: double
ATS_LOCAL_TEMP1_C: double
ATS_LOCAL_TEMP2_K: double
ATS_LOCAL_TEMP2_C: double
ATS_LOCAL_TEMP3_K: double
ATS_LOCAL_TEMP3_C: double
ATS_LOCAL_TEMP4_K: double
ATS_LOCAL_TEMP4_C: double
ATS_LOCAL_TEMP5_K: double
ATS_LOCAL_TEMP5_C: double
```
The inventory CSV contains a bounded preview of at most the first 100 rows.

### `large/temperature/Mars_ATS_TIRS_HEIGHT_AWARE_MATCHED_1MIN.parquet`

Extension: `.parquet`; size: 100.526482 MB.
Rows: 1372739; columns: `["mars_sol", "minute_bin", "tirs_observations", "ats_observations", "tirs_air_C", "tirs_air_max_C", "tirs_air_uncertainty_K", "tirs_ground_C", "tirs_ground_uncertainty_K", "ats1_C", "ats2_C", "ats3_C", "ats4_C", "ats5_C", "ats_1p5m_coldest_C", "ats_body_mean_C", "tirs_air_minus_ats_1p5m_C", "tirs_air_minus_ats_body_C", "tirs_ground_minus_ats_1p5m_C", "downward_lw", "upward_lw", "upward_sw", "sun_outside_fov_fraction", "ground_not_in_shadow_fraction", "rover_still_fraction"]`; dtypes: `{"mars_sol": "int32", "minute_bin": "int64", "tirs_observations": "int64", "ats_observations": "int64", "tirs_air_C": "double", "tirs_air_max_C": "double", "tirs_air_uncertainty_K": "double", "tirs_ground_C": "double", "tirs_ground_uncertainty_K": "double", "ats1_C": "double", "ats2_C": "double", "ats3_C": "double", "ats4_C": "double", "ats5_C": "double", "ats_1p5m_coldest_C": "double", "ats_body_mean_C": "double", "tirs_air_minus_ats_1p5m_C": "double", "tirs_air_minus_ats_body_C": "double", "tirs_ground_minus_ats_1p5m_C": "double", "downward_lw": "double", "upward_lw": "double", "upward_sw": "double", "sun_outside_fov_fraction": "double", "ground_not_in_shadow_fraction": "double", "rover_still_fraction": "double"}`.
Schema:
```text
mars_sol: int32
minute_bin: int64
tirs_observations: int64
ats_observations: int64
tirs_air_C: double
tirs_air_max_C: double
tirs_air_uncertainty_K: double
tirs_ground_C: double
tirs_ground_uncertainty_K: double
ats1_C: double
ats2_C: double
ats3_C: double
ats4_C: double
ats5_C: double
ats_1p5m_coldest_C: double
ats_body_mean_C: double
tirs_air_minus_ats_1p5m_C: double
tirs_air_minus_ats_body_C: double
tirs_ground_minus_ats_1p5m_C: double
downward_lw: double
upward_lw: double
upward_sw: double
sun_outside_fov_fraction: double
ground_not_in_shadow_fraction: double
rover_still_fraction: double
```
The inventory CSV contains a bounded preview of at most the first 100 rows.

### `large/temperature/Mars_TIRS_FULL_MASTER.parquet`

Extension: `.parquet`; size: 1537.237472 MB.
Rows: 80882439; columns: `["SCLK", "LMST", "LTST", "DOWNWARD_LW_IRRADIANCE", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY", "AIR_TEMP", "AIR_TEMP_UNCERTAINTY", "UPWARD_SW_IRRADIANCE", "UPWARD_SW_IRRADIANCE_UNCERTAINTY", "UPWARD_LW_IRRADIANCE", "UPWARD_LW_IRRADIANCE_UNCERTAINTY", "GROUND_TEMP", "GROUND_TEMP_UNCERTAINTY", "RSM_HEAD_OUTSIDE_TIRS_UPWARD_LOOKING_FOV", "WHEEL_OUTSIDE_TIRS_DOWNWARD_LOOKING_FOV", "SUN_OUTSIDE_TIRS_FOV", "ROVER_LOW_TILT", "TIRS_GROUND_FOOTPRINT_NOT_IN_SHADOW", "ROVER_HGA_OFF", "SKYCAM_OFF", "ROVER_STILL", "SOURCE_FILE", "PRODUCT", "SOL", "AIR_TEMP_K", "AIR_TEMP_C", "GROUND_TEMP_K", "GROUND_TEMP_C"]`; dtypes: `{"SCLK": "double", "LMST": "string", "LTST": "string", "DOWNWARD_LW_IRRADIANCE": "double", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY": "double", "AIR_TEMP": "double", "AIR_TEMP_UNCERTAINTY": "double", "UPWARD_SW_IRRADIANCE": "double", "UPWARD_SW_IRRADIANCE_UNCERTAINTY": "double", "UPWARD_LW_IRRADIANCE": "double", "UPWARD_LW_IRRADIANCE_UNCERTAINTY": "double", "GROUND_TEMP": "double", "GROUND_TEMP_UNCERTAINTY": "double", "RSM_HEAD_OUTSIDE_TIRS_UPWARD_LOOKING_FOV": "int64", "WHEEL_OUTSIDE_TIRS_DOWNWARD_LOOKING_FOV": "double", "SUN_OUTSIDE_TIRS_FOV": "int64", "ROVER_LOW_TILT": "int64", "TIRS_GROUND_FOOTPRINT_NOT_IN_SHADOW": "int64", "ROVER_HGA_OFF": "double", "SKYCAM_OFF": "double", "ROVER_STILL": "int64", "SOURCE_FILE": "string", "PRODUCT": "string", "SOL": "int64", "AIR_TEMP_K": "double", "AIR_TEMP_C": "double", "GROUND_TEMP_K": "double", "GROUND_TEMP_C": "double"}`.
Schema:
```text
SCLK: double
LMST: string
LTST: string
DOWNWARD_LW_IRRADIANCE: double
DOWNWARD_LW_IRRADIANCE_UNCERTAINTY: double
AIR_TEMP: double
AIR_TEMP_UNCERTAINTY: double
UPWARD_SW_IRRADIANCE: double
UPWARD_SW_IRRADIANCE_UNCERTAINTY: double
UPWARD_LW_IRRADIANCE: double
UPWARD_LW_IRRADIANCE_UNCERTAINTY: double
GROUND_TEMP: double
GROUND_TEMP_UNCERTAINTY: double
RSM_HEAD_OUTSIDE_TIRS_UPWARD_LOOKING_FOV: int64
WHEEL_OUTSIDE_TIRS_DOWNWARD_LOOKING_FOV: double
SUN_OUTSIDE_TIRS_FOV: int64
ROVER_LOW_TILT: int64
TIRS_GROUND_FOOTPRINT_NOT_IN_SHADOW: int64
ROVER_HGA_OFF: double
SKYCAM_OFF: double
ROVER_STILL: int64
SOURCE_FILE: string
PRODUCT: string
SOL: int64
AIR_TEMP_K: double
AIR_TEMP_C: double
GROUND_TEMP_K: double
GROUND_TEMP_C: double
```
The inventory CSV contains a bounded preview of at most the first 100 rows.

### `large/terrain/Askja_Reprojected.tif`

Extension: `.tif`; size: 26.311138 MB.
CRS: `EPSG:32727`; pixel size: `[29.99818936288092, 29.998189339968448]`; bounds: `[681433.9853, 17214437.1091, 735580.7171, 17328970.196]`; nodata: `[null]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1048576, "minimum": 0.0, "maximum": 879.9260864257812, "mean": 321.845703125, "std": 159.4658966064453}]`.

### `large/terrain/Askja_Reprojected_roughness.tif`

Extension: `.tif`; size: 26.333338 MB.
CRS: `EPSG:32727`; pixel size: `[29.99818936288092, 29.998189339968448]`; bounds: `[681433.9853, 17214437.1091, 735580.7171, 17328970.196]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 405.094482421875, "mean": 5.80748176574707, "std": 17.42037010192871}]`.

### `large/terrain/Askja_Reprojected_slope.tif`

Extension: `.tif`; size: 26.333338 MB.
CRS: `EPSG:32727`; pixel size: `[29.99818936288092, 29.998189339968448]`; bounds: `[681433.9853, 17214437.1091, 735580.7171, 17328970.196]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 82.37259674072266, "mean": 3.738919258117676, "std": 6.604355812072754}]`.

### `large/terrain/Askja_Roughness.tif`

Extension: `.tif`; size: 24.761145 MB.
CRS: `EPSG:4326`; pixel size: `[0.0005555555555555556, 0.0002777777777777778]`; bounds: `[-17.000277778, 65.000138889, -16.000277778, 66.000138889]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 110.32806396484375, "mean": 5.420685291290283, "std": 7.49233341217041}]`.

### `large/terrain/Askja_Slope.tif`

Extension: `.tif`; size: 24.761145 MB.
CRS: `EPSG:4326`; pixel size: `[0.0005555555555555556, 0.0002777777777777778]`; bounds: `[-17.000277778, 65.000138889, -16.000277778, 66.000138889]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 89.9996566772461, "mean": 89.70311737060547, "std": 4.865141868591309}]`.

### `large/terrain/Atacama_Reprojected.tif`

Extension: `.tif`; size: 49.655531 MB.
CRS: `EPSG:32719`; pixel size: `[29.680407648073597, 29.680407671745545]`; bounds: `[499985.6638, 7456154.0104, 603214.1216, 7567188.4155]`; nodata: `[null]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1048576, "minimum": 0.0, "maximum": 4582.439453125, "mean": 3178.93310546875, "std": 377.6178894042969}]`.

### `large/terrain/Atacama_Reprojected_roughness.tif`

Extension: `.tif`; size: 49.677290 MB.
CRS: `EPSG:32719`; pixel size: `[29.680407648073597, 29.680407671745545]`; bounds: `[499985.6638, 7456154.0104, 603214.1216, 7567188.4155]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 3823.69189453125, "mean": 12.355607986450195, "std": 61.13019943237305}]`.

### `large/terrain/Atacama_Reprojected_slope.tif`

Extension: `.tif`; size: 49.677290 MB.
CRS: `EPSG:32719`; pixel size: `[29.680407648073597, 29.680407671745545]`; bounds: `[499985.6638, 7456154.0104, 603214.1216, 7567188.4155]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 89.1095199584961, "mean": 8.108246803283691, "std": 7.470362663269043}]`.

### `large/terrain/Atacama_Roughness.tif`

Extension: `.tif`; size: 49.480383 MB.
CRS: `EPSG:4326`; pixel size: `[0.0002777777777777778, 0.0002777777777777778]`; bounds: `[-69.000138889, -22.999861111, -68.000138889, -21.999861111]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 114.37158203125, "mean": 12.061357498168945, "std": 11.166790008544922}]`.

### `large/terrain/Atacama_Slope.tif`

Extension: `.tif`; size: 49.480383 MB.
CRS: `EPSG:4326`; pixel size: `[0.0002777777777777778, 0.0002777777777777778]`; bounds: `[-69.000138889, -22.999861111, -68.000138889, -21.999861111]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 89.99967956542969, "mean": 89.98380279541016, "std": 0.8159680962562561}]`.

### `large/terrain/Extent_Askja.gpkg`

Extension: `.gpkg`; size: 0.101562 MB.
Layers and metadata: `[{"layer": "extent", "crs": "EPSG:4326", "geometry_type": "Polygon", "feature_count": 1, "columns": ["MINX", "MINY", "MAXX", "MAXY", "CNTX", "CNTY", "AREA", "PERIM", "HEIGHT", "WIDTH"]}]`.

### `large/terrain/Extent_Atacama.gpkg`

Extension: `.gpkg`; size: 0.101562 MB.
Layers and metadata: `[{"layer": "extent", "crs": "EPSG:4326", "geometry_type": "Polygon", "feature_count": 1, "columns": ["MINX", "MINY", "MAXX", "MAXY", "CNTX", "CNTY", "AREA", "PERIM", "HEIGHT", "WIDTH"]}]`.

### `large/terrain/Extent_Jezero Crater.gpkg`

Extension: `.gpkg`; size: 0.101562 MB.
Layers and metadata: `[{"layer": "extent", "crs": "EPSG:4326", "geometry_type": "Polygon", "feature_count": 1, "columns": ["MINX", "MINY", "MAXX", "MAXY", "CNTX", "CNTY", "AREA", "PERIM", "HEIGHT", "WIDTH"]}]`.

### `large/terrain/Extent_Ladakh.gpkg`

Extension: `.gpkg`; size: 0.101562 MB.
Layers and metadata: `[{"layer": "extent", "crs": "EPSG:4326", "geometry_type": "Polygon", "feature_count": 1, "columns": ["MINX", "MINY", "MAXX", "MAXY", "CNTX", "CNTY", "AREA", "PERIM", "HEIGHT", "WIDTH"]}]`.

### `large/terrain/Ladakh_Reprojected.tif`

Extension: `.tif`; size: 51.046122 MB.
CRS: `EPSG:32643`; pixel size: `[28.294190637152262, 28.294190652337008]`; bounds: `[682503.1086, 3763966.6632, 777090.5879, 3877171.72]`; nodata: `[null]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1048576, "minimum": 0.0, "maximum": 6566.47705078125, "mean": 4393.044921875, "std": 1444.5233154296875}]`.

### `large/terrain/Ladakh_Reprojected_roughness.tif`

Extension: `.tif`; size: 51.069368 MB.
CRS: `EPSG:32643`; pixel size: `[28.294190637152262, 28.294190652337008]`; bounds: `[682503.1086, 3763966.6632, 777090.5879, 3877171.72]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 6109.5908203125, "mean": 65.11235809326172, "std": 316.0396423339844}]`.

### `large/terrain/Ladakh_Reprojected_slope.tif`

Extension: `.tif`; size: 51.069368 MB.
CRS: `EPSG:32643`; pixel size: `[28.294190637152262, 28.294190652337008]`; bounds: `[682503.1086, 3763966.6632, 777090.5879, 3877171.72]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 89.5184326171875, "mean": 29.814498901367188, "std": 16.232036590576172}]`.

### `large/terrain/Ladakh_Roughness.tif`

Extension: `.tif`; size: 49.480383 MB.
CRS: `EPSG:4326`; pixel size: `[0.0002777777777777778, 0.0002777777777777778]`; bounds: `[76.999861111, 34.000138889, 77.999861111, 35.000138889]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 272.271240234375, "mean": 50.55663299560547, "std": 26.740497589111328}]`.

### `large/terrain/Ladakh_Slope.tif`

Extension: `.tif`; size: 49.480383 MB.
CRS: `EPSG:4326`; pixel size: `[0.0002777777777777778, 0.0002777777777777778]`; bounds: `[76.999861111, 34.000138889, 77.999861111, 35.000138889]`; nodata: `[-9999.0]`; dtype: `["float32"]`.
Window/overview statistics: `[{"band": 1, "method": "top_left_window_max_1024x1024", "sampled_valid_pixels": 1046529, "minimum": 0.0, "maximum": 89.99987030029297, "mean": 89.98129272460938, "std": 1.237838625907898}]`.

### `large/terrain/site_boundaries.gpkg`

Extension: `.gpkg`; size: 0.093750 MB.
Layers and metadata: `[{"layer": "site_boundaries", "crs": "EPSG:4326", "geometry_type": "Polygon", "feature_count": 0, "columns": []}]`.

### `large/terrain/site_boundaries.gpkg.geojson`

Extension: `.geojson`; size: 0.002516 MB.

### `large/terrain/site_boundaries.gpkg.qmd`

Extension: `.qmd`; size: 0.000648 MB.

### `package/ASHWARYA_TEMPERATURE_ANALYSIS_UPDATE.txt`

Extension: `.txt`; size: 0.001482 MB.

### `package/Data_Quality_and_Limitations.md`

Extension: `.md`; size: 0.000942 MB.

### `package/Earth_Data_Methodology.md`

Extension: `.md`; size: 0.000572 MB.

### `package/Earth_temperature_daily_analysis.csv`

Extension: `.csv`; size: 0.009754 MB.
Rows: 93.
Columns: `["site", "date", "day_mean_C", "day_valid_pixels", "night_mean_C", "night_valid_pixels", "T2M_C", "_merge", "MODIS_day_available", "MODIS_night_available", "POWER_available", "day_LST_minus_air_C", "night_LST_minus_air_C", "day_night_range_C"]`.
Dtypes: `{"site": "str", "date": "str", "day_mean_C": "float64", "day_valid_pixels": "int64", "night_mean_C": "float64", "night_valid_pixels": "int64", "T2M_C": "float64", "_merge": "str", "MODIS_day_available": "bool", "MODIS_night_available": "bool", "POWER_available": "bool", "day_LST_minus_air_C": "float64", "night_LST_minus_air_C": "float64", "day_night_range_C": "float64"}`.
First five rows:
```json
[
  {
    "site": "Atacama",
    "date": "2024-07-01",
    "day_mean_C": 25.917195122,
    "day_valid_pixels": 164,
    "night_mean_C": 6.1342735043,
    "night_valid_pixels": 234,
    "T2M_C": 15.2,
    "_merge": "both",
    "MODIS_day_available": true,
    "MODIS_night_available": true,
    "POWER_available": true,
    "day_LST_minus_air_C": 10.717195122,
    "night_LST_minus_air_C": -9.0657264957,
    "day_night_range_C": 19.7829216177
  },
  {
    "site": "Atacama",
    "date": "2024-07-02",
    "day_mean_C": 29.1803333333,
    "day_valid_pixels": 60,
    "night_mean_C": 7.0513675214,
    "night_valid_pixels": 234,
    "T2M_C": 16.55,
    "_merge": "both",
    "MODIS_day_available": true,
    "MODIS_night_available": true,
    "POWER_available": true,
    "day_LST_minus_air_C": 12.6303333333,
    "night_LST_minus_air_C": -9.4986324786,
    "day_night_range_C": 22.128965812
  },
  {
    "site": "Atacama",
    "date": "2024-07-03",
    "day_mean_C": 18.7107692308,
    "day_valid_pixels": 26,
    "night_mean_C": 4.9087179487,
    "night_valid_pixels": 234,
    "T2M_C": 16.16,
    "_merge": "both",
    "MODIS_day_available": true,
    "MODIS_night_available": true,
    "POWER_available": true,
    "day_LST_minus_air_C": 2.5507692308,
    "night_LST_minus_air_C": -11.2512820513,
    "day_night_range_C": 13.8020512821
  },
  {
    "site": "Atacama",
    "date": "2024-07-04",
    "day_mean_C": 26.7996078431,
    "day_valid_pixels": 204,
    "night_mean_C": 2.2105128205,
    "night_valid_pixels": 234,
    "T2M_C": 13.41,
    "_merge": "both",
    "MODIS_day_available": true,
    "MODIS_night_available": true,
    "POWER_available": true,
    "day_LST_minus_air_C": 13.3896078431,
    "night_LST_minus_air_C": -11.1994871795,
    "day_night_range_C": 24.5890950226
  },
  {
    "site": "Atacama",
    "date": "2024-07-05",
    "day_mean_C": 27.8768055556,
    "day_valid_pixels": 144,
    "night_mean_C": 3.3631623932,
    "night_valid_pixels": 234,
    "T2M_C": 11.23,
    "_merge": "both",
    "MODIS_day_available": true,
    "MODIS_night_available": true,
    "POWER_available": true,
    "day_LST_minus_air_C": 16.6468055556,
    "night_LST_minus_air_C": -7.8668376068,
    "day_night_range_C": 24.5136431624
  }
]
```

### `package/Earth_temperature_summary_July2024.csv`

Extension: `.csv`; size: 0.000728 MB.
Rows: 3.
Columns: `["site", "total_days", "MODIS_day_valid_days", "MODIS_day_coverage_pct", "MODIS_day_mean_C", "MODIS_day_median_C", "MODIS_day_std_C", "MODIS_day_min_C", "MODIS_day_max_C", "MODIS_night_valid_days", "MODIS_night_coverage_pct", "MODIS_night_mean_C", "MODIS_night_median_C", "MODIS_night_std_C", "MODIS_night_min_C", "MODIS_night_max_C", "paired_day_night_days", "mean_day_night_range_C", "POWER_valid_days", "POWER_mean_T2M_C", "POWER_min_T2M_C", "POWER_max_T2M_C"]`.
Dtypes: `{"site": "str", "total_days": "int64", "MODIS_day_valid_days": "int64", "MODIS_day_coverage_pct": "float64", "MODIS_day_mean_C": "float64", "MODIS_day_median_C": "float64", "MODIS_day_std_C": "float64", "MODIS_day_min_C": "float64", "MODIS_day_max_C": "float64", "MODIS_night_valid_days": "int64", "MODIS_night_coverage_pct": "float64", "MODIS_night_mean_C": "float64", "MODIS_night_median_C": "float64", "MODIS_night_std_C": "float64", "MODIS_night_min_C": "float64", "MODIS_night_max_C": "float64", "paired_day_night_days": "int64", "mean_day_night_range_C": "float64", "POWER_valid_days": "int64", "POWER_mean_T2M_C": "float64", "POWER_min_T2M_C": "float64", "POWER_max_T2M_C": "float64"}`.
First five rows:
```json
[
  {
    "site": "Atacama",
    "total_days": 31,
    "MODIS_day_valid_days": 24,
    "MODIS_day_coverage_pct": 77.42,
    "MODIS_day_mean_C": 25.562,
    "MODIS_day_median_C": 26.132,
    "MODIS_day_std_C": 5.105,
    "MODIS_day_min_C": 15.143,
    "MODIS_day_max_C": 36.094,
    "MODIS_night_valid_days": 28,
    "MODIS_night_coverage_pct": 90.32,
    "MODIS_night_mean_C": 3.006,
    "MODIS_night_median_C": 3.067,
    "MODIS_night_std_C": 2.989,
    "MODIS_night_min_C": -2.772,
    "MODIS_night_max_C": 8.88,
    "paired_day_night_days": 21,
    "mean_day_night_range_C": 22.331,
    "POWER_valid_days": 31,
    "POWER_mean_T2M_C": 12.04,
    "POWER_min_T2M_C": 4.89,
    "POWER_max_T2M_C": 16.8
  },
  {
    "site": "Iceland",
    "total_days": 31,
    "MODIS_day_valid_days": 8,
    "MODIS_day_coverage_pct": 25.81,
    "MODIS_day_mean_C": 14.822,
    "MODIS_day_median_C": 10.417,
    "MODIS_day_std_C": 8.184,
    "MODIS_day_min_C": 6.501,
    "MODIS_day_max_C": 26.669,
    "MODIS_night_valid_days": 8,
    "MODIS_night_coverage_pct": 25.81,
    "MODIS_night_mean_C": 2.382,
    "MODIS_night_median_C": 2.072,
    "MODIS_night_std_C": 1.996,
    "MODIS_night_min_C": -0.026,
    "MODIS_night_max_C": 5.59,
    "paired_day_night_days": 5,
    "mean_day_night_range_C": 9.877,
    "POWER_valid_days": 31,
    "POWER_mean_T2M_C": 2.919,
    "POWER_min_T2M_C": 0.77,
    "POWER_max_T2M_C": 5.46
  },
  {
    "site": "Ladakh",
    "total_days": 31,
    "MODIS_day_valid_days": 25,
    "MODIS_day_coverage_pct": 80.65,
    "MODIS_day_mean_C": 36.373,
    "MODIS_day_median_C": 36.271,
    "MODIS_day_std_C": 3.085,
    "MODIS_day_min_C": 28.703,
    "MODIS_day_max_C": 41.376,
    "MODIS_night_valid_days": 23,
    "MODIS_night_coverage_pct": 74.19,
    "MODIS_night_mean_C": 18.029,
    "MODIS_night_median_C": 17.616,
    "MODIS_night_std_C": 2.526,
    "MODIS_night_min_C": 11.802,
    "MODIS_night_max_C": 22.882,
    "paired_day_night_days": 18,
    "mean_day_night_range_C": 18.404,
    "POWER_valid_days": 31,
    "POWER_mean_T2M_C": 10.373,
    "POWER_min_T2M_C": 7.16,
    "POWER_max_T2M_C": 14.82
  }
]
```

### `package/FINAL_PACKAGE_FILE_INDEX.csv`

Extension: `.csv`; size: 0.000541 MB.
Rows: 11.
Columns: `["filename", "size_kb"]`.
Dtypes: `{"filename": "str", "size_kb": "float64"}`.
First five rows:
```json
[
  {
    "filename": "ASHWARYA_TEMPERATURE_ANALYSIS_UPDATE.txt",
    "size_kb": 1.52
  },
  {
    "filename": "MASTER_ASSIGNED_TASK_COMPLETION_TRACKER.csv",
    "size_kb": 1.47
  },
  {
    "filename": "MASTER_EARTH_SITE_MEASUREMENT_AUDIT.csv",
    "size_kb": 0.59
  },
  {
    "filename": "MASTER_GEOMETRY_AND_FLAG_VERIFICATION_TRACKER.csv",
    "size_kb": 0.51
  },
  {
    "filename": "MASTER_MARS_SEASONAL_LOCAL_TIME_COVERAGE.csv",
    "size_kb": 0.26
  }
]
```

### `package/FINAL_PACKAGE_FILE_INDEX.xlsx`

Extension: `.xlsx`; size: 0.005552 MB.

### `package/Mars_MEDA_Methodology.md`

Extension: `.md`; size: 0.000731 MB.

### `package/MASTER_ASSIGNED_TASK_COMPLETION_TRACKER.csv`

Extension: `.csv`; size: 0.001434 MB.
Rows: 7.
Columns: `["assigned_task", "status", "evidence", "remaining"]`.
Dtypes: `{"assigned_task": "str", "status": "str", "evidence": "str", "remaining": "str"}`.
First five rows:
```json
[
  {
    "assigned_task": "Check prepared Mars and Earth temperature datasets",
    "status": "COMPLETED",
    "evidence": "Earth daily audit, TIRS per-sol audit, ATS/TIRS dataset inventory and validation outputs.",
    "remaining": "No major data audit pending."
  },
  {
    "assigned_task": "Confirm measurement types and units",
    "status": "MOSTLY COMPLETED",
    "evidence": "POWER T2M, MODIS LST, TIRS air and ground temperature identified and separated.",
    "remaining": "Verify official irradiance units and all source product measurement definitions."
  },
  {
    "assigned_task": "Confirm observation periods",
    "status": "COMPLETED WITH LIMITATIONS",
    "evidence": "Earth daily audit and Mars per-sol coverage audits.",
    "remaining": "Earth currently covers July 2024 only. Mars Ls is mapped for 1,496 of 1,751 TIRS sols."
  },
  {
    "assigned_task": "Confirm quality flags",
    "status": "PARTIALLY COMPLETED",
    "evidence": "Per-sol flag fractions and uncertainty summaries generated.",
    "remaining": "Official flag semantics and filtering rules require PDS documentation."
  },
  {
    "assigned_task": "Identify scientifically valid comparisons",
    "status": "COMPLETED",
    "evidence": "Measurement-class comparison matrix generated.",
    "remaining": "Use air-to-air and surface-to-surface comparisons; state spatial and temporal caveats."
  }
]
```

### `package/MASTER_ASSIGNED_TASK_COMPLETION_TRACKER.xlsx`

Extension: `.xlsx`; size: 0.005962 MB.

### `package/MASTER_EARTH_SITE_MEASUREMENT_AUDIT.csv`

Extension: `.csv`; size: 0.000581 MB.
Rows: 3.
Columns: `["site", "period_start", "period_end", "daily_records", "POWER_T2M_valid_days", "POWER_T2M_mean_C", "MODIS_day_valid_days", "MODIS_night_valid_days", "MODIS_day_mean_C", "MODIS_night_mean_C", "MODIS_day_mean_valid_pixels", "MODIS_night_mean_valid_pixels"]`.
Dtypes: `{"site": "str", "period_start": "str", "period_end": "str", "daily_records": "int64", "POWER_T2M_valid_days": "int64", "POWER_T2M_mean_C": "float64", "MODIS_day_valid_days": "int64", "MODIS_night_valid_days": "int64", "MODIS_day_mean_C": "float64", "MODIS_night_mean_C": "float64", "MODIS_day_mean_valid_pixels": "float64", "MODIS_night_mean_valid_pixels": "float64"}`.
First five rows:
```json
[
  {
    "site": "Atacama",
    "period_start": "2024-07-01",
    "period_end": "2024-07-31",
    "daily_records": 31,
    "POWER_T2M_valid_days": 31,
    "POWER_T2M_mean_C": 12.04,
    "MODIS_day_valid_days": 24,
    "MODIS_night_valid_days": 28,
    "MODIS_day_mean_C": 25.5616995565,
    "MODIS_night_mean_C": 3.0061370574,
    "MODIS_day_mean_valid_pixels": 142.2903225806,
    "MODIS_night_mean_valid_pixels": 204.9677419355
  },
  {
    "site": "Iceland",
    "period_start": "2024-07-01",
    "period_end": "2024-07-31",
    "daily_records": 31,
    "POWER_T2M_valid_days": 31,
    "POWER_T2M_mean_C": 2.9190322581,
    "MODIS_day_valid_days": 8,
    "MODIS_night_valid_days": 8,
    "MODIS_day_mean_C": 14.8217414655,
    "MODIS_night_mean_C": 2.3817085287,
    "MODIS_day_mean_valid_pixels": 10.7741935484,
    "MODIS_night_mean_valid_pixels": 8.3548387097
  },
  {
    "site": "Ladakh",
    "period_start": "2024-07-01",
    "period_end": "2024-07-31",
    "daily_records": 31,
    "POWER_T2M_valid_days": 31,
    "POWER_T2M_mean_C": 10.3725806452,
    "MODIS_day_valid_days": 25,
    "MODIS_night_valid_days": 23,
    "MODIS_day_mean_C": 36.3725445707,
    "MODIS_night_mean_C": 18.0290119614,
    "MODIS_day_mean_valid_pixels": 127.6451612903,
    "MODIS_night_mean_valid_pixels": 158.6129032258
  }
]
```

### `package/MASTER_EARTH_SITE_MEASUREMENT_AUDIT.xlsx`

Extension: `.xlsx`; size: 0.005509 MB.

### `package/MASTER_GEOMETRY_AND_FLAG_VERIFICATION_TRACKER.csv`

Extension: `.csv`; size: 0.000498 MB.
Rows: 5.
Columns: `["item", "status", "next_action"]`.
Dtypes: `{"item": "str", "status": "str", "next_action": "str"}`.
First five rows:
```json
[
  {
    "item": "Solar elevation / zenith",
    "status": "Not verified",
    "next_action": "Check official MEDA ancillary products and metadata."
  },
  {
    "item": "Solar azimuth",
    "status": "Not verified",
    "next_action": "Check official MEDA ancillary products and metadata."
  },
  {
    "item": "Rover pitch / roll / attitude",
    "status": "Not verified",
    "next_action": "Locate rover geometry and attitude records."
  },
  {
    "item": "MEDA condition flag definitions",
    "status": "Data fractions computed; semantics pending",
    "next_action": "Verify against official product documentation."
  },
  {
    "item": "Irradiance units and viewing geometry",
    "status": "Requires documentation verification",
    "next_action": "Verify official TIRS product documentation."
  }
]
```

### `package/MASTER_MARS_SEASONAL_LOCAL_TIME_COVERAGE.csv`

Extension: `.csv`; size: 0.000251 MB.
Rows: 4.
Columns: `["Season", "local_time_bins", "eligible_bins", "minimum_sols", "median_sols", "maximum_sols", "eligible_percentage"]`.
Dtypes: `{"Season": "str", "local_time_bins": "int64", "eligible_bins": "int64", "minimum_sols": "int64", "median_sols": "float64", "maximum_sols": "int64", "eligible_percentage": "float64"}`.
First five rows:
```json
[
  {
    "Season": "Northern Autumn",
    "local_time_bins": 48,
    "eligible_bins": 48,
    "minimum_sols": 166,
    "median_sols": 200.0,
    "maximum_sols": 221,
    "eligible_percentage": 100.0
  },
  {
    "Season": "Northern Spring",
    "local_time_bins": 48,
    "eligible_bins": 48,
    "minimum_sols": 384,
    "median_sols": 438.5,
    "maximum_sols": 473,
    "eligible_percentage": 100.0
  },
  {
    "Season": "Northern Summer",
    "local_time_bins": 48,
    "eligible_bins": 48,
    "minimum_sols": 301,
    "median_sols": 336.5,
    "maximum_sols": 355,
    "eligible_percentage": 100.0
  },
  {
    "Season": "Northern Winter",
    "local_time_bins": 48,
    "eligible_bins": 48,
    "minimum_sols": 121,
    "median_sols": 215.0,
    "maximum_sols": 270,
    "eligible_percentage": 100.0
  }
]
```

### `package/MASTER_MARS_SEASONAL_LOCAL_TIME_COVERAGE.xlsx`

Extension: `.xlsx`; size: 0.005251 MB.

### `package/MASTER_MEDА_FLAG_VERIFICATION_TRACKER.csv`

Extension: `.csv`; size: 0.000694 MB.
Rows: 6.
Columns: `["flag", "data_available", "fraction_computed", "official_semantics_verified", "allowed_interpretation"]`.
Dtypes: `{"flag": "str", "data_available": "str", "fraction_computed": "str", "official_semantics_verified": "str", "allowed_interpretation": "str"}`.
First five rows:
```json
[
  {
    "flag": "SUN_OUTSIDE_TIRS_FOV_mean",
    "data_available": "Yes",
    "fraction_computed": "Yes",
    "official_semantics_verified": "No",
    "allowed_interpretation": "Descriptive flag fraction only; do not infer good/bad quality."
  },
  {
    "flag": "ROVER_LOW_TILT_mean",
    "data_available": "Yes",
    "fraction_computed": "Yes",
    "official_semantics_verified": "No",
    "allowed_interpretation": "Descriptive flag fraction only; do not infer good/bad quality."
  },
  {
    "flag": "TIRS_GROUND_FOOTPRINT_NOT_IN_SHADOW_mean",
    "data_available": "Yes",
    "fraction_computed": "Yes",
    "official_semantics_verified": "No",
    "allowed_interpretation": "Descriptive flag fraction only; do not infer good/bad quality."
  },
  {
    "flag": "ROVER_STILL_mean",
    "data_available": "Yes",
    "fraction_computed": "Yes",
    "official_semantics_verified": "No",
    "allowed_interpretation": "Descriptive flag fraction only; do not infer good/bad quality."
  },
  {
    "flag": "RSM_HEAD_OUTSIDE_TIRS_UPWARD_LOOKING_FOV_mean",
    "data_available": "Yes",
    "fraction_computed": "Yes",
    "official_semantics_verified": "No",
    "allowed_interpretation": "Descriptive flag fraction only; do not infer good/bad quality."
  }
]
```

### `package/MASTER_MEDА_FLAG_VERIFICATION_TRACKER.xlsx`

Extension: `.xlsx`; size: 0.005361 MB.

### `package/MASTER_SCIENTIFIC_COMPARISON_VALIDITY_MATRIX.csv`

Extension: `.csv`; size: 0.001478 MB.
Rows: 5.
Columns: `["earth_measurement", "mars_measurement", "measurement_class", "scientific_status", "reason", "limitations"]`.
Dtypes: `{"earth_measurement": "str", "mars_measurement": "str", "measurement_class": "str", "scientific_status": "str", "reason": "str", "limitations": "str"}`.
First five rows:
```json
[
  {
    "earth_measurement": "NASA POWER T2M",
    "mars_measurement": "MEDA TIRS AIR_TEMP",
    "measurement_class": "Near-surface air temperature",
    "scientific_status": "VALID MEASUREMENT-CLASS PAIRING",
    "reason": "Both represent air temperature, but differ in sensor, location, spatial support and temporal sampling.",
    "limitations": "Daily Earth values versus Mars observations/per-sol summaries; atmospheric measurement heights and sampling must be checked."
  },
  {
    "earth_measurement": "MODIS daytime LST",
    "mars_measurement": "MEDA TIRS GROUND_TEMP",
    "measurement_class": "Surface temperature",
    "scientific_status": "VALID WITH CAVEATS",
    "reason": "Both represent surface thermal conditions, but have different spatial footprints, retrieval methods and observation geometry.",
    "limitations": "Cloud/pixel coverage, surface emissivity, footprint, and viewing geometry affect comparability."
  },
  {
    "earth_measurement": "MODIS nighttime LST",
    "mars_measurement": "MEDA TIRS GROUND_TEMP",
    "measurement_class": "Surface temperature",
    "scientific_status": "VALID WITH CAVEATS",
    "reason": "Both represent surface thermal conditions. Nighttime MODIS and Mars local-time sampling are not automatically time-aligned.",
    "limitations": "Day/night categories are not exact local-solar-time matching. Satellite pixel coverage must be retained."
  },
  {
    "earth_measurement": "NASA POWER T2M",
    "mars_measurement": "MEDA TIRS GROUND_TEMP",
    "measurement_class": "Air versus surface temperature",
    "scientific_status": "NOT A DIRECT TEMPERATURE PAIRING",
    "reason": "Air temperature and surface temperature are distinct physical measurements.",
    "limitations": "Can be discussed as coupled environmental variables, but should not be presented as equivalent temperatures."
  },
  {
    "earth_measurement": "MODIS LST",
    "mars_measurement": "MEDA TIRS AIR_TEMP",
    "measurement_class": "Surface versus air temperature",
    "scientific_status": "NOT A DIRECT TEMPERATURE PAIRING",
    "reason": "Satellite surface skin temperature is not equivalent to rover-measured air temperature.",
    "limitations": "Do not combine into one temperature-overlap score."
  }
]
```

### `package/MASTER_TEMPERATURE_DATASET_INVENTORY.csv`

Extension: `.csv`; size: 0.001297 MB.
Rows: 4.
Columns: `["dataset", "file_or_source", "dataset_type", "measurement", "units", "coverage", "availability", "notes"]`.
Dtypes: `{"dataset": "str", "file_or_source": "str", "dataset_type": "str", "measurement": "str", "units": "str", "coverage": "str", "availability": "str", "notes": "str"}`.
First five rows:
```json
[
  {
    "dataset": "NASA POWER",
    "file_or_source": "NASA_POWER_T2M_all_sites.csv",
    "dataset_type": "Earth gridded meteorological product",
    "measurement": "2-metre air temperature",
    "units": "°C",
    "coverage": "July 2024; 31 daily records per site in current analysis",
    "availability": "Available",
    "notes": "Daily air temperature; not surface skin temperature."
  },
  {
    "dataset": "MODIS LST",
    "file_or_source": "MODIS_LST_daily_site_summary.csv",
    "dataset_type": "Satellite land-surface temperature product",
    "measurement": "Daytime and nighttime land-surface temperature",
    "units": "°C",
    "coverage": "July 2024; valid pixel coverage differs by site and day",
    "availability": "Available",
    "notes": "Surface temperature, not 2-m air temperature."
  },
  {
    "dataset": "Mars MEDA TIRS",
    "file_or_source": "/content/drive/MyDrive/TERRAOPS_Research/data/processed/MARS_MEDA_FULL/MASTER_DATASET/Mars_TIRS_FULL_MASTER.parquet",
    "dataset_type": "Mars rover environmental observations",
    "measurement": "Air temperature, ground temperature, irradiance and uncertainty",
    "units": "Temperature °C; uncertainty K; irradiance units require source verification",
    "coverage": "1,751 sols; 1–1,859 overall sol range",
    "availability": "Available",
    "notes": "Observation-level data aggregated by sol and local solar time."
  },
  {
    "dataset": "Mars MEDA ATS",
    "file_or_source": "/content/drive/MyDrive/TERRAOPS_Research/data/processed/MARS_MEDA_FULL/MASTER_DATASET/Mars_ATS_FULL_MASTER.parquet",
    "dataset_type": "Mars rover atmospheric temperature sensors",
    "measurement": "Five separate ATS temperature sensor measurements",
    "units": "°C after conversion",
    "coverage": "1,754 sols; 1–1,859 overall sol range",
    "availability": "Available",
    "notes": "Keep sensor channels separate unless measurement geometry supports aggregation."
  }
]
```

### `package/MASTER_TEMPERATURE_MATCHING_METHODOLOGY.csv`

Extension: `.csv`; size: 0.001180 MB.
Rows: 7.
Columns: `["step", "method", "implementation", "status"]`.
Dtypes: `{"step": "int64", "method": "str", "implementation": "str", "status": "str"}`.
First five rows:
```json
[
  {
    "step": 1,
    "method": "Measurement harmonisation",
    "implementation": "Compare NASA POWER T2M with MEDA AIR_TEMP; compare MODIS LST with MEDA GROUND_TEMP.",
    "status": "Defined"
  },
  {
    "step": 2,
    "method": "Mars seasonal assignment",
    "implementation": "Use official PDS Ls mapping and northern Mars seasons: Spring 0–90°, Summer 90–180°, Autumn 180–270°, Winter 270–360°.",
    "status": "Implemented for mapped sols"
  },
  {
    "step": 3,
    "method": "Local-time aggregation",
    "implementation": "Parse LTST, bin Mars observations into 30-minute intervals, calculate per-sol bin means, then summarise across sols.",
    "status": "Implemented"
  },
  {
    "step": 4,
    "method": "Seasonal reference envelope",
    "implementation": "Calculate Mars per-sol temperature distributions and P05–P95 reference intervals for each season.",
    "status": "Implemented"
  },
  {
    "step": 5,
    "method": "Earth comparison",
    "implementation": "Calculate the number and percentage of Earth daily observations inside the relevant Mars seasonal envelope.",
    "status": "Implemented; interpretation preliminary"
  }
]
```

### `package/MASTER_WHEN_TO_TEST_FEASIBILITY_DECISION.csv`

Extension: `.csv`; size: 0.000818 MB.
Rows: 5.
Columns: `["feature", "decision", "reason"]`.
Dtypes: `{"feature": "str", "decision": "str", "reason": "str"}`.
First five rows:
```json
[
  {
    "feature": "Seasonal Mars reference temperature",
    "decision": "FEASIBLE",
    "reason": "All four seasons have substantial contributing-sol coverage in the generated 30-minute LTST reference profiles."
  },
  {
    "feature": "Earth site temperature comparison",
    "decision": "FEASIBLE AS PRELIMINARY COMPARISON",
    "reason": "Compatible measurement classes can be compared, but Earth data currently cover one month."
  },
  {
    "feature": "Season-specific local-time matching",
    "decision": "PARTIALLY FEASIBLE",
    "reason": "Mars local-time references are available. Earth daily POWER data do not provide exact local-time matching."
  },
  {
    "feature": "Annual When-to-Test calendar",
    "decision": "NOT YET VALIDATED",
    "reason": "Earth coverage is limited to July 2024 and official quality/geometry verification remains outstanding."
  },
  {
    "feature": "Preliminary When-to-Test guidance",
    "decision": "FEASIBLE WITH EXPLICIT LIMITATIONS",
    "reason": "Can provide a preliminary seasonal comparison and identify candidate observation windows, not validated operational recommendations."
  }
]
```

### `package/MODIS_QC_flag_diagnostics.csv`

Extension: `.csv`; size: 0.012399 MB.
Rows: 186.
Columns: `["site", "date", "period", "total_pixels", "mandatory_qa_0", "mandatory_qa_1", "mandatory_qa_2", "mandatory_qa_3", "data_quality_0", "data_quality_1", "data_quality_2", "data_quality_3", "emissivity_error_0", "emissivity_error_1", "emissivity_error_2", "emissivity_error_3", "lst_error_0", "lst_error_1", "lst_error_2", "lst_error_3"]`.
Dtypes: `{"site": "str", "date": "str", "period": "str", "total_pixels": "int64", "mandatory_qa_0": "int64", "mandatory_qa_1": "int64", "mandatory_qa_2": "int64", "mandatory_qa_3": "int64", "data_quality_0": "int64", "data_quality_1": "int64", "data_quality_2": "int64", "data_quality_3": "int64", "emissivity_error_0": "int64", "emissivity_error_1": "int64", "emissivity_error_2": "int64", "emissivity_error_3": "int64", "lst_error_0": "int64", "lst_error_1": "int64", "lst_error_2": "int64", "lst_error_3": "int64"}`.
First five rows:
```json
[
  {
    "site": "Atacama",
    "date": "2024-07-01",
    "period": "day",
    "total_pixels": 234,
    "mandatory_qa_0": 164,
    "mandatory_qa_1": 67,
    "mandatory_qa_2": 3,
    "mandatory_qa_3": 0,
    "data_quality_0": 234,
    "data_quality_1": 0,
    "data_quality_2": 0,
    "data_quality_3": 0,
    "emissivity_error_0": 234,
    "emissivity_error_1": 0,
    "emissivity_error_2": 0,
    "emissivity_error_3": 0,
    "lst_error_0": 167,
    "lst_error_1": 67,
    "lst_error_2": 0,
    "lst_error_3": 0
  },
  {
    "site": "Atacama",
    "date": "2024-07-01",
    "period": "night",
    "total_pixels": 234,
    "mandatory_qa_0": 234,
    "mandatory_qa_1": 0,
    "mandatory_qa_2": 0,
    "mandatory_qa_3": 0,
    "data_quality_0": 234,
    "data_quality_1": 0,
    "data_quality_2": 0,
    "data_quality_3": 0,
    "emissivity_error_0": 234,
    "emissivity_error_1": 0,
    "emissivity_error_2": 0,
    "emissivity_error_3": 0,
    "lst_error_0": 234,
    "lst_error_1": 0,
    "lst_error_2": 0,
    "lst_error_3": 0
  },
  {
    "site": "Atacama",
    "date": "2024-07-02",
    "period": "day",
    "total_pixels": 234,
    "mandatory_qa_0": 60,
    "mandatory_qa_1": 140,
    "mandatory_qa_2": 34,
    "mandatory_qa_3": 0,
    "data_quality_0": 234,
    "data_quality_1": 0,
    "data_quality_2": 0,
    "data_quality_3": 0,
    "emissivity_error_0": 234,
    "emissivity_error_1": 0,
    "emissivity_error_2": 0,
    "emissivity_error_3": 0,
    "lst_error_0": 94,
    "lst_error_1": 140,
    "lst_error_2": 0,
    "lst_error_3": 0
  },
  {
    "site": "Atacama",
    "date": "2024-07-02",
    "period": "night",
    "total_pixels": 234,
    "mandatory_qa_0": 234,
    "mandatory_qa_1": 0,
    "mandatory_qa_2": 0,
    "mandatory_qa_3": 0,
    "data_quality_0": 234,
    "data_quality_1": 0,
    "data_quality_2": 0,
    "data_quality_3": 0,
    "emissivity_error_0": 234,
    "emissivity_error_1": 0,
    "emissivity_error_2": 0,
    "emissivity_error_3": 0,
    "lst_error_0": 234,
    "lst_error_1": 0,
    "lst_error_2": 0,
    "lst_error_3": 0
  },
  {
    "site": "Atacama",
    "date": "2024-07-03",
    "period": "day",
    "total_pixels": 234,
    "mandatory_qa_0": 26,
    "mandatory_qa_1": 135,
    "mandatory_qa_2": 73,
    "mandatory_qa_3": 0,
    "data_quality_0": 234,
    "data_quality_1": 0,
    "data_quality_2": 0,
    "data_quality_3": 0,
    "emissivity_error_0": 234,
    "emissivity_error_1": 0,
    "emissivity_error_2": 0,
    "emissivity_error_3": 0,
    "lst_error_0": 99,
    "lst_error_1": 135,
    "lst_error_2": 0,
    "lst_error_3": 0
  }
]
```

### `package/New_Terrain _metrics.txt`

Extension: `.txt`; size: 0.001655 MB.

### `package/README_TERRAOPS.md`

Extension: `.md`; size: 0.001716 MB.

### `package/temperature/documentation/66_FINAL_WORKSTREAM_UPDATE.txt`

Extension: `.txt`; size: 0.001644 MB.

### `package/temperature/documentation/FINAL_TEMPERATURE_ANALYSIS_INTERPRETATION.txt`

Extension: `.txt`; size: 0.001697 MB.

### `package/temperature/documentation/TERRAOPS_FINAL_RESEARCH_HANDOFF.txt`

Extension: `.txt`; size: 0.009132 MB.

### `package/temperature/earth/14_earth_site_temperature_summary.csv`

Extension: `.csv`; size: 0.001685 MB.
Rows: 3.
Columns: `["site", "period_start", "period_end", "total_calendar_days", "MODIS_day_valid_days", "MODIS_day_coverage_pct", "MODIS_night_valid_days", "MODIS_night_coverage_pct", "POWER_valid_days", "POWER_coverage_pct", "paired_MODIS_day_night_days", "paired_MODIS_day_POWER_days", "paired_MODIS_night_POWER_days", "MODIS_day_mean_C", "MODIS_day_median_C", "MODIS_day_std_C", "MODIS_day_min_C", "MODIS_day_max_C", "MODIS_night_mean_C", "MODIS_night_median_C", "MODIS_night_std_C", "MODIS_night_min_C", "MODIS_night_max_C", "POWER_T2M_mean_C", "POWER_T2M_median_C", "POWER_T2M_std_C", "POWER_T2M_min_C", "POWER_T2M_max_C", "mean_MODIS_day_minus_POWER_C", "mean_MODIS_night_minus_POWER_C", "mean_MODIS_day_night_range_C"]`.
Dtypes: `{"site": "str", "period_start": "str", "period_end": "str", "total_calendar_days": "int64", "MODIS_day_valid_days": "int64", "MODIS_day_coverage_pct": "float64", "MODIS_night_valid_days": "int64", "MODIS_night_coverage_pct": "float64", "POWER_valid_days": "int64", "POWER_coverage_pct": "float64", "paired_MODIS_day_night_days": "int64", "paired_MODIS_day_POWER_days": "int64", "paired_MODIS_night_POWER_days": "int64", "MODIS_day_mean_C": "float64", "MODIS_day_median_C": "float64", "MODIS_day_std_C": "float64", "MODIS_day_min_C": "float64", "MODIS_day_max_C": "float64", "MODIS_night_mean_C": "float64", "MODIS_night_median_C": "float64", "MODIS_night_std_C": "float64", "MODIS_night_min_C": "float64", "MODIS_night_max_C": "float64", "POWER_T2M_mean_C": "float64", "POWER_T2M_median_C": "float64", "POWER_T2M_std_C": "float64", "POWER_T2M_min_C": "float64", "POWER_T2M_max_C": "float64", "mean_MODIS_day_minus_POWER_C": "float64", "mean_MODIS_night_minus_POWER_C": "float64", "mean_MODIS_day_night_range_C": "float64"}`.
First five rows:
```json
[
  {
    "site": "Atacama",
    "period_start": "2024-07-01",
    "period_end": "2024-07-31",
    "total_calendar_days": 31,
    "MODIS_day_valid_days": 24,
    "MODIS_day_coverage_pct": 77.4193548387,
    "MODIS_night_valid_days": 28,
    "MODIS_night_coverage_pct": 90.3225806452,
    "POWER_valid_days": 31,
    "POWER_coverage_pct": 100.0,
    "paired_MODIS_day_night_days": 21,
    "paired_MODIS_day_POWER_days": 24,
    "paired_MODIS_night_POWER_days": 28,
    "MODIS_day_mean_C": 25.5616995565,
    "MODIS_day_median_C": 26.1324437148,
    "MODIS_day_std_C": 5.1046041287,
    "MODIS_day_min_C": 15.142826087,
    "MODIS_day_max_C": 36.0937606838,
    "MODIS_night_mean_C": 3.0061370574,
    "MODIS_night_median_C": 3.0670512821,
    "MODIS_night_std_C": 2.9886225049,
    "MODIS_night_min_C": -2.7723076923,
    "MODIS_night_max_C": 8.8803418803,
    "POWER_T2M_mean_C": 12.04,
    "POWER_T2M_median_C": 12.18,
    "POWER_T2M_std_C": 3.3888464114,
    "POWER_T2M_min_C": 4.89,
    "POWER_T2M_max_C": 16.8,
    "mean_MODIS_day_minus_POWER_C": 13.3258662231,
    "mean_MODIS_night_minus_POWER_C": -9.2792200855,
    "mean_MODIS_day_night_range_C": 22.3308391137
  },
  {
    "site": "Iceland",
    "period_start": "2024-07-01",
    "period_end": "2024-07-31",
    "total_calendar_days": 31,
    "MODIS_day_valid_days": 8,
    "MODIS_day_coverage_pct": 25.8064516129,
    "MODIS_night_valid_days": 8,
    "MODIS_night_coverage_pct": 25.8064516129,
    "POWER_valid_days": 31,
    "POWER_coverage_pct": 100.0,
    "paired_MODIS_day_night_days": 5,
    "paired_MODIS_day_POWER_days": 8,
    "paired_MODIS_night_POWER_days": 8,
    "MODIS_day_mean_C": 14.8217414655,
    "MODIS_day_median_C": 10.4165333333,
    "MODIS_day_std_C": 8.1842744444,
    "MODIS_day_min_C": 6.5005882353,
    "MODIS_day_max_C": 26.66875,
    "MODIS_night_mean_C": 2.3817085287,
    "MODIS_night_median_C": 2.0717730496,
    "MODIS_night_std_C": 1.9959470593,
    "MODIS_night_min_C": -0.02625,
    "MODIS_night_max_C": 5.59,
    "POWER_T2M_mean_C": 2.9190322581,
    "POWER_T2M_median_C": 2.8,
    "POWER_T2M_std_C": 1.1089074348,
    "POWER_T2M_min_C": 0.77,
    "POWER_T2M_max_C": 5.46,
    "mean_MODIS_day_minus_POWER_C": 11.5867414655,
    "mean_MODIS_night_minus_POWER_C": -0.6070414713,
    "mean_MODIS_day_night_range_C": 9.8767322228
  },
  {
    "site": "Ladakh",
    "period_start": "2024-07-01",
    "period_end": "2024-07-31",
    "total_calendar_days": 31,
    "MODIS_day_valid_days": 25,
    "MODIS_day_coverage_pct": 80.6451612903,
    "MODIS_night_valid_days": 23,
    "MODIS_night_coverage_pct": 74.1935483871,
    "POWER_valid_days": 31,
    "POWER_coverage_pct": 100.0,
    "paired_MODIS_day_night_days": 18,
    "paired_MODIS_day_POWER_days": 25,
    "paired_MODIS_night_POWER_days": 23,
    "MODIS_day_mean_C": 36.3725445707,
    "MODIS_day_median_C": 36.2707272727,
    "MODIS_day_std_C": 3.084671669,
    "MODIS_day_min_C": 28.7027272727,
    "MODIS_day_max_C": 41.3757004831,
    "MODIS_night_mean_C": 18.0290119614,
    "MODIS_night_median_C": 17.6157692308,
    "MODIS_night_std_C": 2.525886183,
    "MODIS_night_min_C": 11.802265625,
    "MODIS_night_max_C": 22.8822807018,
    "POWER_T2M_mean_C": 10.3725806452,
    "POWER_T2M_median_C": 10.32,
    "POWER_T2M_std_C": 2.1061924061,
    "POWER_T2M_min_C": 7.16,
    "POWER_T2M_max_C": 14.82,
    "mean_MODIS_day_minus_POWER_C": 25.9137445707,
    "mean_MODIS_night_minus_POWER_C": 7.6281423962,
    "mean_MODIS_day_night_range_C": 18.4039750289
  }
]
```

### `package/temperature/earth/14B_earth_site_temporal_coverage.csv`

Extension: `.csv`; size: 0.000144 MB.
Rows: 3.
Columns: `["site", "rows", "unique_dates", "first_date", "last_date"]`.
Dtypes: `{"site": "str", "rows": "int64", "unique_dates": "int64", "first_date": "str", "last_date": "str"}`.
First five rows:
```json
[
  {
    "site": "Atacama",
    "rows": 31,
    "unique_dates": 31,
    "first_date": "2024-07-01",
    "last_date": "2024-07-31"
  },
  {
    "site": "Iceland",
    "rows": 31,
    "unique_dates": 31,
    "first_date": "2024-07-01",
    "last_date": "2024-07-31"
  },
  {
    "site": "Ladakh",
    "rows": 31,
    "unique_dates": 31,
    "first_date": "2024-07-01",
    "last_date": "2024-07-31"
  }
]
```

### `package/temperature/earth/14D_earth_original_summary_preserved.csv`

Extension: `.csv`; size: 0.000728 MB.
Rows: 3.
Columns: `["site", "total_days", "MODIS_day_valid_days", "MODIS_day_coverage_pct", "MODIS_day_mean_C", "MODIS_day_median_C", "MODIS_day_std_C", "MODIS_day_min_C", "MODIS_day_max_C", "MODIS_night_valid_days", "MODIS_night_coverage_pct", "MODIS_night_mean_C", "MODIS_night_median_C", "MODIS_night_std_C", "MODIS_night_min_C", "MODIS_night_max_C", "paired_day_night_days", "mean_day_night_range_C", "POWER_valid_days", "POWER_mean_T2M_C", "POWER_min_T2M_C", "POWER_max_T2M_C"]`.
Dtypes: `{"site": "str", "total_days": "int64", "MODIS_day_valid_days": "int64", "MODIS_day_coverage_pct": "float64", "MODIS_day_mean_C": "float64", "MODIS_day_median_C": "float64", "MODIS_day_std_C": "float64", "MODIS_day_min_C": "float64", "MODIS_day_max_C": "float64", "MODIS_night_valid_days": "int64", "MODIS_night_coverage_pct": "float64", "MODIS_night_mean_C": "float64", "MODIS_night_median_C": "float64", "MODIS_night_std_C": "float64", "MODIS_night_min_C": "float64", "MODIS_night_max_C": "float64", "paired_day_night_days": "int64", "mean_day_night_range_C": "float64", "POWER_valid_days": "int64", "POWER_mean_T2M_C": "float64", "POWER_min_T2M_C": "float64", "POWER_max_T2M_C": "float64"}`.
First five rows:
```json
[
  {
    "site": "Atacama",
    "total_days": 31,
    "MODIS_day_valid_days": 24,
    "MODIS_day_coverage_pct": 77.42,
    "MODIS_day_mean_C": 25.562,
    "MODIS_day_median_C": 26.132,
    "MODIS_day_std_C": 5.105,
    "MODIS_day_min_C": 15.143,
    "MODIS_day_max_C": 36.094,
    "MODIS_night_valid_days": 28,
    "MODIS_night_coverage_pct": 90.32,
    "MODIS_night_mean_C": 3.006,
    "MODIS_night_median_C": 3.067,
    "MODIS_night_std_C": 2.989,
    "MODIS_night_min_C": -2.772,
    "MODIS_night_max_C": 8.88,
    "paired_day_night_days": 21,
    "mean_day_night_range_C": 22.331,
    "POWER_valid_days": 31,
    "POWER_mean_T2M_C": 12.04,
    "POWER_min_T2M_C": 4.89,
    "POWER_max_T2M_C": 16.8
  },
  {
    "site": "Iceland",
    "total_days": 31,
    "MODIS_day_valid_days": 8,
    "MODIS_day_coverage_pct": 25.81,
    "MODIS_day_mean_C": 14.822,
    "MODIS_day_median_C": 10.417,
    "MODIS_day_std_C": 8.184,
    "MODIS_day_min_C": 6.501,
    "MODIS_day_max_C": 26.669,
    "MODIS_night_valid_days": 8,
    "MODIS_night_coverage_pct": 25.81,
    "MODIS_night_mean_C": 2.382,
    "MODIS_night_median_C": 2.072,
    "MODIS_night_std_C": 1.996,
    "MODIS_night_min_C": -0.026,
    "MODIS_night_max_C": 5.59,
    "paired_day_night_days": 5,
    "mean_day_night_range_C": 9.877,
    "POWER_valid_days": 31,
    "POWER_mean_T2M_C": 2.919,
    "POWER_min_T2M_C": 0.77,
    "POWER_max_T2M_C": 5.46
  },
  {
    "site": "Ladakh",
    "total_days": 31,
    "MODIS_day_valid_days": 25,
    "MODIS_day_coverage_pct": 80.65,
    "MODIS_day_mean_C": 36.373,
    "MODIS_day_median_C": 36.271,
    "MODIS_day_std_C": 3.085,
    "MODIS_day_min_C": 28.703,
    "MODIS_day_max_C": 41.376,
    "MODIS_night_valid_days": 23,
    "MODIS_night_coverage_pct": 74.19,
    "MODIS_night_mean_C": 18.029,
    "MODIS_night_median_C": 17.616,
    "MODIS_night_std_C": 2.526,
    "MODIS_night_min_C": 11.802,
    "MODIS_night_max_C": 22.882,
    "paired_day_night_days": 18,
    "mean_day_night_range_C": 18.404,
    "POWER_valid_days": 31,
    "POWER_mean_T2M_C": 10.373,
    "POWER_min_T2M_C": 7.16,
    "POWER_max_T2M_C": 14.82
  }
]
```

### `package/temperature/earth/14E_MODIS_QC_site_period_summary.csv`

Extension: `.csv`; size: 0.001770 MB.
Rows: 6.
Columns: `["site", "period", "dates_with_QC_records", "total_pixel_observations", "mandatory_qa_0_count", "mandatory_qa_0_pct_of_pixels", "mandatory_qa_1_count", "mandatory_qa_1_pct_of_pixels", "mandatory_qa_2_count", "mandatory_qa_2_pct_of_pixels", "mandatory_qa_3_count", "mandatory_qa_3_pct_of_pixels", "data_quality_0_count", "data_quality_0_pct_of_pixels", "data_quality_1_count", "data_quality_1_pct_of_pixels", "data_quality_2_count", "data_quality_2_pct_of_pixels", "data_quality_3_count", "data_quality_3_pct_of_pixels", "lst_error_0_count", "lst_error_0_pct_of_pixels", "lst_error_1_count", "lst_error_1_pct_of_pixels", "lst_error_2_count", "lst_error_2_pct_of_pixels", "lst_error_3_count", "lst_error_3_pct_of_pixels"]`.
Dtypes: `{"site": "str", "period": "str", "dates_with_QC_records": "int64", "total_pixel_observations": "int64", "mandatory_qa_0_count": "int64", "mandatory_qa_0_pct_of_pixels": "float64", "mandatory_qa_1_count": "int64", "mandatory_qa_1_pct_of_pixels": "float64", "mandatory_qa_2_count": "int64", "mandatory_qa_2_pct_of_pixels": "float64", "mandatory_qa_3_count": "int64", "mandatory_qa_3_pct_of_pixels": "float64", "data_quality_0_count": "int64", "data_quality_0_pct_of_pixels": "float64", "data_quality_1_count": "int64", "data_quality_1_pct_of_pixels": "float64", "data_quality_2_count": "int64", "data_quality_2_pct_of_pixels": "float64", "data_quality_3_count": "int64", "data_quality_3_pct_of_pixels": "float64", "lst_error_0_count": "int64", "lst_error_0_pct_of_pixels": "float64", "lst_error_1_count": "int64", "lst_error_1_pct_of_pixels": "float64", "lst_error_2_count": "int64", "lst_error_2_pct_of_pixels": "float64", "lst_error_3_count": "int64", "lst_error_3_pct_of_pixels": "float64"}`.
First five rows:
```json
[
  {
    "site": "Atacama",
    "period": "day",
    "dates_with_QC_records": 31,
    "total_pixel_observations": 7254,
    "mandatory_qa_0_count": 4411,
    "mandatory_qa_0_pct_of_pixels": 60.8078301627,
    "mandatory_qa_1_count": 1137,
    "mandatory_qa_1_pct_of_pixels": 15.6741108354,
    "mandatory_qa_2_count": 1706,
    "mandatory_qa_2_pct_of_pixels": 23.5180590019,
    "mandatory_qa_3_count": 0,
    "mandatory_qa_3_pct_of_pixels": 0.0,
    "data_quality_0_count": 7254,
    "data_quality_0_pct_of_pixels": 100.0,
    "data_quality_1_count": 0,
    "data_quality_1_pct_of_pixels": 0.0,
    "data_quality_2_count": 0,
    "data_quality_2_pct_of_pixels": 0.0,
    "data_quality_3_count": 0,
    "data_quality_3_pct_of_pixels": 0.0,
    "lst_error_0_count": 6117,
    "lst_error_0_pct_of_pixels": 84.3258891646,
    "lst_error_1_count": 1137,
    "lst_error_1_pct_of_pixels": 15.6741108354,
    "lst_error_2_count": 0,
    "lst_error_2_pct_of_pixels": 0.0,
    "lst_error_3_count": 0,
    "lst_error_3_pct_of_pixels": 0.0
  },
  {
    "site": "Atacama",
    "period": "night",
    "dates_with_QC_records": 31,
    "total_pixel_observations": 7254,
    "mandatory_qa_0_count": 6354,
    "mandatory_qa_0_pct_of_pixels": 87.5930521092,
    "mandatory_qa_1_count": 211,
    "mandatory_qa_1_pct_of_pixels": 2.9087400055,
    "mandatory_qa_2_count": 689,
    "mandatory_qa_2_pct_of_pixels": 9.4982078853,
    "mandatory_qa_3_count": 0,
    "mandatory_qa_3_pct_of_pixels": 0.0,
    "data_quality_0_count": 7254,
    "data_quality_0_pct_of_pixels": 100.0,
    "data_quality_1_count": 0,
    "data_quality_1_pct_of_pixels": 0.0,
    "data_quality_2_count": 0,
    "data_quality_2_pct_of_pixels": 0.0,
    "data_quality_3_count": 0,
    "data_quality_3_pct_of_pixels": 0.0,
    "lst_error_0_count": 7043,
    "lst_error_0_pct_of_pixels": 97.0912599945,
    "lst_error_1_count": 211,
    "lst_error_1_pct_of_pixels": 2.9087400055,
    "lst_error_2_count": 0,
    "lst_error_2_pct_of_pixels": 0.0,
    "lst_error_3_count": 0,
    "lst_error_3_pct_of_pixels": 0.0
  },
  {
    "site": "Iceland",
    "period": "day",
    "dates_with_QC_records": 31,
    "total_pixel_observations": 3627,
    "mandatory_qa_0_count": 335,
    "mandatory_qa_0_pct_of_pixels": 9.2362834298,
    "mandatory_qa_1_count": 739,
    "mandatory_qa_1_pct_of_pixels": 20.3749655363,
    "mandatory_qa_2_count": 2553,
    "mandatory_qa_2_pct_of_pixels": 70.3887510339,
    "mandatory_qa_3_count": 0,
    "mandatory_qa_3_pct_of_pixels": 0.0,
    "data_quality_0_count": 3609,
    "data_quality_0_pct_of_pixels": 99.5037220844,
    "data_quality_1_count": 0,
    "data_quality_1_pct_of_pixels": 0.0,
    "data_quality_2_count": 18,
    "data_quality_2_pct_of_pixels": 0.4962779156,
    "data_quality_3_count": 0,
    "data_quality_3_pct_of_pixels": 0.0,
    "lst_error_0_count": 2888,
    "lst_error_0_pct_of_pixels": 79.6250344637,
    "lst_error_1_count": 739,
    "lst_error_1_pct_of_pixels": 20.3749655363,
    "lst_error_2_count": 0,
    "lst_error_2_pct_of_pixels": 0.0,
    "lst_error_3_count": 0,
    "lst_error_3_pct_of_pixels": 0.0
  },
  {
    "site": "Iceland",
    "period": "night",
    "dates_with_QC_records": 31,
    "total_pixel_observations": 3627,
    "mandatory_qa_0_count": 260,
    "mandatory_qa_0_pct_of_pixels": 7.1684587814,
    "mandatory_qa_1_count": 1033,
    "mandatory_qa_1_pct_of_pixels": 28.4808381583,
    "mandatory_qa_2_count": 2334,
    "mandatory_qa_2_pct_of_pixels": 64.3507030604,
    "mandatory_qa_3_count": 0,
    "mandatory_qa_3_pct_of_pixels": 0.0,
    "data_quality_0_count": 3598,
    "data_quality_0_pct_of_pixels": 99.2004411359,
    "data_quality_1_count": 0,
    "data_quality_1_pct_of_pixels": 0.0,
    "data_quality_2_count": 29,
    "data_quality_2_pct_of_pixels": 0.7995588641,
    "data_quality_3_count": 0,
    "data_quality_3_pct_of_pixels": 0.0,
    "lst_error_0_count": 2594,
    "lst_error_0_pct_of_pixels": 71.5191618417,
    "lst_error_1_count": 1033,
    "lst_error_1_pct_of_pixels": 28.4808381583,
    "lst_error_2_count": 0,
    "lst_error_2_pct_of_pixels": 0.0,
    "lst_error_3_count": 0,
    "lst_error_3_pct_of_pixels": 0.0
  },
  {
    "site": "Ladakh",
    "period": "day",
    "dates_with_QC_records": 31,
    "total_pixel_observations": 8060,
    "mandatory_qa_0_count": 3960,
    "mandatory_qa_0_pct_of_pixels": 49.1315136476,
    "mandatory_qa_1_count": 2328,
    "mandatory_qa_1_pct_of_pixels": 28.8833746898,
    "mandatory_qa_2_count": 1772,
    "mandatory_qa_2_pct_of_pixels": 21.9851116625,
    "mandatory_qa_3_count": 0,
    "mandatory_qa_3_pct_of_pixels": 0.0,
    "data_quality_0_count": 8057,
    "data_quality_0_pct_of_pixels": 99.9627791563,
    "data_quality_1_count": 0,
    "data_quality_1_pct_of_pixels": 0.0,
    "data_quality_2_count": 3,
    "data_quality_2_pct_of_pixels": 0.0372208437,
    "data_quality_3_count": 0,
    "data_quality_3_pct_of_pixels": 0.0,
    "lst_error_0_count": 5758,
    "lst_error_0_pct_of_pixels": 71.4392059553,
    "lst_error_1_count": 2302,
    "lst_error_1_pct_of_pixels": 28.5607940447,
    "lst_error_2_count": 0,
    "lst_error_2_pct_of_pixels": 0.0,
    "lst_error_3_count": 0,
    "lst_error_3_pct_of_pixels": 0.0
  }
]
```

### `package/temperature/earth/REVIEW_MODIS_Earth_Mars_seasonal_comparison.csv`

Extension: `.csv`; size: 0.004580 MB.
Rows: 24.
Columns: `["earth_site", "earth_variable", "mars_variable", "mars_season", "earth_observations", "mars_per_sol_observations", "mars_p05_C", "mars_p95_C", "earth_mean_C", "earth_median_C", "earth_min_C", "earth_max_C", "earth_observations_inside_band", "earth_overlap_percent"]`.
Dtypes: `{"earth_site": "str", "earth_variable": "str", "mars_variable": "str", "mars_season": "str", "earth_observations": "int64", "mars_per_sol_observations": "int64", "mars_p05_C": "float64", "mars_p95_C": "float64", "earth_mean_C": "float64", "earth_median_C": "float64", "earth_min_C": "float64", "earth_max_C": "float64", "earth_observations_inside_band": "int64", "earth_overlap_percent": "float64"}`.
First five rows:
```json
[
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS daytime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Spring",
    "earth_observations": 24,
    "mars_per_sol_observations": 528,
    "mars_p05_C": -54.2012220576,
    "mars_p95_C": -40.0062883748,
    "earth_mean_C": 25.5616995565,
    "earth_median_C": 26.1324437148,
    "earth_min_C": 15.142826087,
    "earth_max_C": 36.0937606838,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0
  },
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS daytime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Summer",
    "earth_observations": 24,
    "mars_per_sol_observations": 404,
    "mars_p05_C": -50.0903358755,
    "mars_p95_C": -36.5803662314,
    "earth_mean_C": 25.5616995565,
    "earth_median_C": 26.1324437148,
    "earth_min_C": 15.142826087,
    "earth_max_C": 36.0937606838,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0
  },
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS daytime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Autumn",
    "earth_observations": 24,
    "mars_per_sol_observations": 262,
    "mars_p05_C": -66.054188416,
    "mars_p95_C": -39.2974072871,
    "earth_mean_C": 25.5616995565,
    "earth_median_C": 26.1324437148,
    "earth_min_C": 15.142826087,
    "earth_max_C": 36.0937606838,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0
  },
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS daytime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Winter",
    "earth_observations": 24,
    "mars_per_sol_observations": 302,
    "mars_p05_C": -64.5992472305,
    "mars_p95_C": -44.9843753264,
    "earth_mean_C": 25.5616995565,
    "earth_median_C": 26.1324437148,
    "earth_min_C": 15.142826087,
    "earth_max_C": 36.0937606838,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0
  },
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS nighttime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Spring",
    "earth_observations": 28,
    "mars_per_sol_observations": 528,
    "mars_p05_C": -54.2012220576,
    "mars_p95_C": -40.0062883748,
    "earth_mean_C": 3.0061370574,
    "earth_median_C": 3.0670512821,
    "earth_min_C": -2.7723076923,
    "earth_max_C": 8.8803418803,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0
  }
]
```

### `package/temperature/mars/11_ATS_temperature_reference_by_sol.csv`

Extension: `.csv`; size: 0.693313 MB.
Rows: 1754.
Columns: `["sol", "ATS_LOCAL_TEMP1_C_mean", "ATS_LOCAL_TEMP1_C_sd", "ATS_LOCAL_TEMP1_C_min", "ATS_LOCAL_TEMP1_C_max", "ATS_LOCAL_TEMP1_C_n", "ATS_LOCAL_TEMP2_C_mean", "ATS_LOCAL_TEMP2_C_sd", "ATS_LOCAL_TEMP2_C_min", "ATS_LOCAL_TEMP2_C_max", "ATS_LOCAL_TEMP2_C_n", "ATS_LOCAL_TEMP3_C_mean", "ATS_LOCAL_TEMP3_C_sd", "ATS_LOCAL_TEMP3_C_min", "ATS_LOCAL_TEMP3_C_max", "ATS_LOCAL_TEMP3_C_n", "ATS_LOCAL_TEMP4_C_mean", "ATS_LOCAL_TEMP4_C_sd", "ATS_LOCAL_TEMP4_C_min", "ATS_LOCAL_TEMP4_C_max", "ATS_LOCAL_TEMP4_C_n", "ATS_LOCAL_TEMP5_C_mean", "ATS_LOCAL_TEMP5_C_sd", "ATS_LOCAL_TEMP5_C_min", "ATS_LOCAL_TEMP5_C_max", "ATS_LOCAL_TEMP5_C_n"]`.
Dtypes: `{"sol": "int64", "ATS_LOCAL_TEMP1_C_mean": "float64", "ATS_LOCAL_TEMP1_C_sd": "float64", "ATS_LOCAL_TEMP1_C_min": "float64", "ATS_LOCAL_TEMP1_C_max": "float64", "ATS_LOCAL_TEMP1_C_n": "int64", "ATS_LOCAL_TEMP2_C_mean": "float64", "ATS_LOCAL_TEMP2_C_sd": "float64", "ATS_LOCAL_TEMP2_C_min": "float64", "ATS_LOCAL_TEMP2_C_max": "float64", "ATS_LOCAL_TEMP2_C_n": "int64", "ATS_LOCAL_TEMP3_C_mean": "float64", "ATS_LOCAL_TEMP3_C_sd": "float64", "ATS_LOCAL_TEMP3_C_min": "float64", "ATS_LOCAL_TEMP3_C_max": "float64", "ATS_LOCAL_TEMP3_C_n": "int64", "ATS_LOCAL_TEMP4_C_mean": "float64", "ATS_LOCAL_TEMP4_C_sd": "float64", "ATS_LOCAL_TEMP4_C_min": "float64", "ATS_LOCAL_TEMP4_C_max": "float64", "ATS_LOCAL_TEMP4_C_n": "int64", "ATS_LOCAL_TEMP5_C_mean": "float64", "ATS_LOCAL_TEMP5_C_sd": "float64", "ATS_LOCAL_TEMP5_C_min": "float64", "ATS_LOCAL_TEMP5_C_max": "float64", "ATS_LOCAL_TEMP5_C_n": "int64"}`.
First five rows:
```json
[
  {
    "sol": 1,
    "ATS_LOCAL_TEMP1_C_mean": -23.6244679666,
    "ATS_LOCAL_TEMP1_C_sd": 1.9930858702,
    "ATS_LOCAL_TEMP1_C_min": -28.39,
    "ATS_LOCAL_TEMP1_C_max": -18.4,
    "ATS_LOCAL_TEMP1_C_n": 1795,
    "ATS_LOCAL_TEMP2_C_mean": -2.6983398329,
    "ATS_LOCAL_TEMP2_C_sd": 0.6769448437,
    "ATS_LOCAL_TEMP2_C_min": -5.37,
    "ATS_LOCAL_TEMP2_C_max": -0.97,
    "ATS_LOCAL_TEMP2_C_n": 1795,
    "ATS_LOCAL_TEMP3_C_mean": -20.3484456825,
    "ATS_LOCAL_TEMP3_C_sd": 1.4619083074,
    "ATS_LOCAL_TEMP3_C_min": -24.36,
    "ATS_LOCAL_TEMP3_C_max": -17.25,
    "ATS_LOCAL_TEMP3_C_n": 1795,
    "ATS_LOCAL_TEMP4_C_mean": -27.7336935933,
    "ATS_LOCAL_TEMP4_C_sd": 0.9446703788,
    "ATS_LOCAL_TEMP4_C_min": -30.5,
    "ATS_LOCAL_TEMP4_C_max": -25.58,
    "ATS_LOCAL_TEMP4_C_n": 1795,
    "ATS_LOCAL_TEMP5_C_mean": -22.6948022284,
    "ATS_LOCAL_TEMP5_C_sd": 1.4298490235,
    "ATS_LOCAL_TEMP5_C_min": -26.9,
    "ATS_LOCAL_TEMP5_C_max": -18.86,
    "ATS_LOCAL_TEMP5_C_n": 1795
  },
  {
    "sol": 2,
    "ATS_LOCAL_TEMP1_C_mean": -28.8099158654,
    "ATS_LOCAL_TEMP1_C_sd": 1.0184492436,
    "ATS_LOCAL_TEMP1_C_min": -31.5,
    "ATS_LOCAL_TEMP1_C_max": -26.3,
    "ATS_LOCAL_TEMP1_C_n": 832,
    "ATS_LOCAL_TEMP2_C_mean": -12.1843509615,
    "ATS_LOCAL_TEMP2_C_sd": 0.4042152289,
    "ATS_LOCAL_TEMP2_C_min": -15.15,
    "ATS_LOCAL_TEMP2_C_max": -11.64,
    "ATS_LOCAL_TEMP2_C_n": 832,
    "ATS_LOCAL_TEMP3_C_mean": -29.4130048077,
    "ATS_LOCAL_TEMP3_C_sd": 1.0220666918,
    "ATS_LOCAL_TEMP3_C_min": -32.03,
    "ATS_LOCAL_TEMP3_C_max": -26.79,
    "ATS_LOCAL_TEMP3_C_n": 832,
    "ATS_LOCAL_TEMP4_C_mean": -28.3002764423,
    "ATS_LOCAL_TEMP4_C_sd": 1.069356024,
    "ATS_LOCAL_TEMP4_C_min": -30.32,
    "ATS_LOCAL_TEMP4_C_max": -25.78,
    "ATS_LOCAL_TEMP4_C_n": 832,
    "ATS_LOCAL_TEMP5_C_mean": -23.8029206731,
    "ATS_LOCAL_TEMP5_C_sd": 1.0574658095,
    "ATS_LOCAL_TEMP5_C_min": -26.69,
    "ATS_LOCAL_TEMP5_C_max": -20.94,
    "ATS_LOCAL_TEMP5_C_n": 832
  },
  {
    "sol": 9,
    "ATS_LOCAL_TEMP1_C_mean": -37.7553704735,
    "ATS_LOCAL_TEMP1_C_sd": 4.8808368156,
    "ATS_LOCAL_TEMP1_C_min": -47.62,
    "ATS_LOCAL_TEMP1_C_max": -31.28,
    "ATS_LOCAL_TEMP1_C_n": 1795,
    "ATS_LOCAL_TEMP2_C_mean": -38.9547520891,
    "ATS_LOCAL_TEMP2_C_sd": 3.811808953,
    "ATS_LOCAL_TEMP2_C_min": -47.39,
    "ATS_LOCAL_TEMP2_C_max": -33.13,
    "ATS_LOCAL_TEMP2_C_n": 1795,
    "ATS_LOCAL_TEMP3_C_mean": -40.2264178273,
    "ATS_LOCAL_TEMP3_C_sd": 3.6442837347,
    "ATS_LOCAL_TEMP3_C_min": -48.45,
    "ATS_LOCAL_TEMP3_C_max": -33.1,
    "ATS_LOCAL_TEMP3_C_n": 1795,
    "ATS_LOCAL_TEMP4_C_mean": -33.5669470752,
    "ATS_LOCAL_TEMP4_C_sd": 2.9764907238,
    "ATS_LOCAL_TEMP4_C_min": -42.56,
    "ATS_LOCAL_TEMP4_C_max": -28.6,
    "ATS_LOCAL_TEMP4_C_n": 1795,
    "ATS_LOCAL_TEMP5_C_mean": -29.0987688022,
    "ATS_LOCAL_TEMP5_C_sd": 4.8527215168,
    "ATS_LOCAL_TEMP5_C_min": -43.36,
    "ATS_LOCAL_TEMP5_C_max": -22.54,
    "ATS_LOCAL_TEMP5_C_n": 1795
  },
  {
    "sol": 10,
    "ATS_LOCAL_TEMP1_C_mean": -28.7102718808,
    "ATS_LOCAL_TEMP1_C_sd": 4.6199778752,
    "ATS_LOCAL_TEMP1_C_min": -35.86,
    "ATS_LOCAL_TEMP1_C_max": -17.39,
    "ATS_LOCAL_TEMP1_C_n": 2685,
    "ATS_LOCAL_TEMP2_C_mean": -17.7313519553,
    "ATS_LOCAL_TEMP2_C_sd": 5.2440497539,
    "ATS_LOCAL_TEMP2_C_min": -34.54,
    "ATS_LOCAL_TEMP2_C_max": -12.91,
    "ATS_LOCAL_TEMP2_C_n": 2685,
    "ATS_LOCAL_TEMP3_C_mean": -30.8798919926,
    "ATS_LOCAL_TEMP3_C_sd": 2.2492963189,
    "ATS_LOCAL_TEMP3_C_min": -35.81,
    "ATS_LOCAL_TEMP3_C_max": -23.58,
    "ATS_LOCAL_TEMP3_C_n": 2685,
    "ATS_LOCAL_TEMP4_C_mean": -28.1099217877,
    "ATS_LOCAL_TEMP4_C_sd": 1.7219394634,
    "ATS_LOCAL_TEMP4_C_min": -34.07,
    "ATS_LOCAL_TEMP4_C_max": -23.53,
    "ATS_LOCAL_TEMP4_C_n": 2685,
    "ATS_LOCAL_TEMP5_C_mean": -22.3733296089,
    "ATS_LOCAL_TEMP5_C_sd": 3.0753784637,
    "ATS_LOCAL_TEMP5_C_min": -30.32,
    "ATS_LOCAL_TEMP5_C_max": -16.16,
    "ATS_LOCAL_TEMP5_C_n": 2685
  },
  {
    "sol": 14,
    "ATS_LOCAL_TEMP1_C_mean": -68.5156399132,
    "ATS_LOCAL_TEMP1_C_sd": 0.5353116448,
    "ATS_LOCAL_TEMP1_C_min": -69.5,
    "ATS_LOCAL_TEMP1_C_max": -66.2,
    "ATS_LOCAL_TEMP1_C_n": 461,
    "ATS_LOCAL_TEMP2_C_mean": -68.4756182213,
    "ATS_LOCAL_TEMP2_C_sd": 0.3896758653,
    "ATS_LOCAL_TEMP2_C_min": -69.14,
    "ATS_LOCAL_TEMP2_C_max": -66.76,
    "ATS_LOCAL_TEMP2_C_n": 461,
    "ATS_LOCAL_TEMP3_C_mean": -68.4870281996,
    "ATS_LOCAL_TEMP3_C_sd": 0.5508405211,
    "ATS_LOCAL_TEMP3_C_min": -69.4,
    "ATS_LOCAL_TEMP3_C_max": -66.11,
    "ATS_LOCAL_TEMP3_C_n": 461,
    "ATS_LOCAL_TEMP4_C_mean": -68.5333839479,
    "ATS_LOCAL_TEMP4_C_sd": 0.3364343758,
    "ATS_LOCAL_TEMP4_C_min": -69.13,
    "ATS_LOCAL_TEMP4_C_max": -67.6,
    "ATS_LOCAL_TEMP4_C_n": 461,
    "ATS_LOCAL_TEMP5_C_mean": -65.6104555315,
    "ATS_LOCAL_TEMP5_C_sd": 0.3836240357,
    "ATS_LOCAL_TEMP5_C_min": -66.71,
    "ATS_LOCAL_TEMP5_C_max": -64.61,
    "ATS_LOCAL_TEMP5_C_n": 461
  }
]
```

### `package/temperature/mars/11_Martian_season_verification.csv`

Extension: `.csv`; size: 0.000206 MB.
Rows: 1.
Columns: `["candidate_Ls_fields", "candidate_found", "verified", "seasonal_profiles_generated", "reason"]`.
Dtypes: `{"candidate_Ls_fields": "float64", "candidate_found": "bool", "verified": "bool", "seasonal_profiles_generated": "bool", "reason": "str"}`.
First five rows:
```json
[
  {
    "candidate_Ls_fields": null,
    "candidate_found": false,
    "verified": false,
    "seasonal_profiles_generated": false,
    "reason": "No solar-longitude field found in the available master schemas. Sol number alone is not used as a substitute for Ls."
  }
]
```

### `package/temperature/mars/12_TIRS_temperature_reference_by_sol.csv`

Extension: `.csv`; size: 0.280518 MB.
Rows: 1751.
Columns: `["sol", "AIR_TEMP_C_mean", "AIR_TEMP_C_sd", "AIR_TEMP_C_min", "AIR_TEMP_C_max", "AIR_TEMP_C_n", "GROUND_TEMP_C_mean", "GROUND_TEMP_C_sd", "GROUND_TEMP_C_min", "GROUND_TEMP_C_max", "GROUND_TEMP_C_n"]`.
Dtypes: `{"sol": "int64", "AIR_TEMP_C_mean": "float64", "AIR_TEMP_C_sd": "float64", "AIR_TEMP_C_min": "float64", "AIR_TEMP_C_max": "float64", "AIR_TEMP_C_n": "int64", "GROUND_TEMP_C_mean": "float64", "GROUND_TEMP_C_sd": "float64", "GROUND_TEMP_C_min": "float64", "GROUND_TEMP_C_max": "float64", "GROUND_TEMP_C_n": "int64"}`.
First five rows:
```json
[
  {
    "sol": 1,
    "AIR_TEMP_C_mean": 11.7886666667,
    "AIR_TEMP_C_sd": 4.1658440476,
    "AIR_TEMP_C_min": 4.93,
    "AIR_TEMP_C_max": 19.24,
    "AIR_TEMP_C_n": 90,
    "GROUND_TEMP_C_mean": -82.1975555556,
    "GROUND_TEMP_C_sd": 0.8066581236,
    "GROUND_TEMP_C_min": -83.85,
    "GROUND_TEMP_C_max": -80.73,
    "GROUND_TEMP_C_n": 90
  },
  {
    "sol": 2,
    "AIR_TEMP_C_mean": -25.2921884498,
    "AIR_TEMP_C_sd": 14.1505329366,
    "AIR_TEMP_C_min": -60.85,
    "AIR_TEMP_C_max": 19.21,
    "AIR_TEMP_C_n": 329,
    "GROUND_TEMP_C_mean": -19.8045288754,
    "GROUND_TEMP_C_sd": 0.7006098214,
    "GROUND_TEMP_C_min": -21.51,
    "GROUND_TEMP_C_max": -17.57,
    "GROUND_TEMP_C_n": 329
  },
  {
    "sol": 9,
    "AIR_TEMP_C_mean": -6.1962222222,
    "AIR_TEMP_C_sd": 4.4185107506,
    "AIR_TEMP_C_min": -13.58,
    "AIR_TEMP_C_max": 0.51,
    "AIR_TEMP_C_n": 90,
    "GROUND_TEMP_C_mean": -12.2163333333,
    "GROUND_TEMP_C_sd": 0.2023927098,
    "GROUND_TEMP_C_min": -12.6,
    "GROUND_TEMP_C_max": -11.86,
    "GROUND_TEMP_C_n": 90
  },
  {
    "sol": 10,
    "AIR_TEMP_C_mean": -33.3892685851,
    "AIR_TEMP_C_sd": 2.1812419898,
    "AIR_TEMP_C_min": -37.86,
    "AIR_TEMP_C_max": -27.68,
    "AIR_TEMP_C_n": 2502,
    "GROUND_TEMP_C_mean": -6.6530695444,
    "GROUND_TEMP_C_sd": 0.5132462973,
    "GROUND_TEMP_C_min": -7.61,
    "GROUND_TEMP_C_max": -5.76,
    "GROUND_TEMP_C_n": 2502
  },
  {
    "sol": 14,
    "AIR_TEMP_C_mean": -67.1562608696,
    "AIR_TEMP_C_sd": 0.6982460382,
    "AIR_TEMP_C_min": -68.62,
    "AIR_TEMP_C_max": -65.4,
    "AIR_TEMP_C_n": 230,
    "GROUND_TEMP_C_mean": -69.9913478261,
    "GROUND_TEMP_C_sd": 0.074132013,
    "GROUND_TEMP_C_min": -70.18,
    "GROUND_TEMP_C_max": -69.84,
    "GROUND_TEMP_C_n": 230
  }
]
```

### `package/temperature/mars/12B_TIRS_uncertainty_by_sol.csv`

Extension: `.csv`; size: 0.458444 MB.
Rows: 1751.
Columns: `["sol", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_mean", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_sd", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_min", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_max", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_n", "AIR_TEMP_UNCERTAINTY_mean", "AIR_TEMP_UNCERTAINTY_sd", "AIR_TEMP_UNCERTAINTY_min", "AIR_TEMP_UNCERTAINTY_max", "AIR_TEMP_UNCERTAINTY_n", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_mean", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_sd", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_min", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_max", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_n", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_mean", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_sd", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_min", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_max", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_n", "GROUND_TEMP_UNCERTAINTY_mean", "GROUND_TEMP_UNCERTAINTY_sd", "GROUND_TEMP_UNCERTAINTY_min", "GROUND_TEMP_UNCERTAINTY_max", "GROUND_TEMP_UNCERTAINTY_n"]`.
Dtypes: `{"sol": "int64", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_mean": "float64", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_sd": "float64", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_min": "float64", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_max": "float64", "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_n": "int64", "AIR_TEMP_UNCERTAINTY_mean": "float64", "AIR_TEMP_UNCERTAINTY_sd": "float64", "AIR_TEMP_UNCERTAINTY_min": "float64", "AIR_TEMP_UNCERTAINTY_max": "float64", "AIR_TEMP_UNCERTAINTY_n": "int64", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_mean": "float64", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_sd": "float64", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_min": "float64", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_max": "float64", "UPWARD_SW_IRRADIANCE_UNCERTAINTY_n": "int64", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_mean": "float64", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_sd": "float64", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_min": "float64", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_max": "float64", "UPWARD_LW_IRRADIANCE_UNCERTAINTY_n": "int64", "GROUND_TEMP_UNCERTAINTY_mean": "float64", "GROUND_TEMP_UNCERTAINTY_sd": "float64", "GROUND_TEMP_UNCERTAINTY_min": "float64", "GROUND_TEMP_UNCERTAINTY_max": "float64", "GROUND_TEMP_UNCERTAINTY_n": "int64"}`.
First five rows:
```json
[
  {
    "sol": 1,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 5.0041111111,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 0.0121687059,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_min": 4.98,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_max": 5.02,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_n": 90,
    "AIR_TEMP_UNCERTAINTY_mean": 1.6737777778,
    "AIR_TEMP_UNCERTAINTY_sd": 0.2517202736,
    "AIR_TEMP_UNCERTAINTY_min": 1.27,
    "AIR_TEMP_UNCERTAINTY_max": 2.12,
    "AIR_TEMP_UNCERTAINTY_n": 90,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_mean": 6.2838888889,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_sd": 0.0872642177,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_min": 6.13,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_max": 6.43,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_n": 90,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 2.6123333333,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 0.0128997866,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_min": 2.59,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_max": 2.64,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_n": 90,
    "GROUND_TEMP_UNCERTAINTY_mean": 3.9525555556,
    "GROUND_TEMP_UNCERTAINTY_sd": 0.0926702637,
    "GROUND_TEMP_UNCERTAINTY_min": 3.79,
    "GROUND_TEMP_UNCERTAINTY_max": 4.14,
    "GROUND_TEMP_UNCERTAINTY_n": 90
  },
  {
    "sol": 2,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 4.5246808511,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 0.0358601403,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_min": 4.41,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_max": 4.59,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_n": 329,
    "AIR_TEMP_UNCERTAINTY_mean": 1.4838601824,
    "AIR_TEMP_UNCERTAINTY_sd": 0.4889791431,
    "AIR_TEMP_UNCERTAINTY_min": 0.65,
    "AIR_TEMP_UNCERTAINTY_max": 4.46,
    "AIR_TEMP_UNCERTAINTY_n": 329,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_mean": 1.8818844985,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_sd": 0.1739150305,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_min": 1.53,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_max": 2.46,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_n": 329,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 0.7299088146,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 0.0119062989,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_min": 0.7,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_max": 0.76,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_n": 329,
    "GROUND_TEMP_UNCERTAINTY_mean": 0.3789665653,
    "GROUND_TEMP_UNCERTAINTY_sd": 0.0091479426,
    "GROUND_TEMP_UNCERTAINTY_min": 0.35,
    "GROUND_TEMP_UNCERTAINTY_max": 0.4,
    "GROUND_TEMP_UNCERTAINTY_n": 329
  },
  {
    "sol": 9,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 2.9325555556,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 0.0161844086,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_min": 2.91,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_max": 2.96,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_n": 90,
    "AIR_TEMP_UNCERTAINTY_mean": 1.9951111111,
    "AIR_TEMP_UNCERTAINTY_sd": 0.2592956945,
    "AIR_TEMP_UNCERTAINTY_min": 1.56,
    "AIR_TEMP_UNCERTAINTY_max": 2.39,
    "AIR_TEMP_UNCERTAINTY_n": 90,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_mean": 3.9962222222,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_sd": 0.0538115266,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_min": 3.9,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_max": 4.09,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_n": 90,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 1.2137777778,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 0.0115707669,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_min": 1.19,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_max": 1.23,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_n": 90,
    "GROUND_TEMP_UNCERTAINTY_mean": 0.5556666667,
    "GROUND_TEMP_UNCERTAINTY_sd": 0.0049831176,
    "GROUND_TEMP_UNCERTAINTY_min": 0.55,
    "GROUND_TEMP_UNCERTAINTY_max": 0.56,
    "GROUND_TEMP_UNCERTAINTY_n": 90
  },
  {
    "sol": 10,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 4.1173341327,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 0.0617106489,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_min": 4.0,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_max": 4.24,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_n": 2502,
    "AIR_TEMP_UNCERTAINTY_mean": 1.2858513189,
    "AIR_TEMP_UNCERTAINTY_sd": 0.1308715543,
    "AIR_TEMP_UNCERTAINTY_min": 0.92,
    "AIR_TEMP_UNCERTAINTY_max": 1.57,
    "AIR_TEMP_UNCERTAINTY_n": 2502,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_mean": 3.0309872102,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_sd": 0.0449134473,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_min": 2.95,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_max": 3.13,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_n": 2502,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 0.9703796962,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 0.051732632,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_min": 0.89,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_max": 1.05,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_n": 2502,
    "GROUND_TEMP_UNCERTAINTY_mean": 0.4226818545,
    "GROUND_TEMP_UNCERTAINTY_sd": 0.0192055815,
    "GROUND_TEMP_UNCERTAINTY_min": 0.39,
    "GROUND_TEMP_UNCERTAINTY_max": 0.45,
    "GROUND_TEMP_UNCERTAINTY_n": 2502
  },
  {
    "sol": 14,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 1.0174347826,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 0.0043766559,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_min": 1.01,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_max": 1.02,
    "DOWNWARD_LW_IRRADIANCE_UNCERTAINTY_n": 230,
    "AIR_TEMP_UNCERTAINTY_mean": 0.7233043478,
    "AIR_TEMP_UNCERTAINTY_sd": 0.0051563738,
    "AIR_TEMP_UNCERTAINTY_min": 0.72,
    "AIR_TEMP_UNCERTAINTY_max": 0.74,
    "AIR_TEMP_UNCERTAINTY_n": 230,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_mean": 0.0927826087,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_sd": 0.0044911998,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_min": 0.09,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_max": 0.1,
    "UPWARD_SW_IRRADIANCE_UNCERTAINTY_n": 230,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_mean": 0.33,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_sd": 6.8e-09,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_min": 0.33,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_max": 0.33,
    "UPWARD_LW_IRRADIANCE_UNCERTAINTY_n": 230,
    "GROUND_TEMP_UNCERTAINTY_mean": 0.3995652174,
    "GROUND_TEMP_UNCERTAINTY_sd": 0.002043759,
    "GROUND_TEMP_UNCERTAINTY_min": 0.39,
    "GROUND_TEMP_UNCERTAINTY_max": 0.4,
    "GROUND_TEMP_UNCERTAINTY_n": 230
  }
]
```

### `package/temperature/mars/19_mars_sol_reference_validation.csv`

Extension: `.csv`; size: 0.000163 MB.
Rows: 3.
Columns: `["dataset", "rows", "unique_sols", "first_sol", "last_sol", "duplicate_sol_rows", "missing_sol_values"]`.
Dtypes: `{"dataset": "str", "rows": "int64", "unique_sols": "int64", "first_sol": "int64", "last_sol": "int64", "duplicate_sol_rows": "int64", "missing_sol_values": "int64"}`.
First five rows:
```json
[
  {
    "dataset": "ATS",
    "rows": 1754,
    "unique_sols": 1754,
    "first_sol": 1,
    "last_sol": 1859,
    "duplicate_sol_rows": 0,
    "missing_sol_values": 0
  },
  {
    "dataset": "TIRS",
    "rows": 1751,
    "unique_sols": 1751,
    "first_sol": 1,
    "last_sol": 1859,
    "duplicate_sol_rows": 0,
    "missing_sol_values": 0
  },
  {
    "dataset": "TIRS uncertainty",
    "rows": 1751,
    "unique_sols": 1751,
    "first_sol": 1,
    "last_sol": 1859,
    "duplicate_sol_rows": 0,
    "missing_sol_values": 0
  }
]
```

### `package/temperature/mars/38_MARS_SEASONAL_TEMPERATURE_COVERAGE.csv`

Extension: `.csv`; size: 0.000303 MB.
Rows: 4.
Columns: `["northern_season", "sol_count", "first_sol", "last_sol", "mean_Ls_deg", "min_Ls_deg", "max_Ls_deg"]`.
Dtypes: `{"northern_season": "str", "sol_count": "int64", "first_sol": "int64", "last_sol": "int64", "mean_Ls_deg": "float64", "min_Ls_deg": "float64", "max_Ls_deg": "float64"}`.
First five rows:
```json
[
  {
    "northern_season": "Northern Autumn",
    "sol_count": 264,
    "first_sol": 362,
    "last_sol": 1172,
    "mean_Ls_deg": 223.9864583333,
    "min_Ls_deg": 180.09,
    "max_Ls_deg": 269.68
  },
  {
    "northern_season": "Northern Spring",
    "sol_count": 340,
    "first_sol": 1,
    "last_sol": 851,
    "mean_Ls_deg": 47.7118823529,
    "min_Ls_deg": 0.04,
    "max_Ls_deg": 89.87
  },
  {
    "northern_season": "Northern Summer",
    "sol_count": 337,
    "first_sol": 184,
    "last_sol": 1029,
    "mean_Ls_deg": 134.4891246291,
    "min_Ls_deg": 90.32,
    "max_Ls_deg": 179.97
  },
  {
    "northern_season": "Northern Winter",
    "sol_count": 238,
    "first_sol": 504,
    "last_sol": 1258,
    "mean_Ls_deg": 309.5231932773,
    "min_Ls_deg": 270.04,
    "max_Ls_deg": 359.54
  }
]
```

### `package/temperature/mars/53_FINAL_MARS_SEASONAL_TEMPERATURE_SUMMARY.csv`

Extension: `.csv`; size: 0.003997 MB.
Rows: 4.
Columns: `["northern_season", "sol_count", "first_sol", "last_sol", "mean_Ls_deg", "min_Ls_deg", "max_Ls_deg", "ATS_LOCAL_TEMP1_C_mean_mean", "ATS_LOCAL_TEMP1_C_sd_mean", "ATS_LOCAL_TEMP1_C_min_mean", "ATS_LOCAL_TEMP1_C_max_mean", "ATS_LOCAL_TEMP1_C_n_mean", "ATS_LOCAL_TEMP2_C_mean_mean", "ATS_LOCAL_TEMP2_C_sd_mean", "ATS_LOCAL_TEMP2_C_min_mean", "ATS_LOCAL_TEMP2_C_max_mean", "ATS_LOCAL_TEMP2_C_n_mean", "ATS_LOCAL_TEMP3_C_mean_mean", "ATS_LOCAL_TEMP3_C_sd_mean", "ATS_LOCAL_TEMP3_C_min_mean", "ATS_LOCAL_TEMP3_C_max_mean", "ATS_LOCAL_TEMP3_C_n_mean", "ATS_LOCAL_TEMP4_C_mean_mean", "ATS_LOCAL_TEMP4_C_sd_mean", "ATS_LOCAL_TEMP4_C_min_mean", "ATS_LOCAL_TEMP4_C_max_mean", "ATS_LOCAL_TEMP4_C_n_mean", "ATS_LOCAL_TEMP5_C_mean_mean", "ATS_LOCAL_TEMP5_C_sd_mean", "ATS_LOCAL_TEMP5_C_min_mean", "ATS_LOCAL_TEMP5_C_max_mean", "ATS_LOCAL_TEMP5_C_n_mean", "AIR_TEMP_C_mean_mean", "AIR_TEMP_C_sd_mean", "AIR_TEMP_C_min_mean", "AIR_TEMP_C_max_mean", "AIR_TEMP_C_n_mean", "GROUND_TEMP_C_mean_mean", "GROUND_TEMP_C_sd_mean", "GROUND_TEMP_C_min_mean", "GROUND_TEMP_C_max_mean", "GROUND_TEMP_C_n_mean", "ATS_Ls_deg_mean", "TIRS_Ls_deg_mean", "ANC_Ls_deg_mean", "ATS_TIRS_difference_deg_mean"]`.
Dtypes: `{"northern_season": "str", "sol_count": "int64", "first_sol": "int64", "last_sol": "int64", "mean_Ls_deg": "float64", "min_Ls_deg": "float64", "max_Ls_deg": "float64", "ATS_LOCAL_TEMP1_C_mean_mean": "float64", "ATS_LOCAL_TEMP1_C_sd_mean": "float64", "ATS_LOCAL_TEMP1_C_min_mean": "float64", "ATS_LOCAL_TEMP1_C_max_mean": "float64", "ATS_LOCAL_TEMP1_C_n_mean": "float64", "ATS_LOCAL_TEMP2_C_mean_mean": "float64", "ATS_LOCAL_TEMP2_C_sd_mean": "float64", "ATS_LOCAL_TEMP2_C_min_mean": "float64", "ATS_LOCAL_TEMP2_C_max_mean": "float64", "ATS_LOCAL_TEMP2_C_n_mean": "float64", "ATS_LOCAL_TEMP3_C_mean_mean": "float64", "ATS_LOCAL_TEMP3_C_sd_mean": "float64", "ATS_LOCAL_TEMP3_C_min_mean": "float64", "ATS_LOCAL_TEMP3_C_max_mean": "float64", "ATS_LOCAL_TEMP3_C_n_mean": "float64", "ATS_LOCAL_TEMP4_C_mean_mean": "float64", "ATS_LOCAL_TEMP4_C_sd_mean": "float64", "ATS_LOCAL_TEMP4_C_min_mean": "float64", "ATS_LOCAL_TEMP4_C_max_mean": "float64", "ATS_LOCAL_TEMP4_C_n_mean": "float64", "ATS_LOCAL_TEMP5_C_mean_mean": "float64", "ATS_LOCAL_TEMP5_C_sd_mean": "float64", "ATS_LOCAL_TEMP5_C_min_mean": "float64", "ATS_LOCAL_TEMP5_C_max_mean": "float64", "ATS_LOCAL_TEMP5_C_n_mean": "float64", "AIR_TEMP_C_mean_mean": "float64", "AIR_TEMP_C_sd_mean": "float64", "AIR_TEMP_C_min_mean": "float64", "AIR_TEMP_C_max_mean": "float64", "AIR_TEMP_C_n_mean": "float64", "GROUND_TEMP_C_mean_mean": "float64", "GROUND_TEMP_C_sd_mean": "float64", "GROUND_TEMP_C_min_mean": "float64", "GROUND_TEMP_C_max_mean": "float64", "GROUND_TEMP_C_n_mean": "float64", "ATS_Ls_deg_mean": "float64", "TIRS_Ls_deg_mean": "float64", "ANC_Ls_deg_mean": "float64", "ATS_TIRS_difference_deg_mean": "float64"}`.
First five rows:
```json
[
  {
    "northern_season": "Northern Autumn",
    "sol_count": 264,
    "first_sol": 362,
    "last_sol": 1172,
    "mean_Ls_deg": 223.9863762626,
    "min_Ls_deg": 180.09,
    "max_Ls_deg": 269.68,
    "ATS_LOCAL_TEMP1_C_mean_mean": -53.829705638,
    "ATS_LOCAL_TEMP1_C_sd_mean": 19.0965526927,
    "ATS_LOCAL_TEMP1_C_min_mean": -79.0776893939,
    "ATS_LOCAL_TEMP1_C_max_mean": -13.2227272727,
    "ATS_LOCAL_TEMP1_C_n_mean": 49612.7234848485,
    "ATS_LOCAL_TEMP2_C_mean_mean": -52.9207698796,
    "ATS_LOCAL_TEMP2_C_sd_mean": 18.150741554,
    "ATS_LOCAL_TEMP2_C_min_mean": -77.8028787879,
    "ATS_LOCAL_TEMP2_C_max_mean": -12.9037878788,
    "ATS_LOCAL_TEMP2_C_n_mean": 49612.0492424242,
    "ATS_LOCAL_TEMP3_C_mean_mean": -51.9296301383,
    "ATS_LOCAL_TEMP3_C_sd_mean": 20.3802977036,
    "ATS_LOCAL_TEMP3_C_min_mean": -78.2798484848,
    "ATS_LOCAL_TEMP3_C_max_mean": -8.1048106061,
    "ATS_LOCAL_TEMP3_C_n_mean": 49612.0492424242,
    "ATS_LOCAL_TEMP4_C_mean_mean": -48.1585699682,
    "ATS_LOCAL_TEMP4_C_sd_mean": 21.71092864,
    "ATS_LOCAL_TEMP4_C_min_mean": -75.596780303,
    "ATS_LOCAL_TEMP4_C_max_mean": -6.3202651515,
    "ATS_LOCAL_TEMP4_C_n_mean": 49612.9886363636,
    "ATS_LOCAL_TEMP5_C_mean_mean": -51.2966011631,
    "ATS_LOCAL_TEMP5_C_sd_mean": 19.8329027494,
    "ATS_LOCAL_TEMP5_C_min_mean": -76.8924242424,
    "ATS_LOCAL_TEMP5_C_max_mean": -13.7562878788,
    "ATS_LOCAL_TEMP5_C_n_mean": 49612.0492424242,
    "AIR_TEMP_C_mean_mean": -56.7755215055,
    "AIR_TEMP_C_sd_mean": 14.7023533536,
    "AIR_TEMP_C_min_mean": -79.4695038168,
    "AIR_TEMP_C_max_mean": -23.9869847328,
    "AIR_TEMP_C_n_mean": 48194.5534351145,
    "GROUND_TEMP_C_mean_mean": -51.8614618995,
    "GROUND_TEMP_C_sd_mean": 25.5141197592,
    "GROUND_TEMP_C_min_mean": -79.9302290076,
    "GROUND_TEMP_C_max_mean": -4.1566030534,
    "GROUND_TEMP_C_n_mean": 48194.5534351145,
    "ATS_Ls_deg_mean": 223.9862121212,
    "TIRS_Ls_deg_mean": 223.8245419847,
    "ANC_Ls_deg_mean": 223.9862121212,
    "ATS_TIRS_difference_deg_mean": -0.0004961832
  },
  {
    "northern_season": "Northern Spring",
    "sol_count": 528,
    "first_sol": 1,
    "last_sol": 1519,
    "mean_Ls_deg": 46.9609659091,
    "min_Ls_deg": 0.04,
    "max_Ls_deg": 89.87,
    "ATS_LOCAL_TEMP1_C_mean_mean": -53.3454220066,
    "ATS_LOCAL_TEMP1_C_sd_mean": 17.5113671654,
    "ATS_LOCAL_TEMP1_C_min_mean": -78.524375,
    "ATS_LOCAL_TEMP1_C_max_mean": -17.5075189394,
    "ATS_LOCAL_TEMP1_C_n_mean": 59846.9867424242,
    "ATS_LOCAL_TEMP2_C_mean_mean": -52.0966361792,
    "ATS_LOCAL_TEMP2_C_sd_mean": 17.0244381399,
    "ATS_LOCAL_TEMP2_C_min_mean": -76.8423295455,
    "ATS_LOCAL_TEMP2_C_max_mean": -17.2121590909,
    "ATS_LOCAL_TEMP2_C_n_mean": 59847.2784090909,
    "ATS_LOCAL_TEMP3_C_mean_mean": -52.2518470015,
    "ATS_LOCAL_TEMP3_C_sd_mean": 17.5484789341,
    "ATS_LOCAL_TEMP3_C_min_mean": -77.2519128788,
    "ATS_LOCAL_TEMP3_C_max_mean": -16.5098106061,
    "ATS_LOCAL_TEMP3_C_n_mean": 59847.2045454545,
    "ATS_LOCAL_TEMP4_C_mean_mean": -48.4685315622,
    "ATS_LOCAL_TEMP4_C_sd_mean": 19.2309444462,
    "ATS_LOCAL_TEMP4_C_min_mean": -74.6120454545,
    "ATS_LOCAL_TEMP4_C_max_mean": -13.9926704545,
    "ATS_LOCAL_TEMP4_C_n_mean": 59846.5170454545,
    "ATS_LOCAL_TEMP5_C_mean_mean": -49.3850260141,
    "ATS_LOCAL_TEMP5_C_sd_mean": 19.9915535392,
    "ATS_LOCAL_TEMP5_C_min_mean": -75.7791287879,
    "ATS_LOCAL_TEMP5_C_max_mean": -12.2276136364,
    "ATS_LOCAL_TEMP5_C_n_mean": 59847.4564393939,
    "AIR_TEMP_C_mean_mean": -56.5945314049,
    "AIR_TEMP_C_sd_mean": 14.1681860627,
    "AIR_TEMP_C_min_mean": -78.3199621212,
    "AIR_TEMP_C_max_mean": -20.633030303,
    "AIR_TEMP_C_n_mean": 46913.2727272727,
    "GROUND_TEMP_C_mean_mean": -47.5453354771,
    "GROUND_TEMP_C_sd_mean": 26.6884818802,
    "GROUND_TEMP_C_min_mean": -78.7807765152,
    "GROUND_TEMP_C_max_mean": -3.9109280303,
    "GROUND_TEMP_C_n_mean": 46913.2727272727,
    "ATS_Ls_deg_mean": 46.9609090909,
    "TIRS_Ls_deg_mean": 46.9609090909,
    "ANC_Ls_deg_mean": 46.9610795455,
    "ATS_TIRS_difference_deg_mean": 0.0
  },
  {
    "northern_season": "Northern Summer",
    "sol_count": 432,
    "first_sol": 184,
    "last_sol": 1619,
    "mean_Ls_deg": 129.7357021605,
    "min_Ls_deg": 90.15,
    "max_Ls_deg": 179.97,
    "ATS_LOCAL_TEMP1_C_mean_mean": -49.7521846268,
    "ATS_LOCAL_TEMP1_C_sd_mean": 19.5435823743,
    "ATS_LOCAL_TEMP1_C_min_mean": -76.225625,
    "ATS_LOCAL_TEMP1_C_max_mean": -10.7228703704,
    "ATS_LOCAL_TEMP1_C_n_mean": 51334.525462963,
    "ATS_LOCAL_TEMP2_C_mean_mean": -48.7634380263,
    "ATS_LOCAL_TEMP2_C_sd_mean": 18.5793149865,
    "ATS_LOCAL_TEMP2_C_min_mean": -74.5396296296,
    "ATS_LOCAL_TEMP2_C_max_mean": -11.5694675926,
    "ATS_LOCAL_TEMP2_C_n_mean": 51335.0532407407,
    "ATS_LOCAL_TEMP3_C_mean_mean": -48.7103186224,
    "ATS_LOCAL_TEMP3_C_sd_mean": 19.0735391724,
    "ATS_LOCAL_TEMP3_C_min_mean": -75.1331712963,
    "ATS_LOCAL_TEMP3_C_max_mean": -10.7079398148,
    "ATS_LOCAL_TEMP3_C_n_mean": 51335.099537037,
    "ATS_LOCAL_TEMP4_C_mean_mean": -44.7176480366,
    "ATS_LOCAL_TEMP4_C_sd_mean": 20.5549837506,
    "ATS_LOCAL_TEMP4_C_min_mean": -71.9640509259,
    "ATS_LOCAL_TEMP4_C_max_mean": -8.2504861111,
    "ATS_LOCAL_TEMP4_C_n_mean": 51333.900462963,
    "ATS_LOCAL_TEMP5_C_mean_mean": -45.6379974127,
    "ATS_LOCAL_TEMP5_C_sd_mean": 21.8049219616,
    "ATS_LOCAL_TEMP5_C_min_mean": -73.2879861111,
    "ATS_LOCAL_TEMP5_C_max_mean": -5.490162037,
    "ATS_LOCAL_TEMP5_C_n_mean": 51334.8263888889,
    "AIR_TEMP_C_mean_mean": -53.1496107384,
    "AIR_TEMP_C_sd_mean": 14.9618256849,
    "AIR_TEMP_C_min_mean": -75.2806264501,
    "AIR_TEMP_C_max_mean": -18.0684222738,
    "AIR_TEMP_C_n_mean": 50854.9582366589,
    "GROUND_TEMP_C_mean_mean": -44.3217490432,
    "GROUND_TEMP_C_sd_mean": 26.5198981932,
    "GROUND_TEMP_C_min_mean": -75.3435962877,
    "GROUND_TEMP_C_max_mean": 0.0730858469,
    "GROUND_TEMP_C_n_mean": 50854.9582366589,
    "ATS_Ls_deg_mean": 129.7356944444,
    "TIRS_Ls_deg_mean": 129.7161881188,
    "ANC_Ls_deg_mean": 129.7779118329,
    "ATS_TIRS_difference_deg_mean": -2.47525e-05
  },
  {
    "northern_season": "Northern Winter",
    "sol_count": 302,
    "first_sol": 504,
    "last_sol": 1326,
    "mean_Ls_deg": 316.2858940397,
    "min_Ls_deg": 270.04,
    "max_Ls_deg": 359.96,
    "ATS_LOCAL_TEMP1_C_mean_mean": -56.3136576315,
    "ATS_LOCAL_TEMP1_C_sd_mean": 20.3344632102,
    "ATS_LOCAL_TEMP1_C_min_mean": -83.2861589404,
    "ATS_LOCAL_TEMP1_C_max_mean": -15.0100331126,
    "ATS_LOCAL_TEMP1_C_n_mean": 31725.4503311258,
    "ATS_LOCAL_TEMP2_C_mean_mean": -56.500465006,
    "ATS_LOCAL_TEMP2_C_sd_mean": 18.258488366,
    "ATS_LOCAL_TEMP2_C_min_mean": -82.1601655629,
    "ATS_LOCAL_TEMP2_C_max_mean": -18.3685761589,
    "ATS_LOCAL_TEMP2_C_n_mean": 31725.4503311258,
    "ATS_LOCAL_TEMP3_C_mean_mean": -56.1551177957,
    "ATS_LOCAL_TEMP3_C_sd_mean": 18.9879946623,
    "ATS_LOCAL_TEMP3_C_min_mean": -82.2121854305,
    "ATS_LOCAL_TEMP3_C_max_mean": -15.1885761589,
    "ATS_LOCAL_TEMP3_C_n_mean": 31725.4503311258,
    "ATS_LOCAL_TEMP4_C_mean_mean": -50.9192370265,
    "ATS_LOCAL_TEMP4_C_sd_mean": 21.4347515948,
    "ATS_LOCAL_TEMP4_C_min_mean": -79.2591390728,
    "ATS_LOCAL_TEMP4_C_max_mean": -10.5162251656,
    "ATS_LOCAL_TEMP4_C_n_mean": 31726.2715231788,
    "ATS_LOCAL_TEMP5_C_mean_mean": -53.400726324,
    "ATS_LOCAL_TEMP5_C_sd_mean": 22.3892984609,
    "ATS_LOCAL_TEMP5_C_min_mean": -81.5807615894,
    "ATS_LOCAL_TEMP5_C_max_mean": -11.0773178808,
    "ATS_LOCAL_TEMP5_C_n_mean": 31725.4503311258,
    "AIR_TEMP_C_mean_mean": -62.1723551599,
    "AIR_TEMP_C_sd_mean": 14.4630615534,
    "AIR_TEMP_C_min_mean": -84.2186423841,
    "AIR_TEMP_C_max_mean": -29.8440066225,
    "AIR_TEMP_C_n_mean": 31385.2880794702,
    "GROUND_TEMP_C_mean_mean": -55.0777984112,
    "GROUND_TEMP_C_sd_mean": 26.6944731014,
    "GROUND_TEMP_C_min_mean": -85.301986755,
    "GROUND_TEMP_C_max_mean": -8.9333443709,
    "GROUND_TEMP_C_n_mean": 31385.2880794702,
    "ATS_Ls_deg_mean": 316.2858940397,
    "TIRS_Ls_deg_mean": 316.2858940397,
    "ANC_Ls_deg_mean": 316.2858940397,
    "ATS_TIRS_difference_deg_mean": 0.0
  }
]
```

### `package/temperature/validation/10_measurement_comparability_matrix.csv`

Extension: `.csv`; size: 0.000586 MB.
Rows: 4.
Columns: `["Earth_variable", "Mars_variable", "measurement_class", "status", "caveat"]`.
Dtypes: `{"Earth_variable": "str", "Mars_variable": "str", "measurement_class": "str", "status": "str", "caveat": "str"}`.
First five rows:
```json
[
  {
    "Earth_variable": "POWER T2M",
    "Mars_variable": "MEDA TIRS AIR_TEMP",
    "measurement_class": "Air temperature",
    "status": "Potentially comparable",
    "caveat": "Different height, spatial footprint, sampling and atmospheric conditions. Requires documented harmonisation."
  },
  {
    "Earth_variable": "MODIS LST",
    "Mars_variable": "MEDA TIRS GROUND_TEMP",
    "measurement_class": "Surface temperature",
    "status": "Potentially comparable",
    "caveat": "Different retrieval/instrument footprints and surface conditions."
  },
  {
    "Earth_variable": "MODIS LST",
    "Mars_variable": "MEDA TIRS AIR_TEMP",
    "measurement_class": "Surface versus air",
    "status": "Not directly comparable",
    "caveat": "Different physical measurement quantities."
  },
  {
    "Earth_variable": "POWER T2M",
    "Mars_variable": "MEDA TIRS GROUND_TEMP",
    "measurement_class": "Air versus surface",
    "status": "Not directly comparable",
    "caveat": "Different physical measurement quantities."
  }
]
```

### `package/temperature/validation/25_FINAL_EARTH_MARS_COMPARABILITY_MATRIX.csv`

Extension: `.csv`; size: 0.001254 MB.
Rows: 5.
Columns: `["Earth_site_measurement", "Mars_measurement", "physical_quantity", "comparison_status", "reason", "required_caveat"]`.
Dtypes: `{"Earth_site_measurement": "str", "Mars_measurement": "str", "physical_quantity": "str", "comparison_status": "str", "reason": "str", "required_caveat": "str"}`.
First five rows:
```json
[
  {
    "Earth_site_measurement": "MODIS daytime LST",
    "Mars_measurement": "MEDA TIRS GROUND_TEMP",
    "physical_quantity": "Surface temperature",
    "comparison_status": "Potentially comparable",
    "reason": "Both represent surface temperature, but retrieval methods, spatial footprints, observation timing and surface properties differ.",
    "required_caveat": "Compare harmonized distributions and observation conditions; do not assume identical measurement geometry."
  },
  {
    "Earth_site_measurement": "MODIS nighttime LST",
    "Mars_measurement": "MEDA TIRS GROUND_TEMP",
    "physical_quantity": "Surface temperature",
    "comparison_status": "Potentially comparable",
    "reason": "Both are surface temperature measurements, subject to different local times and sampling conditions.",
    "required_caveat": "Nighttime observation timing and coverage must be considered."
  },
  {
    "Earth_site_measurement": "POWER T2M",
    "Mars_measurement": "MEDA TIRS AIR_TEMP",
    "physical_quantity": "Near-surface air temperature",
    "comparison_status": "Potentially comparable",
    "reason": "Both represent atmospheric temperature, but spatial resolution, measurement height and instrument characteristics differ.",
    "required_caveat": "Height and temporal aggregation must be harmonized where possible."
  },
  {
    "Earth_site_measurement": "MODIS LST",
    "Mars_measurement": "MEDA TIRS AIR_TEMP",
    "physical_quantity": "Surface versus air temperature",
    "comparison_status": "Not directly comparable",
    "reason": "Different physical measurement quantities.",
    "required_caveat": "Do not interpret differences as direct climate similarity."
  },
  {
    "Earth_site_measurement": "POWER T2M",
    "Mars_measurement": "MEDA TIRS GROUND_TEMP",
    "physical_quantity": "Air versus surface temperature",
    "comparison_status": "Not directly comparable",
    "reason": "Different physical measurement quantities.",
    "required_caveat": "Keep atmospheric and surface comparison tracks separate."
  }
]
```

### `package/temperature/validation/28_FINAL_OUTPUT_MANIFEST.csv`

Extension: `.csv`; size: 0.002836 MB.
Rows: 52.
Columns: `["category", "filename", "size_bytes", "size_KB", "nonempty"]`.
Dtypes: `{"category": "str", "filename": "str", "size_bytes": "int64", "size_KB": "float64", "nonempty": "bool"}`.
First five rows:
```json
[
  {
    "category": "report",
    "filename": "01_mars_download_inventory.csv",
    "size_bytes": 389,
    "size_KB": 0.38,
    "nonempty": true
  },
  {
    "category": "report",
    "filename": "02_earth_drive_candidates.csv",
    "size_bytes": 6055,
    "size_KB": 5.91,
    "nonempty": true
  },
  {
    "category": "report",
    "filename": "02_resolved_dataset_paths.csv",
    "size_bytes": 169,
    "size_KB": 0.17,
    "nonempty": true
  },
  {
    "category": "report",
    "filename": "03_MEDA_schema_and_metadata_inventory.csv",
    "size_bytes": 1,
    "size_KB": 0.0,
    "nonempty": true
  },
  {
    "category": "report",
    "filename": "03_pds_label_candidates.csv",
    "size_bytes": 1,
    "size_KB": 0.0,
    "nonempty": true
  }
]
```

### `package/temperature/validation/FINAL_REVISED_SCIENTIFIC_LIMITATIONS_REGISTER.csv`

Extension: `.csv`; size: 0.002621 MB.
Rows: 10.
Columns: `["topic", "status", "finding", "next_action"]`.
Dtypes: `{"topic": "str", "status": "str", "finding": "str", "next_action": "str"}`.
First five rows:
```json
[
  {
    "topic": "Earth temporal window",
    "status": "Limited",
    "finding": "The current Earth temperature comparison covers July 2024, not a full annual climatology.",
    "next_action": "Extend Earth observations across seasons before making annual suitability claims."
  },
  {
    "topic": "Iceland MODIS coverage",
    "status": "Limited",
    "finding": "Only 8 of 31 days have valid daytime and 8 of 31 have valid nighttime MODIS observations.",
    "next_action": "Treat Iceland surface temperature estimates as lower-coverage descriptive evidence."
  },
  {
    "topic": "Martian seasonal reference",
    "status": "Partial — 87.001% coverage",
    "finding": "Official PDS Ls reference coverage is available for 1,526 of 1,754 ATS sols. The remaining 228 sols are unresolved and have not been interpolated.",
    "next_action": "Recover missing Ls values only from an authoritative PDS source; preserve unresolved sols as missing."
  },
  {
    "topic": "MEDA geometry",
    "status": "Partially verified",
    "finding": "Available index metadata do not independently establish dynamic sensor pointing or terrain footprint.",
    "next_action": "Verify instrument mounting, boresight, FOV, frame and ancillary geometry against authoritative documentation."
  },
  {
    "topic": "ATS-TIRS time alignment",
    "status": "Provisional — dataset files not located",
    "finding": "SCLK-derived minute-bin matching was previously reported, but the matched and height-aware Parquet files were not located in the current Google Drive project search. Exact clock coincidence is not established.",
    "next_action": "Recover and verify the original matched datasets before including them as downloadable integration artifacts."
  }
]
```

### `package/temperature/validation/handover/05_EARTH_MARS_FINAL_RECALCULATED_TABLE.csv`

Extension: `.csv`; size: 0.005358 MB.
Rows: 24.
Columns: `["earth_site", "earth_variable", "mars_variable", "mars_season", "earth_observations", "mars_per_sol_observations", "mars_p05_C", "mars_p95_C", "earth_mean_C", "earth_median_C", "earth_min_C", "earth_max_C", "earth_observations_inside_band", "earth_overlap_percent", "comparison_class", "earth_range_overlaps_mars_5_95_percentile", "earth_range_overlap_fraction_percent"]`.
Dtypes: `{"earth_site": "str", "earth_variable": "str", "mars_variable": "str", "mars_season": "str", "earth_observations": "int64", "mars_per_sol_observations": "int64", "mars_p05_C": "float64", "mars_p95_C": "float64", "earth_mean_C": "float64", "earth_median_C": "float64", "earth_min_C": "float64", "earth_max_C": "float64", "earth_observations_inside_band": "int64", "earth_overlap_percent": "float64", "comparison_class": "str", "earth_range_overlaps_mars_5_95_percentile": "bool", "earth_range_overlap_fraction_percent": "float64"}`.
First five rows:
```json
[
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS daytime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Spring",
    "earth_observations": 24,
    "mars_per_sol_observations": 528,
    "mars_p05_C": -54.2012220576,
    "mars_p95_C": -40.0062883748,
    "earth_mean_C": 25.5616995565,
    "earth_median_C": 26.1324437148,
    "earth_min_C": 15.142826087,
    "earth_max_C": 36.0937606838,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0,
    "comparison_class": "SURFACE_TEMPERATURE",
    "earth_range_overlaps_mars_5_95_percentile": false,
    "earth_range_overlap_fraction_percent": 0.0
  },
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS daytime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Summer",
    "earth_observations": 24,
    "mars_per_sol_observations": 404,
    "mars_p05_C": -50.0903358755,
    "mars_p95_C": -36.5803662314,
    "earth_mean_C": 25.5616995565,
    "earth_median_C": 26.1324437148,
    "earth_min_C": 15.142826087,
    "earth_max_C": 36.0937606838,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0,
    "comparison_class": "SURFACE_TEMPERATURE",
    "earth_range_overlaps_mars_5_95_percentile": false,
    "earth_range_overlap_fraction_percent": 0.0
  },
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS daytime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Autumn",
    "earth_observations": 24,
    "mars_per_sol_observations": 262,
    "mars_p05_C": -66.054188416,
    "mars_p95_C": -39.2974072871,
    "earth_mean_C": 25.5616995565,
    "earth_median_C": 26.1324437148,
    "earth_min_C": 15.142826087,
    "earth_max_C": 36.0937606838,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0,
    "comparison_class": "SURFACE_TEMPERATURE",
    "earth_range_overlaps_mars_5_95_percentile": false,
    "earth_range_overlap_fraction_percent": 0.0
  },
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS daytime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Winter",
    "earth_observations": 24,
    "mars_per_sol_observations": 302,
    "mars_p05_C": -64.5992472305,
    "mars_p95_C": -44.9843753264,
    "earth_mean_C": 25.5616995565,
    "earth_median_C": 26.1324437148,
    "earth_min_C": 15.142826087,
    "earth_max_C": 36.0937606838,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0,
    "comparison_class": "SURFACE_TEMPERATURE",
    "earth_range_overlaps_mars_5_95_percentile": false,
    "earth_range_overlap_fraction_percent": 0.0
  },
  {
    "earth_site": "Atacama",
    "earth_variable": "MODIS nighttime LST",
    "mars_variable": "TIRS ground temperature",
    "mars_season": "Northern Spring",
    "earth_observations": 28,
    "mars_per_sol_observations": 528,
    "mars_p05_C": -54.2012220576,
    "mars_p95_C": -40.0062883748,
    "earth_mean_C": 3.0061370574,
    "earth_median_C": 3.0670512821,
    "earth_min_C": -2.7723076923,
    "earth_max_C": 8.8803418803,
    "earth_observations_inside_band": 0,
    "earth_overlap_percent": 0.0,
    "comparison_class": "SURFACE_TEMPERATURE",
    "earth_range_overlaps_mars_5_95_percentile": false,
    "earth_range_overlap_fraction_percent": 0.0
  }
]
```

### `package/temperature/validation/handover/06_EARTH_MARS_COMPARISON_CLASS_SUMMARY.csv`

Extension: `.csv`; size: 0.000051 MB.
Rows: 1.
Columns: `["comparison_class", "rows", "sites"]`.
Dtypes: `{"comparison_class": "str", "rows": "int64", "sites": "int64"}`.
First five rows:
```json
[
  {
    "comparison_class": "SURFACE_TEMPERATURE",
    "rows": 24,
    "sites": 3
  }
]
```

### `package/temperature/validation/handover/FINAL_HANDOVER_SUMMARY.txt`

Extension: `.txt`; size: 0.002437 MB.

### `package/temperature/validation/handover/FINAL_THREE_STREAM_CLOSURE_REPORT.md`

Extension: `.md`; size: 0.001663 MB.

### `package/temperature/validation/validation2/FINAL_DRIVE_TRANSFER_MANIFEST.json`

Extension: `.json`; size: 0.079623 MB.

### `package/temperature/validation/validation2/FINAL_HANDOVER_SUMMARY.txt`

Extension: `.txt`; size: 0.002437 MB.

### `package/Terrain_metrics.txt`

Extension: `.txt`; size: 0.004899 MB.

### `package/TERRAOPS_Data_Dictionary.csv`

Extension: `.csv`; size: 0.009857 MB.
Rows: 105.
Columns: `["dataset", "column", "description", "unit", "data_type"]`.
Dtypes: `{"dataset": "str", "column": "str", "description": "str", "unit": "str", "data_type": "str"}`.
First five rows:
```json
[
  {
    "dataset": "Earth_temperature_daily_analysis.csv",
    "column": "site",
    "description": "Refer to original dataset documentation",
    "unit": "Not specified",
    "data_type": null
  },
  {
    "dataset": "Earth_temperature_daily_analysis.csv",
    "column": "date",
    "description": "Refer to original dataset documentation",
    "unit": "Not specified",
    "data_type": null
  },
  {
    "dataset": "Earth_temperature_daily_analysis.csv",
    "column": "day_mean_C",
    "description": "Temperature converted to Celsius",
    "unit": "°C",
    "data_type": null
  },
  {
    "dataset": "Earth_temperature_daily_analysis.csv",
    "column": "day_valid_pixels",
    "description": "Refer to original dataset documentation",
    "unit": "Not specified",
    "data_type": null
  },
  {
    "dataset": "Earth_temperature_daily_analysis.csv",
    "column": "night_mean_C",
    "description": "Temperature converted to Celsius",
    "unit": "°C",
    "data_type": null
  }
]
```

### `package/TERRAOPS_Data_Sources.csv`

Extension: `.csv`; size: 0.000351 MB.
Rows: 4.
Columns: `["dataset", "source", "url"]`.
Dtypes: `{"dataset": "str", "source": "str", "url": "str"}`.
First five rows:
```json
[
  {
    "dataset": "Mars MEDA ATS and TIRS",
    "source": "NASA Mars 2020 MEDA calibrated environmental archive",
    "url": "https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/data_calibrated_env/"
  },
  {
    "dataset": "MODIS",
    "source": "NASA MODIS",
    "url": "https://modis.gsfc.nasa.gov/data/"
  },
  {
    "dataset": "NASA POWER",
    "source": "NASA POWER",
    "url": "https://power.larc.nasa.gov/"
  },
  {
    "dataset": "Copernicus DEM",
    "source": "Copernicus Data Space Ecosystem",
    "url": "https://dataspace.copernicus.eu/"
  }
]
```

### `package/TERRAOPS_TEMPERATURE_ANALYSIS_FINAL_DOCUMENTATION.md`

Extension: `.md`; size: 0.003654 MB.

### `package/TERRAOPS_Transfer_Manifest.csv`

Extension: `.csv`; size: 0.009556 MB.
Rows: 76.
Columns: `["filename", "category", "folder", "size_bytes", "drive_file_id", "status"]`.
Dtypes: `{"filename": "str", "category": "str", "folder": "str", "size_bytes": "int64", "drive_file_id": "str", "status": "str"}`.
First five rows:
```json
[
  {
    "filename": "Earth_temperature_daily_analysis.csv",
    "category": "Earth processed dataset",
    "folder": "Earth",
    "size_bytes": 10228,
    "drive_file_id": "1lD459WsiHAjWivsTfRW_mgAUZ5P71dEt",
    "status": "Already uploaded (same size)"
  },
  {
    "filename": "Earth_temperature_summary_July2024.csv",
    "category": "Earth processed dataset",
    "folder": "Earth",
    "size_bytes": 763,
    "drive_file_id": "1gRe0RHwntrNug17BKY1tYArYnpUgMnXL",
    "status": "Already uploaded (same size)"
  },
  {
    "filename": "MODIS_QC_flag_diagnostics.csv",
    "category": "Earth processed dataset",
    "folder": "Earth",
    "size_bytes": 13001,
    "drive_file_id": "10ybzniyP4QXSQyBZPrcdfxYc9E48Ff2w",
    "status": "Already uploaded (same size)"
  },
  {
    "filename": "Mars_ATS_FULL_MASTER.parquet",
    "category": "Mars master dataset",
    "folder": "Mars",
    "size_bytes": 2857288345,
    "drive_file_id": "1Tif6At431IyDMP3XnyGzqnaZP_Jay4kF",
    "status": "Uploaded and verified"
  },
  {
    "filename": "Mars_TIRS_FULL_MASTER.parquet",
    "category": "Mars master dataset",
    "folder": "Mars",
    "size_bytes": 1611910319,
    "drive_file_id": "1jJveqP3jbdmGUVsKmmjJaqq-IYlScGKW",
    "status": "Uploaded and verified"
  }
]
```
