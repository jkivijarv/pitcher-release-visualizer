"""
viz.py — builds the 3D release-point chart (Part 2's drawing logic).

Kept as a reusable function so both a quick local preview AND the Streamlit
app can call the exact same figure-builder.

Quick preview:
    python viz.py          # reads data/agg_2024.parquet, writes preview.html
"""

from pathlib import Path

import pandas as pd
import plotly.express as px

# Which DataFrame column feeds each 3D axis, and the human-readable axis title.
X_COL, Y_COL, Z_COL = "release_pos_x", "release_extension", "release_pos_z"
X_TITLE = "Horizontal release (ft, catcher's view)"
Y_TITLE = "Extension toward plate (ft)"
Z_TITLE = "Release height (ft)"

# Maps a friendly color-toggle label to the DataFrame column that drives the
# dot colors. None means "all dots one color".
COLOR_COLUMNS = {
    "None": None,
    "Handedness": "p_throws",
    "Team": "team",
}


def build_figure(df: pd.DataFrame, color_mode: str = "None"):
    """Return an interactive 3D scatter: one marker per pitcher.

    color_mode: one of COLOR_COLUMNS' keys ("None", "Handedness", "Team").
    """
    color_col = COLOR_COLUMNS.get(color_mode)
    fig = px.scatter_3d(
        df,
        x=X_COL,
        y=Y_COL,
        z=Z_COL,
        color=color_col,            # None -> single color; else color by this column
        hover_name="player_name",   # bold title shown when you hover a dot
    )
    # Make the dots a readable size and slightly see-through (so clusters show depth).
    fig.update_traces(marker=dict(size=4, opacity=0.8))
    # Label the three axes and trim empty whitespace around the scene.
    fig.update_layout(
        title="Average release point by pitcher",
        scene=dict(
            xaxis_title=X_TITLE,
            yaxis_title=Y_TITLE,
            zaxis_title=Z_TITLE,
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


if __name__ == "__main__":
    data_path = Path(__file__).parent / "data" / "agg_2024.parquet"
    df = pd.read_parquet(data_path)
    fig = build_figure(df)
    out_path = Path(__file__).parent / "preview.html"
    fig.write_html(out_path)
    print(f"Wrote {out_path} from {len(df)} pitchers")
