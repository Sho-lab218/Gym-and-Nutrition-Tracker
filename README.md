# Gym & Nutrition Tracker

A modern, full-stack fitness tracking application built with React and FastAPI. Track your workouts, nutrition, and body weight with ML-powered forecasts.

## ✨ Features

- **Workouts**: Log exercises, track volume, see progression charts, and get strength forecasts
- **Nutrition**: Log meals, track macros, set TDEE, and view daily nutrition breakdowns
- **Progress**: Track body weight, set goals, and get ML-powered weight forecasts
- **Modern UI**: Beautiful, responsive React interface with dark theme
- **ML Forecasting**: Improved algorithms with polynomial regression, Holt-Winters, and weighted trend analysis

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the FastAPI server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## 📁 Project Structure

```
gym-nutrition-tracker/
├── backend/
│   ├── main.py              # FastAPI server
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── api.ts           # API client
│   │   └── App.tsx          # Main app component
│   └── package.json
├── data/                    # CSV data files
├── src/                     # Shared Python modules
│   ├── forecast.py          # ML forecasting (improved)
│   ├── analyze.py           # Data analysis
│   └── utils.py             # Utilities
└── README.md
```

## 🧠 ML Improvements

The forecasting models have been significantly improved:

1. **Polynomial Regression**: Better handles non-linear trends
2. **Holt-Winters Exponential Smoothing**: Improved time series forecasting
3. **Weighted Regression**: Recent data points have more influence
4. **Outlier Detection**: IQR-based outlier removal for cleaner predictions
5. **Data Smoothing**: Moving average smoothing to reduce noise
6. **Expanding Confidence Intervals**: Uncertainty increases with forecast horizon
7. **Better Error Handling**: Robust fallbacks and validation

## 📊 API Endpoints

### Workouts
- `GET /api/workouts` - Get all workouts
- `POST /api/workouts` - Add a workout
- `DELETE /api/workouts` - Reset all workouts
- `GET /api/workouts/stats` - Get workout statistics
- `GET /api/workouts/progression?exercise={name}` - Get exercise progression
- `GET /api/workouts/forecast?exercise={name}&horizon={weeks}` - Get strength forecast

### Nutrition
- `GET /api/meals` - Get all meals
- `POST /api/meals` - Add a meal
- `DELETE /api/meals` - Reset all meals
- `GET /api/meals/daily?selected_date={date}` - Get daily meals

### Weight
- `GET /api/weight` - Get all weight entries
- `POST /api/weight` - Add weight entry
- `GET /api/weight/stats` - Get weight statistics
- `GET /api/weight/forecast?mode={plan|calorie}&target_rate_pct={%}&horizon={weeks}` - Get weight forecast

### Profile
- `GET /api/profile` - Get user profile
- `POST /api/profile` - Update profile
- `GET /api/profile/tdee` - Get estimated TDEE

## 🛠️ Technologies

- **Frontend**: React 18, TypeScript, Tailwind CSS, Recharts, React Router
- **Backend**: FastAPI, Python, Pandas, scikit-learn, statsmodels
- **ML**: Linear/Polynomial Regression, Holt-Winters Exponential Smoothing

## 📝 Notes

- Data is stored in CSV files in the `data/` directory
- The app uses the Mifflin-St Jeor equation for TDEE estimation
- 1RM estimation uses the Epley formula: `1RM ≈ weight * (1 + reps/30)`
- Weight forecasts account for realistic rate limits (max 1.5% bodyweight per week)

## 🔮 Future Enhancements

- [ ] SQLite database migration
- [ ] User authentication
- [ ] Mobile app
- [ ] Advanced analytics dashboard
- [ ] Export/import data
- [ ] Social features

## 📄 License

MIT
