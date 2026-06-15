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

# Fixed colors for handedness so R/L stay consistent every run.
HAND_COLORS = {"R": "#1f77b4", "L": "#ff7f0e"}

# Best-effort MLB team primary colors, keyed by Statcast's team codes.
TEAM_COLORS = {
    "AZ": "#A71930", "ATL": "#CE1141", "BAL": "#DF4601", "BOS": "#BD3039",
    "CHC": "#0E3386", "CWS": "#27251F", "CIN": "#C6011F", "CLE": "#0C2340",
    "COL": "#333366", "DET": "#0C2340", "HOU": "#EB6E1F", "KC": "#004687",
    "LAA": "#BA0021", "LAD": "#005A9C", "MIA": "#00A3E0", "MIL": "#12284B",
    "MIN": "#002B5C", "NYM": "#FF5910", "NYY": "#003087", "OAK": "#003831",
    "ATH": "#003831", "PHI": "#E81828", "PIT": "#FDB827", "SD": "#2F241D",
    "SF": "#FD5A1E", "SEA": "#0C2C56", "STL": "#C41E3A", "TB": "#092C5C",
    "TEX": "#003278", "TOR": "#134A8E", "WSH": "#AB0003",
}


def _color_map(df: pd.DataFrame, color_mode: str):
    """Return a {value: color} map for the chosen color column (or None)."""
    if color_mode == "Handedness":
        return HAND_COLORS
    if color_mode == "Team":
        # Real team color where known; distinct fallbacks for anything missing
        # (e.g. a relocated team whose code we don't have yet).
        pool = iter(px.colors.qualitative.Dark24 + px.colors.qualitative.Light24)
        used = set(TEAM_COLORS.values())
        out = {}
        for team in sorted(df["team"].dropna().unique()):
            if team in TEAM_COLORS:
                out[team] = TEAM_COLORS[team]
            else:
                c = next(pool)
                while c in used:
                    c = next(pool)
                used.add(c)
                out[team] = c
        return out
    return None


def build_figure(df: pd.DataFrame, color_mode: str = "None", height: int | None = None):
    """Return an interactive 3D scatter: one marker per pitcher.

    color_mode: one of COLOR_COLUMNS' keys ("None", "Handedness", "Team").
    height: exact pixel height (to fit the viewport), or None to autosize.
    """
    color_col = COLOR_COLUMNS.get(color_mode)
    fig = px.scatter_3d(
        df,
        x=X_COL,
        y=Y_COL,
        z=Z_COL,
        color=color_col,
        color_discrete_map=_color_map(df, color_mode),
        custom_data=["player_name", "team", "p_throws", "n",
                     "release_pos_x", "release_pos_z", "release_extension"],
    )
    # One rich tooltip per dot, with labels + units.
    fig.update_traces(
        marker=dict(size=4, opacity=0.85),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]} · throws %{customdata[2]}<br>"
            "Pitches: %{customdata[3]:,}<br>"
            "Horizontal: %{customdata[4]:.2f} ft<br>"
            "Height: %{customdata[5]:.2f} ft<br>"
            "Extension: %{customdata[6]:.2f} ft"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        height=height,                   # exact pixel height (viewport-fit) or None
        autosize=True,
        scene=dict(
            xaxis_title=X_TITLE,
            yaxis_title=Y_TITLE,
            zaxis_title=Z_TITLE,
        ),
        legend=dict(title=(color_mode if color_col else None)),
        margin=dict(l=0, r=0, t=0, b=0),  # no in-figure title; use the full box
    )
    return fig


if __name__ == "__main__":
    data_path = Path(__file__).parent / "data" / "agg_2024.parquet"
    df = pd.read_parquet(data_path)
    fig = build_figure(df)
    out_path = Path(__file__).parent / "preview.html"
    fig.write_html(out_path)
    print(f"Wrote {out_path} from {len(df)} pitchers")
