import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd

from src.style import apply_mpl_style
from src.ui import sidebar_common
from src.utils import write_json, upsert_weight_entry

apply_mpl_style(dark=True)
st.title("⚙️ Settings")
sidebar_common("Settings", "Quick weight override")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
BW_PATH = os.path.join(DATA_DIR, "bodyweight.csv")
os.makedirs(DATA_DIR, exist_ok=True)

with st.expander("Update current weight", expanded=True):
    cur_lbs = st.number_input("Current weight (lbs)", min_value=70.0, step=0.5, value=170.0)
    if st.button("Save as today's weight", type="primary"):
        upsert_weight_entry(BW_PATH, float(cur_lbs))  # signature: (path, weight, when=None, goal=None)
        # also mirror in profile for the TDEE calc convenience
        prof = {}
        if os.path.exists(PROFILE_PATH):
            try:
                prof = json.load(open(PROFILE_PATH))
            except Exception:
                prof = {}
        prof["curr_weight_lbs"] = float(cur_lbs)
        write_json(PROFILE_PATH, prof)
        st.success("Updated. Check Progress.")
        st.rerun()
