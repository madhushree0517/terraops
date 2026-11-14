import streamlit as st

from app.utils.config import get_data_source


st.set_page_config(page_title="When to Test | TERRAOPS", layout="wide")
st.title("When to Test")
if get_data_source() == "sample":
    st.warning("PLACEHOLDER DATA: values shown by this app are illustrative only.", icon="⚠️")
st.info("Seasonal test-window exploration will be added after validated project data is supplied.")