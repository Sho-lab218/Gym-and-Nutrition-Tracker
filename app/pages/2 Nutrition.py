import sys, os, csv, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

from src.style import apply_mpl_style
from src.ui import sidebar_common
from src.utils import load_meals, meals_daily, write_json, upsert_weight_entry

from src.forecast import estimate_tdee_msj

apply_mpl_style(dark=True)
st.title("🍎 Nutrition")
sidebar_common("Nutrition", "Log meals & set TDEE for forecasts")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
MEALS_PATH = os.path.join(DATA_DIR, "meals.csv")
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
BW_PATH = os.path.join(DATA_DIR, "bodyweight.csv")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- TDEE / profile ----------------
st.subheader("TDEE settings")
with st.expander("⚙️ Personal details (used for weight prediction)", expanded=True):
    prof = {}
    if os.path.exists(PROFILE_PATH):
        try:
            prof = json.load(open(PROFILE_PATH))
        except Exception:
            prof = {}

    sex = st.selectbox("Sex", ["Male","Female"], index=0 if prof.get("sex","Male")=="Male" else 1)
    age = st.number_input("Age", min_value=12, max_value=90, value=int(prof.get("age", 22)))
    height_cm = st.number_input("Height (cm)", min_value=120, max_value=230, value=int(prof.get("height_cm", 175)))
    cur_lbs = st.number_input("Current weight (lbs)", min_value=70.0, step=0.5, value=float(prof.get("curr_weight_lbs", 170.0)))
    act = st.selectbox("Activity", ["Sedentary","Light","Moderate","Active","Very Active"],
                       index=["Sedentary","Light","Moderate","Active","Very Active"].index(prof.get("activity","Moderate").title()))

    if st.button("Save TDEE settings", type="primary", key="save_tdee"):
        write_json(PROFILE_PATH, {
            "sex": sex, "age": age, "height_cm": height_cm,
            "curr_weight_lbs": float(cur_lbs), "activity": act
        })
        # also push to bodyweight as "today" so Progress shows it immediately
        upsert_weight_entry(BW_PATH, float(cur_lbs))
        st.success("Saved. Current weight synced to Progress.")
        st.rerun()

    tdee = estimate_tdee_msj(sex, age, height_cm, cur_lbs/2.20462, act)
    st.caption(f"Estimated TDEE: **{tdee:.0f} kcal/day** (used by Progress).")

st.divider()

# ---------------- Add / Reset meals ----------------
with st.expander("➕ Add a meal", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    m_date  = c1.date_input("Date", value=date.today())
    carbs   = c2.number_input("Carbs (g)",   min_value=0.0, step=1.0, key="carbs_in")
    protein = c3.number_input("Protein (g)", min_value=0.0, step=1.0, key="protein_in")
    fat     = c4.number_input("Fat (g)",     min_value=0.0, step=1.0, key="fat_in")

    kcal_auto = carbs*4 + protein*4 + fat*9
    kcal = st.number_input("Calories (kcal, optional — auto if 0)", min_value=0.0, step=1.0, value=0.0, key="kcal_in")
    notes = st.text_input("Notes (optional)", key="notes_in")

    cc1, cc2 = st.columns([1,1])
    if cc1.button("Save meal", type="primary", key="save_meal_btn"):
        with open(MEALS_PATH, "a", newline="") as f:
            w = csv.writer(f)
            w.writerow([pd.Timestamp(m_date).isoformat(), kcal_auto if kcal == 0 else kcal,
                        protein, carbs, fat, notes])
        st.success("Saved.")
        st.rerun()

    if cc2.button("↺ Reset all meals", key="reset_meals_btn"):
        pd.DataFrame(columns=["date","calories","protein_g","carbs_g","fat_g","notes"]).to_csv(MEALS_PATH, index=False)
        st.success("All meals cleared.")
        st.rerun()

# ---------------- Daily totals + day view ----------------
raw = load_meals(MEALS_PATH)
daily = meals_daily(raw)

show_day = st.date_input("Show day", value=(daily["date"].dt.date.max() if not daily.empty else date.today()))
if daily.empty:
    st.info("No meals yet.")
else:
    today_tot = daily[daily["date"].dt.date == show_day]
    if today_tot.empty:
        st.info("No meals for that day.")
    else:
        r = today_tot.iloc[0]
        kcal_breakdown = {"Carbs": r["carbs_g"]*4, "Protein": r["protein_g"]*4, "Fat": r["fat_g"]*9}
        fig = px.pie(values=list(kcal_breakdown.values()),
                     names=list(kcal_breakdown.keys()),
                     title=f"Daily Macros (kcal) — {show_day}", hole=0.55)
        fig.update_traces(textinfo="percent+label", pull=[0.03,0.03,0.03])
        fig.update_layout(template="plotly_dark", height=360, margin=dict(l=10,r=10,t=50,b=20))
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Meals (raw entries)")
if raw.empty:
    st.caption("—")
else:
    st.dataframe(raw.rename(columns={"date":"time"}), use_container_width=True, hide_index=True)
