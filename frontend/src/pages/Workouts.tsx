import { useState, useEffect } from 'react';
import { workoutsApi, exercisesApi } from '../api';
import type { WorkoutEntry } from '../api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

export function Workouts() {
  const [workouts, setWorkouts] = useState<WorkoutEntry[]>([]);
  const [stats, setStats] = useState({ sessions_this_week: 0, total_volume: 0, distinct_exercises: 0 });
  const [exerciseCatalog, setExerciseCatalog] = useState<Record<string, string[]>>({});
  const [catalogLoaded, setCatalogLoaded] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<string>('(All)');
  const [selectedExercise, setSelectedExercise] = useState<string>('');
  const [progression, setProgression] = useState<Array<{date: string; top_weight: number}>>([]);
  const [forecast, setForecast] = useState<{actual: Array<{date: string; value: number}>; forecast: Array<{date: string; value: number}>} | null>(null);
  const [horizon, setHorizon] = useState(8);
  const [loading, setLoading] = useState(true);
  
  // Form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    date: format(new Date(), 'yyyy-MM-dd'),
    exercise: '',
    sets: 3,
    reps: 8,
    weight_kg: 0,
    muscle_group: '',
    notes: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedExercise && !loading) {
      loadProgression();
      loadForecast();
    }
  }, [selectedExercise, horizon]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [workoutsData, statsData, catalog] = await Promise.all([
        workoutsApi.getAll(),
        workoutsApi.getStats(),
        exercisesApi.getCatalog(),
      ]);
      setWorkouts(workoutsData);
      setStats(statsData);
      setExerciseCatalog(catalog);
      setCatalogLoaded(true);
      
      const availableExercises = workoutsData.map(w => w.exercise);
      if (availableExercises.length > 0 && !selectedExercise) {
        setSelectedExercise(availableExercises[0]);
      }
    } catch (error: any) {
      console.error('Failed to load data:', error);
      // Set empty catalog if API fails, but still allow form to work
      if (!catalogLoaded) {
        // Try to load catalog separately
        exercisesApi.getCatalog()
          .then(cat => {
            setExerciseCatalog(cat);
            setCatalogLoaded(true);
          })
          .catch(() => {
            // If catalog fails, set empty but mark as loaded
            setExerciseCatalog({});
            setCatalogLoaded(true);
          });
      }
    } finally {
      setLoading(false);
    }
  };

  const loadProgression = async () => {
    try {
      const data = await workoutsApi.getProgression(selectedExercise);
      setProgression(data);
    } catch (error) {
      console.error('Failed to load progression:', error);
    }
  };

  const loadForecast = async () => {
    try {
      const data = await workoutsApi.getForecast(selectedExercise, horizon);
      setForecast(data);
    } catch (error) {
      console.error('Failed to load forecast:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const exerciseAdded = formData.exercise;
      await workoutsApi.add(formData);
      setShowAddForm(false);
      setFormData({
        date: format(new Date(), 'yyyy-MM-dd'),
        exercise: '',
        sets: 3,
        reps: 8,
        weight_kg: 0,
        muscle_group: '',
        notes: '',
      });
      // Reload data to refresh stats and forecasts
      await loadData();
      // Always reload progression and forecast for the currently selected exercise
      // This ensures forecasts update even if we just added data for a different exercise
      if (selectedExercise) {
        await loadProgression();
        await loadForecast();
      }
    } catch (error: any) {
      console.error('Failed to add workout:', error);
      const errorMsg = error?.response?.data?.detail || error?.message || 'Unknown error';
      alert(`Failed to add workout: ${errorMsg}`);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to delete all workout data?')) return;
    try {
      await workoutsApi.reset();
      loadData();
    } catch (error) {
      console.error('Failed to reset workouts:', error);
    }
  };

  const availableExercises = selectedGroup === '(All)'
    ? Array.from(new Set(workouts.map(w => w.exercise))).sort()
    : exerciseCatalog[selectedGroup] || [];

  const exerciseOptions = selectedGroup === '(All)'
    ? availableExercises
    : exerciseCatalog[selectedGroup] || [];

  if (loading) {
    return <div className="text-center text-slate-400">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">🏋️ Workouts</h1>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="text-sm text-slate-400">Sessions (this week)</div>
          <div className="text-2xl font-bold text-white">{stats.sessions_this_week}</div>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="text-sm text-slate-400">Total Volume</div>
          <div className="text-2xl font-bold text-white">{stats.total_volume.toLocaleString()}</div>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="text-sm text-slate-400">Distinct Exercises</div>
          <div className="text-2xl font-bold text-white">{stats.distinct_exercises}</div>
        </div>
      </div>

      {/* Add Workout Form */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">➕ Log a workout</h2>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="text-primary-400 hover:text-primary-300"
          >
            {showAddForm ? 'Hide' : 'Show'}
          </button>
        </div>
        
        {showAddForm && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Date</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Muscle Group</label>
                <select
                  value={formData.muscle_group}
                  onChange={(e) => {
                    setFormData({ ...formData, muscle_group: e.target.value, exercise: '' });
                    setSelectedGroup(e.target.value);
                  }}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                  disabled={!catalogLoaded}
                >
                  <option value="">{catalogLoaded ? 'Select...' : 'Loading...'}</option>
                  {Object.keys(exerciseCatalog).sort().map(group => (
                    <option key={group} value={group}>{group}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Exercise</label>
                <select
                  value={formData.exercise}
                  onChange={(e) => setFormData({ ...formData, exercise: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                  disabled={!formData.muscle_group}
                >
                  <option value="">Select...</option>
                  {exerciseCatalog[formData.muscle_group]?.map(ex => (
                    <option key={ex} value={ex}>{ex}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Sets</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={formData.sets}
                  onChange={(e) => setFormData({ ...formData, sets: parseInt(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Reps</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={formData.reps}
                  onChange={(e) => setFormData({ ...formData, reps: parseInt(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Weight (kg)</label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={formData.weight_kg}
                  onChange={(e) => setFormData({ ...formData, weight_kg: parseFloat(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Notes</label>
              <input
                type="text"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
            <button
              type="submit"
              className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
            >
              Save Workout
            </button>
          </form>
        )}
      </div>

      {/* Reset Button */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <button
          onClick={handleReset}
          className="flex items-center text-red-400 hover:text-red-300 transition-colors"
        >
          <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Reset all workout data
        </button>
      </div>

      {/* Exercise Progression */}
      {workouts.length > 0 && (
        <div className="space-y-6">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Exercise Progression</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Muscle Group</label>
                <select
                  value={selectedGroup}
                  onChange={(e) => {
                    setSelectedGroup(e.target.value);
                    setSelectedExercise('');
                  }}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="(All)">(All)</option>
                  {Object.keys(exerciseCatalog).sort().map(group => (
                    <option key={group} value={group}>{group}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Exercise</label>
                <select
                  value={selectedExercise}
                  onChange={(e) => setSelectedExercise(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="">Select...</option>
                  {exerciseOptions.map(ex => (
                    <option key={ex} value={ex}>{ex}</option>
                  ))}
                </select>
              </div>
            </div>

            {selectedExercise && progression.length > 0 && (
              <div className="mt-4">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={progression}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#94a3b8"
                      tickFormatter={(value) => format(new Date(value), 'MMM d')}
                    />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                      labelFormatter={(value) => format(new Date(value), 'MMM d, yyyy')}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="top_weight" 
                      stroke="#38bdf8" 
                      strokeWidth={2}
                      name="Top Weight (kg)"
                      dot={{ fill: '#38bdf8' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Forecast */}
          {selectedExercise && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">Projected Strength</h2>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-slate-300">Horizon (weeks):</label>
                  <input
                    type="number"
                    min="4"
                    max="26"
                    value={horizon}
                    onChange={(e) => setHorizon(parseInt(e.target.value))}
                    className="w-20 bg-slate-900 border border-slate-600 rounded-lg px-3 py-1 text-white"
                  />
                </div>
              </div>
              
              {forecast && forecast.actual.length > 0 ? (
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={[...forecast.actual, ...forecast.forecast]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#94a3b8"
                      tickFormatter={(value) => format(new Date(value), 'MMM d')}
                    />
                    <YAxis stroke="#94a3b8" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                      labelFormatter={(value) => format(new Date(value), 'MMM d, yyyy')}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#38bdf8" 
                      strokeWidth={2}
                      name="Actual"
                      dot={{ fill: '#38bdf8' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#fbbf24" 
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Forecast"
                      dot={{ fill: '#fbbf24' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-slate-400 text-center py-8">
                  {selectedExercise ? 'Not enough data to forecast. Add more workouts for this exercise.' : 'Select an exercise to see forecast'}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {workouts.length === 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center text-slate-400">
          No workouts logged yet. Add your first workout above!
        </div>
      )}
    </div>
  );
}

