import json
import re
from pathlib import Path

import pandas as pd


INVENTORY_COLUMNS = (
    "relative_path",
    "extension",
    "size_mb",
    "crs",
    "resolution",
    "bounds",
    "nodata",
    "dtype",
    "geometry_type",
    "feature_count",
    "columns",
    "variables",
    "time_range",
    "error",
)
RASTER_EXTENSIONS = {".tif", ".tiff", ".img", ".vrt", ".jp2", ".asc", ".grd"}
VECTOR_EXTENSIONS = {".shp", ".gpkg", ".geojson", ".json", ".gml", ".kml", ".fgb"}
TIME_COLUMN_PATTERN = re.compile(r"time|date|datetime|timestamp|period|year", re.I)


def _time_range(values: pd.Series) -> str:
    parsed = pd.to_datetime(values, errors="coerce", utc=True)
    parsed = parsed.dropna()
    if parsed.empty:
        return ""
    return json.dumps([parsed.min().isoformat(), parsed.max().isoformat()])


def _inspect_csv(path: Path, row: dict) -> None:
    headers = pd.read_csv(path, nrows=0)
    row["columns"] = json.dumps([str(column) for column in headers.columns])
    time_columns = [
        str(column)
        for column in headers.columns
        if TIME_COLUMN_PATTERN.search(str(column))
    ]
    time_values = {column: [] for column in time_columns}
    if not time_columns:
        return
    for chunk in pd.read_csv(path, usecols=time_columns, chunksize=50000):
        for column in time_columns:
            parsed = pd.to_datetime(chunk[column], errors="coerce", utc=True).dropna()
            if not parsed.empty:
                time_values[column].extend([parsed.min(), parsed.max()])
    ranges = {}
    for column, values in time_values.items():
        if values:
            ranges[column] = json.loads(_time_range(pd.Series(values)))
    if ranges:
        row["time_range"] = json.dumps(ranges)


def _inspect_netcdf(path: Path, row: dict) -> None:
    import xarray as xr

    with xr.open_dataset(path) as dataset:
        row["variables"] = json.dumps(
            [str(variable) for variable in (*dataset.data_vars, *dataset.coords)]
        )
        time_variables = [
            variable
            for variable in dataset.variables
            if TIME_COLUMN_PATTERN.search(str(variable))
        ]
        ranges = {}
        for variable in time_variables:
            values = pd.to_datetime(
                dataset[variable].values.ravel(), errors="coerce", utc=True
            ).dropna()
            if not values.empty:
                ranges[str(variable)] = [
                    values.min().isoformat(),
                    values.max().isoformat(),
                ]
        if ranges:
            row["time_range"] = json.dumps(ranges)


def _inspect_raster(path: Path, row: dict) -> None:
    import rasterio

    with rasterio.open(path) as dataset:
        row["crs"] = str(dataset.crs) if dataset.crs else ""
        row["resolution"] = json.dumps(list(dataset.res))
        row["bounds"] = json.dumps(list(dataset.bounds))
        row["nodata"] = json.dumps(list(dataset.nodatavals))
        row["dtype"] = json.dumps(list(dataset.dtypes))


def _inspect_vector(path: Path, row: dict) -> None:
    import geopandas as gpd

    frame = gpd.read_file(path)
    row["crs"] = str(frame.crs) if frame.crs else ""
    geometry_types = sorted(
        str(value) for value in frame.geometry.geom_type.dropna().unique()
    )
    row["geometry_type"] = json.dumps(geometry_types)
    row["feature_count"] = len(frame)
    row["columns"] = json.dumps([str(column) for column in frame.columns])


def inventory_raw_data(
    raw_dir: str | Path | None = None,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    project_root = Path(__file__).resolve().parents[1]
    source_dir = Path(raw_dir) if raw_dir is not None else project_root / "data" / "raw"
    destination = (
        Path(output_path)
        if output_path is not None
        else project_root / "data" / "raw_inventory.csv"
    )
    rows = []
    paths = sorted(path for path in source_dir.rglob("*") if path.is_file()) if source_dir.is_dir() else []

    for path in paths:
        row = {column: "" for column in INVENTORY_COLUMNS}
        row.update(
            relative_path=path.relative_to(source_dir).as_posix(),
            extension=path.suffix.lower(),
        )
        try:
            stat = path.stat()
            row["size_mb"] = round(stat.st_size / (1024 * 1024), 6)
            extension = path.suffix.lower()
            if extension in RASTER_EXTENSIONS:
                _inspect_raster(path, row)
            elif extension in VECTOR_EXTENSIONS:
                _inspect_vector(path, row)
            elif extension == ".csv":
                _inspect_csv(path, row)
            elif extension in {".nc", ".netcdf"}:
                _inspect_netcdf(path, row)
        except Exception as error:
            row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)

    inventory = pd.DataFrame(rows, columns=INVENTORY_COLUMNS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(destination, index=False)
    return inventory


def main() -> None:
    inventory = inventory_raw_data()
    error_count = int(inventory["error"].fillna("").ne("").sum())
    print(f"Inventoried {len(inventory)} file(s); {error_count} read error(s).")
    if inventory.empty:
        print("No files found under data/raw/.")
    print(f"Inventory written to {Path(__file__).resolve().parents[1] / 'data' / 'raw_inventory.csv'}")


if __name__ == "__main__":
    main()