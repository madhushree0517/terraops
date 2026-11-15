import pandas as pd

from app.utils.location import build_location_consistency


def test_location_consistency_computes_supplied_atacama_note_offsets():
    sites = pd.DataFrame(
        [
            {"site_id": "jezero", "lat": 18.4, "lon": 77.6},
            {"site_id": "askja", "lat": 65.500138889, "lon": -16.500277778},
            {"site_id": "atacama", "lat": -22.499861111, "lon": -68.500138889},
            {"site_id": "ladakh", "lat": 34.500138889, "lon": 77.499861111},
        ]
    )

    table = build_location_consistency(sites)
    atacama_notes = table.loc[
        table["Location source"].str.contains("Atacama note|MODIS analysis", regex=True)
    ]

    assert atacama_notes["Distance from terrain centroid (km)"].tolist() == ["273.0", "54.9"]
    assert atacama_notes["Finding"].str.startswith("Warning:").all()
    temperature_rows = table.loc[table["Location source"] == "Earth temperature source CSV"]
    assert len(temperature_rows) == 4
    assert temperature_rows["Coordinates (lat, lon)"].eq("Not stated in source files").all()
    jezero_extent = table.loc[
        (table["Site"] == "Jezero")
        & (table["Location source"] == "Supplied terrain extent")
    ].iloc[0]
    assert "invalid under EPSG:4326" in jezero_extent["Coordinates (lat, lon)"]
