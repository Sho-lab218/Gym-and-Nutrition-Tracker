# tools_fix_csvs.py
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

BW = DATA / "bodyweight.csv"
MEALS = DATA / "meals.csv"

def fix_bodyweight():
    cols = ["date","body_weight_lbs","goal_weight_lbs"]
    if not BW.exists():
        print("No bodyweight.csv found")
        return
    # Try robust read (handles bad lines)
    df = pd.read_csv(BW, header=0, dtype=str, on_bad_lines="skip", engine="python")
    # keep only first 3 cols or add missing
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[cols]
    # types
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["body_weight_lbs"] = pd.to_numeric(df["body_weight_lbs"], errors="coerce")
    df["goal_weight_lbs"] = pd.to_numeric(df["goal_weight_lbs"], errors="coerce")
    df = df.dropna(subset=["date","body_weight_lbs"]).sort_values("date")
    df.to_csv(BW, index=False)
    print(f"Rewrote {BW} with {len(df)} rows")

def fix_meals():
    cols = ["date","calories","protein_g","carbs_g","fat_g","notes"]
    if not MEALS.exists():
        print("No meals.csv found")
        return
    df = pd.read_csv(MEALS, header=0, dtype=str, on_bad_lines="skip", engine="python")
    # upgrade old 4-col files
    if {"date","calories","protein_g","notes"}.issubset(df.columns) and "carbs_g" not in df.columns:
        df["carbs_g"] = "0"
        df["fat_g"] = "0"
    # ensure all expected columns exist
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[cols]
    # types
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in ["calories","protein_g","carbs_g","fat_g"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df = df.dropna(subset=["date"]).sort_values("date")
    df.to_csv(MEALS, index=False)
    print(f"Rewrote {MEALS} with {len(df)} rows")

if __name__ == "__main__":
    fix_bodyweight()
    fix_meals()
    print("Done.")
