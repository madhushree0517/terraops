import pandas as pd
import streamlit as st

from app.utils.config import get_contract_file_statuses
from app.utils.loaders import (
    check_temperature_variable_types,
    get_data_quality_summary,
    load_datasets_catalogue,
    load_mars_temperature_envelope,
    load_temperature_monthly,
)


st.set_page_config(page_title="Data Sources | TERRAOPS", layout="wide")
st.title("Data Sources")
file_statuses = get_contract_file_statuses()
active_sources = {source for source in file_statuses.values() if source != "missing"}
data_mode = next(iter(active_sources)) if len(active_sources) == 1 else (
    "mixed" if active_sources else "missing"
)
st.markdown(f"**Data mode:** `{data_mode}`")
status_labels = {
    "processed": "Real data (processed)",
    "sample": "Placeholder data (sample)",
    "missing": "Missing",
}
st.subheader("Contract file sources")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Contract file": filename,
                "Active source": (
                    "processed (draft, pending review)"
                    if filename == "analogy_gaps.json" and source == "processed"
                    else status_labels[source]
                ),
            }
            for filename, source in file_statuses.items()
        ]
    ),
    hide_index=True,
    width="stretch",
)
sample_files = [filename for filename, source in file_statuses.items() if source == "sample"]
if sample_files:
    st.warning(
        "PLACEHOLDER DATA is still used for: " + ", ".join(f"`{name}`" for name in sample_files),
        icon="⚠️",
    )

st.subheader("Dataset catalogue")
try:
    catalogue = load_datasets_catalogue().copy()
    body_by_dataset = {
        "Mars MEDA TIRS": "Mars",
        "Mars MEDA ATS": "Mars",
        "MODIS LST": "Earth",
        "NASA POWER": "Earth",
        "Copernicus DEM": "Earth",
    }
    catalogue["body"] = catalogue["dataset_name"].map(body_by_dataset).fillna("Unspecified")
    catalogue_display = catalogue.copy()
    for column in catalogue_display.columns:
        catalogue_display[column] = catalogue_display[column].map(
            lambda value: (
                "not documented"
                if pd.isna(value) or not str(value).strip()
                else value
            )
        )
    body_filter = st.selectbox("Filter datasets by body", ["All", "Mars", "Earth", "Unspecified"])
    visible_catalogue = (
        catalogue_display
        if body_filter == "All"
        else catalogue_display.loc[catalogue["body"] == body_filter]
    )
    st.dataframe(
        visible_catalogue[
            [
                "body",
                "dataset_name",
                "source",
                "spatial_resolution",
                "observation_period",
                "units",
                "crs",
                "limitations",
                "citation",
                "licence",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Body labels are assigned from the exact catalogue dataset names; catalogue rows "
        "and metadata are otherwise shown as loaded."
    )
except Exception as error:
    st.error(f"Could not load the dataset catalogue: {error}")

st.subheader("Temperature compatibility")
try:
    temperatures = load_temperature_monthly()
    envelope = load_mars_temperature_envelope()
    mismatches = check_temperature_variable_types(temperatures, envelope)
    has_sample_inputs = any(
        file_statuses[filename] == "sample"
        for filename in ("temperature_monthly.csv", "mars_temperature_envelope.json")
    )
    message = "Only variable labels are compared; this is not a physical validation."
    if mismatches:
        mismatch_details = [
            mismatch.replace(
                "This check compares variable_type labels only; it is not a physical validation. ",
                "",
            )
            for mismatch in mismatches
        ]
        message += " " + " ".join(mismatch_details)
    warning_title = (
        "Known limitation: Earth temperature is currently air temperature; surface comparison pending"
    )
    sample_prefix = "PLACEHOLDER DATA. " if has_sample_inputs else ""
    st.warning(f"{warning_title}. {sample_prefix}{message}")
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
try:
    if catalogue_display.empty:
        st.info("No dataset provenance records are available.")
    else:
        st.dataframe(
            catalogue_display[
                ["dataset_name", "source", "url", "citation", "licence", "limitations"]
            ],
            hide_index=True,
            width="stretch",
        )
except NameError:
    st.info("No dataset provenance records are available.")