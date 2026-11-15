import pandas as pd
from pyproj import Geod


ATACAMA_NOTE_COORDINATES = (
    ("MODIS analysis coordinate (team-supplied)", -24.60, -69.90),
    ("Other Atacama note coordinate (team-supplied)", -22.91, -68.20),
)
SITE_ORDER = ("jezero", "askja", "atacama", "ladakh")
SITE_LABELS = {
    "jezero": "Jezero",
    "askja": "Askja",
    "atacama": "Atacama",
    "ladakh": "Ladakh",
}
GEOD = Geod(ellps="WGS84")


def build_location_consistency(sites: pd.DataFrame) -> pd.DataFrame:
    records = []
    indexed = sites.set_index("site_id")
    for site_id in SITE_ORDER:
        site = indexed.loc[site_id] if site_id in indexed.index else None
        has_centroid = (
            site is not None
            and pd.notna(site.get("lat"))
            and pd.notna(site.get("lon"))
            and site_id != "jezero"
        )
        centroid = (float(site["lon"]), float(site["lat"])) if has_centroid else None
        if centroid:
            records.append(
                {
                    "Site": SITE_LABELS[site_id],
                    "Location source": "Supplied terrain extent centroid",
                    "Coordinates (lat, lon)": f"{centroid[1]:.5f}, {centroid[0]:.5f}",
                    "Distance from terrain centroid (km)": "Reference point",
                    "Finding": "Extent centroid; not a validated field boundary.",
                }
            )
        elif site_id == "jezero":
            records.append(
                {
                    "Site": SITE_LABELS[site_id],
                    "Location source": "Supplied terrain extent",
                    "Coordinates (lat, lon)": "Not usable; extent is invalid under EPSG:4326",
                    "Distance from terrain centroid (km)": "Not available",
                    "Finding": "No valid terrain centroid.",
                }
            )

        records.append(
            {
                "Site": SITE_LABELS[site_id],
                "Location source": "Earth temperature source CSV",
                "Coordinates (lat, lon)": "Not stated in source files",
                "Distance from terrain centroid (km)": "Not available",
                "Finding": "Cannot compare without source coordinates.",
            }
        )

        if site_id == "atacama":
            for label, latitude, longitude in ATACAMA_NOTE_COORDINATES:
                distance = (
                    GEOD.inv(centroid[0], centroid[1], longitude, latitude)[2] / 1000
                    if centroid
                    else None
                )
                records.append(
                    {
                        "Site": SITE_LABELS[site_id],
                        "Location source": label,
                        "Coordinates (lat, lon)": f"{latitude:.2f}, {longitude:.2f}",
                        "Distance from terrain centroid (km)": (
                            f"{distance:.1f}" if distance is not None else "Not available"
                        ),
                        "Finding": (
                            "Warning: more than 20 km from terrain centroid."
                            if distance is not None and distance > 20
                            else "Within 20 km of terrain centroid."
                            if distance is not None
                            else "Cannot compare without a terrain centroid."
                        ),
                    }
                )
        elif site_id == "jezero" and site is not None:
            records.append(
                {
                    "Site": SITE_LABELS[site_id],
                    "Location source": "Approximate Mars reference in sites file",
                    "Coordinates (lat, lon)": f"{float(site['lat']):.5f}, {float(site['lon']):.5f}",
                    "Distance from terrain centroid (km)": "Not available",
                    "Finding": "Approximate reference only; not a terrain centroid.",
                }
            )

    return pd.DataFrame(
        records,
        columns=(
            "Site",
            "Location source",
            "Coordinates (lat, lon)",
            "Distance from terrain centroid (km)",
            "Finding",
        ),
    )