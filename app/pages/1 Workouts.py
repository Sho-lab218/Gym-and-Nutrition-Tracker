import sys, os, csv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.style import apply_mpl_style
from src.ui import sidebar_common
from src.utils import load_workouts
from src.catalog import EXERCISE_CATALOG

apply_mpl_style(dark=True)
st.title("🏋️ Workouts")
sidebar_common("Workouts", "Log sessions • Progress • Forecast")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
WK_PATH  = os.path.join(DATA_DIR, "workouts.csv")
os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(WK_PATH):
    pd.DataFrame(columns=[
        "date","exercise","sets","reps","weight_kg","muscle_group","notes"
    ]).to_csv(WK_PATH, index=False)

# -------- Reset
with st.expander("⚙️ Reset Workouts", expanded=False):
    st.caption("Delete all logged workouts and start with an empty sheet.")
    if st.button("🗑️ Reset all workout data", type="primary", key="reset_workouts"):
        pd.DataFrame(columns=[
            "date","exercise","sets","reps","weight_kg","muscle_group","notes"
        ]).to_csv(WK_PATH, index=False)
        st.success("All workout data has been cleared.")
        st.rerun()

# -------- Log a workout
with st.expander("➕ Log a workout", expanded=True):
    c1, c2 = st.columns(2)
    wdate   = c1.date_input("Date", value=pd.Timestamp.today().date())
    group   = c2.selectbox("Muscle group", sorted(EXERCISE_CATALOG.keys()))
    exercise = st.selectbox("Exercise", EXERCISE_CATALOG.get(group, []))
    c3, c4, c5 = st.columns(3)
    sets   = c3.number_input("Sets", 1, 50, 3)
    reps   = c4.number_input("Reps", 1, 100, 8)
    weight = c5.number_input("Weight (kg)", min_value=0.0, step=0.5, value=0.0)
    notes  = st.text_input("Notes", value="")

    if st.button("Save workout", type="primary", key="save_workout"):
        with open(WK_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([pd.Timestamp(wdate).normalize().isoformat(), exercise, sets, reps, weight, group, notes])
        st.success("Saved.")
        st.rerun()

# -------- Load
wdf = load_workouts(WK_PATH)
if wdf.empty:
    c1,c2,c3 = st.columns(3)
    c1.metric("Sessions (this week)", 0)
    c2.metric("Total Volume", "0")
    c3.metric("Distinct Exercises", 0)
    st.info("Log your first workout above to see charts.")
    st.stop()

# -------- KPIs
this_week = wdf["week"].max()
sessions = int(wdf[wdf["week"]==this_week]["date"].nunique())
total_vol = int(wdf["volume"].sum())
distinct  = int(wdf["exercise"].nunique())

k1,k2,k3 = st.columns(3)
k1.metric("Sessions (this week)", sessions)
k2.metric("Total Volume", f"{total_vol:,}")
k3.metric("Distinct Exercises", distinct)

# -------- Progress chart (historical top weight)
st.subheader("Exercise progression (top weight)")
pc1, pc2 = st.columns(2)
sel_group = pc1.selectbox("Filter by muscle group", ["(All)"] + sorted(EXERCISE_CATALOG.keys()))
if sel_group == "(All)":
    ex_options = sorted(wdf["exercise"].unique())
else:
    ex_options = EXERCISE_CATALOG.get(sel_group, [])
sel_ex = pc2.selectbox("Exercise", ex_options, index=0 if ex_options else None)

if sel_ex:
    hist = wdf[wdf["exercise"] == sel_ex].copy()
    if hist.empty:
        st.info("No sets logged for this exercise yet.")
    else:
        prog = (hist.groupby("date", as_index=False)
                    .agg(top_weight=("weight_kg","max"))
                    .sort_values("date"))
        fig_prog = go.Figure()
        fig_prog.add_trace(go.Scatter(x=prog["date"], y=prog["top_weight"],
                                      mode="lines+markers", name="Top weight (kg)"))
        fig_prog.update_layout(title=f"{sel_ex} — top weight (history)",
                               xaxis_title="", yaxis_title="kg",
                               template="plotly_dark", height=360,
                               margin=dict(l=10,r=10,t=50,b=20))
        st.plotly_chart(fig_prog, use_container_width=True)

# -------- “If you keep training & dieting” forecast (up-only)
st.subheader("Projected strength (keep training & dieting)")
horizon = st.slider("Forecast horizon (weeks)", 4, 26, 8)

if sel_ex:
    hist = wdf[wdf["exercise"] == sel_ex].copy()
    if hist.empty or hist["weight_kg"].count() < 2:
        st.info("Log a couple of sessions for this exercise to show a forecast.")
    else:
        # weekly top weight series
        wk = (hist.groupby(pd.Grouper(key="date", freq="W-MON"))["weight_kg"]
                    .max().dropna().reset_index(name="top"))
        # simple slope on recent points, clamp to non-negative
        if len(wk) >= 2:
            import numpy as np
            t = np.arange(len(wk))
            A = np.vstack([np.ones_like(t), t]).T
            b0, b1 = np.linalg.lstsq(A, wk["top"].to_numpy(), rcond=None)[0]
            b1 = max(0.0, float(b1))
            t_last = t[-1]
            tf = np.arange(t_last+1, t_last+1+horizon)
            preds = b0 + b1*tf
            last_date = wk["date"].iloc[-1]
            future_dates = [last_date + pd.Timedelta(days=7*i) for i in range(1, horizon+1)]

            figf = go.Figure()
            figf.add_trace(go.Scatter(x=wk["date"], y=wk["top"], mode="lines+markers", name="Actual (weekly)"))
            figf.add_trace(go.Scatter(x=future_dates, y=preds, mode="lines+markers",
                                      name="Forecast", line=dict(dash="dash")))
            figf.update_layout(template="plotly_dark", height=380,
                               margin=dict(l=10,r=10,t=50,b=20))
            st.plotly_chart(figf, use_container_width=True)
