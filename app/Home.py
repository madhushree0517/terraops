import streamlit as st

from app.utils.config import get_contract_file_statuses
from app.components.site_profile import render_page_banner


st.set_page_config(page_title="TERRAOPS", page_icon="🌍", layout="wide")
st.title("TERRAOPS")
st.write(
    "TERRAOPS helps a Mars exploration team find Earth locations for rover-mobility rehearsal "
    "by comparing their terrain and environmental data with Jezero Crater. "
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
    ("Open the app", "Home.py"),
    ("Select Mars", "pages/1_Mars_Reference.py"),
    ("Select Jezero", "pages/1_Mars_Reference.py"),
    ("Select rover mobility", "pages/3_Terrain_Comparison.py"),
    ("View the terrain reference", "pages/1_Mars_Reference.py"),
    ("View the Earth candidates", "pages/2_Earth_Candidates.py"),
    ("Compare terrain", "pages/3_Terrain_Comparison.py"),
    ("Read the band matrix", "pages/3_Terrain_Comparison.py"),
    ("Open When-to-Test", "pages/4_When_to_Test.py"),
    ("View the temperature bands", "pages/4_When_to_Test.py"),
    ("Open the Analogy Gap Detector", "pages/5_Analogy_Gap_Detector.py"),
    ("View the final recommendation and limitations", "pages/5_Analogy_Gap_Detector.py"),
]
for step_number, (label, page) in enumerate(demo_steps, start=1):
    st.page_link(page, label=f"{step_number}. {label}")
st.page_link("pages/6_Data_Sources.py", label="Data Sources: where each file comes from")
