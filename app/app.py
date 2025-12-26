import streamlit as st

st.set_page_config(page_title="Gym & Nutrition Tracker", layout="wide")

hero = """
<div style="
  background: radial-gradient(1000px 400px at 10% -10%, rgba(56,189,248,.18), transparent 60%),
              radial-gradient(800px 300px at 90% 0%, rgba(34,197,94,.18), transparent 60%);
  border:1px solid rgba(148,163,184,.15);
  padding: 32px; border-radius: 16px; ">
  <h1 style="margin:0;font-size:44px;">🏋️‍♂️ Gym & Nutrition Tracker</h1>
  <p style="opacity:.9;margin:6px 0 0;">
    Train smarter. Log workouts & meals. See progress with forecasts.
  </p>
</div>
"""
st.markdown(hero, unsafe_allow_html=True)
st.write("")

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("🏋️ Workouts")
    st.caption("Volume, trends, recent sessions.")
    st.page_link("pages/1 Workouts.py", label="🏋️ Open Workouts →")

with c2:
    st.subheader("🍎 Nutrition")
    st.caption("Log meals & view macros.")
    st.page_link("pages/2 Nutrition.py", label="🍎 Open Nutrition →")

with c3:
    st.subheader("📈 Progress")
    st.caption("Body weight trend with ML projection.")
    st.page_link("pages/3 Progress.py", label="📈 Open Progress →")

st.divider()
st.subheader("Today")
st.caption("Use each page’s sidebar to filter and forecast. Add weight/meals to see live updates.")
