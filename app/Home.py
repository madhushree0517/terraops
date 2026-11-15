import streamlit as st

from app.utils.config import get_contract_file_statuses
from app.components.site_profile import render_page_banner


st.set_page_config(page_title="TERRAOPS", page_icon="🌍", layout="wide")
st.title("TERRAOPS")
st.write(
    "The tool is scoped to Mars rover mobility, with Jezero as the reference. "
    "It organizes evidence and does not certify any site."
)

render_page_banner(None, get_contract_file_statuses())

st.subheader("Scientific safeguards")
st.markdown(
    "- Compare only compatible measurements, including units, resolution, period, and method.\n"
    "- Do not interpret comparisons as probabilities of mission or test success.\n"
    "- Do not claim that any Earth site reproduces Mars. Earth locations can only support "
    "limited rehearsals of selected conditions."
)

st.subheader("Demo path")
demo_steps = [
    ("Review the Jezero reference", "pages/1_Mars_Reference.py"),
    ("Explore Earth candidate sites", "pages/2_Earth_Candidates.py"),
    ("Compare terrain measures", "pages/3_Terrain_Comparison.py"),
    ("Review seasonal temperature coverage", "pages/4_When_to_Test.py"),
    ("Review mission analogy gaps", "pages/5_Analogy_Gap_Detector.py"),
    ("Check dataset sources and limitations", "pages/6_Data_Sources.py"),
]
for step_number, (label, page) in enumerate(demo_steps, start=1):
    st.page_link(page, label=f"{step_number}. {label}")
