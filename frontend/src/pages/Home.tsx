import { Link } from 'react-router-dom';
import { FireIcon, BeakerIcon, ChartBarIcon } from '@heroicons/react/24/outline';

export function Home() {
  console.log('Home component rendering...');
  
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-primary-900/20 via-slate-900 to-emerald-900/20 border border-slate-700 rounded-2xl p-8 md:p-12">
        <div className="relative">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            🏋️‍♂️ Gym & Nutrition Tracker
          </h1>
          <p className="text-xl text-slate-300 mb-6">
            Train smarter. Log workouts & meals. See progress with forecasts.
          </p>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/workouts"
          className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-primary-500 transition-colors group"
        >
          <div className="flex items-center mb-4">
            <FireIcon className="h-8 w-8 text-primary-400 mr-3" />
            <h2 className="text-xl font-semibold text-white">Workouts</h2>
          </div>
          <p className="text-slate-400 mb-4">
            Volume, trends, recent sessions. Track your strength progress and see forecasts.
          </p>
          <span className="text-primary-400 group-hover:text-primary-300 font-medium">
            Open Workouts →
          </span>
        </Link>

        <Link
          to="/nutrition"
          className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-primary-500 transition-colors group"
        >
          <div className="flex items-center mb-4">
            <BeakerIcon className="h-8 w-8 text-emerald-400 mr-3" />
            <h2 className="text-xl font-semibold text-white">Nutrition</h2>
          </div>
          <p className="text-slate-400 mb-4">
            Log meals & view macros. Set your TDEE for accurate weight predictions.
          </p>
          <span className="text-emerald-400 group-hover:text-emerald-300 font-medium">
            Open Nutrition →
          </span>
        </Link>

        <Link
          to="/progress"
          className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-primary-500 transition-colors group"
        >
          <div className="flex items-center mb-4">
            <ChartBarIcon className="h-8 w-8 text-blue-400 mr-3" />
            <h2 className="text-xl font-semibold text-white">Progress</h2>
          </div>
          <p className="text-slate-400 mb-4">
            Body weight trend with ML projection. Set goals and track your journey.
          </p>
          <span className="text-blue-400 group-hover:text-blue-300 font-medium">
            Open Progress →
          </span>
        </Link>
      </div>

      {/* Info Section */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-2">Today</h3>
        <p className="text-slate-400">
          Use each page to log your workouts, meals, and weight. The app will automatically
          update your progress and provide ML-powered forecasts based on your data.
        </p>
      </div>
    </div>
  );
}

