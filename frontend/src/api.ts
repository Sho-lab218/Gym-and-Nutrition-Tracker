import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface WorkoutEntry {
  date: string;
  exercise: string;
  sets: number;
  reps: number;
  weight_kg: number;
  muscle_group: string;
  notes?: string;
}

export interface MealEntry {
  date: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  notes?: string;
}

export interface WeightEntry {
  date: string;
  body_weight_lbs: number;
  goal_weight_lbs?: number;
}

export interface Profile {
  sex: string;
  age: number;
  height_cm: number;
  curr_weight_lbs: number;
  activity: string;
}

export interface ExerciseCatalog {
  [key: string]: string[];
}

// Workouts API
export const workoutsApi = {
  getAll: () => api.get<WorkoutEntry[]>('/api/workouts').then(res => res.data),
  add: (workout: WorkoutEntry) => api.post('/api/workouts', workout).then(res => res.data),
  reset: () => api.delete('/api/workouts').then(res => res.data),
  getStats: () => api.get('/api/workouts/stats').then(res => res.data),
  getProgression: (exercise: string) => 
    api.get<Array<{date: string; top_weight: number}>>(`/api/workouts/progression?exercise=${encodeURIComponent(exercise)}`).then(res => res.data),
  getForecast: (exercise: string, horizon: number = 8) =>
    api.get<{actual: Array<{date: string; value: number}>; forecast: Array<{date: string; value: number}>}>(
      `/api/workouts/forecast?exercise=${encodeURIComponent(exercise)}&horizon=${horizon}`
    ).then(res => res.data),
};

// Meals API
export const mealsApi = {
  getAll: () => api.get<MealEntry[]>('/api/meals').then(res => res.data),
  add: (meal: MealEntry) => api.post('/api/meals', meal).then(res => res.data),
  reset: () => api.delete('/api/meals').then(res => res.data),
  getDaily: (date?: string) => 
    api.get<MealEntry[]>(`/api/meals/daily${date ? `?selected_date=${date}` : ''}`).then(res => res.data),
};

// Weight API
export const weightApi = {
  getAll: () => api.get<WeightEntry[]>('/api/weight').then(res => res.data),
  add: (weight: WeightEntry) => api.post('/api/weight', weight).then(res => res.data),
  reset: () => api.delete('/api/weight').then(res => res.data),
  getStats: () => api.get('/api/weight/stats').then(res => res.data),
  getForecast: (mode: 'plan' | 'calorie', targetRatePct?: number, horizon: number = 12, smoothDays: number = 7) => {
    const params = new URLSearchParams({
      mode,
      horizon: horizon.toString(),
      smooth_days: smoothDays.toString(),
    });
    if (targetRatePct !== undefined) {
      params.append('target_rate_pct', targetRatePct.toString());
    }
    return api.get<{actual: Array<{date: string; value: number; lower: number; upper: number}>; forecast: Array<{date: string; value: number; lower: number; upper: number}>}>(
      `/api/weight/forecast?${params.toString()}`
    ).then(res => res.data);
  },
};

// Profile API
export const profileApi = {
  get: () => api.get<Profile>('/api/profile').then(res => res.data),
  update: (profile: Profile) => api.post('/api/profile', profile).then(res => res.data),
  getTdee: () => api.get<{tdee: number}>('/api/profile/tdee').then(res => res.data),
};

// Exercises API
export const exercisesApi = {
  getCatalog: () => api.get<{catalog: ExerciseCatalog}>('/api/exercises').then(res => res.data.catalog),
};

export default api;

