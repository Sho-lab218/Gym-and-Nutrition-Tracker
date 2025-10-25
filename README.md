# 🏋️ Gym & Nutrition Tracker (with ML Forecast)

A polished, UX-friendly tracker that ingests workout logs, computes weekly volume & estimated 1RM, detects PRs, and **projects future gains** using a lightweight ML model.  
Built to showcase both **engineering** and **UX thinking** — combining data analysis, visualization, and user experience design in one cohesive app.

---

## ✨ Features
- 🗂️ CSV-based logging (easy to start; upgradeable to SQLite)
- 📊 Analytics via pandas: weekly volume, PR detection, and Epley 1RM formula
- 🤖 ML forecast (Linear Regression) with projected future performance
- 📈 Streamlit dashboard featuring KPI cards, interactive graphs, and forecast trends
- 🧮 Integrated Nutrition & Progress tracking (calories, macros, weight trends)
- 🧠 Modular structure for future scaling (e.g., API, database integration)
- 📷 Clean dark UI built for clarity and presentation

---

## 🚀 Quick Start

```bash
# 1️⃣ Clone & enter
git clone https://github.com/<your-username>/Gym-and-Nutrition-Tracker.git
cd Gym-and-Nutrition-Tracker

# 2️⃣ Create & activate virtual environment
python -m venv .venv
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Run the Streamlit app
streamlit run app/app.py

