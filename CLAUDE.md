# CLAUDE.md — Pitcher Release-Point Visualizer

> The developer is learning programming; explain changes and the "why," not just the "how."
> (Global teaching prefs live in `~/.claude/CLAUDE.md`.)

## What this is

An interactive 3D web app showing **every MLB pitcher's average release point**
(horizontal `release_pos_x`, vertical `release_pos_z`, extension `release_extension`)
plotted together — the whole league at once, vs. MLB Savant's one-pitcher-one-game tool.
Built for the developer's brother-in-law (uses Mac/iPhone/iPad → must be mobile-friendly).

## Architecture (two clean halves)

```
fetch_data.py   -->  data/agg_<year>.parquet   -->  app.py + viz.py (Streamlit + Plotly)
(slow pipeline)        (tiny committed files)         (fast UI; only reads the files)
```

- **`fetch_data.py`** — pulls one season of Statcast via pybaseball, keeps regular-season +
  playoffs only (`KEEP_GAME_TYPES`), averages each pitcher's release point, writes one
  `data/agg_<year>.parquet` (one row per pitcher, with pitch count `n`). `cache.enable()` keeps
  raw pulls on disk. CLI: `python fetch_data.py 2024 [start] [end]`.
- **`viz.py`** — `build_figure(df, color_mode, height)` builds the Plotly `Scatter3d`. Holds the
  axis mapping (x=horizontal, y=extension, z=height), `TEAM_COLORS`, `HAND_COLORS`, hover template.
- **`app.py`** — Streamlit UI. Loads all parquet files (`@st.cache_data`), sidebar filters
  (seasons / All time / color / pitcher search / pitch-count range), `combine_seasons()` does the
  **pitch-count-weighted** multi-season average, then draws the chart.

## Commands (Windows — always use the venv's python!)

```bash
# Every command uses the venv python, NOT bare `python`:
.venv/Scripts/python.exe fetch_data.py 2024            # build/refresh one season
.venv/Scripts/python.exe -m streamlit run app.py --server.headless true --server.port 8501
.venv/Scripts/python.exe -m pip install -r requirements.txt
```
(On the brother's Mac the venv folder is `bin/` not `Scripts/`.)

## Gotchas (learned the hard way)

- **Restart Streamlit after editing `viz.py`.** Streamlit hot-reloads `app.py` but keeps imported
  modules (`viz.py`) cached — changes there (e.g. removing a title) need a server restart.
- **`data/` IS committed** (not gitignored) — the hosted app reads those files. `.venv/` and
  `preview.html` are ignored.
- **Combining seasons needs `n`.** Weighted mean = Σ(meanᵢ·nᵢ)/Σnᵢ; that's why each row stores its
  pitch count. Plain averaging of season-averages is wrong.
- **Position players inflate counts.** Guys who pitched in blowouts (e.g. Miguel Sanó) appear with
  tiny `n` — the pitch-count slider filters them; default dataset keeps them (they did pitch).
- **"All time" = 2015+** (Statcast tracking start). ~850–900 pitchers per season is normal.
- **gh CLI PATH:** after installing gh, refresh PATH in an existing shell:
  `$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")`

## Deployment

- GitHub repo: `jkivijarv/pitcher-release-visualizer` (public). Hosted on **Streamlit Community
  Cloud** (main file `app.py`, branch `main`).
- **Nightly auto-refresh:** `.github/workflows/refresh.yml` runs daily (11:00 UTC), re-pulls the
  current season, commits `data/`, which auto-redeploys the site. Confirmed working.
- Pushing any commit to `main` redeploys the hosted app.

## Current status

Shipped and live with seasons **2015–2026**. Polish done (hover, team colors, sidebar-only chrome).
**Viewport-fit done (shipped 2026-06-14):** the chart fills the browser viewport exactly (no page
scroll that fights touch gestures on mobile) via `streamlit-js-eval` measuring `window.innerHeight`
and setting the chart's pixel height (`chart_h = innerHeight - 20`, fallback 700). No open work.

## Possible v2 (pending brother-in-law feedback)

One-dot-per-pitch-type split (his original screenshot color-codes pitch types), arm-angle metric,
batter-handedness filter. All are contained changes to `fetch_data.py` + a small chart tweak.
