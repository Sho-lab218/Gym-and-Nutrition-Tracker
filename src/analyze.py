import pandas as pd


def weekly_volume(df: pd.DataFrame) -> pd.DataFrame:
    needed = {"year","week","exercise","volume"}
    if not needed.issubset(df.columns):
        raise ValueError("DataFrame missing required columns")
    out = (df.groupby(["year","week","exercise"], as_index=False)
             .agg(weekly_volume=("volume","sum"),
                  sessions=("id","count")))
    out["year_week"] = out["year"].astype(str) + "-W" + out["week"].astype(str)
    return out


def estimate_1rm_row(row):
    return row["weight_kg"] * (1 + row["reps"]/30.0)


def weekly_best_1rm(df: pd.DataFrame, exercise: str) -> pd.DataFrame:
    dfe = df[df["exercise"] == exercise].copy()
    if dfe.empty:
        return pd.DataFrame(columns=["year","week","year_week","best_1rm"])
    dfe["est_1rm"] = dfe.apply(estimate_1rm_row, axis=1)
    out = (dfe.groupby(["year","week"], as_index=False)
             .agg(best_1rm=("est_1rm","max")))
    out["year_week"] = out["year"].astype(str) + "-W" + out["week"].astype(str)
    out = out.sort_values(["year","week"]).reset_index(drop=True)
    return out


def personal_bests(df: pd.DataFrame) -> pd.DataFrame:
    dfe = df.copy()
    if dfe.empty:
        return dfe
    dfe["est_1rm"] = dfe.apply(estimate_1rm_row, axis=1)
    idx = dfe.groupby("exercise")["est_1rm"].idxmax()
    return dfe.loc[idx, ["exercise","date","weight_kg","reps","est_1rm"]].sort_values("exercise")