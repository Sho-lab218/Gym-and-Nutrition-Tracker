import { useState } from 'react';
import { workoutsApi, mealsApi, weightApi } from '../api';

export function Settings() {
  const [resetting, setResetting] = useState<string | null>(null);

  const handleResetWorkouts = async () => {
    if (!confirm('Are you sure you want to delete ALL workout data? This action cannot be undone.')) return;
    setResetting('workouts');
    try {
      await workoutsApi.reset();
      alert('Workout data reset successfully!');
    } catch (error) {
      console.error('Failed to reset workouts:', error);
      alert('Failed to reset workout data. Please try again.');
    } finally {
      setResetting(null);
    }
  };

  const handleResetMeals = async () => {
    if (!confirm('Are you sure you want to delete ALL meal data? This action cannot be undone.')) return;
    setResetting('meals');
    try {
      await mealsApi.reset();
      alert('Meal data reset successfully!');
    } catch (error) {
      console.error('Failed to reset meals:', error);
      alert('Failed to reset meal data. Please try again.');
    } finally {
      setResetting(null);
    }
  };

  const handleResetWeights = async () => {
    if (!confirm('Are you sure you want to delete ALL weight data? This action cannot be undone.')) return;
    setResetting('weights');
    try {
      await weightApi.reset();
      alert('Weight data reset successfully!');
    } catch (error) {
      console.error('Failed to reset weights:', error);
      alert('Failed to reset weight data. Please try again.');
    } finally {
      setResetting(null);
    }
  };

  const handleResetAll = async () => {
    if (!confirm('⚠️ WARNING: This will delete ALL your data (workouts, meals, and weights). This action cannot be undone. Are you absolutely sure?')) return;
    setResetting('all');
    try {
      await Promise.all([
        workoutsApi.reset(),
        mealsApi.reset(),
        weightApi.reset(),
      ]);
      alert('All data reset successfully!');
    } catch (error) {
      console.error('Failed to reset all data:', error);
      alert('Failed to reset some data. Please try again.');
    } finally {
      setResetting(null);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">⚙️ Settings</h1>
      
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Data Management</h2>
        <p className="text-slate-300 mb-6">
          Reset your data to start fresh. You can manage your profile and TDEE settings on the Nutrition page.
        </p>

        <div className="space-y-4">
          <div className="border border-slate-700 rounded-lg p-4">
            <h3 className="text-lg font-medium text-white mb-2">Reset Individual Data</h3>
            <div className="flex flex-wrap gap-4">
              <button
                onClick={handleResetWorkouts}
                disabled={resetting !== null}
                className="flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Reset Workouts
              </button>
              
              <button
                onClick={handleResetMeals}
                disabled={resetting !== null}
                className="flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Reset Meals
              </button>
              
              <button
                onClick={handleResetWeights}
                disabled={resetting !== null}
                className="flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Reset Weights
              </button>
            </div>
          </div>

          <div className="border-2 border-red-600 rounded-lg p-4 bg-red-900/20">
            <h3 className="text-lg font-medium text-red-400 mb-2">⚠️ Reset All Data</h3>
            <p className="text-slate-300 text-sm mb-4">
              This will permanently delete all workouts, meals, and weight entries. This action cannot be undone.
            </p>
            <button
              onClick={handleResetAll}
              disabled={resetting !== null}
              className="px-6 py-2 bg-red-700 hover:bg-red-800 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
            >
              {resetting === 'all' ? 'Resetting...' : 'Reset All Data'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

