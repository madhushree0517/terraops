import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def terrain_metric_chart(terrain: pd.DataFrame, metric: str) -> go.Figure:
    """Create a simple candidate-site chart for one terrain metric."""
    return px.bar(terrain, x="site_id", y=metric, title=metric.replace("_", " ").title())


def slope_histogram_chart(histograms: pd.DataFrame) -> go.Figure:
    """Create readable, translucent site overlays with draft threshold markers."""
    colors = {
        "atacama": "#4CC9F0",
        "ladakh": "#FFB000",
        "askja": "#7AE582",
        "jezero": "#FF6B9A",
    }
    fallback_colors = ("#B8A1FF", "#F4A261", "#80ED99", "#FF8FA3")
    figure = go.Figure()
    for index, (site_id, site_rows) in enumerate(histograms.groupby("site_id", sort=False)):
        site_key = str(site_id).casefold()
        color = colors.get(site_key, fallback_colors[index % len(fallback_colors)])
        figure.add_trace(
            go.Bar(
                x=site_rows["bin_start"],
                y=site_rows["share"],
                width=1,
                name=str(site_id).title(),
                marker={"color": color, "opacity": 0.55},
                hovertemplate=(
                    "%{x:.0f} to %{customdata:.0f}"
                    "<br>Share of valid pixels: %{y:.2%}<extra>%{fullData.name}</extra>"
                ),
                customdata=site_rows["bin_end"],
            )
        )
    figure.update_layout(
        barmode="overlay",
        xaxis_title="Slope value (unit unconfirmed)",
        yaxis_title="Share of valid pixels",
        legend_title="Site",
    )
    for threshold in (10, 17, 24):
        figure.add_vline(
            x=threshold,
            line_dash="dash",
            line_color="#E8EDF2",
            annotation_text=str(threshold),
            annotation_position="top",
            annotation_font_color="#FFFFFF",
        )
    return figure


def terrain_parameter_chart(
    terrain: pd.DataFrame,
    sites: pd.DataFrame,
    site_ids: list[str],
    parameter: str,
    label: str | None = None,
) -> go.Figure:
    selected_sites = sites.loc[sites["site_id"].isin(site_ids), ["site_id", "name", "body"]]
    chart_data = selected_sites.merge(terrain, on="site_id", how="left")
    chart_data["role"] = chart_data["body"].map(
        {"Mars": "Jezero reference", "Earth": "Earth candidate"}
    )
    figure = px.bar(
        chart_data,
        x="name",
        y=parameter,
        color="role",
        barmode="group",
        title=label or parameter.replace("_", " ").title(),
        labels={"name": "Site", "role": "Site type", parameter: label or parameter},
    )
    figure.update_layout(legend_title_text="")
    return figure


def normalized_terrain_radar(
    terrain: pd.DataFrame,
    site_ids: list[str],
    parameter_names: list[str],
    display_names: dict[str, str],
    metric_labels: dict[str, str] | None = None,
) -> go.Figure:
    visible = terrain.loc[terrain["site_id"].isin(site_ids)].set_index("site_id")
    normalized = pd.DataFrame(index=visible.index)
    for parameter in parameter_names:
        values = pd.to_numeric(visible[parameter], errors="coerce")
        minimum = values.min(skipna=True)
        maximum = values.max(skipna=True)
        if pd.isna(minimum) or pd.isna(maximum):
            normalized[parameter] = float("nan")
        elif maximum == minimum:
            normalized[parameter] = values.map(lambda value: 1.0 if pd.notna(value) else float("nan"))
        else:
            normalized[parameter] = (values - minimum) / (maximum - minimum)

    figure = go.Figure()
    theta = [
        (metric_labels or {}).get(parameter, parameter.replace("_", " ").title())
        for parameter in parameter_names
    ]
    for site_id in site_ids:
        if site_id not in normalized.index:
            continue
        values = [
            None if pd.isna(value) else float(value)
            for value in normalized.loc[site_id, parameter_names].tolist()
        ]
        figure.add_trace(
            go.Scatterpolar(
                r=values + values[:1],
                theta=theta + theta[:1],
                name=display_names.get(site_id, site_id),
                connectgaps=False,
                fill="toself" if all(value is not None for value in values) else None,
            )
        )
    figure.update_layout(
        title="Normalized terrain values (0-1 within displayed sites)",
        polar={"radialaxis": {"visible": True, "range": [0, 1]}},
        showlegend=True,
    )
    return figure