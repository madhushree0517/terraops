import json

import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from rasterio.transform import from_origin

from scripts.inventory_raw_data import inventory_raw_data


def test_inventory_reads_csv_columns_and_time_range(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    output_path = tmp_path / "raw_inventory.csv"
    pd.DataFrame(
        {
            "site_id": ["a", "b"],
            "observation_time": ["2020-01-01", "2022-06-30"],
        }
    ).to_csv(raw_dir / "temperature.csv", index=False)

    inventory = inventory_raw_data(raw_dir, output_path)

    assert inventory.loc[0, "relative_path"] == "temperature.csv"
    assert inventory.loc[0, "extension"] == ".csv"
    assert '"observation_time"' in inventory.loc[0, "columns"]
    assert "2020-01-01" in inventory.loc[0, "time_range"]
    assert output_path.is_file()


def test_unreadable_file_is_recorded_without_aborting(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "broken.csv").write_bytes(b"\xff\xfe\xff")
    pd.DataFrame({"value": [1]}).to_csv(raw_dir / "valid.csv", index=False)

    inventory = inventory_raw_data(raw_dir, tmp_path / "raw_inventory.csv")

    broken = inventory.loc[inventory["relative_path"] == "broken.csv"].iloc[0]
    valid = inventory.loc[inventory["relative_path"] == "valid.csv"].iloc[0]
    assert broken["error"]
    assert valid["error"] == ""


def test_missing_raw_directory_writes_empty_inventory(tmp_path):
    output_path = tmp_path / "raw_inventory.csv"

    inventory = inventory_raw_data(tmp_path / "missing", output_path)

    assert inventory.empty
    assert output_path.is_file()
    assert list(pd.read_csv(output_path).columns) == list(inventory.columns)


def test_inventory_reads_raster_metadata(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raster_path = raw_dir / "terrain.tif"
    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=2,
        width=3,
        count=1,
        dtype="int16",
        crs="EPSG:4326",
        transform=from_origin(10, 20, 0.5, 0.25),
        nodata=-9999,
    ) as dataset:
        dataset.write(np.ones((2, 3), dtype=np.int16), 1)

    inventory = inventory_raw_data(raw_dir, tmp_path / "inventory.csv")
    raster = inventory.iloc[0]

    assert raster["crs"] == "EPSG:4326"
    assert json.loads(raster["resolution"]) == [0.5, 0.25]
    assert json.loads(raster["nodata"]) == [-9999.0]
    assert json.loads(raster["dtype"]) == ["int16"]
    assert not raster["error"]


def test_inventory_reads_vector_metadata(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "site.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [1, 2]},
                        "properties": {"site_id": "sample"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    inventory = inventory_raw_data(raw_dir, tmp_path / "inventory.csv")
    vector = inventory.iloc[0]

    assert vector["feature_count"] == 1
    assert json.loads(vector["geometry_type"]) == ["Point"]
    assert "site_id" in json.loads(vector["columns"])
    assert vector["crs"]
    assert not vector["error"]


def test_inventory_reads_netcdf_variables_and_time_range(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    dataset = xr.Dataset(
        {"surface_temperature": ("time", [1.0, 2.0])},
        coords={"time": pd.to_datetime(["2021-01-01", "2021-03-01"])},
    )
    dataset.to_netcdf(raw_dir / "mars.nc", engine="h5netcdf")

    inventory = inventory_raw_data(raw_dir, tmp_path / "inventory.csv")
    netcdf = inventory.iloc[0]

    assert "surface_temperature" in json.loads(netcdf["variables"])
    assert "2021-01-01" in netcdf["time_range"]
    assert "2021-03-01" in netcdf["time_range"]
    assert not netcdf["error"]