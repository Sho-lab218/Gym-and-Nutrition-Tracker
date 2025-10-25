
# Gym & Nutrition Tracker (with ML forecast)

A polished, UX-friendly tracker that ingests workout logs, computes weekly volume & estimated 1RM, detects PRs, and **projects future gains** with a simple ML model. Built for showcasing both **engineering** and **UX thinking**.

## ✨ Features
- CSV-based logging (easy to start; can upgrade to SQLite)
- pandas analytics: weekly volume, PR detection, 1RM (Epley)
- ML forecast (LinearRegression) with dashed future line
- Streamlit dashboard with KPI cards & charts
- Sample data included

## 🚀 Quick Start
```bash
# 1) clone & enter
# git clone <your-fork-url>
cd gym-nutrition-tracker

# 2) create & activate venv
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

# 3) install deps
pip install -r requirements.txt

# 4) run app
streamlit run app/app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

## 🗂️ Structure
```
app/            # Streamlit UI
src/            # logic (analytics, forecast, viz)
data/           # CSV inputs (sample included)
figures/        # charts (if you save them)
reports/        # future reports
requirements.txt
README.md
```

## 🧠 Notes
- 1RM uses Epley: `1RM ≈ weight * (1 + reps/30)`
- Forecast is a straight-line trend for simplicity; upgrade later to polynomial or Prophet.

## 📸 Screenshots
(Add screenshots/GIFs of the dashboard and charts here.)

## 📈 Roadmap
- [ ] Nutrition join (kcal/protein weekly + correlation note)
- [ ] SQLite migration, forms for logging via UI
- [ ] Better time-series model; confidence band
- [ ] Tests + CI
```

