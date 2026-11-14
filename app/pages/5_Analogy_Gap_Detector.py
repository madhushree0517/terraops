import streamlit as st

from app.utils.config import get_data_source


st.set_page_config(page_title="Analogy Gap Detector | TERRAOPS", layout="wide")
st.title("Analogy Gap Detector")
if get_data_source() == "sample":
    st.warning("PLACEHOLDER DATA: values shown by this app are illustrative only.", icon="⚠️")
st.info("Known analogy limitations will be surfaced after reviewed project notes are supplied.")