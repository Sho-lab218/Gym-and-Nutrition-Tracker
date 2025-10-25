"""
Migration script to import CSV data into Supabase
Run this once after setting up Supabase to migrate existing data
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database import supabase, get_workouts, get_meals, get_weights

def migrate_workouts():
    """Migrate workouts from CSV to Supabase"""
    data_dir = Path(__file__).parent.parent / "data"
    csv_path = data_dir / "workouts.csv"
    
    if not csv_path.exists():
        print("No workouts.csv found, skipping...")
        return
    
    # Check if Supabase already has data
    existing = get_workouts()
    if existing:
        print(f"⚠️  Found {len(existing)} workouts in Supabase. Skipping migration.")
        response = input("Do you want to import CSV data anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Load CSV
    from src.utils import load_workouts
    df = load_workouts(str(csv_path))
    
    if df.empty:
        print("No workouts to migrate.")
        return
    
    print(f"Migrating {len(df)} workouts...")
    
    # Convert to dict format
    workouts = []
    for _, row in df.iterrows():
        workout = {
            "date": row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else None,
            "exercise": str(row["exercise"]) if pd.notna(row["exercise"]) else "",
            "sets": int(row["sets"]) if pd.notna(row["sets"]) else 0,
            "reps": int(row["reps"]) if pd.notna(row["reps"]) else 0,
            "weight_kg": float(row["weight_kg"]) if pd.notna(row["weight_kg"]) else 0.0,
            "muscle_group": str(row["muscle_group"]) if pd.notna(row["muscle_group"]) else "",
            "notes": str(row["notes"]) if pd.notna(row.get("notes")) else "",
        }
        workouts.append(workout)
    
    # Insert in batches
    batch_size = 100
    for i in range(0, len(workouts), batch_size):
        batch = workouts[i:i+batch_size]
        supabase.table("workouts").insert(batch).execute()
        print(f"  Migrated {min(i+batch_size, len(workouts))}/{len(workouts)} workouts...")
    
    print("✅ Workouts migration complete!")

def migrate_meals():
    """Migrate meals from CSV to Supabase"""
    data_dir = Path(__file__).parent.parent / "data"
    csv_path = data_dir / "meals.csv"
    
    if not csv_path.exists():
        print("No meals.csv found, skipping...")
        return
    
    existing = get_meals()
    if existing:
        print(f"⚠️  Found {len(existing)} meals in Supabase. Skipping migration.")
        response = input("Do you want to import CSV data anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    from src.utils import load_meals
    df = load_meals(str(csv_path))
    
    if df.empty:
        print("No meals to migrate.")
        return
    
    print(f"Migrating {len(df)} meals...")
    
    meals = []
    for _, row in df.iterrows():
        meal = {
            "date": row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else None,
            "calories": float(row["calories"]) if pd.notna(row["calories"]) else 0.0,
            "protein_g": float(row["protein_g"]) if pd.notna(row["protein_g"]) else 0.0,
            "carbs_g": float(row["carbs_g"]) if pd.notna(row["carbs_g"]) else 0.0,
            "fat_g": float(row["fat_g"]) if pd.notna(row["fat_g"]) else 0.0,
            "notes": str(row["notes"]) if pd.notna(row.get("notes")) else "",
        }
        meals.append(meal)
    
    batch_size = 100
    for i in range(0, len(meals), batch_size):
        batch = meals[i:i+batch_size]
        supabase.table("meals").insert(batch).execute()
        print(f"  Migrated {min(i+batch_size, len(meals))}/{len(meals)} meals...")
    
    print("✅ Meals migration complete!")

def migrate_weights():
    """Migrate weight data from CSV to Supabase"""
    data_dir = Path(__file__).parent.parent / "data"
    csv_path = data_dir / "bodyweight.csv"
    
    if not csv_path.exists():
        print("No bodyweight.csv found, skipping...")
        return
    
    existing = get_weights()
    if existing:
        print(f"⚠️  Found {len(existing)} weight entries in Supabase. Skipping migration.")
        response = input("Do you want to import CSV data anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    from src.utils import read_bodyweight
    df = read_bodyweight(str(csv_path))
    
    if df.empty:
        print("No weight data to migrate.")
        return
    
    print(f"Migrating {len(df)} weight entries...")
    
    weights = []
    for _, row in df.iterrows():
        weight = {
            "date": row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else None,
            "body_weight_lbs": float(row["body_weight_lbs"]) if pd.notna(row["body_weight_lbs"]) else 0.0,
        }
        if "goal_weight_lbs" in row and pd.notna(row["goal_weight_lbs"]):
            weight["goal_weight_lbs"] = float(row["goal_weight_lbs"])
        weights.append(weight)
    
    batch_size = 100
    for i in range(0, len(weights), batch_size):
        batch = weights[i:i+batch_size]
        supabase.table("bodyweight").upsert(batch, on_conflict="date").execute()
        print(f"  Migrated {min(i+batch_size, len(weights))}/{len(weights)} weight entries...")
    
    print("✅ Weight data migration complete!")

def migrate_profile():
    """Migrate profile from JSON to Supabase"""
    data_dir = Path(__file__).parent.parent / "data"
    json_path = data_dir / "profile.json"
    
    if not json_path.exists():
        print("No profile.json found, skipping...")
        return
    
    import json
    with open(json_path) as f:
        profile = json.load(f)
    
    # Check if profile exists
    from database import get_profile
    existing = get_profile()
    if existing:
        print("⚠️  Profile already exists in Supabase. Skipping migration.")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            return
    
    profile["id"] = 1  # Single user profile
    supabase.table("profile").upsert(profile, on_conflict="id").execute()
    print("✅ Profile migration complete!")

if __name__ == "__main__":
    print("🚀 Starting CSV to Supabase migration...\n")
    
    try:
        migrate_workouts()
        print()
        migrate_meals()
        print()
        migrate_weights()
        print()
        migrate_profile()
        print()
        print("🎉 Migration complete! Your data is now in Supabase.")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

