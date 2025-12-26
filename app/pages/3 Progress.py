# app/pages/3 Progress.py
import sys, os, csv, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from src.style import apply_mpl_style
from src.ui import sidebar_common
from src.utils import load_meals
from src.forecast import (
    estimate_tdee_msj,          # (sex, age, height_cm, weight_kg, activity)
    daily_kcal_vs_tdee,
    forecast_weight_energy,
    forecast_weight_realistic,  # target %/week -> realistic band + CI
)

apply_mpl_style(dark=True)
st.title("📈 Progress (Body Weight)")
sidebar_common("Progress", "Start → Goal → Log → Forecast")

# ── paths ───────────────────────────────────────────────────────────────
DATA_DIR   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
BW_PATH    = os.path.join(DATA_DIR, "bodyweight.csv")
PROFILE_FN = os.path.join(DATA_DIR, "profile.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ensure file exists with correct columns
if not os.path.exists(BW_PATH):
    pd.DataFrame(columns=["date","body_weight_lbs","goal_weight_lbs"]).to_csv(BW_PATH, index=False)

# helpers
def read_bw() -> pd.DataFrame:
    df = pd.read_csv(BW_PATH)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    for c in ("body_weight_lbs","goal_weight_lbs"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df



def write_bw(df: pd.DataFrame):
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out = out.sort_values("date")
    out.to_csv(BW_PATH, index=False)

def upsert_weight_for_date(the_date: date, weight_lbs: float, goal_lbs: float | None = None):
    d = read_bw()
    ts = pd.Timestamp(the_date).normalize()
    # remove any row with same date
    d = d[~(d["date"].dt.date == ts.date())]
    # append the new entry
    row = {
        "date": ts,
        "body_weight_lbs": float(weight_lbs),
        "goal_weight_lbs": (None if (goal_lbs is None or goal_lbs == 0) else float(goal_lbs)),
    }
    d = pd.concat([d, pd.DataFrame([row])], ignore_index=True).sort_values("date").reset_index(drop=True)
    write_bw(d)


# ── START & GOAL (baseline) ─────────────────────────────────────────────
with st.expander("🎯 Start & Goal", expanded=True):
    left, right = st.columns([4,1])

    with left:
        c1, c2 = st.columns(2)
        start_date = c1.date_input("Start date", value=date.today(), key="baseline_date")
        start_w    = c2.number_input("Start weight (lbs)", min_value=0.0, step=0.1, value=170.0, key="baseline_sw")

        g1, _ = st.columns([2,1])
        goal_w  = g1.number_input("Goal weight (lbs)", min_value=0.0, step=0.5, value=160.0, key="baseline_gw")

        if st.button("Set start & goal", type="primary", key="baseline_save"):
            cur = read_bw()
            start_ts = pd.Timestamp(start_date).normalize()

            # remove any existing baseline on the same day to avoid duplicates
            cur = cur[~(cur["date"].dt.date == start_ts.date())]
            base = pd.DataFrame([{
                "date": start_ts,
                "body_weight_lbs": start_w,
                "goal_weight_lbs": goal_w
            }])
            newdf = pd.concat([base, cur], ignore_index=True).sort_values("date")
            write_bw(newdf)
            st.success("Baseline saved.")
            st.rerun()

    with right:
        st.caption(" ")  # spacer
        st.caption(" ")
        # small reset button on the side that *replaces all data*
        if st.button("↺ Reset", help="Replace ALL data with this baseline only", key="baseline_reset"):
            start_ts = pd.Timestamp(start_date).normalize()
            base = pd.DataFrame([{
                "date": start_ts,
                "body_weight_lbs": start_w,
                "goal_weight_lbs": goal_w
            }])
            write_bw(base)
            st.success("All data cleared and replaced with the new baseline.")
            st.rerun()

# ── ADD WEIGHT ENTRY ────────────────────────────────────────────────────
with st.expander("➕ Add a weight entry", expanded=False):
    c1, c2, c3 = st.columns(3)
    entry_date = c1.date_input("Date", value=date.today(), key="log_date")
    entry_w    = c2.number_input("Body weight (lbs)", min_value=0.0, step=0.1, key="log_weight")
    goal_w_in  = c3.number_input("Goal (optional)", min_value=0.0, step=0.5, value=0.0, key="log_goal")

if st.button("Save entry", type="primary", key="log_save"):
    upsert_weight_for_date(entry_date, entry_w, goal_w_in if goal_w_in > 0 else None)
    st.success("Saved.")
    st.rerun()


# ── LOAD DATA ───────────────────────────────────────────────────────────
bw = read_bw()
if bw.empty or bw["body_weight_lbs"].dropna().empty:
    st.info("Add a baseline or your first weight to begin.")
    st.stop()

start_w   = float(bw["body_weight_lbs"].iloc[0])
current_w = float(bw["body_weight_lbs"].iloc[-1])
delta     = current_w - start_w
goal_col  = bw["goal_weight_lbs"].dropna()
goal_w    = float(goal_col.iloc[-1]) if not goal_col.empty else None

m1, m2, m3 = st.columns(3)
m1.metric("Start",   f"{start_w:.0f} lbs")
m2.metric("Current", f"{current_w:.0f} lbs", f"{delta:+.1f} lbs")
if goal_w is not None:
    m3.metric("Goal", f"{goal_w:.0f} lbs")

# ── TREND CHART ─────────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Scatter(x=bw["date"], y=bw["body_weight_lbs"], mode="lines+markers", name="Weight"))
if goal_w is not None:
    fig.add_hline(y=goal_w, line_dash="dash", annotation_text=f"Goal {goal_w:.0f} lbs")
fig.update_layout(
    title="Body Weight",
    xaxis_title="", yaxis_title="lbs",
    template="plotly_dark",
    height=380, margin=dict(l=10, r=10, t=50, b=20)
)
st.plotly_chart(fig, use_container_width=True)

# ── PROFILE (for TDEE + suggestions) ────────────────────────────────────
prof = {}
if os.path.exists(PROFILE_FN):
    try:
        prof = json.load(open(PROFILE_FN))
    except Exception:
        prof = {}
sex        = prof.get("sex", "Male")
age        = int(prof.get("age", 22))
height_cm  = float(prof.get("height_cm", 175))
activity   = prof.get("activity", "Moderate")  # Sedentary/Light/Moderate/Active/Very Active
# Use the *actual* current scale reading rather than profile's stored weight.
tdee_est = estimate_tdee_msj(sex, age, height_cm, current_w/2.20462, activity)

# ── FORECASTS ───────────────────────────────────────────────────────────
st.subheader("Forecasts")

tab_plan, tab_cal = st.tabs(["📐 Plan: lose / maintain / gain", "🔥 From calorie trend"])

with tab_plan:
    # bring back Lose / Maintain / Gain controls
    mode = st.radio(
        "Goal",
        ["Lose weight", "Maintain", "Gain weight"],
        index=0 if (goal_w is not None and goal_w < current_w) else (2 if goal_w is not None and goal_w > current_w else 1),
        horizontal=True,
        key="plan_mode",
    )

    if mode == "Maintain":
        pace_pct = st.slider("Pace (% bodyweight per week)", 0.0, 0.5, 0.0, 0.1, key="pace_maint")
        target_rate_pct = 0.0
    elif mode == "Lose weight":
        pace_pct = st.slider("Pace (% bodyweight lost per week)", 0.1, 2.0, 0.7, 0.1, key="pace_cut")
        target_rate_pct = -abs(pace_pct)
    else:
        pace_pct = st.slider("Pace (% bodyweight gained per week)", 0.1, 1.5, 0.5, 0.1, key="pace_gain")
        target_rate_pct = abs(pace_pct)

    horizon = st.slider("Forecast horizon (weeks)", 4, 26, 12, key="plan_hor")
    series_plan = forecast_weight_realistic(bw, horizon_weeks=horizon, target_rate_pct=target_rate_pct)

    # show suggested daily calories for the chosen pace
    # kg/week = pct/100 * current_kg ; kcal/day ≈ kg/week*7700 / 7 / adapt
    adapt = 0.75
    curr_kg = current_w / 2.20462
    kg_per_wk = curr_kg * (target_rate_pct/100.0)
    kcal_per_day_offset = (kg_per_wk * 7700.0) / 7.0 / adapt   # negative for loss
    suggested_intake = tdee_est + kcal_per_day_offset

    colA, colB = st.columns(2)
    colA.metric("Estimated TDEE", f"{tdee_est:.0f} kcal/day")
    colB.metric("Suggested daily calories", f"{suggested_intake:.0f} kcal/day", help="Based on your chosen pace")

    if series_plan.empty:
        st.info("Need a few weigh-ins to show a projection.")
    else:
        act  = series_plan[series_plan["kind"] == "actual"]
        pred = series_plan[series_plan["kind"] == "pred"]

        figp = go.Figure()
        figp.add_trace(go.Scatter(x=act["date"], y=act["value"], mode="lines+markers", name="Actual"))
        figp.add_trace(go.Scatter(x=pred["date"], y=pred["value"], mode="lines+markers",
                                  name="Forecast", line=dict(dash="dash")))
        figp.add_traces([go.Scatter(
            x=pd.concat([pred["date"], pred["date"][::-1]]),
            y=pd.concat([pred["upper"], pred["lower"][::-1]]),
            fill="toself", fillcolor="rgba(56,189,248,0.18)",
            line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", name="±95%",
        )])
        figp.update_layout(template="plotly_dark", height=380,
                           margin=dict(l=10, r=10, t=50, b=20),
                           title="Projected Weight (based on chosen pace)")
        st.plotly_chart(figp, use_container_width=True)

        if goal_w is not None:
            # determine if we cross the goal under the plan
            if goal_w < current_w:
                hit = pred[pred["value"] <= goal_w]
            elif goal_w > current_w:
                hit = pred[pred["value"] >= goal_w]
            else:
                hit = pred.iloc[:0]
            if not hit.empty:
                st.success(f"📅 With this plan you reach **{goal_w:.0f} lbs** around **{hit.iloc[0]['date'].date()}**.")
            else:
                st.info("This plan doesn’t hit the goal within the selected horizon.")

with tab_cal:
    st.caption("Uses the moving average of your logged calories vs estimated TDEE.")
    smooth_days = st.slider("Calorie smoothing (days)", 3, 14, 7, key="cal_smooth")
    horizon2     = st.slider("Trend horizon (weeks)", 4, 26, 12, key="cal_hor")

    meals = load_meals("data/meals.csv")
    energy_df = daily_kcal_vs_tdee(meals, tdee_est)
    series = forecast_weight_energy(bw, energy_df, horizon_weeks=horizon2, smooth_days=smooth_days)

    if series.empty:
        st.info("Log meals on the Nutrition page to enable a calorie-based projection.")
    else:
        act  = series[series["kind"] == "actual"]
        pred = series[series["kind"] == "pred"]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=act["date"], y=act["value"], mode="lines+markers", name="Actual"))
        fig2.add_trace(go.Scatter(x=pred["date"], y=pred["value"], mode="lines+markers",
                                  name="Forecast", line=dict(dash="dash")))
        fig2.add_traces([go.Scatter(
            x=pd.concat([pred["date"], pred["date"][::-1]]),
            y=pd.concat([pred["upper"], pred["lower"][::-1]]),
            fill="toself", fillcolor="rgba(56,189,248,0.18)",
            line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", name="±95%",
        )])
        fig2.update_layout(template="plotly_dark", height=380,
                           margin=dict(l=10, r=10, t=50, b=20),
                           title="Projected Weight (based on calorie trend)")
        st.plotly_chart(fig2, use_container_width=True)

        if goal_w is not None:
            hit = pred.loc[(pred["value"] >= goal_w) if delta >= 0 else (pred["value"] <= goal_w)]
            if not hit.empty:
                st.success(f"📅 At this intake/TDEE you reach **{goal_w:.0f} lbs** around **{hit.iloc[0]['date'].date()}**.")
            else:
                st.info("Current calorie trend doesn’t hit the goal within the selected horizon.")
