import pandas as pd

from app.components.chart_helpers import slope_histogram_chart, terrain_slope_distribution_chart


def test_slope_histogram_uses_lines_and_emphasizes_selected_site():
    histograms = pd.DataFrame(
        [
            {"site_id": "atacama", "bin_start": 0, "bin_end": 1, "share": 0.6},
            {"site_id": "ladakh", "bin_start": 0, "bin_end": 1, "share": 0.4},
        ]
    )

    figure = slope_histogram_chart(histograms, emphasized_site="atacama")

    assert figure.layout.yaxis.title.text == "Share of valid pixels"
    assert [trace.mode for trace in figure.data] == ["lines", "lines"]
    assert [trace.opacity for trace in figure.data] == [1.0, 0.35]
    assert [trace.line.width for trace in figure.data] == [3.5, 1.2]
    assert len({trace.line.color for trace in figure.data}) == 2
    assert [(shape.x0, shape.line.dash) for shape in figure.layout.shapes] == [
        (10, "dash"), (17, "dash"), (24, "dash"),
    ]


def test_terrain_distribution_chart_has_percent_axes_and_threshold_markers():
    histograms = pd.DataFrame([
        {"site_id": "atacama", "bin_start": 0, "bin_end": 1, "share": 0.6},
        {"site_id": "atacama", "bin_start": 1, "bin_end": 2, "share": 0.4},
    ])
    figure = terrain_slope_distribution_chart(histograms, mode="Distribution")
    assert figure.layout.height == 420
    assert figure.layout.xaxis.title.text == "Slope value"
    assert "unit unconfirmed" not in figure.data[0].hovertemplate.casefold()
    assert figure.layout.yaxis.title.text == "Share of valid area (%)"
    assert figure.data[0].line.width == 3
    assert len(figure.layout.shapes) == 3
    cumulative = terrain_slope_distribution_chart(histograms, mode="Share steeper than")
    assert list(cumulative.data[0].y) == [100.0, 40.0]
