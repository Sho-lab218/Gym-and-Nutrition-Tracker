import { useState, useEffect } from 'react';
import { mealsApi, profileApi } from '../api';
import type { Profile, MealEntry } from '../api';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { format } from 'date-fns';

export function Nutrition() {
  const [meals, setMeals] = useState<MealEntry[]>([]);
  const [dailyMeals, setDailyMeals] = useState<MealEntry[]>([]);
  const [selectedDate, setSelectedDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [, setProfile] = useState<Profile | null>(null);
  const [tdee, setTdee] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [showMealForm, setShowMealForm] = useState(false);
  
  const [profileForm, setProfileForm] = useState<Profile>({
    sex: 'Male',
    age: 22,
    height_cm: 175,
    curr_weight_lbs: 170,
    activity: 'Moderate',
  });

  const [mealForm, setMealForm] = useState({
    date: format(new Date(), 'yyyy-MM-dd'),
    calories: 0,
    protein_g: 0,
    carbs_g: 0,
    fat_g: 0,
    notes: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadDailyMeals();
  }, [selectedDate]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [mealsData, profileData, tdeeData] = await Promise.all([
        mealsApi.getAll(),
        profileApi.get(),
        profileApi.getTdee(),
      ]);
      setMeals(mealsData);
      if (profileData) {
        setProfile(profileData);
        // Initialize profileForm with existing profile data, ensuring all fields have defaults
        setProfileForm({
          sex: profileData.sex || 'Male',
          age: profileData.age || 22,
          height_cm: profileData.height_cm || 175,
          curr_weight_lbs: profileData.curr_weight_lbs || 170,
          activity: profileData.activity || 'Moderate',
        });
      } else {
        setProfile(null);
      }
      setTdee(tdeeData.tdee);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDailyMeals = async () => {
    try {
      const data = await mealsApi.getDaily(selectedDate);
      // Ensure data is an array
      setDailyMeals(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load daily meals:', error);
      setDailyMeals([]);
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Validate all fields are filled
    if (!profileForm.sex || !profileForm.age || !profileForm.height_cm || !profileForm.curr_weight_lbs || !profileForm.activity) {
      alert('Please fill in all fields');
      return;
    }
    try {
      await profileApi.update(profileForm);
      const tdeeData = await profileApi.getTdee();
      setTdee(tdeeData.tdee);
      setProfile(profileForm);
      setShowProfileForm(false);
      loadData();
    } catch (error: any) {
      console.error('Failed to update profile:', error);
      let errorMsg = 'Unknown error';
      if (error?.response?.data?.detail) {
        errorMsg = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail);
      } else if (error?.message) {
        errorMsg = error.message;
      } else if (typeof error === 'string') {
        errorMsg = error;
      }
      alert(`Failed to update profile: ${errorMsg}`);
    }
  };

  const handleMealSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Ensure all values are numbers, not NaN
    const carbs = Number(mealForm.carbs_g) || 0;
    const protein = Number(mealForm.protein_g) || 0;
    const fat = Number(mealForm.fat_g) || 0;
    const calories = mealForm.calories || (carbs * 4 + protein * 4 + fat * 9);
    
    try {
      await mealsApi.add({ 
        ...mealForm, 
        calories: Number(calories) || 0,
        carbs_g: carbs,
        protein_g: protein,
        fat_g: fat,
      });
      setShowMealForm(false);
      setMealForm({
        date: format(new Date(), 'yyyy-MM-dd'),
        calories: 0,
        protein_g: 0,
        carbs_g: 0,
        fat_g: 0,
        notes: '',
      });
      await loadData();
      await loadDailyMeals();
    } catch (error: any) {
      console.error('Failed to add meal:', error);
      const errorMsg = error?.response?.data?.detail || error?.message || 'Unknown error';
      alert(`Failed to add meal: ${errorMsg}`);
    }
  };

  const handleResetMeals = async () => {
    if (!confirm('Are you sure you want to delete all meal data?')) return;
    try {
      await mealsApi.reset();
      loadData();
    } catch (error) {
      console.error('Failed to reset meals:', error);
    }
  };

  // dailyMeals from API is already aggregated by date for the selected date
  // The API filters by selected_date, so we should have at most one entry
  // Find the entry that matches the selected date (in case of any date format mismatches)
  const dailyTotal = dailyMeals.length > 0 
    ? (dailyMeals.find(m => m.date === selectedDate) || dailyMeals[0])
    : { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 };

  const macroData = [
    { name: 'Carbs', value: Number(dailyTotal.carbs_g || 0) * 4, grams: Number(dailyTotal.carbs_g || 0) },
    { name: 'Protein', value: Number(dailyTotal.protein_g || 0) * 4, grams: Number(dailyTotal.protein_g || 0) },
    { name: 'Fat', value: Number(dailyTotal.fat_g || 0) * 9, grams: Number(dailyTotal.fat_g || 0) },
  ].filter(item => item.value > 0);

  const COLORS = ['#38bdf8', '#10b981', '#f59e0b'];

  if (loading) {
    return <div className="text-center text-slate-400">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">🍎 Nutrition</h1>

      {/* TDEE Settings */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">TDEE Settings</h2>
          <button
            onClick={() => setShowProfileForm(!showProfileForm)}
            className="text-primary-400 hover:text-primary-300"
          >
            {showProfileForm ? 'Hide' : 'Edit'}
          </button>
        </div>

        {showProfileForm ? (
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Sex</label>
                <select
                  value={profileForm.sex}
                  onChange={(e) => setProfileForm({ ...profileForm, sex: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Age</label>
                <input
                  type="number"
                  min="12"
                  max="90"
                  value={profileForm.age || ''}
                  onChange={(e) => setProfileForm({ ...profileForm, age: parseInt(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Height (cm)</label>
                <input
                  type="number"
                  min="120"
                  max="230"
                  value={profileForm.height_cm || ''}
                  onChange={(e) => setProfileForm({ ...profileForm, height_cm: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Current Weight (lbs)</label>
                <input
                  type="number"
                  min="70"
                  step="0.5"
                  value={profileForm.curr_weight_lbs || ''}
                  onChange={(e) => setProfileForm({ ...profileForm, curr_weight_lbs: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Activity Level</label>
                <select
                  value={profileForm.activity}
                  onChange={(e) => setProfileForm({ ...profileForm, activity: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="Sedentary">Sedentary</option>
                  <option value="Light">Light</option>
                  <option value="Moderate">Moderate</option>
                  <option value="Active">Active</option>
                  <option value="Very Active">Very Active</option>
                </select>
              </div>
            </div>
            <button
              type="submit"
              className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
            >
              Save TDEE Settings
            </button>
          </form>
        ) : (
          <div className="text-slate-300">
            <p>Estimated TDEE: <span className="text-primary-400 font-semibold">{tdee.toFixed(0)} kcal/day</span></p>
            <p className="text-sm text-slate-400 mt-1">Used by Progress page for weight predictions</p>
          </div>
        )}
      </div>

      {/* Add Meal Form */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">➕ Add a meal</h2>
          <button
            onClick={() => setShowMealForm(!showMealForm)}
            className="text-primary-400 hover:text-primary-300"
          >
            {showMealForm ? 'Hide' : 'Show'}
          </button>
        </div>

        {showMealForm && (
          <form onSubmit={handleMealSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Date</label>
              <input
                type="date"
                value={mealForm.date}
                onChange={(e) => setMealForm({ ...mealForm, date: e.target.value })}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                required
              />
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Carbs (g)</label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={mealForm.carbs_g}
                  onChange={(e) => setMealForm({ ...mealForm, carbs_g: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Protein (g)</label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={mealForm.protein_g}
                  onChange={(e) => setMealForm({ ...mealForm, protein_g: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Fat (g)</label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={mealForm.fat_g}
                  onChange={(e) => setMealForm({ ...mealForm, fat_g: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Calories (optional)</label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={mealForm.calories}
                  onChange={(e) => setMealForm({ ...mealForm, calories: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  placeholder="Auto if 0"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Notes</label>
              <input
                type="text"
                value={mealForm.notes}
                onChange={(e) => setMealForm({ ...mealForm, notes: e.target.value })}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
              />
            </div>
            <div className="flex gap-4">
              <button
                type="submit"
                className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-lg transition-colors"
              >
                Save Meal
              </button>
              <button
                type="button"
                onClick={handleResetMeals}
                className="flex items-center text-red-400 hover:text-red-300 transition-colors"
              >
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Reset all meals
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Daily Macros */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-300 mb-1">Show day</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white"
          />
        </div>

        <div>
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-white mb-2">
              Daily Macros — {format(new Date(selectedDate), 'MMM d, yyyy')}
            </h3>
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-slate-400">Calories</div>
                <div className="text-xl font-bold text-white">{Number(dailyTotal.calories || 0).toFixed(0)}</div>
              </div>
              <div>
                <div className="text-slate-400">Protein</div>
                <div className="text-xl font-bold text-white">{Number(dailyTotal.protein_g || 0).toFixed(1)}g</div>
              </div>
              <div>
                <div className="text-slate-400">Carbs</div>
                <div className="text-xl font-bold text-white">{Number(dailyTotal.carbs_g || 0).toFixed(1)}g</div>
              </div>
              <div>
                <div className="text-slate-400">Fat</div>
                <div className="text-xl font-bold text-white">{Number(dailyTotal.fat_g || 0).toFixed(1)}g</div>
              </div>
            </div>
          </div>
          {macroData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={macroData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(props: any) => {
                      const { name, value } = props;
                      const grams = macroData.find((m: any) => m.name === name)?.grams || 0;
                      return `${name}: ${value.toFixed(0)} kcal (${grams.toFixed(1)}g)`;
                    }}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {macroData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-slate-400 text-center py-8">
                No macros recorded for this day
              </div>
            )}
        </div>
      </div>

      {/* Meals List */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Meals (raw entries)</h2>
        {meals.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-2 px-4 text-slate-300">Date</th>
                  <th className="text-left py-2 px-4 text-slate-300">Calories</th>
                  <th className="text-left py-2 px-4 text-slate-300">Protein (g)</th>
                  <th className="text-left py-2 px-4 text-slate-300">Carbs (g)</th>
                  <th className="text-left py-2 px-4 text-slate-300">Fat (g)</th>
                  <th className="text-left py-2 px-4 text-slate-300">Notes</th>
                </tr>
              </thead>
              <tbody>
                {meals.map((meal, idx) => (
                  <tr key={idx} className="border-b border-slate-700">
                    <td className="py-2 px-4 text-slate-300">{format(new Date(meal.date), 'MMM d, yyyy')}</td>
                    <td className="py-2 px-4 text-white">{meal.calories.toFixed(0)}</td>
                    <td className="py-2 px-4 text-white">{meal.protein_g.toFixed(1)}</td>
                    <td className="py-2 px-4 text-white">{meal.carbs_g.toFixed(1)}</td>
                    <td className="py-2 px-4 text-white">{meal.fat_g.toFixed(1)}</td>
                    <td className="py-2 px-4 text-slate-400">{meal.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center text-slate-400 py-4">No meals logged yet</div>
        )}
      </div>
    </div>
  );
}

