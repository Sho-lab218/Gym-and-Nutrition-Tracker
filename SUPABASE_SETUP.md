# Supabase Setup Guide

**This app requires Supabase** - CSV mode has been removed for better reliability and scalability.

## Quick Start with Supabase

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in
3. Create a new project
4. Wait for the project to be ready

### 2. Get Your Credentials

1. In your Supabase project, go to **Settings** → **API**
2. Copy your:
   - **Project URL** (under "Project URL")
   - **anon/public key** (under "Project API keys")

### 3. Create Database Tables

Run this SQL in your Supabase SQL Editor:

```sql
-- Workouts table
CREATE TABLE IF NOT EXISTS workouts (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    exercise TEXT NOT NULL,
    sets INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight_kg DECIMAL NOT NULL,
    muscle_group TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Meals table
CREATE TABLE IF NOT EXISTS meals (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    calories DECIMAL NOT NULL,
    protein_g DECIMAL NOT NULL,
    carbs_g DECIMAL NOT NULL,
    fat_g DECIMAL NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bodyweight table
CREATE TABLE IF NOT EXISTS bodyweight (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    body_weight_lbs DECIMAL NOT NULL,
    goal_weight_lbs DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Profile table
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY DEFAULT 1,
    sex TEXT NOT NULL,
    age INTEGER NOT NULL,
    height_cm DECIMAL NOT NULL,
    curr_weight_lbs DECIMAL NOT NULL,
    activity TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (optional, for multi-user later)
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE bodyweight ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for now, restrict later if needed)
CREATE POLICY "Allow all operations" ON workouts FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON meals FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON bodyweight FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON profile FOR ALL USING (true);
```

### 4. Configure Backend

1. Copy `.env.example` to `.env`:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials (REQUIRED):
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-anon-key-here
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   python main.py
   ```
   
   The server will fail to start if Supabase credentials are missing or invalid.

### 5. Migrate Existing Data (Optional)

If you have existing CSV data, you can migrate it:

```python
# Run this script once to migrate data
python backend/migrate_to_supabase.py
```

## Benefits of Supabase

✅ **Reliable**: No file system issues  
✅ **Scalable**: Handles large datasets  
✅ **Real-time**: Can add real-time updates later  
✅ **Backup**: Automatic backups  
✅ **Multi-device**: Access from anywhere  
✅ **Future-proof**: Easy to add authentication, sharing, etc.

## Migration from CSV (if you have existing data)

If you have existing CSV data in the `data/` folder, you can migrate it to Supabase:

1. Make sure your Supabase tables are created (step 3 above)
2. Run the migration script:
   ```bash
   python backend/migrate_csv_to_supabase.py
   ```

This will import all your existing workouts, meals, and weight data into Supabase.

