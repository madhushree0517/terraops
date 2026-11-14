import streamlit as st

from app.utils.config import get_data_source


st.set_page_config(page_title="TERRAOPS", page_icon="🌍", layout="wide")
st.title("TERRAOPS")
st.write(
    "TERRAOPS helps a Mars exploration team identify Earth locations for rover-mobility "
    "rehearsal by comparing terrain and environmental data with conditions at Jezero "
    "Crater. It is an evidence-organizing tool, not a site-certification system."
)

if get_data_source() == "sample":
    st.warning(
        "PLACEHOLDER DATA: this app is reading illustrative fixtures from `data/sample/`. "
        "Do not use these values as scientific evidence or for operational decisions.",
        icon="⚠️",
    )

st.subheader("Scientific safeguards")
st.markdown(
    "- Compare only compatible measurements, including units, resolution, period, and method.\n"
    "- Do not interpret comparisons as probabilities of mission or test success.\n"
    "- Do not claim that any Earth site reproduces Mars. Earth locations can only support "
    "limited rehearsals of selected conditions."
)

st.subheader("Explore")
pages = [
    ("Mars Reference", "pages/1_Mars_Reference.py"),
    ("Earth Candidates", "pages/2_Earth_Candidates.py"),
    ("Terrain Comparison", "pages/3_Terrain_Comparison.py"),
    ("When to Test", "pages/4_When_to_Test.py"),
    ("Analogy Gap Detector", "pages/5_Analogy_Gap_Detector.py"),
    ("Data Sources", "pages/6_Data_Sources.py"),
]
for label, page in pages:
    st.page_link(page, label=label)