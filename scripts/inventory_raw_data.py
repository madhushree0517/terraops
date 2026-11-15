import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


INVENTORY_COLUMNS = (
    "relative_path", "extension", "size_mb", "crs", "pixel_size", "resolution", "bounds",
    "nodata", "dtype", "statistics", "layers", "geometry_type", "feature_count",
    "columns", "row_count", "dtypes", "variables", "time_range", "csv_preview_first_5", "schema",
    "preview_first_100", "error",
)
RASTER_EXTENSIONS = {".tif", ".tiff"}
TIME_COLUMN_PATTERN = re.compile(r"time|date|datetime|timestamp|period|year", re.I)


def _json_value(value: Any) -> Any:
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _inspect_raster(path: Path, row: dict[str, Any]) -> None:
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import Window

    with rasterio.open(path) as dataset:
        row["crs"] = str(dataset.crs) if dataset.crs else ""
        row["pixel_size"] = json.dumps(dataset.res)
        row["resolution"] = row["pixel_size"]
        row["bounds"] = json.dumps(list(dataset.bounds))
        row["nodata"] = json.dumps(list(dataset.nodatavals))
        row["dtype"] = json.dumps(list(dataset.dtypes))
        band_stats = []
        for band_index in range(1, dataset.count + 1):
            overviews = dataset.overviews(band_index)
            if overviews:
                factor = max(overviews)
                height = max(1, math.ceil(dataset.height / factor))
                width = max(1, math.ceil(dataset.width / factor))
                values = dataset.read(
                    band_index, out_shape=(height, width),
                    resampling=Resampling.nearest, masked=True,
                )
                method = f"overview_factor_{factor}"
            else:
                window = Window(0, 0, min(dataset.width, 1024), min(dataset.height, 1024))
                values = dataset.read(band_index, window=window, masked=True)
                method = "top_left_window_max_1024x1024"
            valid = values.compressed()
            stats = {"band": band_index, "method": method, "sampled_valid_pixels": int(valid.size)}
            if valid.size:
                stats.update(
                    minimum=_json_value(valid.min()), maximum=_json_value(valid.max()),
                    mean=_json_value(valid.mean()), std=_json_value(valid.std()),
                )
            band_stats.append(stats)
        row["statistics"] = json.dumps(band_stats, ensure_ascii=False)


def _inspect_geopackage(path: Path, row: dict[str, Any]) -> None:
    import geopandas as gpd
    import pyogrio

    layer_rows = []
    layer_names = [str(name) for name, _ in pyogrio.list_layers(path)]
    for layer_name in layer_names:
        info = pyogrio.read_info(path, layer=layer_name)
        layer_rows.append({
            "layer": layer_name,
            "crs": info.get("crs") or "",
            "geometry_type": info.get("geometry_type") or "",
            "feature_count": int(info.get("features", -1)),
            "columns": [str(column) for column in info.get("fields", [])],
        })
    row["layers"] = json.dumps(layer_rows, ensure_ascii=False)
    if layer_names:
        frame = gpd.read_file(path, layer=layer_names[0], rows=0)
        row["crs"] = str(frame.crs) if frame.crs else ""
        row["geometry_type"] = layer_rows[0]["geometry_type"]
        row["feature_count"] = layer_rows[0]["feature_count"]
        row["columns"] = json.dumps([str(column) for column in frame.columns])


def _inspect_geojson(path: Path, row: dict[str, Any]) -> None:
    import geopandas as gpd

    frame = gpd.read_file(path)
    row["crs"] = str(frame.crs) if frame.crs else ""
    row["geometry_type"] = json.dumps(
        sorted(str(value) for value in frame.geometry.geom_type.dropna().unique())
    )
    row["feature_count"] = int(len(frame))
    row["columns"] = json.dumps([str(column) for column in frame.columns])


def _inspect_json(path: Path, row: dict[str, Any]) -> None:
    with path.open(encoding="utf-8") as source:
        value = json.load(source)
    if isinstance(value, dict):
        row["columns"] = json.dumps([str(key) for key in value.keys()], ensure_ascii=False)
        row["row_count"] = len(value)
    elif isinstance(value, list):
        row["row_count"] = len(value)
        if value and isinstance(value[0], dict):
            row["columns"] = json.dumps([str(key) for key in value[0].keys()], ensure_ascii=False)
    row["schema"] = json.dumps(
        {"root_type": type(value).__name__}, ensure_ascii=False
    )


def _inspect_csv(path: Path, row: dict[str, Any]) -> None:
    frame = pd.read_csv(path)
    row["columns"] = json.dumps([str(column) for column in frame.columns])
    row["row_count"] = int(len(frame))
    row["dtypes"] = json.dumps(
        {str(column): str(dtype) for column, dtype in frame.dtypes.items()}, ensure_ascii=False
    )
    row["csv_preview_first_5"] = frame.head(5).to_json(
        orient="records", date_format="iso", force_ascii=False
    )
    time_ranges = {}
    for column in frame.columns:
        if not TIME_COLUMN_PATTERN.search(str(column)):
            continue
        parsed = pd.to_datetime(frame[column], format="mixed", errors="coerce", utc=True).dropna()
        if not parsed.empty:
            time_ranges[str(column)] = [parsed.min().isoformat(), parsed.max().isoformat()]
    if time_ranges:
        row["time_range"] = json.dumps(time_ranges, ensure_ascii=False)


def _inspect_netcdf(path: Path, row: dict[str, Any]) -> None:
    import xarray as xr

    with xr.open_dataset(path) as dataset:
        variables = [str(name) for name in (*dataset.data_vars, *dataset.coords)]
        row["variables"] = json.dumps(variables, ensure_ascii=False)
        time_ranges = {}
        for name in dataset.variables:
            if not TIME_COLUMN_PATTERN.search(str(name)):
                continue
            parsed = pd.to_datetime(dataset[name].values.ravel(), format="mixed", errors="coerce", utc=True).dropna()
            if not parsed.empty:
                time_ranges[str(name)] = [parsed.min().isoformat(), parsed.max().isoformat()]
        if time_ranges:
            row["time_range"] = json.dumps(time_ranges, ensure_ascii=False)


def _inspect_parquet(path: Path, row: dict[str, Any]) -> None:
    import pyarrow.parquet as pq

    parquet_file = pq.ParquetFile(path)
    row["schema"] = str(parquet_file.schema_arrow)
    row["row_count"] = int(parquet_file.metadata.num_rows)
    row["columns"] = json.dumps(parquet_file.schema_arrow.names, ensure_ascii=False)
    row["dtypes"] = json.dumps(
        {field.name: str(field.type) for field in parquet_file.schema_arrow}, ensure_ascii=False
    )
    preview_batch = next(parquet_file.iter_batches(batch_size=100), None)
    row["preview_first_100"] = "[]" if preview_batch is None else json.dumps(
        preview_batch.to_pylist(), ensure_ascii=False,
        default=lambda value: value.isoformat() if hasattr(value, "isoformat") else str(value),
    )


def inventory_raw_data(
    raw_dir: str | Path | None = None,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    project_root = Path(__file__).resolve().parents[1]
    source_dir = Path(raw_dir) if raw_dir is not None else project_root / "data" / "raw"
    destination = Path(output_path) if output_path is not None else project_root / "data" / "raw_inventory.csv"
    paths = sorted(path for path in source_dir.rglob("*") if path.is_file()) if source_dir.is_dir() else []
    rows = []
    for path in paths:
        row = {column: "" for column in INVENTORY_COLUMNS}
        row.update(relative_path=path.relative_to(source_dir).as_posix(), extension=path.suffix.lower())
        try:
            row["size_mb"] = round(path.stat().st_size / (1024 * 1024), 6)
            extension = path.suffix.lower()
            if extension == ".crdownload":
                row["error"] = "Incomplete download (.crdownload); inspection skipped."
            elif extension in RASTER_EXTENSIONS:
                _inspect_raster(path, row)
            elif extension == ".gpkg":
                _inspect_geopackage(path, row)
            elif extension == ".geojson":
                _inspect_geojson(path, row)
            elif extension == ".json":
                _inspect_json(path, row)
            elif extension == ".csv":
                _inspect_csv(path, row)
            elif extension == ".parquet":
                _inspect_parquet(path, row)
            elif extension in {".nc", ".netcdf"}:
                _inspect_netcdf(path, row)
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)
    inventory = pd.DataFrame(rows, columns=INVENTORY_COLUMNS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(destination, index=False)
    return inventory


def write_raw_data_report(inventory: pd.DataFrame, project_root: Path | None = None) -> Path:
    """Write the evidence-led raw report, including each CSV schema and first rows."""
    root = project_root or Path(__file__).resolve().parents[1]
    report_path = root / "docs" / "RAW_DATA_REPORT.md"
    raw_root = root / "data" / "raw"
    lines = [
        "# Raw Data Report",
        "",
        "Generated from `data/raw/` by `python -m scripts.inventory_raw_data`. "
        "No raw source file is modified.",
        "",
        f"Inventory file count: **{len(inventory)}**. Incomplete `.crdownload` files: "
        f"**{int(inventory['extension'].eq('.crdownload').sum())}**. Inventory read errors: "
        f"**{int(inventory['error'].fillna('').astype(str).ne('').sum())}**.",
        "",
        "## Documentation Findings",
        "",
        "The package includes `README_TERRAOPS.md`, `Earth_Data_Methodology.md`, "
        "`Mars_MEDA_Methodology.md`, `Data_Quality_and_Limitations.md`, "
        "`TERRAOPS_TEMPERATURE_ANALYSIS_FINAL_DOCUMENTATION.md`, and "
        "`ASHWARYA_TEMPERATURE_ANALYSIS_UPDATE.txt`. The requested final files are in "
        "`package/temperature/documentation/` and `package/temperature/validation/`; "
        "there are no `.docx` files.",
        "",
        "### Final handoff and status notes",
        "",
        "`66_FINAL_WORKSTREAM_UPDATE.txt` states ATS 88,656,007 observations/1,754 sols; "
        "TIRS 80,882,439 observations/1,751 sols; and 1,526 of 1,754 temperature-reference "
        "sols with sourced Ls (87.001%), with 228 unresolved. "
        "`TERRAOPS_FINAL_RESEARCH_HANDOFF.txt` contains earlier Ls figures (1,179/1,754, "
        "67.218%) and, in later embedded verification sections, ATS 1,526 Ls records and "
        "TIRS 1,496 Ls records. Its later final consolidated status again says 1,526 of "
        "1,754 sols and 87.001%. These figures refer to different instrument/index stages "
        "and are retained as stated, not reconciled by inference.",
        "",
        "Both copies of `FINAL_HANDOVER_SUMMARY.txt` have the same SHA-256 "
        "`CC61ECD68763F05DC6BCAC337AA85B2E985AA119635ADE8F937B9721B4ED67CB`; they are identical. "
        "That handover reports 113 SPICE kernels loaded, 52 text-declared frame IDs recognized, "
        "84 CK files and 15 CK object IDs, but explicitly says MEDA/TIRS-specific frames/time "
        "coverage were not established. `FINAL_THREE_STREAM_CLOSURE_REPORT.md` instead marks "
        "all three closure streams `Scientific pass: NO`, flags MEDA polarity for context "
        "review, Earth–Mars comparison as exploratory scope-limited, and SPICE geometry "
        "`ERROR_OR_DOWNLOAD_BLOCKED` with `SpiceTYPEMISMATCH()`.",
        "",
        "The revised limitations register says the 293 K threshold is a chosen screening "
        "threshold, not an instrument operating limit; the matched Parquet artifacts were "
        "not located in its Drive search even though matched Parquet files are present in "
        "this local raw tree. These are different statements and both are retained.",
        "",
        "`FINAL_TEMPERATURE_ANALYSIS_INTERPRETATION.txt` says the main ATS/TIRS and Earth "
        "descriptive processing is complete, but seasonal Ls coverage is partial, flag "
        "interpretation requires PDS definitions, dynamic geometry remains unverified, and "
        "no habitat-suitability ranking is claimed. It specifically distinguishes MODIS "
        "surface skin temperature from POWER near-surface air temperature and MEDA channel roles.",
        "",
        "`FINAL_THREE_STREAM_CLOSURE_REPORT.md` retains 24 recalculated rows, all classified "
        "`SURFACE_TEMPERATURE`, and states the comparison is exploratory, not a simultaneous "
        "matched-site experiment or causal climatic-equivalence claim. The recalculated file "
        "uses MODIS LST versus TIRS ground temperature. This differs in scope from the older "
        "air-to-air POWER T2M/TIRS AIR_TEMP pairing; both measurement classes must remain separate.",
        "",
        "### Terrain",
        "",
        "`New_Terrain _metrics.txt` records whole-raster QGIS slope statistics for the "
        "preferred Askja/Atacama/Ladakh reprojected slope files. The older `Terrain_metrics.txt` "
        "records superseded slope/roughness and Copernicus GLO30 DEM statistics. The newer "
        "package has preferred reprojected slope and roughness TIFFs for Askja, Atacama and "
        "Ladakh; no Jezero slope or roughness TIFF exists. Statistics describe whole raster "
        "extents, not a separately validated field boundary. "
        "The aggregate `site_boundaries.gpkg` has zero features. The individual `Extent_*.gpkg` "
        "files are rectangular raster extents. The Jezero extent has coordinates "
        "0..1865 and -1495..0 despite an EPSG:4326 label, so it is not usable as a geographic "
        "boundary. No Jezero slope/roughness TIFF or DEM statistics are supplied.",
        "",
        "New_Terrain _metrics slope values are quoted exactly from its raw QGIS output:",
        "",
        "| Site | Metric | Count | Min | Max | Mean | Std dev |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        "| Askja | Reprojected slope | 6880248 | 0.0 | 87.40215301513672 | 3.676787553963025 | 7.0877596636742535 |",
        "| Atacama | Reprojected slope | 12996764 | 0.0 | 89.41896057128906 | 6.412182581141583 | 7.9977308509604566 |",
        "| Ladakh | Reprojected slope | 13360659 | 0.0 | 89.53579711914063 | 26.551391952664954 | 14.788001085014608 |",
        "",
        "| Site | DEM source evidence | Projected base-raster pixel size | CRS status |",
        "| --- | --- | ---: | --- |",
        "| Askja | Copernicus GLO30 named in older Terrain_metrics input; reprojected base TIFF present | 29.99818936288092 × 29.998189339968448 map units | EPSG:32727 area of use excludes Askja at about 65°N; suspect and skipped by builder |",
        "| Atacama | Copernicus GLO30 named in older Terrain_metrics input; reprojected base TIFF present | 29.680407648073597 × 29.680407671745545 m | EPSG:32719; CRS area of use contains site |",
        "| Ladakh | Copernicus GLO30 named in older Terrain_metrics input; reprojected base TIFF present | 28.294190637152262 × 28.294190652337008 m | EPSG:32643; CRS area of use contains site |",
        "| Iceland | No Iceland-named terrain/DEM raster; Askja is a separate raw label | Not available | Not available |",
        "| Jezero | No DEM/slope/roughness raster; Jezero extent is invalid under EPSG:4326 | Not available | Not valid geographic extent |",
        "",
        "The preferred reprojected TIFF rows below are inventory samples from a top-left "
        "1024×1024 window (or overview where present), not whole-raster or extent statistics:",
        "",
        "The raw notes do not define the roughness algorithm/window size or explicit units for "
        "the slope/roughness rasters. TIFF metadata gives CRS, pixel size and nodata below. "
        "The DEM inputs named in Terrain_metrics are not themselves included as TIFFs, so an "
        "exact per-site DEM pixel size cannot be read from this package.",
        "",
        "### Temperature Definitions and Periods",
        "",
        "The final documentation and scientific comparison matrix identify NASA POWER T2M "
        "(2-m near-surface air temperature) versus MEDA TIRS AIR_TEMP as the air-to-air "
        "pairing. MODIS daytime/nighttime LST is surface temperature and pairs only with "
        "MEDA TIRS GROUND_TEMP, with caveats. ATS is a distinct air-temperature instrument "
        "with five separate channels; the documentation says to keep channels separate "
        "unless measurement geometry supports aggregation.",
        "",
        "Earth data cover **2024-07-01 through 2024-07-31** (31 daily rows per site). "
        "TIRS coverage is documented as 1,751 sols over Sol 1–1859; ATS as 1,754 sols "
        "over Sol 1–1859. Official Ls mapping is documented for 1,496 of 1,751 TIRS sols. "
        "Four northern Mars seasons and 48 half-hour LTST bins per season are documented; "
        "the minimum contributing-sol rule is 10 per bin. The newer recalculated "
        "surface comparison explicitly supplies seasonal TIRS GROUND_TEMP P05–P95 bounds:",
        "",
        "| Northern season | TIRS GROUND_TEMP P05 (°C) | TIRS GROUND_TEMP P95 (°C) |",
        "| --- | ---: | ---: |",
        "| Spring | -54.20122205756504 | -40.00628837476505 |",
        "| Summer | -50.0903358755237 | -36.58036623135518 |",
        "| Autumn | -66.0541884160499 | -39.297407287068815 |",
        "| Winter | -64.59924723051415 | -44.98437532637752 |",
        "",
        "These are season-specific surface-temperature bounds, not air-temperature thresholds. "
        "No single global envelope was stated; the report does not collapse these seasonal "
        "values into one range.",
        "",
        "| Earth site label | MODIS day valid / 31 | Day coverage | MODIS night valid / 31 | Night coverage | POWER valid / 31 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        "| Atacama | 24 | 77.42% | 28 | 90.32% | 31 |",
        "| Iceland | 8 | 25.81% | 8 | 25.81% | 31 |",
        "| Ladakh | 25 | 80.65% | 23 | 74.19% | 31 |",
        "",
        "MODIS valid-pixel coverage varies by site/day. Earth daily local-time matching is not "
        "established. MEDA flag fractions are descriptive only; official flag semantics, "
        "SCLK units/time correlation, solar/rover geometry and irradiance definitions remain "
        "unverified. Statistical outlier thresholds are diagnostic, not instrument limits. "
        "Sol 367 is retained and no temperature interpolation is performed across its gap. "
        "The current Earth data do not support a validated annual testing calendar.",
        "",
        "## File-by-File Inventory",
        "",
    ]

    preferred_tiffs = inventory.loc[
        inventory["relative_path"].astype(str).str.contains(r"_Reprojected.*\.tif$", regex=True)
    ].sort_values("relative_path")
    if not preferred_tiffs.empty:
        lines.extend([
            "### Preferred reprojected TIFF inventory samples",
            "",
            "| File | CRS | Pixel size | Sample method | Valid sample pixels | Min | Max | Mean | Std dev |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ])
        for row in preferred_tiffs.to_dict(orient="records"):
            try:
                stats = json.loads(row["statistics"])[0]
            except (TypeError, ValueError, IndexError, KeyError):
                stats = {}
            lines.append(
                f"| `{row['relative_path']}` | {row['crs']} | `{row['pixel_size']}` | "
                f"{stats.get('method', '')} | {stats.get('sampled_valid_pixels', '')} | "
                f"{stats.get('minimum', '')} | {stats.get('maximum', '')} | "
                f"{stats.get('mean', '')} | {stats.get('std', '')} |"
            )
        lines.append("")

    inventory_by_path = inventory.set_index("relative_path", drop=False)
    for path in sorted(raw_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(raw_root).as_posix()
        row = inventory_by_path.loc[relative]
        lines.extend([f"### `{relative}`", "", f"Extension: `{path.suffix.lower() or '[none]'}`; size: {path.stat().st_size / (1024 * 1024):.6f} MB."])
        if path.suffix.lower() == ".csv":
            lines.extend([
                f"Rows: {row['row_count']}.",
                f"Columns: `{row['columns']}`.",
                f"Dtypes: `{row['dtypes']}`.",
                "First five rows:",
                "```json",
                json.dumps(json.loads(row["csv_preview_first_5"] or "[]"), ensure_ascii=False, indent=2, default=str),
                "```",
            ])
        elif path.suffix.lower() in RASTER_EXTENSIONS:
            lines.append(
                f"CRS: `{row['crs']}`; pixel size: `{row['pixel_size']}`; bounds: "
                f"`{row['bounds']}`; nodata: `{row['nodata']}`; dtype: `{row['dtype']}`."
            )
            lines.append(f"Window/overview statistics: `{row['statistics']}`.")
        elif path.suffix.lower() == ".gpkg":
            lines.append(f"Layers and metadata: `{row['layers']}`.")
        elif path.suffix.lower() == ".parquet":
            lines.extend([
                f"Rows: {row['row_count']}; columns: `{row['columns']}`; dtypes: `{row['dtypes']}`.",
                "Schema:",
                "```text",
                str(row["schema"]),
                "```",
                "The inventory CSV contains a bounded preview of at most the first 100 rows.",
            ])
        elif row.get("error") and str(row["error"]) not in {"", "nan"}:
            lines.append(f"Inspection error: {row['error']}.")
        lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    inventory = inventory_raw_data()
    error_count = int(inventory["error"].fillna("").astype(str).ne("").sum())
    incomplete = inventory.loc[inventory["extension"] == ".crdownload", "relative_path"].tolist()
    print(f"Inventoried {len(inventory)} file(s); {error_count} error/incomplete file(s).")
    print(f"Incomplete downloads: {len(incomplete)}")
    for filename in incomplete:
        print(f"  {filename}")
    print(f"Inventory written to {Path(__file__).resolve().parents[1] / 'data' / 'raw_inventory.csv'}")
    print(f"Raw data report written to {write_raw_data_report(inventory)}")


if __name__ == "__main__":
    main()