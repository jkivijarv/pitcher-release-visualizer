# League-Wide Pitcher Release-Point Visualizer

An interactive 3D visualization of **every MLB pitcher's average release point**
(horizontal, vertical, and extension) plotted together — inspired by MLB Savant's
Pitch 3D tool, but showing the whole league at once instead of one pitcher in one game.

Built with Python, [pybaseball](https://github.com/jldbc/pybaseball) (Statcast data),
pandas (aggregation), [Plotly](https://plotly.com/python/) (3D chart), and
[Streamlit](https://streamlit.io/) (web UI).

## What it shows

Each dot is one pitcher's **average release point** over the selected seasons:

- **x** = horizontal release (feet, catcher's view) — lefties and righties split apart
- **y** = extension toward the plate (feet)
- **z** = release height (feet)

Filters: choose any season(s) or "all time", color by handedness/team, search for
specific pitchers, and restrict to a pitch-count range.

## Project layout

| File | Role |
|------|------|
| `fetch_data.py` | Pipeline: pulls a season from Statcast, averages each pitcher's release point, writes `data/agg_<year>.parquet` |
| `viz.py` | Builds the Plotly 3D figure (shared by the preview and the app) |
| `app.py` | The Streamlit app (the toggles + chart) |
| `data/` | Small per-season aggregate files (committed, so the hosted app can read them) |

## Run it locally

```bash
# 1. Create the virtual environment and install dependencies
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux

# 2. Build data for a season (repeat per year you want)
.venv/Scripts/python.exe fetch_data.py 2024

# 3. Launch the app
.venv/Scripts/python.exe -m streamlit run app.py
```

Then open http://localhost:8501.

## Data scope

- Statcast pitch tracking begins in **2015**, so "all time" means 2015–present.
- Only **regular season + playoffs** are included (spring training / exhibition /
  All-Star games are dropped).
- Re-running `fetch_data.py` for the current year refreshes it with newer games.
