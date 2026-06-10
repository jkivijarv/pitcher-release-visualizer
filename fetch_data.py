"""
fetch_data.py — the data pipeline (Part 1 of the project).

Pulls one season of Statcast pitch data from Baseball Savant (via pybaseball),
averages each pitcher's release point, and saves a tiny summary file that the
Streamlit app reads.

Usage:
    python fetch_data.py 2024                       # full 2024 season
    python fetch_data.py 2024 2024-06-01 2024-06-02 # a small window (for testing)

Output:
    data/agg_<year>.parquet  — one row per pitcher
"""

import sys
from pathlib import Path

import pandas as pd
from pybaseball import cache, statcast

# Save raw downloads to disk so re-runs (and the nightly refresh) reuse them
# instead of re-downloading days we've already fetched.
cache.enable()

# The three release-point numbers we care about (all in feet, catcher's POV).
RELEASE_COLS = ["release_pos_x", "release_pos_z", "release_extension"]

# Game types that "count": regular season (R) + the playoff rounds
# (F=wild card, D=division, L=league championship, W=World Series).
# Everything else (S=spring training, E=exhibition, A=All-Star) is dropped.
KEEP_GAME_TYPES = {"R", "F", "D", "L", "W"}

# Where the saved summary files live.
DATA_DIR = Path(__file__).parent / "data"


def fetch_season(year: int, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Download every pitch in the date range as a DataFrame (one row per pitch)."""
    # Default to a window that comfortably covers the regular season + playoffs.
    start = start or f"{year}-03-15"
    end = end or f"{year}-11-15"
    print(f"Fetching pitches from {start} to {end} ...")
    return statcast(start, end)


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse pitch-level rows into one averaged row per pitcher."""
    # 1. A pitcher's team isn't a direct column, so derive it: in the TOP of an
    #    inning the HOME team is pitching; in the BOTTOM the AWAY team pitches.
    df = df.copy()
    df["pitcher_team"] = df["home_team"].where(df["inning_topbot"] == "Top", df["away_team"])

    # 2a. Keep only games that "count" (regular season + playoffs); drop spring
    #     training, exhibition, and All-Star games.
    df = df[df["game_type"].isin(KEEP_GAME_TYPES)]

    # 2b. Drop any pitch missing a release value (can't average what isn't there).
    df = df.dropna(subset=RELEASE_COLS)

    # 3. Group all pitches by pitcher id, then summarize each pile.
    agg = df.groupby("pitcher").agg(
        player_name=("player_name", "first"),                 # name is the same on every row
        p_throws=("p_throws", "first"),                       # handedness, same every row
        team=("pitcher_team", lambda s: s.mode().iat[0]),     # the team he threw most pitches for
        n=("release_pos_x", "size"),                          # how many pitches (the weight!)
        release_pos_x=("release_pos_x", "mean"),              # average horizontal release
        release_pos_z=("release_pos_z", "mean"),              # average release height
        release_extension=("release_extension", "mean"),      # average extension
    ).reset_index()                                           # turn the pitcher-id index back into a column

    return agg


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python fetch_data.py <year> [start_date] [end_date]")
        sys.exit(1)

    year = int(sys.argv[1])
    start = sys.argv[2] if len(sys.argv) > 2 else None
    end = sys.argv[3] if len(sys.argv) > 3 else None

    df = fetch_season(year, start, end)
    agg = aggregate(df)
    agg["season"] = year  # tag every row with its season, so files can be combined later

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / f"agg_{year}.parquet"
    agg.to_parquet(out_path, index=False)

    print(f"Saved {len(agg)} pitchers to {out_path}")


if __name__ == "__main__":
    main()
