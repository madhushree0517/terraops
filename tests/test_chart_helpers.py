import pandas as pd

from app.components.chart_helpers import slope_histogram_chart


def test_slope_histogram_is_translucent_overlaid_and_keeps_thresholds():
    histograms = pd.DataFrame(
        [
            {"site_id": "atacama", "bin_start": 0, "bin_end": 1, "share": 0.6},
            {"site_id": "ladakh", "bin_start": 0, "bin_end": 1, "share": 0.4},
        ]
    )

    figure = slope_histogram_chart(histograms)

    assert figure.layout.barmode == "overlay"
    assert figure.layout.yaxis.title.text == "Share of valid pixels"
    assert [trace.marker.opacity for trace in figure.data] == [0.55, 0.55]
    assert len({trace.marker.color for trace in figure.data}) == 2
    assert [(shape.x0, shape.line.dash) for shape in figure.layout.shapes] == [
        (10, "dash"), (17, "dash"), (24, "dash"),
    ]