# Gym & Nutrition Tracker (with ML forecast)

A modern, full-stack fitness tracking application built with **React** and **FastAPI**, powered by **Supabase**. Track your workouts, nutrition, and body weight with ML-powered forecasts.

## ✨ Features

- **Workouts**: Log exercises, track volume, see progression charts, and get strength forecasts
- **Nutrition**: Log meals, track macros, set TDEE, and view daily nutrition breakdowns
- **Progress**: Track body weight, set goals, and get ML-powered weight forecasts
- **Modern UI**: Beautiful, responsive React interface with dark theme
- **ML Forecasting**: Improved algorithms with polynomial regression, Holt-Winters, and weighted trend analysis
- **Supabase Backend**: Reliable PostgreSQL database with automatic backups

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn
- Supabase account (free tier available)

### 1. Set Up Supabase

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Run the SQL from `SUPABASE_SETUP.md` to create tables
4. Get your credentials from Settings → API

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Supabase (create .env file from template)
cp .env.example .env
# Edit .env and add your SUPABASE_URL and SUPABASE_KEY
# Get these from your Supabase project: Settings → API

# Start the server
python main.py
```

The API will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:5173`

### 4. Migrate Existing Data (Optional)

If you have existing CSV data:

```bash
cd backend
python migrate_csv_to_supabase.py
```

## 📁 Project Structure

```
gym-nutrition-tracker/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── database.py          # Supabase database layer
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Supabase credentials (create from .env.example)
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── api.ts           # API client
│   │   └── App.tsx          # Main app component
│   └── package.json
├── src/                     # Shared Python modules
│   ├── forecast.py          # ML forecasting (improved)
│   ├── analyze.py           # Data analysis
│   └── utils.py             # Utilities
└── SUPABASE_SETUP.md        # Supabase setup guide
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
- **Database**: Supabase (PostgreSQL)
- **ML**: Linear/Polynomial Regression, Holt-Winters Exponential Smoothing

## 📝 Notes

- Data is stored in Supabase PostgreSQL database
- The app uses the Mifflin-St Jeor equation for TDEE estimation
- 1RM estimation uses the Epley formula: `1RM ≈ weight * (1 + reps/30)`
- Weight forecasts account for realistic rate limits (max 1.5% bodyweight per week)

## 🔮 Future Enhancements

- [ ] User authentication with Supabase Auth
- [ ] Mobile app
- [ ] Advanced analytics dashboard
- [ ] Export/import data
- [ ] Social features and sharing
- [ ] Real-time updates

## 📄 License

MIT
