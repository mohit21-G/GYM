import React, { useState, useEffect } from 'react';
import { apiClient } from '../config/api';
import { useAuthStore } from '../store/authStore';
import {
  User,
  Mail,
  Shield,
  Clock,
  Save,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Scale,
  Ruler,
  Flame,
  Droplets,
  Moon,
  Globe,
} from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user } = useAuthStore();
  const [profileData, setProfileData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    timezone: 'Asia/Kolkata',
    preferredLanguage: 'en',
    age: '',
    gender: 'MALE',
    heightCm: '',
    currentWeightKg: '',
    targetWeightKg: '',
    dailyCalorieTarget: 2000,
    dailyWaterMlTarget: 2500,
    dailySleepMinutesTarget: 480,
    activityLevel: 'MODERATE',
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/users/profile');
      const data = res.data;
      setProfileData(data);
      const profile = data.profile || {};
      setFormData({
        name: data.name || '',
        timezone: data.timezone || 'Asia/Kolkata',
        preferredLanguage: data.preferredLanguage || 'en',
        age: profile.age ? String(profile.age) : '',
        gender: profile.gender || 'MALE',
        heightCm: profile.heightCm ? String(profile.heightCm) : '',
        currentWeightKg: profile.currentWeightKg ? String(profile.currentWeightKg) : '',
        targetWeightKg: profile.targetWeightKg ? String(profile.targetWeightKg) : '',
        dailyCalorieTarget: profile.dailyCalorieTarget || 2000,
        dailyWaterMlTarget: profile.dailyWaterMlTarget || 2500,
        dailySleepMinutesTarget: profile.dailySleepMinutesTarget || 480,
        activityLevel: profile.activityLevel || 'MODERATE',
      });
    } catch (err: any) {
      setErrorMsg('Failed to load profile.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const payload: any = {
        name: formData.name.trim(),
        timezone: formData.timezone,
        preferredLanguage: formData.preferredLanguage,
        gender: formData.gender,
        activityLevel: formData.activityLevel,
        dailyCalorieTarget: Number(formData.dailyCalorieTarget) || 2000,
        dailyWaterMlTarget: Number(formData.dailyWaterMlTarget) || 2500,
        dailySleepMinutesTarget: Number(formData.dailySleepMinutesTarget) || 480,
      };

      if (formData.age) payload.age = Number(formData.age);
      if (formData.heightCm) payload.heightCm = Number(formData.heightCm);
      if (formData.currentWeightKg) payload.currentWeightKg = Number(formData.currentWeightKg);
      if (formData.targetWeightKg) payload.targetWeightKg = Number(formData.targetWeightKg);

      await apiClient.patch('/users/profile', payload);
      setSuccessMsg('Profile and fitness goals updated successfully!');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Failed to update profile.';
      setErrorMsg(Array.isArray(msg) ? msg.join(', ') : msg);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="flex items-center space-x-2 text-slate-400 text-sm">
          <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
          <span>Loading profile...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="border-b border-slate-800 pb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Account & Health Profile
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Customize your personal measurements, daily nutrition targets, and assistant preferences
        </p>
      </div>

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center space-x-3">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Account Info Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 shadow-xl space-y-4">
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <User className="w-5 h-5 text-emerald-400" />
            <span>Account Details</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Full Name
              </label>
              <input
                type="text"
                name="name"
                required
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Email Address (read-only)
              </label>
              <input
                type="email"
                disabled
                value={profileData?.email || user?.email || ''}
                className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-800 rounded-xl text-slate-400 text-sm cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        {/* Biometrics Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 shadow-xl space-y-4">
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <Scale className="w-5 h-5 text-teal-400" />
            <span>Body & Measurements</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Age
              </label>
              <input
                type="number"
                name="age"
                min="10"
                max="120"
                value={formData.age}
                onChange={handleChange}
                placeholder="25"
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Gender
              </label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Height (cm)
              </label>
              <input
                type="number"
                step="0.5"
                name="heightCm"
                value={formData.heightCm}
                onChange={handleChange}
                placeholder="175"
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Current Weight (kg)
              </label>
              <input
                type="number"
                step="0.1"
                name="currentWeightKg"
                value={formData.currentWeightKg}
                onChange={handleChange}
                placeholder="72.0"
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Target Weight (kg)
              </label>
              <input
                type="number"
                step="0.1"
                name="targetWeightKg"
                value={formData.targetWeightKg}
                onChange={handleChange}
                placeholder="68.0"
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div className="sm:col-span-2 lg:col-span-3">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Activity Level
              </label>
              <select
                name="activityLevel"
                value={formData.activityLevel}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="SEDENTARY">Sedentary (Little or no exercise)</option>
                <option value="LIGHT">Light (Exercise 1-3 days/week)</option>
                <option value="MODERATE">Moderate (Exercise 3-5 days/week)</option>
                <option value="VERY_ACTIVE">Very Active (Hard exercise 6-7 days/week)</option>
                <option value="EXTRA_ACTIVE">Extra Active (Very hard exercise or physical job)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Daily Goals Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 shadow-xl space-y-4">
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <Flame className="w-5 h-5 text-amber-400" />
            <span>Daily Health Targets</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Daily Calorie Target (kcal)
              </label>
              <input
                type="number"
                name="dailyCalorieTarget"
                value={formData.dailyCalorieTarget}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Daily Water Goal (ml)
              </label>
              <input
                type="number"
                name="dailyWaterMlTarget"
                value={formData.dailyWaterMlTarget}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Daily Sleep Goal (minutes)
              </label>
              <input
                type="number"
                name="dailySleepMinutesTarget"
                value={formData.dailySleepMinutesTarget}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">
                {Math.round((Number(formData.dailySleepMinutesTarget) / 60) * 10) / 10} hours
              </span>
            </div>
          </div>
        </div>

        {/* Preferences Card */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-6 shadow-xl space-y-4">
          <h2 className="text-base font-bold text-white flex items-center space-x-2">
            <Globe className="w-5 h-5 text-blue-400" />
            <span>Assistant & Localization</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Preferred Assistant Language
              </label>
              <select
                name="preferredLanguage"
                value={formData.preferredLanguage}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="en">English</option>
                <option value="hi">Hindi (हिंदी)</option>
                <option value="gu">Gujarati (ગુજરાતી)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Timezone
              </label>
              <select
                name="timezone"
                value={formData.timezone}
                onChange={handleChange}
                className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="Asia/Kolkata">IST (Asia/Kolkata)</option>
                <option value="UTC">UTC</option>
                <option value="America/New_York">EST (New York)</option>
                <option value="Europe/London">GMT (London)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-medium rounded-xl shadow-lg shadow-emerald-500/25 transition-all disabled:opacity-50 cursor-pointer"
          >
            {saving ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Saving changes...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save Profile & Targets</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
