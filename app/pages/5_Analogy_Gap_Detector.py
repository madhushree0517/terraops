import streamlit as st

from app.components.site_profile import render_next_step, render_page_banner
from app.utils.config import get_data_file_source
from app.utils.loaders import load_analogy_gaps


st.set_page_config(page_title="Analogy Gap Detector | TERRAOPS", layout="wide")
st.title("Analogy Gap Detector")
st.caption(
    "How to use this page: filter the reviewed analogy decisions, then open a factor to read what can be rehearsed and what remains different."
)
render_page_banner(
    "Earth results show relative terrain difficulty, not absolute passability on Mars.",
    {"analogy_gaps.json": get_data_file_source("analogy_gaps.json")},
)

try:
    gaps = load_analogy_gaps()
except Exception as error:
    st.error(f"Could not load analogy limitations: {error}")
    st.stop()

can_rehearse_count = sum(gap["can_rehearse_on_earth"] is True for gap in gaps)
simulation_count = sum(gap["can_rehearse_on_earth"] is False for gap in gaps)
pending_count = sum(gap["can_rehearse_on_earth"] is None for gap in gaps)
reviewed_count = can_rehearse_count + simulation_count
st.write(
    f"{reviewed_count} factors reviewed: {can_rehearse_count} can be rehearsed on Earth, "
    f"{simulation_count} need simulation or other testing."
)
if pending_count:
    st.caption(f"{pending_count} factors are pending review; they remain visible under All.")

if hasattr(st, "segmented_control"):
    selected_group = st.segmented_control(
        "Filter analogy factors",
        options=("All", "Can be rehearsed", "Needs simulation"),
        default="All",
        label_visibility="collapsed",
    )
else:
    selected_group = st.radio(
        "Filter analogy factors",
        options=("All", "Can be rehearsed", "Needs simulation"),
        horizontal=True,
        label_visibility="collapsed",
    )

if selected_group == "Can be rehearsed":
    visible_gaps = [gap for gap in gaps if gap["can_rehearse_on_earth"] is True]
elif selected_group == "Needs simulation":
    visible_gaps = [gap for gap in gaps if gap["can_rehearse_on_earth"] is False]
else:
    visible_gaps = gaps

st.write(
    'A "Can be rehearsed on Earth" decision applies only to that specific aspect; '
    "it does not mean Earth reproduces Mars."
)

core_fields = {"schema_version", "factor", "can_rehearse_on_earth", "explanation"}
for gap in visible_gaps:
    with st.expander(str(gap["factor"]), expanded=False):
        st.write(gap["explanation"])
        for field, value in gap.items():
            if field in core_fields or value is None or str(value).strip() == "":
                continue
            st.markdown(f"**{field.replace('_', ' ').capitalize()}**")
            st.write(value)

st.caption(
    "No overall Earth-site recommendation is made here. This page records scope limits and "
    "does not certify site suitability or mission success."
)
render_next_step("pages/6_Data_Sources.py", "Next step: Data Sources")
