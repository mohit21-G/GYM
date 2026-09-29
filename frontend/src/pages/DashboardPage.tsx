import React, { useState, useEffect } from 'react';
import { apiClient } from '../config/api';
import {
  Flame,
  Utensils,
  Droplets,
  Moon,
  Scale,
  TrendingDown,
  TrendingUp,
  Minus,
  RefreshCw,
  PlusCircle,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  const [todayData, setTodayData] = useState<any>(null);
  const [weekData, setWeekData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [todayRes, weekRes] = await Promise.all([
        apiClient.get('/dashboard/today'),
        apiClient.get('/dashboard/week'),
      ]);
      setTodayData(todayRes.data);
      setWeekData(weekRes.data);
    } catch (err: any) {
      setError(
        err.response?.data?.message ||
          'Failed to load dashboard metrics. Please try again.',
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="flex items-center space-x-3 text-slate-400">
          <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
          <span>Loading your fitness dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <div className="bg-rose-500/10 border border-rose-500/20 rounded-2xl p-6 mb-4 text-rose-300">
          {error}
        </div>
        <button
          onClick={fetchDashboardData}
          className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-sm font-medium transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const { calories, macros, activity, hydration, sleep, weight, recentLogs } =
    todayData || {};

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Daily Health Summary
          </h1>
          <p className="text-sm text-slate-400 mt-1 flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-emerald-400" />
            <span>Today, {todayData?.date}</span>
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDashboardData}
            className="p-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-slate-300 hover:text-white transition-colors"
            title="Refresh metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/chat"
            className="flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white text-sm font-medium rounded-xl shadow-lg shadow-emerald-500/20 transition-all cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span>Ask AI Assistant</span>
          </Link>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Calories Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Calories Consumed
            </span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Utensils className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">
              {calories?.consumed ?? 0}
            </span>
            <span className="text-xs text-slate-400">/ {calories?.target ?? 2000} kcal</span>
          </div>
          <div className="mt-4 space-y-2">
            <div className="w-full bg-slate-700/60 rounded-full h-2 overflow-hidden">
              <div
                className="bg-emerald-400 h-2 rounded-full transition-all duration-500"
                style={{ width: `${calories?.percentTarget ?? 0}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-400">
              <span>{calories?.remaining ?? 0} kcal left</span>
              <span>{calories?.percentTarget ?? 0}%</span>
            </div>
          </div>
        </div>

        {/* Burned / Activity Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Calories Burned
            </span>
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-amber-400">
              {activity?.caloriesBurned ?? 0}
            </span>
            <span className="text-xs text-slate-400">kcal burned</span>
          </div>
          <div className="mt-4 text-xs text-slate-400 flex justify-between items-center border-t border-slate-700/50 pt-3">
            <span>Active Workout Time:</span>
            <span className="text-slate-200 font-semibold">
              {activity?.durationMinutes ?? 0} mins
            </span>
          </div>
        </div>

        {/* Hydration Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Water Intake
            </span>
            <div className="w-8 h-8 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
              <Droplets className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-cyan-400">
              {hydration?.amountMl ?? 0}
            </span>
            <span className="text-xs text-slate-400">/ {hydration?.targetMl ?? 2500} ml</span>
          </div>
          <div className="mt-4 space-y-2">
            <div className="w-full bg-slate-700/60 rounded-full h-2 overflow-hidden">
              <div
                className="bg-cyan-400 h-2 rounded-full transition-all duration-500"
                style={{ width: `${hydration?.percentTarget ?? 0}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-400">
              <span>{Math.round((hydration?.amountMl ?? 0) / 250)} glasses</span>
              <span>{hydration?.percentTarget ?? 0}%</span>
            </div>
          </div>
        </div>

        {/* Sleep & Weight Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Sleep & Weight
            </span>
            <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <Moon className="w-4 h-4" />
            </div>
          </div>
          <div className="flex justify-between items-baseline mb-2">
            <div className="text-2xl font-bold text-indigo-300">
              {sleep?.durationHours ?? 0} hrs
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
              {sleep?.quality || 'GOOD'}
            </span>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-700/50 flex justify-between items-center text-xs">
            <span className="text-slate-400 flex items-center space-x-1">
              <Scale className="w-3.5 h-3.5 text-emerald-400" />
              <span>Weight:</span>
            </span>
            <div className="flex items-center space-x-1">
              <span className="font-semibold text-white">
                {weight?.currentWeightKg ? `${weight.currentWeightKg} kg` : 'Not logged'}
              </span>
              {weight?.trend === 'DOWN' && <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />}
              {weight?.trend === 'UP' && <TrendingUp className="w-3.5 h-3.5 text-rose-400" />}
              {weight?.trend === 'STABLE' && <Minus className="w-3.5 h-3.5 text-slate-400" />}
            </div>
          </div>
        </div>
      </div>

      {/* Middle: Macros and Weekly Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Macros Breakdown */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 shadow-xl">
          <h2 className="text-base font-bold text-white mb-4">
            Macronutrients Breakdown
          </h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Protein</span>
                <span className="font-semibold text-blue-400">{macros?.proteinG ?? 0} g</span>
              </div>
              <div className="w-full bg-slate-700/60 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-blue-400 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (macros?.proteinG ?? 0) * 1.2)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Carbohydrates</span>
                <span className="font-semibold text-amber-400">{macros?.carbsG ?? 0} g</span>
              </div>
              <div className="w-full bg-slate-700/60 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-amber-400 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (macros?.carbsG ?? 0) * 0.5)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Fat</span>
                <span className="font-semibold text-rose-400">{macros?.fatG ?? 0} g</span>
              </div>
              <div className="w-full bg-slate-700/60 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-rose-400 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (macros?.fatG ?? 0) * 1.5)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Fiber</span>
                <span className="font-semibold text-emerald-400">{macros?.fiberG ?? 0} g</span>
              </div>
              <div className="w-full bg-slate-700/60 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-emerald-400 h-2 rounded-full"
                  style={{ width: `${Math.min(100, (macros?.fiberG ?? 0) * 3)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* 7-Day Chart Summary */}
        <div className="lg:col-span-2 bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 shadow-xl">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-base font-bold text-white">7-Day Calorie Trends</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Daily intake vs active calories burned
              </p>
            </div>
            <div className="flex items-center space-x-4 text-xs">
              <div className="flex items-center space-x-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                <span className="text-slate-300">Calories In</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                <span className="text-slate-300">Calories Out</span>
              </div>
            </div>
          </div>

          {/* Simple Visual Bar Chart */}
          <div className="grid grid-cols-7 gap-2 h-44 items-end pt-4 border-b border-slate-700">
            {weekData?.chartData?.map((item: any, i: number) => {
              const maxVal = 2500;
              const inHeight = Math.min(100, Math.max(10, (item.caloriesConsumed / maxVal) * 100));
              const outHeight = Math.min(100, Math.max(10, (item.caloriesBurned / maxVal) * 100));
              return (
                <div key={i} className="flex flex-col items-center h-full justify-end group">
                  <div className="w-full flex justify-center items-end space-x-1 h-32">
                    <div
                      className="w-3 bg-emerald-400/80 group-hover:bg-emerald-400 rounded-t transition-all"
                      style={{ height: `${inHeight}%` }}
                      title={`In: ${item.caloriesConsumed} kcal`}
                    />
                    <div
                      className="w-3 bg-amber-400/80 group-hover:bg-amber-400 rounded-t transition-all"
                      style={{ height: `${outHeight}%` }}
                      title={`Out: ${item.caloriesBurned} kcal`}
                    />
                  </div>
                  <span className="text-[11px] text-slate-400 mt-2 font-medium">
                    {item.dayOfWeek}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-3 gap-4 text-center mt-4 text-xs">
            <div>
              <span className="text-slate-400">Avg Intake:</span>{' '}
              <span className="font-semibold text-emerald-400">
                {weekData?.averages?.dailyCaloriesConsumed ?? 0} kcal
              </span>
            </div>
            <div>
              <span className="text-slate-400">Avg Burn:</span>{' '}
              <span className="font-semibold text-amber-400">
                {weekData?.averages?.dailyCaloriesBurned ?? 0} kcal
              </span>
            </div>
            <div>
              <span className="text-slate-400">Avg Water:</span>{' '}
              <span className="font-semibold text-cyan-400">
                {weekData?.averages?.dailyWaterMl ?? 0} ml
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity List */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 shadow-xl">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-base font-bold text-white">Recent Health Entries</h2>
          <Link
            to="/logs"
            className="text-xs text-emerald-400 hover:text-emerald-300 font-medium"
          >
            View all logs →
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Foods */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Food
            </span>
            {recentLogs?.food?.map((f: any) => (
              <div
                key={f.id}
                className="p-3 bg-slate-900/60 rounded-xl border border-slate-700/40 text-xs flex justify-between items-center"
              >
                <div>
                  <div className="font-medium text-slate-200">{f.foodName}</div>
                  <div className="text-[10px] text-slate-400">
                    {f.quantity} {f.unit} • {f.mealType}
                  </div>
                </div>
                <div className="text-emerald-400 font-semibold">{f.calories} kcal</div>
              </div>
            ))}
            {(!recentLogs?.food || recentLogs.food.length === 0) && (
              <p className="text-xs text-slate-500 italic">No meals logged today</p>
            )}
          </div>

          {/* Activities */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Activities
            </span>
            {recentLogs?.activity?.map((a: any) => (
              <div
                key={a.id}
                className="p-3 bg-slate-900/60 rounded-xl border border-slate-700/40 text-xs flex justify-between items-center"
              >
                <div>
                  <div className="font-medium text-slate-200">{a.activityName}</div>
                  <div className="text-[10px] text-slate-400">
                    {a.durationMinutes} minutes
                  </div>
                </div>
                <div className="text-amber-400 font-semibold">
                  {a.caloriesBurned} kcal
                </div>
              </div>
            ))}
            {(!recentLogs?.activity || recentLogs.activity.length === 0) && (
              <p className="text-xs text-slate-500 italic">No workouts logged today</p>
            )}
          </div>

          {/* Hydration */}
          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Hydration
            </span>
            {recentLogs?.hydration?.map((h: any) => (
              <div
                key={h.id}
                className="p-3 bg-slate-900/60 rounded-xl border border-slate-700/40 text-xs flex justify-between items-center"
              >
                <div className="font-medium text-slate-200">Water Intake</div>
                <div className="text-cyan-400 font-semibold">+{h.amountMl} ml</div>
              </div>
            ))}
            {(!recentLogs?.hydration || recentLogs.hydration.length === 0) && (
              <p className="text-xs text-slate-500 italic">No water logged today</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
