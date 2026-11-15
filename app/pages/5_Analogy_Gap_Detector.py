import streamlit as st

from app.components.site_profile import render_page_banner
from app.utils.config import get_data_file_source
from app.utils.analogy import format_data_method_note
from app.utils.loaders import load_analogy_gaps


st.set_page_config(page_title="Analogy Gap Detector | TERRAOPS", layout="wide")
st.title("Analogy Gap Detector")
render_page_banner(
    "Earth results show relative terrain difficulty, not absolute passability on Mars.",
    {"analogy_gaps.json": get_data_file_source("analogy_gaps.json")},
)

try:
    gaps = load_analogy_gaps()
except Exception as error:
    st.error(f"Could not load analogy limitations: {error}")
    st.stop()

mission_gaps = (
    (
        "Reduced gravity",
        "Earth gravity is about 2.6 times Mars, so sinkage and traction differ.",
    ),
    ("Thin CO2 atmosphere", "Earth does not reproduce the thin CO2 atmosphere on Mars."),
    ("Radiation", "Radiation exposure requires separate assessment or simulation."),
    ("Regolith and soil properties", "Earth soils do not establish Martian regolith behavior."),
    ("Dust adhesion", "Dust adhesion requires separate material and environment testing."),
    (
        "Thermal environment",
        "Similar temperatures do not mean equivalent thermal conditions.",
    ),
    (
        "Navigation and communication latency",
        "Earth rehearsal does not reproduce Mars communication latency or all navigation constraints.",
    ),
)

st.subheader("Mission-relevant analogy gaps")
for factor, explanation in mission_gaps:
    with st.container(border=True):
        st.markdown(f"**{factor}**")
        st.write(explanation)
        st.caption("Status: pending review")

if gaps:
    with st.expander("Data and method notes (for the team)", expanded=False):
        for gap in gaps:
            status = str(gap.get("review_status", "")).casefold()
            decision = gap.get("can_rehearse_on_earth")
            if decision is None or "draft" in status or "pending engineering review" in status:
                label = "Pending engineering review"
            else:
                label = "Reviewed decision recorded"
            factor = str(gap.get("factor", ""))
            explanation = str(gap.get("explanation", ""))
            explanation = format_data_method_note(factor, explanation)
            st.markdown(f"**{factor}**")
            st.write(explanation)
            st.caption(label)

st.caption(
    "No overall Earth-site recommendation is made here. This page records scope limits and "
    "does not certify site suitability or mission success."
)