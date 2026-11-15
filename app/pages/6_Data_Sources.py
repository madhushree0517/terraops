import pandas as pd
import streamlit as st

from app.utils.config import get_contract_file_statuses
from app.utils.loaders import (
    check_temperature_variable_types,
    get_data_quality_summary,
    load_datasets_catalogue,
    load_mars_temperature_envelope,
    load_sites,
    load_temperature_monthly,
)
from app.utils.location import build_location_consistency


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
                    "processed (reviewed decisions)"
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
    body_filter = st.selectbox("Filter datasets by body", ["All", "Mars", "Earth", "Unspecified"])
    visible_catalogue = (
        catalogue
        if body_filter == "All"
        else catalogue.loc[catalogue["body"] == body_filter]
    )
    catalogue_columns = [
        "body",
        "dataset_name",
        "source",
        "url",
        "file_format",
        "spatial_resolution",
        "temporal_resolution",
        "observation_period",
        "units",
        "crs",
        "citation",
        "licence",
    ]
    catalogue_display = visible_catalogue[catalogue_columns].copy()
    for column in catalogue_display.columns:
        if column == "url":
            catalogue_display[column] = catalogue_display[column].map(
                lambda value: None if pd.isna(value) or not str(value).strip() else str(value)
            )
        else:
            catalogue_display[column] = catalogue_display[column].map(
                lambda value: (
                    "not documented"
                    if pd.isna(value) or not str(value).strip()
                    else value
                )
            )
    st.dataframe(
        catalogue_display,
        hide_index=True,
        width="stretch",
        column_config={
            "body": "Body",
            "dataset_name": "Dataset",
            "source": "Provider",
            "url": st.column_config.LinkColumn("URL", display_text="Open source"),
            "file_format": "Format",
            "spatial_resolution": "Spatial resolution",
            "temporal_resolution": "Temporal resolution",
            "observation_period": "Observation period",
            "units": "Units",
            "crs": "CRS",
            "citation": "Citation",
            "licence": "Licence",
        },
    )
    for _, row in visible_catalogue.iterrows():
        with st.expander(str(row["dataset_name"]), expanded=False):
            limitation = row.get("limitations")
            st.write(
                "Not documented."
                if pd.isna(limitation) or not str(limitation).strip()
                else str(limitation)
            )
except Exception as error:
    st.error(f"Could not load the dataset catalogue: {error}")

st.subheader("Location consistency")
try:
    location_table = build_location_consistency(load_sites())
    st.dataframe(location_table, hide_index=True, width="stretch")
    warning_rows = location_table.loc[
        location_table["Finding"].str.startswith("Warning:")
    ]
    for site_name in warning_rows["Site"].drop_duplicates():
        site_rows = warning_rows.loc[warning_rows["Site"] == site_name]
        details = "; ".join(
            f"{row['Location source']}: {row['Distance from terrain centroid (km)']} km"
            for _, row in site_rows.iterrows()
        )
        st.warning(
            f"{site_name}: {details}. These coordinates remain distinct; no location has been selected."
        )
    st.caption(
        "Earth temperature CSVs do not state extraction coordinates. The Iceland-to-Askja "
        "mapping follows team identity confirmation and is not a coordinate-distance validation."
    )
except FileNotFoundError:
    st.info("Site location data are not available for a consistency check.")

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

