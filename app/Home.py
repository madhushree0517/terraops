# Streamlit's script runner may omit the repository root from sys.path.
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import json

import pandas as pd
import streamlit as st

from app.components.site_profile import render_page_banner, render_team_wordmark
from app.utils.config import DATA_ROOT, get_contract_file_statuses


st.set_page_config(page_title="TERRAOPS", page_icon="🌍", layout="wide")
render_team_wordmark()
st.title("TERRAOPS")
st.caption(
    "How to use this page: review the findings so far, keep the scientific safeguards in mind, then follow the guided demo."
)
st.write(
    "The tool is scoped to Mars rover mobility, with Jezero as the reference. "
    "It organizes evidence and does not certify any site."
)
render_page_banner(None, get_contract_file_statuses())

processed = DATA_ROOT / "processed"


def _csv(name: str) -> pd.DataFrame:
    path = processed / name
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()


def _json(name: str, default):
    path = processed / name
    if not path.is_file():
        return default
    with path.open(encoding="utf-8") as source:
        return json.load(source)


sites_document = _json("sites.geojson", {"features": []})
site_properties = {
    str(feature.get("properties", {}).get("site_id", "")): feature.get("properties", {})
    for feature in sites_document.get("features", [])
}
terrain = _csv("terrain_metrics.csv")
if not terrain.empty and {"value", "tier", "site_id"}.issubset(terrain.columns):
    terrain_mask = terrain["value"].notna() & terrain["tier"].astype("string").fillna("").str.strip().ne("")
    terrain_ids = set(terrain.loc[terrain_mask, "site_id"].astype(str))
else:
    terrain_ids = set()
surface = _csv("temperature_monthly.csv")
if not surface.empty and "variable_type" in surface:
    surface = surface.loc[surface["variable_type"].astype(str) == "surface_temp"]
jezero_terrain = "jezero" in terrain_ids

st.subheader("Findings so far")
if terrain_ids:
    metric_rows = terrain.loc[
        terrain["site_id"].astype(str).isin(terrain_ids)
        & terrain["metric_name"].isin({"slope_p90_deg", "pct_area_slope_gt24", "roughness"})
        & terrain["value"].notna()
    ]
    for site_id, rows in metric_rows.groupby("site_id", sort=False):
        name = site_properties.get(str(site_id), {}).get("name", str(site_id))
        measurements = []
        for row in rows.itertuples(index=False):
            if row.metric_name == "slope_p90_deg":
                measurements.append(f"slope P90 {float(row.value):.2f}")
            elif row.metric_name == "pct_area_slope_gt24":
                cutoff = row.metric_name.removeprefix("pct_area_slope_gt")
                measurements.append(f"area above the {cutoff} slope-value cutoff {float(row.value):.2f}%")
            elif row.metric_name == "roughness":
                measurements.append(f"roughness value {float(row.value):.2f}")
        if measurements:
            st.write(f"{name}: " + "; ".join(measurements) + ".")
else:
    st.write("No Earth terrain measurements are available to summarize.")

if not surface.empty:
    dates = pd.to_datetime(surface.get("period_start"), errors="coerce").dropna()
    ends = pd.to_datetime(surface.get("period_end"), errors="coerce").dropna()
    period_text = (
        f"{dates.min().date()} to {ends.max().date()}"
        if not dates.empty and not ends.empty
        else "the period recorded in the temperature summary"
    )
    st.write(f"Earth surface-temperature summaries cover {period_text}, with daytime and nighttime kept separate.")
if not jezero_terrain:
    st.write("Jezero terrain measurements are not available yet.")

st.subheader("Scientific safeguards")
st.markdown(
    "- Compare only compatible measurements, including units, resolution, period, and method.\n"
    "- Do not interpret comparisons as probabilities of mission or test success.\n"
    "- Do not claim that any Earth site reproduces Mars. Earth locations can only support "
    "limited rehearsals of selected conditions.\n"
    "- TERRAOPS does not calculate a composite score or rank Earth sites."
)

st.subheader("Guided demo: rover mobility at Jezero")
st.write(
    "Follow the evidence from the Mars reference through Earth candidates, then check "
    "when the temperature comparison is supported and where the analogy ends."
)
demo_steps = [
    ("1 · Mars reference", "Review Jezero and its available measurements", "pages/1_Mars_Reference.py"),
    ("2 · Earth candidates", "Open the map and inspect a candidate profile", "pages/2_Earth_Candidates.py"),
    ("3 · Terrain comparison", "Choose sites and compare available terrain measures", "pages/3_Terrain_Comparison.py"),
    ("4 · When to test", "Review temperature coverage and compatibility", "pages/4_When_to_Test.py"),
]
for title, description, page in demo_steps:
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(description)
        st.page_link(page, label="Open this step", icon="➡️")

left, right = st.columns(2)
with left:
    st.page_link("pages/5_Analogy_Gap_Detector.py", label="Finish with the analogy gaps", icon="🧭")
with right:
    st.page_link("pages/6_Data_Sources.py", label="Inspect sources and data quality", icon="📚")

st.page_link("pages/1_Mars_Reference.py", label="Next step: Mars Reference", icon="➡️")
