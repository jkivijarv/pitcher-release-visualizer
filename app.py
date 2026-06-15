"""
app.py — the Streamlit app (Part 2 of the project).

Run locally with:
    streamlit run app.py

Streamlit re-runs this whole file top-to-bottom every time a widget changes.
"""

from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

from viz import COLOR_COLUMNS, build_figure

DATA_DIR = Path(__file__).parent / "data"

# The three averaged columns we recombine across seasons.
RELEASE_COLS = ["release_pos_x", "release_pos_z", "release_extension"]


def combine_seasons(stacked: pd.DataFrame) -> pd.DataFrame:
    """Merge one-row-per-pitcher-per-season into one row per pitcher.

    Weighted average (by pitch count n) so a heavy season counts more than a
    light one. Name/team are taken from the pitcher's most recent season.
    """
    stacked = stacked.sort_values("season")        # so "last" picks the newest season
    w = stacked.copy()
    for c in RELEASE_COLS:
        w[c] = w[c] * w["n"]                        # numerator pieces: mean * n
    out = w.groupby("pitcher", as_index=False).agg(
        player_name=("player_name", "last"),
        p_throws=("p_throws", "last"),
        team=("team", "last"),
        n=("n", "sum"),
        release_pos_x=("release_pos_x", "sum"),
        release_pos_z=("release_pos_z", "sum"),
        release_extension=("release_extension", "sum"),
    )
    for c in RELEASE_COLS:
        out[c] = out[c] / out["n"]                  # weighted sum / total pitches
    return out


@st.cache_data
def load_seasons() -> dict[int, pd.DataFrame]:
    """Read every data/agg_<year>.parquet into a dict keyed by year.

    Cached, so the files are read once, not on every widget interaction.
    """
    frames: dict[int, pd.DataFrame] = {}
    for path in sorted(DATA_DIR.glob("agg_*.parquet")):
        year = int(path.stem.split("_")[1])     # "agg_2024" -> 2024
        frames[year] = pd.read_parquet(path)
    return frames


# --- Page setup ---------------------------------------------------------------
st.set_page_config(page_title="Pitcher Release Points", layout="wide")
# Fit the page to the viewport so there's no vertical page-scroll fighting the
# 3D plot's touch gestures — the plot fills the screen height instead. Title,
# help, and all filters live in the sidebar to keep the main area plot-only.
st.markdown(
    "<style>[data-testid='stMain']{overflow:hidden;}"
    ".block-container{padding:0.5rem 1rem 0 1rem;}</style>",
    unsafe_allow_html=True,
)

# Measure the browser's viewport height (called inside the sidebar so its tiny
# helper element never touches the main plot area). Returns None on the first
# run, then the pixel value after a quick round-trip; fall back to 700 until then.
with st.sidebar:
    viewport_h = streamlit_js_eval(js_expressions="window.innerHeight", key="viewport_h")
chart_h = int(viewport_h) - 20 if viewport_h else 700

seasons = load_seasons()
available_years = sorted(seasons.keys())

# --- Sidebar: title, help, and all the toggles --------------------------------
st.sidebar.title("Pitcher Release Points")
st.sidebar.caption(
    "Every MLB pitcher's average release point in 3D. "
    "Drag to rotate · pinch or scroll to zoom · tap a dot for details."
)
st.sidebar.header("Filters")
all_time = st.sidebar.checkbox("All time (every season)")
if all_time:
    chosen_years = available_years
    st.sidebar.caption(
        f"Using all {len(available_years)} seasons "
        f"({min(available_years)}–{max(available_years)})"
    )
else:
    chosen_years = st.sidebar.multiselect(
        "Seasons", available_years, default=[max(available_years)]
    )
color_mode = st.sidebar.radio("Color by", list(COLOR_COLUMNS.keys()))

# --- Guard: need at least one season ------------------------------------------
if not chosen_years:
    st.warning("Pick at least one season in the sidebar.")
    st.stop()   # halts this top-to-bottom pass right here

# --- Combine the chosen seasons -----------------------------------------------
# Stack the chosen seasons, then collapse to one weighted dot per pitcher.
stacked = pd.concat([seasons[y] for y in chosen_years], ignore_index=True)
df = combine_seasons(stacked)

# --- Data-dependent filters ---------------------------------------------------
# Pitcher search: leave empty to show everyone, or pick one+ names to focus.
all_names = sorted(df["player_name"].unique())
chosen_names = st.sidebar.multiselect("Search pitchers (empty = all)", all_names)

# Pitch-count range: show only pitchers whose pitch count is within [low, high].
n_min, n_max = int(df["n"].min()), int(df["n"].max())
if n_min == n_max:           # st.slider needs min < max
    n_max = n_min + 1
count_low, count_high = st.sidebar.slider(
    "Pitch count range", min_value=n_min, max_value=n_max, value=(n_min, n_max)
)

# Apply both filters (a pitcher must pass each).
if chosen_names:
    df = df[df["player_name"].isin(chosen_names)]
df = df[(df["n"] >= count_low) & (df["n"] <= count_high)]

# --- Draw ---------------------------------------------------------------------
if df.empty:
    st.warning("No pitchers match the current filters.")
    st.stop()

# Status line goes in the sidebar so the main area stays plot-only.
st.sidebar.caption(
    f"**{len(df)}** pitchers · seasons {', '.join(map(str, chosen_years))} · "
    f"pitch count {count_low}–{count_high}"
)

fig = build_figure(df, color_mode=color_mode, height=chart_h)
st.plotly_chart(
    fig, use_container_width=True, config={"displaylogo": False, "responsive": True}
)
