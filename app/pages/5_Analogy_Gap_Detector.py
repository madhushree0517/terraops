import streamlit as st

from app.components.site_profile import render_page_banner
from app.utils.config import get_data_file_source
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

st.write(
    'A "Can be rehearsed on Earth" decision applies only to that specific aspect; '
    "it does not mean Earth reproduces Mars."
)

groups = (
    ("Can be rehearsed on Earth", True),
    ("Needs simulation or other testing", False),
    ("Pending review", None),
)
core_fields = {"schema_version", "factor", "can_rehearse_on_earth", "explanation"}
for group_label, decision in groups:
    entries = [gap for gap in gaps if gap["can_rehearse_on_earth"] is decision]
    if not entries:
        continue
    st.subheader(group_label)
    for gap in entries:
        with st.container(border=True):
            st.markdown(f"**{gap['factor']}**")
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