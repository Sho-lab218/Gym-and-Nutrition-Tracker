import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Home } from './pages/Home';
import { Workouts } from './pages/Workouts';
import { Nutrition } from './pages/Nutrition';
import { Progress } from './pages/Progress';
import { Settings } from './pages/Settings';
import { 
  HomeIcon, 
  BeakerIcon, 
  ChartBarIcon, 
  Cog6ToothIcon,
  FireIcon 
} from '@heroicons/react/24/outline';

function Navigation() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', icon: HomeIcon, label: 'Home' },
    { path: '/workouts', icon: FireIcon, label: 'Workouts' },
    { path: '/nutrition', icon: BeakerIcon, label: 'Nutrition' },
    { path: '/progress', icon: ChartBarIcon, label: 'Progress' },
    { path: '/settings', icon: Cog6ToothIcon, label: 'Settings' },
  ];

  return (
    <nav className="bg-slate-900 border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-white">🏋️ Gym & Nutrition Tracker</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive
                        ? 'border-primary-500 text-primary-400'
                        : 'border-transparent text-slate-300 hover:text-slate-100 hover:border-slate-300'
                    }`}
                  >
                    <Icon className="h-5 w-5 mr-2" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  console.log('App component rendering...');
  
  return (
    <Router>
      <div className="min-h-screen bg-slate-950">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/workouts" element={<Workouts />} />
            <Route path="/nutrition" element={<Nutrition />} />
            <Route path="/progress" element={<Progress />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
