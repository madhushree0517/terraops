from pathlib import Path

import pandas as pd
import streamlit as st

from app.components.site_profile import load_profile_terrain_metrics, render_next_step, render_page_banner
from app.utils.config import DATA_ROOT, get_data_file_source
from app.utils.loaders import load_sites


st.set_page_config(page_title="Mars Reference | TERRAOPS", layout="wide")
st.title("Mars Reference")
st.caption(
    "How to use this page: review Jezero's reference location and imagery, then inspect its data status. "
    "A temperature tab appears when both Mars temperature summaries are ready."
)
render_page_banner(
    None,
    {
        filename: get_data_file_source(filename)
        for filename in ("sites.geojson", "terrain_metrics.csv", "datasets_catalogue.csv")
    },
)

temperature_files = (
    DATA_ROOT / "processed" / "mars_tirs_by_sol.csv",
    DATA_ROOT / "processed" / "mars_seasonal_temperature.csv",
)
tabs = ["Location and imagery"]
if all(path.is_file() for path in temperature_files):
    tabs.append("Surface temperature")

try:
    sites = load_sites()
    jezero_rows = sites.loc[sites["site_id"] == "jezero"]
    if jezero_rows.empty:
        st.error("The site information does not contain the required Jezero reference.")
        st.stop()

    jezero = jezero_rows.iloc[0]
    panels = st.tabs(tabs)
    with panels[0]:
        image_dir = Path(__file__).resolve().parents[2] / "assets" / "mars"
        image_paths = sorted(
            path
            for path in image_dir.glob("*")
            if path.is_file() and path.suffix.casefold() in {".png", ".jpg", ".jpeg"}
        ) if image_dir.is_dir() else []
        if image_paths:
            credit_path = image_dir / "CREDITS.txt"
            credit = credit_path.read_text(encoding="utf-8").strip() if credit_path.is_file() else ""
            caption_path = image_dir / "CAPTION.txt"
            image_caption = (
                caption_path.read_text(encoding="utf-8").strip()
                if caption_path.is_file()
                else "Image of the Jezero Crater region"
            )
            for image_path in image_paths:
                left, center, right = st.columns([1, 5, 1])
                with center:
                    st.image(str(image_path), width=900)
                    st.caption(image_caption)
                    if credit:
                        st.caption(credit)
        else:
            st.caption("Mars imagery has not been added yet.")

        with st.container(border=True):
            st.subheader("Jezero Crater, Mars")
            latitude = pd.to_numeric(pd.Series([jezero["lat"]]), errors="coerce").iloc[0]
            longitude = pd.to_numeric(pd.Series([jezero["lon"]]), errors="coerce").iloc[0]
            if pd.notna(latitude) and pd.notna(longitude):
                st.write(
                    f"Approximate coordinate: {float(latitude):.4f}° latitude, "
                    f"{float(longitude):.4f}° longitude"
                )
            note = str(jezero.get("notes", "")).strip()
            if note:
                st.caption(note)

        terrain = load_profile_terrain_metrics()
        jezero_terrain = terrain.loc[terrain["site_id"].astype(str) == "jezero"]
        values_available = (
            jezero_terrain["value"].notna()
            & jezero_terrain["tier"].astype("string").fillna("").str.strip().ne("")
        ).any()
        if not values_available:
            st.write("Jezero terrain information is not available yet.")
            technical_reasons = (
                jezero_terrain["availability_note"].dropna().astype(str).str.strip()
                if "availability_note" in jezero_terrain
                else []
            )
            with st.expander("Terrain data details", expanded=False):
                reason_lines = [reason for reason in technical_reasons if reason]
                if reason_lines:
                    for reason in dict.fromkeys(reason_lines):
                        st.write(reason)
                else:
                    st.write("No technical reason is recorded.")

    if len(panels) > 1:
        with panels[1]:
            for path in temperature_files:
                dataframe = pd.read_csv(path)
                display = dataframe.drop(columns=[column for column in ("source", "source_file", "file") if column in dataframe])
                st.dataframe(display, hide_index=True, width="stretch")
                st.caption("This table shows the available Mars surface-temperature measurements.")
except Exception as error:
    st.error(f"Could not load the Jezero reference data: {error}")

render_next_step("pages/2_Earth_Candidates.py", "Next step: Earth Candidates")
