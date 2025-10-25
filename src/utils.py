import os
import csv
import numpy as np
import pandas as pd

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------- meals (nutrition) -----------------------

MEAL_COLS = ["date", "calories", "protein_g", "carbs_g", "fat_g", "notes"]

def load_meals(path: str) -> pd.DataFrame:
    """Load meals CSV → normalized dataframe with a proper datetime `date`."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=MEAL_COLS)

    df = pd.read_csv(path)
    for c in MEAL_COLS:
        if c not in df.columns:
            df[c] = np.nan

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).copy()
    df["date"] = df["date"].dt.normalize()

    for c in ["calories", "protein_g", "carbs_g", "fat_g"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    return df[MEAL_COLS].sort_values("date").reset_index(drop=True)

def meals_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate meals to daily totals with a datetime `date` column (00:00)."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "calories", "protein_g", "carbs_g", "fat_g"])

    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce").dt.normalize()
    out = (d.groupby("date", as_index=False)
             .agg(calories=("calories","sum"),
                  protein_g=("protein_g","sum"),
                  carbs_g=("carbs_g","sum"),
                  fat_g=("fat_g","sum")))
    return out.sort_values("date").reset_index(drop=True)

# -------------------- workouts helpers (volume etc) --------------------

def load_workouts(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=["date","exercise","sets","reps","weight_kg","muscle_group","notes","volume","week","year"])
    try:
        df = pd.read_csv(path)
        if df.empty:
            return pd.DataFrame(columns=["date","exercise","sets","reps","weight_kg","muscle_group","notes","volume","week","year"])
        
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        for c in ["sets","reps","weight_kg"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

        # total volume per row
        if {"sets","reps","weight_kg"}.issubset(df.columns):
            df["volume"] = df["sets"] * df["reps"] * df["weight_kg"]
        else:
            df["volume"] = 0.0

        # week/year for grouping
        df = df.dropna(subset=["date"])
        if not df.empty and "date" in df.columns:
            iso = df["date"].dt.isocalendar()
            df["week"] = iso.week.astype(int)
            df["year"] = iso.year.astype(int)
        else:
            df["week"] = 0
            df["year"] = 0

        return df.sort_values("date").reset_index(drop=True)
    except Exception as e:
        print(f"Error loading workouts: {e}")
        return pd.DataFrame(columns=["date","exercise","sets","reps","weight_kg","muscle_group","notes","volume","week","year"])

# ---------------------- bodyweight helpers ----------------------

def read_bodyweight(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame(columns=["date","body_weight_lbs","goal_weight_lbs"])
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    for c in ["body_weight_lbs","goal_weight_lbs"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

def write_bodyweight(path: str, df: pd.DataFrame) -> None:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out = out.sort_values("date")
    out.to_csv(path, index=False)

def upsert_weight_entry(path: str, weight_lbs: float, when=None, goal_lbs=None) -> None:
    """Insert or replace the entry for `when` (date-like)."""
    ts = pd.to_datetime(when if when is not None else pd.Timestamp.today()).normalize()
    cur = read_bodyweight(path)
    cur = cur[cur["date"] != ts]
    newrow = pd.DataFrame([{
        "date": ts,
        "body_weight_lbs": float(weight_lbs),
        "goal_weight_lbs": (None if goal_lbs in (None, 0, "") else float(goal_lbs))
    }])
    out = pd.concat([cur, newrow], ignore_index=True).sort_values("date")
    write_bodyweight(path, out)

# --------------- tiny JSON helper for profile ----------------
def write_json(path: str, obj: dict) -> None:
    import json
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
