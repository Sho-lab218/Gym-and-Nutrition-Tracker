"""
Database layer - Supabase only
"""
import os
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Supabase credentials not found! Please set SUPABASE_URL and SUPABASE_KEY in .env file.\n"
        "See SUPABASE_SETUP.md for instructions."
    )

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase")
except Exception as e:
    raise ConnectionError(f"Failed to connect to Supabase: {e}\nPlease check your credentials in .env")

# ==================== Workouts ====================

def get_workouts() -> List[Dict[str, Any]]:
    """Get all workouts"""
    try:
        response = supabase.table("workouts").select("*").order("date", desc=False).execute()
        workouts = []
        for row in response.data:
            workout = dict(row)
            # Convert date to string if it's a datetime
            if "date" in workout and workout["date"]:
                if isinstance(workout["date"], str):
                    workout["date"] = workout["date"][:10]  # Keep only date part
            workouts.append(workout)
        return workouts
    except Exception as e:
        print(f"Error fetching workouts from Supabase: {e}")
        raise

def add_workout(workout: Dict[str, Any]) -> bool:
    """Add a workout"""
    try:
        # Remove any None values and ensure date is string
        clean_workout = {k: v for k, v in workout.items() if v is not None}
        if "date" in clean_workout and isinstance(clean_workout["date"], str):
            clean_workout["date"] = clean_workout["date"][:10]  # Ensure YYYY-MM-DD format
        
        supabase.table("workouts").insert(clean_workout).execute()
        return True
    except Exception as e:
        print(f"Error adding workout to Supabase: {e}")
        raise

# ==================== Meals ====================

def get_meals() -> List[Dict[str, Any]]:
    """Get all meals"""
    try:
        response = supabase.table("meals").select("*").order("date", desc=False).execute()
        meals = []
        for row in response.data:
            meal = dict(row)
            # Convert date to string if needed
            if "date" in meal and meal["date"]:
                if isinstance(meal["date"], str):
                    meal["date"] = meal["date"][:10]
            meals.append(meal)
        return meals
    except Exception as e:
        print(f"Error fetching meals from Supabase: {e}")
        raise

def add_meal(meal: Dict[str, Any]) -> bool:
    """Add a meal"""
    try:
        # Remove any None values and ensure date is string
        clean_meal = {k: v for k, v in meal.items() if v is not None}
        if "date" in clean_meal and isinstance(clean_meal["date"], str):
            clean_meal["date"] = clean_meal["date"][:10]  # Ensure YYYY-MM-DD format
        
        supabase.table("meals").insert(clean_meal).execute()
        return True
    except Exception as e:
        print(f"Error adding meal to Supabase: {e}")
        raise

# ==================== Weight ====================

def get_weights() -> List[Dict[str, Any]]:
    """Get all weight entries"""
    try:
        response = supabase.table("bodyweight").select("*").order("date", desc=False).execute()
        weights = []
        for row in response.data:
            weight = dict(row)
            # Convert date to string if needed
            if "date" in weight and weight["date"]:
                if isinstance(weight["date"], str):
                    weight["date"] = weight["date"][:10]
            weights.append(weight)
        return weights
    except Exception as e:
        print(f"Error fetching weights from Supabase: {e}")
        raise

def add_weight(weight: Dict[str, Any]) -> bool:
    """Add a weight entry (upserts on date)"""
    try:
        # Remove None values and ensure date is string
        clean_weight = {k: v for k, v in weight.items() if v is not None}
        if "date" in clean_weight and isinstance(clean_weight["date"], str):
            clean_weight["date"] = clean_weight["date"][:10]  # Ensure YYYY-MM-DD format
        
        # Upsert based on date (if date is unique constraint)
        supabase.table("bodyweight").upsert(clean_weight, on_conflict="date").execute()
        return True
    except Exception as e:
        print(f"Error adding weight to Supabase: {e}")
        raise

# ==================== Profile ====================

def get_profile() -> Dict[str, Any]:
    """Get user profile"""
    try:
        response = supabase.table("profile").select("*").limit(1).execute()
        if response.data:
            return dict(response.data[0])
        return {}
    except Exception as e:
        print(f"Error fetching profile from Supabase: {e}")
        return {}

def update_profile(profile: Dict[str, Any]) -> bool:
    """Update user profile"""
    try:
        # Ensure id is set for upsert
        if "id" not in profile:
            profile["id"] = 1
        
        # Upsert profile (single user profile)
        supabase.table("profile").upsert(profile, on_conflict="id").execute()
        
        # Also sync current weight to bodyweight table
        if "curr_weight_lbs" in profile:
            from datetime import date
            weight_entry = {
                "date": str(date.today()),
                "body_weight_lbs": profile["curr_weight_lbs"]
            }
            supabase.table("bodyweight").upsert(weight_entry, on_conflict="date").execute()
        
        return True
    except Exception as e:
        print(f"Error updating profile in Supabase: {e}")
        raise

