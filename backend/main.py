from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel
import os
import json

# Import existing modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.forecast import (
    forecast_weight_realistic,
    forecast_weight_energy,
    forecast_1rm,
    estimate_tdee_msj,
    daily_kcal_vs_tdee,
)
from src.analyze import weekly_best_1rm, personal_bests
# CSV utilities no longer needed - using Supabase only
from src.catalog import EXERCISE_CATALOG
from database import (
    get_workouts as db_get_workouts,
    add_workout as db_add_workout,
    get_meals as db_get_meals,
    add_meal as db_add_meal,
    get_weights as db_get_weights,
    add_weight as db_add_weight,
    get_profile as db_get_profile,
    update_profile as db_update_profile,
    supabase,
)

app = FastAPI(title="Gym & Nutrition Tracker API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DATA_DIR no longer needed - using Supabase

# Pydantic models
class WorkoutEntry(BaseModel):
    date: str
    exercise: str
    sets: int
    reps: int
    weight_kg: float
    muscle_group: str
    notes: Optional[str] = ""

class MealEntry(BaseModel):
    date: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    notes: Optional[str] = ""

class WeightEntry(BaseModel):
    date: str
    body_weight_lbs: float
    goal_weight_lbs: Optional[float] = None

class Profile(BaseModel):
    sex: str
    age: int
    height_cm: float
    curr_weight_lbs: float
    activity: str

# Routes
@app.get("/")
async def root():
    return {"message": "Gym & Nutrition Tracker API"}

@app.get("/api/exercises")
async def get_exercises():
    return {"catalog": EXERCISE_CATALOG}

@app.get("/api/workouts")
async def get_workouts():
    try:
        return db_get_workouts()
    except Exception as e:
        import traceback
        print(f"Error in get_workouts: {e}")
        print(traceback.format_exc())
        return []  # Return empty list instead of raising error

@app.post("/api/workouts")
async def add_workout(workout: WorkoutEntry):
    try:
        workout_dict = {
            "date": workout.date,
            "exercise": workout.exercise,
            "sets": workout.sets,
            "reps": workout.reps,
            "weight_kg": workout.weight_kg,
            "muscle_group": workout.muscle_group,
            "notes": workout.notes or "",
        }
        success = db_add_workout(workout_dict)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to save workout")
    except Exception as e:
        import traceback
        print(f"Error adding workout: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/workouts")
async def reset_workouts():
    try:
        # Get all workout IDs first, then delete them
        workouts = db_get_workouts()
        if workouts:
            # Delete all records by selecting and deleting
            # Supabase requires a filter, so we'll delete by getting all IDs
            workout_ids = [w.get("id") for w in workouts if w.get("id")]
            if workout_ids:
                # Delete in batches if needed
                for workout_id in workout_ids:
                    supabase.table("workouts").delete().eq("id", workout_id).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error resetting workouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workouts/stats")
async def get_workout_stats():
    try:
        workouts = db_get_workouts()
        if not workouts:
            return {"sessions_this_week": 0, "total_volume": 0, "distinct_exercises": 0}
        
        df = pd.DataFrame(workouts)
        if df.empty:
            return {"sessions_this_week": 0, "total_volume": 0, "distinct_exercises": 0}
        
        # Calculate volume if we have the columns
        if {"sets", "reps", "weight_kg"}.issubset(df.columns):
            df["volume"] = df["sets"] * df["reps"] * df["weight_kg"]
        else:
            df["volume"] = 0.0
        
        # Calculate week for current week filtering
        df["date"] = pd.to_datetime(df["date"])
        iso = df["date"].dt.isocalendar()
        df["week"] = iso.week.astype(int)
        df["year"] = iso.year.astype(int)
        
        # Get current week
        current_date = pd.Timestamp.now()
        current_week = current_date.isocalendar().week
        current_year = current_date.isocalendar().year
        
        # Filter for this week
        this_week_data = df[(df["week"] == current_week) & (df["year"] == current_year)]
        
        sessions = int(this_week_data["date"].nunique()) if not this_week_data.empty else 0
        total_vol = int(df["volume"].sum())
        distinct = int(df["exercise"].nunique()) if "exercise" in df.columns else 0
        
        return {"sessions_this_week": sessions, "total_volume": total_vol, "distinct_exercises": distinct}
    except Exception as e:
        import traceback
        print(f"Error in get_workout_stats: {e}")
        print(traceback.format_exc())
        return {"sessions_this_week": 0, "total_volume": 0, "distinct_exercises": 0}

@app.get("/api/workouts/progression")
async def get_progression(exercise: str):
    try:
        workouts = db_get_workouts()
        if not workouts:
            return []
        
        df = pd.DataFrame(workouts)
        df["date"] = pd.to_datetime(df["date"])
        hist = df[df["exercise"] == exercise].copy()
        
        if hist.empty:
            return []
        
        prog = (hist.groupby("date", as_index=False)
                .agg(top_weight=("weight_kg", "max"))
                .sort_values("date"))
        prog["date"] = prog["date"].dt.strftime("%Y-%m-%d")
        return prog.to_dict(orient="records")
    except Exception as e:
        print(f"Error getting progression: {e}")
        return []

@app.get("/api/workouts/forecast")
async def get_workout_forecast(exercise: str, horizon: int = 8):
    try:
        workouts = db_get_workouts()
        if not workouts:
            return {"actual": [], "forecast": []}
        
        df = pd.DataFrame(workouts)
        df["date"] = pd.to_datetime(df["date"])
        hist = df[df["exercise"] == exercise].copy()
        
        if hist.empty or len(hist) < 2:
            return {"actual": [], "forecast": []}
        
        wk = (hist.groupby(pd.Grouper(key="date", freq="W-MON"))["weight_kg"]
              .max().dropna().reset_index(name="top"))
        
        if len(wk) < 2:
            return {"actual": [], "forecast": []}
        
        t = np.arange(len(wk))
        A = np.vstack([np.ones_like(t), t]).T
        b0, b1 = np.linalg.lstsq(A, wk["top"].to_numpy(), rcond=None)[0]
        b1 = max(0.0, float(b1))
        t_last = t[-1]
        tf = np.arange(t_last + 1, t_last + 1 + horizon)
        preds = b0 + b1 * tf
        last_date = wk["date"].iloc[-1]
        future_dates = [last_date + pd.Timedelta(days=7 * i) for i in range(1, horizon + 1)]
        
        actual = [{"date": d.strftime("%Y-%m-%d"), "value": float(v)} 
                  for d, v in zip(wk["date"], wk["top"])]
        forecast = [{"date": d.strftime("%Y-%m-%d"), "value": float(v)} 
                    for d, v in zip(future_dates, preds)]
        
        return {"actual": actual, "forecast": forecast}
    except Exception as e:
        import traceback
        print(f"Error getting workout forecast: {e}")
        print(traceback.format_exc())
        return {"actual": [], "forecast": []}

@app.get("/api/meals")
async def get_meals():
    try:
        return db_get_meals()
    except Exception as e:
        print(f"Error getting meals: {e}")
        return []

@app.post("/api/meals")
async def add_meal(meal: MealEntry):
    try:
        meal_dict = {
            "date": meal.date,
            "calories": meal.calories,
            "protein_g": meal.protein_g,
            "carbs_g": meal.carbs_g,
            "fat_g": meal.fat_g,
            "notes": meal.notes or "",
        }
        success = db_add_meal(meal_dict)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to save meal")
    except Exception as e:
        import traceback
        print(f"Error adding meal: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/meals")
async def reset_meals():
    try:
        # Get all meal IDs first, then delete them
        meals = db_get_meals()
        if meals:
            meal_ids = [m.get("id") for m in meals if m.get("id")]
            if meal_ids:
                for meal_id in meal_ids:
                    supabase.table("meals").delete().eq("id", meal_id).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error resetting meals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/meals/daily")
async def get_daily_meals(selected_date: Optional[str] = None):
    try:
        meals = db_get_meals()
        if not meals:
            return []
        
        # Convert to DataFrame for aggregation
        df = pd.DataFrame(meals)
        
        # Check if DataFrame is empty
        if df.empty:
            return []
        
        # Ensure date column exists
        if "date" not in df.columns:
            print("ERROR: 'date' column not found in meals data")
            return []
        
        # Ensure date is datetime
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        # Drop rows with invalid dates
        df = df.dropna(subset=["date"])
        
        if df.empty:
            return []
        
        # Normalize dates
        df["date"] = df["date"].dt.normalize()
        
        # Ensure numeric columns are numeric
        for col in ["calories", "protein_g", "carbs_g", "fat_g"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Aggregate by date
        daily = df.groupby("date", as_index=False).agg({
            "calories": "sum",
            "protein_g": "sum",
            "carbs_g": "sum",
            "fat_g": "sum"
        })
        
        if selected_date:
            try:
                # Normalize the selected date for comparison
                target_date = pd.to_datetime(selected_date).normalize()
                # Filter by matching date - compare as dates to avoid timezone issues
                # Convert both to date objects for comparison
                daily = daily[daily["date"].dt.date == target_date.date()]
                # Debug: print if no matches found
                if len(daily) == 0:
                    available_dates = df["date"].dt.strftime("%Y-%m-%d").unique().tolist()
                    print(f"DEBUG: No meals found for date: {selected_date}, available dates: {available_dates}")
            except Exception as date_error:
                print(f"ERROR parsing selected_date '{selected_date}': {date_error}")
                return []
        
        # Convert date to string for JSON (only if daily is not empty)
        if not daily.empty:
            daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")
            return daily.to_dict(orient="records")
        else:
            return []
    except Exception as e:
        import traceback
        print(f"Error getting daily meals: {e}")
        print(traceback.format_exc())
        return []

@app.get("/api/weight")
async def get_weight():
    try:
        return db_get_weights()
    except Exception as e:
        print(f"Error getting weights: {e}")
        return []

@app.post("/api/weight")
async def add_weight(weight: WeightEntry):
    try:
        weight_dict = {
            "date": weight.date,
            "body_weight_lbs": weight.body_weight_lbs,
            "goal_weight_lbs": weight.goal_weight_lbs,
        }
        success = db_add_weight(weight_dict)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to save weight")
    except Exception as e:
        import traceback
        print(f"Error adding weight: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/weight")
async def reset_weights():
    try:
        # Get all weight IDs first, then delete them
        weights = db_get_weights()
        if weights:
            weight_ids = [w.get("id") for w in weights if w.get("id")]
            if weight_ids:
                for weight_id in weight_ids:
                    supabase.table("bodyweight").delete().eq("id", weight_id).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error resetting weights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weight/stats")
async def get_weight_stats():
    try:
        weights = db_get_weights()
        if not weights:
            return {"start": None, "current": None, "delta": None, "goal": None}
        
        # Sort by date
        weights_sorted = sorted(weights, key=lambda x: x.get("date", ""))
        
        if not weights_sorted or "body_weight_lbs" not in weights_sorted[0]:
            return {"start": None, "current": None, "delta": None, "goal": None}
        
        start_w = float(weights_sorted[0]["body_weight_lbs"])
        current_w = float(weights_sorted[-1]["body_weight_lbs"])
        delta = current_w - start_w
        
        # Find last goal weight
        goal_w = None
        for weight in reversed(weights_sorted):
            if "goal_weight_lbs" in weight and weight["goal_weight_lbs"] is not None:
                goal_w = float(weight["goal_weight_lbs"])
                break
        
        return {
            "start": start_w,
            "current": current_w,
            "delta": delta,
            "goal": goal_w
        }
    except Exception as e:
        import traceback
        print(f"Error in get_weight_stats: {e}")
        print(traceback.format_exc())
        return {"start": None, "current": None, "delta": None, "goal": None}

@app.get("/api/weight/forecast")
async def get_weight_forecast(
    mode: Literal["plan", "calorie"] = "plan",
    target_rate_pct: Optional[float] = None,
    horizon: int = 12,
    smooth_days: int = 7
):
    try:
        weights = db_get_weights()
        if not weights:
            return {"actual": [], "forecast": []}
        
        # Convert to DataFrame for forecasting
        bw_df = pd.DataFrame(weights)
        bw_df["date"] = pd.to_datetime(bw_df["date"])
        bw_df = bw_df.sort_values("date").reset_index(drop=True)
        
        if mode == "plan":
            series = forecast_weight_realistic(
                bw_df,
                horizon_weeks=horizon,
                target_rate_pct=target_rate_pct or 0.0
            )
        else:
            meals = db_get_meals()
            if not meals:
                return {"actual": [], "forecast": []}
            
            meals_df = pd.DataFrame(meals)
            meals_df["date"] = pd.to_datetime(meals_df["date"])
            
            prof = db_get_profile()
            if prof:
                current_w = float(bw_df["body_weight_lbs"].iloc[-1])
                tdee = estimate_tdee_msj(
                    prof["sex"],
                    prof["age"],
                    prof["height_cm"],
                    current_w / 2.20462,
                    prof["activity"]
                )
            else:
                tdee = 2000.0
            
            energy_df = daily_kcal_vs_tdee(meals_df, tdee)
            series = forecast_weight_energy(bw_df, energy_df, horizon_weeks=horizon, smooth_days=smooth_days)
        
        if series.empty:
            return {"actual": [], "forecast": []}
        
        actual = series[series["kind"] == "actual"]
        pred = series[series["kind"] == "pred"]
        
        actual_data = [{
            "date": d.strftime("%Y-%m-%d"),
            "value": float(v),
            "lower": float(l),
            "upper": float(u)
        } for d, v, l, u in zip(actual["date"], actual["value"], actual["lower"], actual["upper"])]
        
        forecast_data = [{
            "date": d.strftime("%Y-%m-%d"),
            "value": float(v),
            "lower": float(l),
            "upper": float(u)
        } for d, v, l, u in zip(pred["date"], pred["value"], pred["lower"], pred["upper"])]
        
        return {"actual": actual_data, "forecast": forecast_data}
    except Exception as e:
        import traceback
        print(f"Error in weight forecast: {e}")
        print(traceback.format_exc())
        return {"actual": [], "forecast": []}

@app.get("/api/profile")
async def get_profile():
    try:
        return db_get_profile()
    except Exception as e:
        print(f"Error getting profile: {e}")
        return {}

@app.post("/api/profile")
async def update_profile(profile: Profile):
    try:
        profile_dict = profile.model_dump()
        success = db_update_profile(profile_dict)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to update profile")
    except Exception as e:
        import traceback
        print(f"Error updating profile: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile/tdee")
async def get_tdee():
    try:
        prof = db_get_profile()
        if not prof:
            return {"tdee": 2000.0}
        
        # Get current weight from bodyweight table
        weights = db_get_weights()
        if weights:
            weights_sorted = sorted(weights, key=lambda x: x.get("date", ""))
            current_w = float(weights_sorted[-1]["body_weight_lbs"]) if weights_sorted else prof.get("curr_weight_lbs", 170.0)
        else:
            current_w = prof.get("curr_weight_lbs", 170.0)
        
        tdee = estimate_tdee_msj(
            prof["sex"],
            prof["age"],
            prof["height_cm"],
            current_w / 2.20462,
            prof["activity"]
        )
        return {"tdee": tdee}
    except Exception as e:
        print(f"Error getting TDEE: {e}")
        return {"tdee": 2000.0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

