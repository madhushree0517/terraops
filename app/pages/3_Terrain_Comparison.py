import streamlit as st
import pandas as pd

from app.components.chart_helpers import (
    normalized_terrain_radar,
    terrain_parameter_chart,
)
from app.components.site_profile import render_placeholder_banner
from app.utils.config import get_data_source
from app.utils.loaders import load_sites, load_terrain_parameters
from app.utils.scoring import (
    load_scoring_config,
    normalize_weights,
    rank_sensitivity,
    resolution_comparability,
    score_candidate,
)


CONTEXT_PARAMETERS = (
    "elevation_mean_m",
    "resolution_m",
)
PARAMETER_LABELS = {
    "elevation_mean_m": "Mean elevation",
    "elevation_std_m": "Elevation standard deviation",
    "slope_mean_deg": "Mean slope",
    "slope_p95_deg": "95th-percentile slope",
    "roughness_metric": "Roughness",
    "resolution_m": "DEM resolution",
}
PARAMETER_UNITS = {
    "elevation_mean_m": "m",
    "elevation_std_m": "m",
    "slope_mean_deg": "degrees",
    "slope_p95_deg": "degrees",
    "roughness_metric": "declared metric",
    "resolution_m": "m",
}


st.set_page_config(page_title="Terrain Comparison | TERRAOPS", layout="wide")
st.title("Terrain Comparison")
render_placeholder_banner(get_data_source())

try:
    sites = load_sites()
    terrain = load_terrain_parameters()
    config = load_scoring_config()
    jezero_rows = sites.loc[sites["site_id"] == "jezero"]
    earth_sites = sites.loc[sites["body"] == "Earth"].copy()
    if jezero_rows.empty:
        st.error("The active sites dataset does not contain a Jezero reference.")
    elif earth_sites.empty:
        st.info("No Earth candidate sites are available.")
    else:
        jezero_id = str(jezero_rows.iloc[0]["site_id"])
        earth_ids = earth_sites["site_id"].astype(str).tolist()
        site_names = dict(zip(sites["site_id"].astype(str), sites["name"].astype(str)))
        selected_ids = st.multiselect(
            "Earth sites to compare",
            options=earth_ids,
            default=earth_ids,
            format_func=lambda site_id: f"{site_names[site_id]} ({site_id})",
        )

        st.sidebar.subheader("Similarity weights")
        edited_weights = {}
        for parameter, default_weight in config["weights"].items():
            edited_weights[parameter] = st.sidebar.number_input(
                f"{PARAMETER_LABELS[parameter]} ({PARAMETER_UNITS[parameter]})",
                min_value=0.0,
                max_value=1.0,
                value=float(default_weight),
                step=0.05,
                format="%.2f",
                key=f"terrain_weight_{parameter}",
            )
        try:
            weights = normalize_weights(edited_weights)
        except ValueError as error:
            st.sidebar.error(f"{error} Using configured defaults.")
            weights = normalize_weights(config["weights"])
        st.sidebar.caption(f"Effective weights are normalized to sum to {sum(weights.values()):.2f}.")

        st.markdown("### Method")
        st.info(
            "Absolute elevation is not comparable across planetary bodies because the "
            "vertical datums differ. Mean elevation is shown as context and has a default "
            "similarity weight of 0.0."
        )
        st.write(
            "This is a configurable terrain similarity heuristic, not a probability of "
            "success and not a claim that an Earth site reproduces Mars. For each "
            "available parameter, similarity is capped at 0-100 using the configured "
            "difference scale; available weights are renormalized per candidate."
        )
        st.latex(
            r"s_{ij}=\max\left(0,100\left(1-\frac{|x_{ij}-x_{Mj}|}{d_j}\right)\right),"
            r"\qquad S_i=\frac{\sum_{j\in A_i} w_j s_{ij}}{\sum_{j\in A_i} w_j}"
        )
        st.caption(
            "A_i contains only parameters present for both the candidate and Jezero; "
            "d_j is the configured difference scale. Similarity weights are normalized "
            "to sum to 1 after edits."
        )
        scale_rows = [
            {
                "Parameter": f"{PARAMETER_LABELS[parameter]} ({PARAMETER_UNITS[parameter]})",
                "Difference scale": value,
                "Source": "TBD; set from rover mobility criteria",
            }
            for parameter, value in config["difference_scales"].items()
        ]
        with st.expander("Configured difference scales", expanded=False):
            st.dataframe(pd.DataFrame(scale_rows), hide_index=True, width="stretch")
            st.caption(
                f"DEM-resolution comparability warning threshold: "
                f"{config['resolution_comparability_factor']:.1f}x. Resolution is metadata, not a score parameter."
            )

        comparison_ids = [jezero_id, *selected_ids]
        comparison_terrain = terrain.loc[
            terrain["site_id"].astype(str).isin(comparison_ids)
        ].copy()
        reference_rows = comparison_terrain.loc[
            comparison_terrain["site_id"].astype(str) == jezero_id
        ]
        if reference_rows.empty:
            st.error("No Jezero terrain parameters are available for comparison.")
        elif not selected_ids:
            st.info("Select at least one Earth candidate to compare with Jezero.")
        else:
            reference = reference_rows.iloc[0]
            candidates = {}
            score_rows = []
            scored_parameters = [
                parameter
                for parameter, weight in weights.items()
                if weight > 0 and parameter != "resolution_m"
            ]
            for site_id in selected_ids:
                candidate_rows = comparison_terrain.loc[
                    comparison_terrain["site_id"].astype(str) == site_id
                ]
                candidate = candidate_rows.iloc[0] if not candidate_rows.empty else pd.Series(dtype=float)
                if "roughness_unit" in reference and "roughness_unit" in candidate:
                    if reference["roughness_unit"] != candidate["roughness_unit"]:
                        candidate = candidate.copy()
                        candidate["roughness_metric"] = float("nan")
                candidates[site_id] = candidate
                result = score_candidate(
                    reference,
                    candidate,
                    weights,
                    config["difference_scales"],
                )
                comparable, resolution_flag = resolution_comparability(
                    reference.get("resolution_m"),
                    candidate.get("resolution_m"),
                    config["resolution_comparability_factor"],
                )
                if comparable is False:
                    st.warning(
                        f"{site_names[site_id]} ({site_id}): DEM resolution is not "
                        f"comparable to Jezero. {resolution_flag}. Resolution is not scored."
                    )
                missing_parameters = [
                    parameter
                    for parameter in result["excluded_parameters"]
                    if weights.get(parameter, 0) > 0
                ]
                score_rows.append(
                    {
                        "site_id": site_id,
                        "site": site_names[site_id],
                        "overall_similarity": result["score"],
                        **{
                            f"{parameter}_similarity": result["parameter_scores"].get(parameter)
                            for parameter in scored_parameters
                        },
                        "dem_resolution_m": candidate.get("resolution_m", float("nan")),
                        "resolution_comparable": comparable,
                        "resolution_flag": resolution_flag,
                        "excluded_parameters": ", ".join(
                            f"{PARAMETER_LABELS[parameter]} ({PARAMETER_UNITS[parameter]})"
                            for parameter in missing_parameters
                        ),
                    }
                )

            st.subheader("Terrain parameters and metadata")
            display_sites = [jezero_id, *selected_ids]
            value_data = comparison_terrain.set_index("site_id")
            vertical_rows = []
            for parameter in dict.fromkeys((*config["weights"].keys(), *CONTEXT_PARAMETERS)):
                parameter_row = {
                    "Parameter": f"{PARAMETER_LABELS[parameter]} ({PARAMETER_UNITS[parameter]})",
                }
                for site_id in display_sites:
                    site_values = (
                        value_data.loc[site_id]
                        if site_id in value_data.index
                        else pd.Series(dtype=float)
                    )
                    parameter_row[f"{site_names.get(site_id, site_id)} ({site_id})"] = site_values.get(
                        parameter, float("nan")
                    )
                vertical_rows.append(parameter_row)
            st.dataframe(pd.DataFrame(vertical_rows), hide_index=True, width="stretch")

            scores = pd.DataFrame(score_rows).sort_values(
                "overall_similarity", ascending=False, na_position="last"
            )
            st.subheader("Weighted similarity and parameter results")
            readable_scores = scores.rename(
                columns={
                    "site": "Site",
                    "overall_similarity": "Overall similarity (0-100)",
                    "dem_resolution_m": "DEM resolution (m)",
                    "resolution_comparable": "DEM resolution comparable",
                    "resolution_flag": "DEM resolution note",
                    "excluded_parameters": "Excluded parameters",
                    **{
                        f"{parameter}_similarity": (
                            f"{PARAMETER_LABELS[parameter]} ({PARAMETER_UNITS[parameter]}) "
                            "similarity (0-100)"
                        )
                        for parameter in scored_parameters
                    },
                }
            )
            score_columns = [
                column
                for column in readable_scores.columns
                if "similarity" in column.lower()
            ]
            readable_scores[score_columns] = readable_scores[score_columns].round(1)
            readable_scores = readable_scores.drop(columns="site_id")
            st.dataframe(readable_scores, hide_index=True, width="stretch")
            for row in score_rows:
                if row["excluded_parameters"]:
                    st.caption(
                        f"{row['site']}: missing or incompatible values excluded for "
                        f"{row['excluded_parameters']}. No missing value was treated as zero."
                    )

            valid_scores = scores.loc[scores["overall_similarity"].notna()]
            st.subheader("Candidate ranking")
            if valid_scores.empty:
                st.info("No candidate has enough comparable terrain data to calculate a score.")
            else:
                rank_table = valid_scores[["site", "overall_similarity", "excluded_parameters"]].copy()
                rank_table.insert(0, "rank", range(1, len(rank_table) + 1))
                rank_table = rank_table.rename(
                    columns={
                        "site": "Site",
                        "overall_similarity": "Similarity (0-100)",
                        "excluded_parameters": "Excluded parameters",
                    }
                )
                rank_table["Similarity (0-100)"] = rank_table["Similarity (0-100)"].round(1)
                st.dataframe(rank_table, hide_index=True, width="stretch")
                top = valid_scores.iloc[0]
                st.metric(
                    f"Top terrain similarity: {top['site']}",
                    f"{top['overall_similarity']:.1f} / 100",
                )
                top_used = [
                    f"{PARAMETER_LABELS[parameter.removesuffix('_similarity')]} "
                    f"({PARAMETER_UNITS[parameter.removesuffix('_similarity')]})"
                    for parameter in scores.columns
                    if parameter.endswith("_similarity")
                    and parameter != "overall_similarity"
                    and pd.notna(top[parameter])
                ]
                st.write(
                    f"{top['site']} ranks first among the selected Earth sites because it "
                    f"has the highest weighted similarity score ({top['overall_similarity']:.1f}/100) "
                    f"across the available parameters: {', '.join(top_used)}. This ranking "
                    "is only a comparison aid, not a physical-equivalence or success claim."
                )

            st.subheader("Weight sensitivity")
            candidate_frame = pd.DataFrame(
                [{"site_id": site_id, **candidate.to_dict()} for site_id, candidate in candidates.items()]
            )
            sensitivity = rank_sensitivity(
                reference,
                candidate_frame,
                weights,
                config["difference_scales"],
            )
            sensitivity["parameter"] = sensitivity["parameter"].map(
                lambda parameter: PARAMETER_LABELS.get(parameter, parameter)
            )
            sensitivity["top_site"] = sensitivity["top_site"].map(
                lambda site_id: site_names.get(site_id, site_id)
            )
            sensitivity = sensitivity.rename(
                columns={
                    "parameter": "Parameter",
                    "change": "Weight change",
                    "top_site": "Top-ranked site",
                    "top_changed": "Top site changed",
                }
            )
            st.dataframe(sensitivity, hide_index=True, width="stretch")

            st.subheader("Per-parameter comparisons")
            name_map = {jezero_id: site_names[jezero_id], **{site_id: site_names[site_id] for site_id in selected_ids}}
            for start in range(0, len(scored_parameters), 2):
                columns = st.columns(2)
                for column, parameter in zip(columns, scored_parameters[start : start + 2]):
                    with column:
                        st.plotly_chart(
                            terrain_parameter_chart(
                                comparison_terrain,
                                sites,
                                comparison_ids,
                                parameter,
                                label=f"{PARAMETER_LABELS[parameter]} ({PARAMETER_UNITS[parameter]})",
                            ),
                            width="stretch",
                        )

            st.subheader("Radar comparison")
            radar_ids = [jezero_id, *selected_ids]
            st.plotly_chart(
                normalized_terrain_radar(
                    comparison_terrain,
                    radar_ids,
                    scored_parameters,
                    name_map,
                    {
                        parameter: f"{PARAMETER_LABELS[parameter]} ({PARAMETER_UNITS[parameter]})"
                        for parameter in scored_parameters
                    },
                ),
                width="stretch",
            )
except Exception as error:
    st.error(f"Could not build the terrain comparison: {error}")