import streamlit as st
import pandas as pd

LOGO_PATH = "assets/logo.png"  # optional; can remove if no logo

def sidebar_common(title: str, subtitle: str = ""):
    s = st.sidebar
    try:
        s.image(LOGO_PATH, width=120)
    except Exception:
        pass
    s.markdown(f"### {title}")
    if subtitle:
        s.caption(subtitle)
    s.markdown("---")


def sidebar_workouts(wdf: pd.DataFrame):
    s = st.sidebar
    groups = []
    if "muscle_group" in wdf.columns and not wdf.empty:
        groups = sorted(wdf["muscle_group"].dropna().unique().tolist())
    picked = s.multiselect("Muscle groups", groups, default=groups)
    if picked:
        wdf = wdf[wdf["muscle_group"].isin(picked)]
    exercises = sorted(wdf["exercise"].unique().tolist()) if not wdf.empty else []
    exercise = s.selectbox("Exercise", exercises, index=0 if exercises else None)
    horizon = s.slider("Forecast window (weeks)", 2, 26, 8)
    algo = s.selectbox("Forecast model", ["Auto (best)", "Holt-Winters", "Linear"])
    return (wdf if not wdf.empty else pd.DataFrame()), picked, exercise, horizon, algo


# src/ui.py  (replace the function)
import streamlit as st

def sidebar_progress():
    s = st.sidebar
    horizon = s.slider("Forecast window (weeks)", 4, 52, 12)
    # Target rate, optional. 0.0 means "auto from recent trend".
    target_rate = s.slider("Target rate (% bodyweight / week)", -1.5, 1.5, 0.0, step=0.1)
    algo = s.selectbox("Model", ["Realistic (clamped)", "Holt-Winters", "Linear"])
    # None if user leaves at 0.0
    use_rate = None if abs(target_rate) < 1e-9 else target_rate
    return horizon, algo, use_rate



def sidebar_nutrition():
    s = st.sidebar
    s.caption("Tip: add `date, calories, protein_g` to meals.csv for richer charts.")