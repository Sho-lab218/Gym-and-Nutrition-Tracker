import { useState, useEffect } from 'react';
import { weightApi, profileApi } from '../api';
import type { WeightEntry } from '../api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { format } from 'date-fns';

export function Progress() {
  const [weights, setWeights] = useState<WeightEntry[]>([]);
  const [stats, setStats] = useState({ start: null as number | null, current: null as number | null, delta: null as number | null, goal: null as number | null });
  const [forecast, setForecast] = useState<{actual: Array<{date: string; value: number; lower: number; upper: number}>; forecast: Array<{date: string; value: number; lower: number; upper: number}>} | null>(null);
  const [mode, setMode] = useState<'plan' | 'calorie'>('plan');
  const [targetRatePct, setTargetRatePct] = useState(0);
  const [horizon, setHorizon] = useState(12);
  const [smoothDays, setSmoothDays] = useState(7);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showBaselineForm, setShowBaselineForm] = useState(true);
  const [tdee, setTdee] = useState(0);
  
  const [baselineForm, setBaselineForm] = useState({
    date: format(new Date(), 'yyyy-MM-dd'),
    start_weight: 170,
    goal_weight: 160,
  });

  const [weightForm, setWeightForm] = useState({
    date: format(new Date(), 'yyyy-MM-dd'),
    body_weight_lbs: 170,
    goal_weight_lbs: 0,
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (weights.length > 0) {
      loadForecast();
    }
  }, [mode, targetRatePct, horizon, smoothDays, weights]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [weightsData, statsData, tdeeData] = await Promise.all([
        weightApi.getAll(),
        weightApi.getStats(),
        profileApi.getTdee().catch(() => ({ tdee: 2000 })),
      ]);
      setWeights(weightsData);
      // Force stats update by fetching fresh data
      const freshStats = await weightApi.getStats();
      setStats(freshStats);
      setTdee(tdeeData.tdee);
      if (weightsData.length > 0) {
        setShowBaselineForm(false);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadForecast = async () => {
    try {
      const data = await weightApi.getForecast(mode, targetRatePct !== 0 ? targetRatePct : undefined, horizon, smoothDays);
      setForecast(data);
    } catch (error) {
      console.error('Failed to load forecast:', error);
    }
  };

  const handleBaselineSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Ensure values are numbers
    const startWeight = Number(baselineForm.start_weight) || 0;
    const goalWeight = Number(baselineForm.goal_weight) || 0;
    
    if (startWeight <= 0) {
      alert('Please enter a valid start weight');
      return;
    }
    
    try {
      await weightApi.add({
        date: baselineForm.date,
        body_weight_lbs: startWeight,
        goal_weight_lbs: goalWeight > 0 ? goalWeight : undefined,
      });
      setShowBaselineForm(false);
      loadData();
    } catch (error: any) {
      console.error('Failed to set baseline:', error);
      const errorMsg = error?.response?.data?.detail || error?.message || 'Unknown error';
      alert(`Failed to set baseline: ${errorMsg}`);
    }
  };

  const handleWeightSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await weightApi.add({
        date: weightForm.date,
        body_weight_lbs: weightForm.body_weight_lbs,
        goal_weight_lbs: weightForm.goal_weight_lbs || undefined,
      });
      setShowAddForm(false);
      setWeightForm({
        date: format(new Date(), 'yyyy-MM-dd'),
        body_weight_lbs: 170,
        goal_weight_lbs: 0,
      });
      // Reload data to refresh stats and weights
      await loadData();
      // Reload forecast after weights are updated
      await loadForecast();
    } catch (error: any) {
      console.error('Failed to add weight:', error);
      const errorMsg = error?.response?.data?.detail || error?.message || 'Unknown error';
      alert(`Failed to add weight: ${errorMsg}`);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to delete all weight data? This action cannot be undone.')) return;
    try {
      await weightApi.reset();
      await loadData();
      await loadForecast();
    } catch (error) {
      console.error('Failed to reset weights:', error);
      alert('Failed to reset weight data. Please try again.');
    }
  };

  const calculateSuggestedCalories = () => {
    if (!stats.current) return 0;
    const adapt = 0.75;
    const curr_kg = stats.current / 2.20462;
    const kg_per_wk = curr_kg * (targetRatePct / 100.0);
    const kcal_per_day_offset = (kg_per_wk * 7700.0) / 7.0 / adapt;
    return tdee + kcal_per_day_offset;
  };

  const chartData = weights.map(w => ({
    date: w.date,
    value: w.body_weight_lbs,
  }));

  if (loading) {
    return <div className="text-center text-slate-400">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">📈 Progress (Body Weight)</h1>

      {/* Start & Goal */}
      {showBaselineForm && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">🎯 Start & Goal</h2>
          <form onSubmit={handleBaselineSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Start Date</label>
                <input
                  type="date"
                  value={baselineForm.date}
                  onChange={(e) => setBaselineForm({ ...baselineForm, date: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Start Weight (lbs)</label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={baselineForm.start_weight}
                  onChange={(e) => setBaselineForm({ ...baselineForm, start_weight: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Goal Weight (lbs)</label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={baselineForm.goal_weight}
                  onChange={(e) => setBaselineForm({ ...baselineForm, goal_weight: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
            </div>
            <div className="flex gap-4">
              <button
                type="submit"
                className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Set Start & Goal
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="text-red-400 hover:text-red-300"
              >
                Reset All
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Reset Button */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <button
          onClick={handleReset}
          className="flex items-center text-red-400 hover:text-red-300 transition-colors"
        >
          <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Reset all weight data
        </button>
      </div>

      {/* Stats */}
      {stats.start !== null && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div className="text-sm text-slate-400">Start</div>
            <div className="text-2xl font-bold text-white">{stats.start.toFixed(0)} lbs</div>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div className="text-sm text-slate-400">Current</div>
            <div className="text-2xl font-bold text-white">
              {stats.current?.toFixed(0)} lbs
              {stats.delta !== null && (
                <span className={`text-sm ml-2 ${stats.delta >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {stats.delta >= 0 ? '+' : ''}{stats.delta.toFixed(1)} lbs
                </span>
              )}
            </div>
          </div>
          {stats.goal !== null && (
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <div className="text-sm text-slate-400">Goal</div>
              <div className="text-2xl font-bold text-white">{stats.goal.toFixed(0)} lbs</div>
            </div>
          )}
        </div>
      )}

      {/* Add Weight Entry */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">➕ Add a weight entry</h2>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="text-primary-400 hover:text-primary-300"
          >
            {showAddForm ? 'Hide' : 'Show'}
          </button>
        </div>

        {showAddForm && (
          <form onSubmit={handleWeightSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Date</label>
                <input
                  type="date"
                  value={weightForm.date}
                  onChange={(e) => setWeightForm({ ...weightForm, date: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Body Weight (lbs)</label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={weightForm.body_weight_lbs}
                  onChange={(e) => setWeightForm({ ...weightForm, body_weight_lbs: parseFloat(e.target.value) })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Goal (optional)</label>
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={weightForm.goal_weight_lbs || ''}
                  onChange={(e) => setWeightForm({ ...weightForm, goal_weight_lbs: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                />
              </div>
            </div>
            <button
              type="submit"
              className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
            >
              Save Entry
            </button>
          </form>
        )}
      </div>

      {/* Trend Chart */}
      {chartData.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Body Weight Trend</h2>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={chartData}>
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
              {stats.goal !== null && (
                <ReferenceLine y={stats.goal} stroke="#f59e0b" strokeDasharray="5 5" label="Goal" />
              )}
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#38bdf8" 
                strokeWidth={2}
                name="Weight (lbs)"
                dot={{ fill: '#38bdf8' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Forecasts */}
      {weights.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Forecasts</h2>
          
          <div className="mb-4">
            <div className="flex gap-4 mb-4">
              <button
                onClick={() => setMode('plan')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  mode === 'plan'
                    ? 'bg-primary-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                📐 Plan: lose / maintain / gain
              </button>
              <button
                onClick={() => setMode('calorie')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  mode === 'calorie'
                    ? 'bg-primary-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                🔥 From calorie trend
              </button>
            </div>

            {mode === 'plan' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Pace (% bodyweight per week): {targetRatePct > 0 ? '+' : ''}{targetRatePct.toFixed(1)}%
                  </label>
                  <input
                    type="range"
                    min="-2"
                    max="1.5"
                    step="0.1"
                    value={targetRatePct}
                    onChange={(e) => setTargetRatePct(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-slate-400 mt-1">
                    <span>-2.0% (lose)</span>
                    <span>0% (maintain)</span>
                    <span>+1.5% (gain)</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-900 rounded-lg p-4">
                    <div className="text-sm text-slate-400">Estimated TDEE</div>
                    <div className="text-xl font-bold text-white">{tdee.toFixed(0)} kcal/day</div>
                  </div>
                  <div className="bg-slate-900 rounded-lg p-4">
                    <div className="text-sm text-slate-400">Suggested daily calories</div>
                    <div className="text-xl font-bold text-white">{calculateSuggestedCalories().toFixed(0)} kcal/day</div>
                  </div>
                </div>
              </div>
            )}

            {mode === 'calorie' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Calorie smoothing (days): {smoothDays}
                </label>
                <input
                  type="range"
                  min="3"
                  max="14"
                  value={smoothDays}
                  onChange={(e) => setSmoothDays(parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
            )}

            <div className="mt-4">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Forecast horizon (weeks): {horizon}
              </label>
              <input
                type="range"
                min="4"
                max="26"
                value={horizon}
                onChange={(e) => setHorizon(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          </div>

          {forecast && forecast.actual.length > 0 && (
            <ResponsiveContainer width="100%" height={400}>
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
                {stats.goal !== null && (
                  <ReferenceLine y={stats.goal} stroke="#f59e0b" strokeDasharray="5 5" label="Goal" />
                )}
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#38bdf8" 
                  strokeWidth={2}
                  name="Actual"
                  dot={{ fill: '#38bdf8' }}
                  data={forecast.actual}
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#fbbf24" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Forecast"
                  dot={{ fill: '#fbbf24' }}
                  data={forecast.forecast}
                />
                <Line 
                  type="monotone" 
                  dataKey="upper" 
                  stroke="#fbbf24" 
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  strokeOpacity={0.3}
                  name="Upper CI"
                  dot={false}
                  data={forecast.forecast}
                />
                <Line 
                  type="monotone" 
                  dataKey="lower" 
                  stroke="#fbbf24" 
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  strokeOpacity={0.3}
                  name="Lower CI"
                  dot={false}
                  data={forecast.forecast}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      )}

      {weights.length === 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center text-slate-400">
          Add a baseline or your first weight to begin.
        </div>
      )}
    </div>
  );
}

