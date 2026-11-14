import streamlit as st

from app.utils.config import get_data_source
from app.utils.loaders import (
    check_temperature_variable_types,
    get_data_quality_summary,
    load_mars_temperature_envelope,
    load_temperature_monthly,
)
from app.utils.validation import temperature_compatibility_status


st.set_page_config(page_title="Data Sources | TERRAOPS", layout="wide")
st.title("Data Sources")
data_source = get_data_source()
st.markdown(f"**Data mode:** `{data_source}`")
if data_source == "sample":
    st.warning("PLACEHOLDER DATA: values shown by this app are illustrative only.", icon="⚠️")

st.subheader("Temperature compatibility")
try:
    temperatures = load_temperature_monthly()
    envelope = load_mars_temperature_envelope()
    mismatches = check_temperature_variable_types(temperatures, envelope)
    status, message = temperature_compatibility_status(data_source, mismatches)
    getattr(st, status)(message)
except Exception as error:
    st.error(f"Could not check temperature compatibility: {error}")

st.subheader("Missing values by file and column")
try:
    quality_summary = get_data_quality_summary()
    if quality_summary.empty:
        st.info("No contract data files are available for a quality summary.")
    else:
        visible_columns = quality_summary.loc[
            ~quality_summary["column"].isin({"schema_version", "geometry"})
        ]
        show_all = st.checkbox("Show all columns", value=False)
        if not show_all:
            visible_columns = visible_columns.loc[
                visible_columns["missing_count"] > 0
            ]
        if visible_columns.empty:
            st.info(
                "No missing values in the displayed columns. Enable 'Show all columns' "
                "to inspect complete columns."
            )
        else:
            for filename, file_summary in visible_columns.groupby("file", sort=False):
                with st.expander(filename, expanded=False):
                    st.dataframe(file_summary.drop(columns="file"), hide_index=True, width="stretch")
except Exception as error:
    st.error(f"Could not build the data-quality summary: {error}")

st.subheader("Dataset provenance")
st.info("Dataset provenance and limitations will be displayed here once source records are provided.")