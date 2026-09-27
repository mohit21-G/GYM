import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, Utensils, Flame, Droplets, Moon, Scale, Sparkles, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../config/api';

export const HomePage: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/health')
      .then((res) => setHealthStatus(res.data?.data || res.data))
      .catch((err) => console.log('Backend health status fetch error:', err.message));
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-between">
      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            Next-Gen Conversational Health Companion
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight">
            Log Your Fitness in <span className="bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">Any Language</span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-slate-400 leading-relaxed">
            Speak or type naturally in English, Hindi, Gujarati, Hinglish, or Gujlish.
            Our intelligent multi-provider AI interprets your meals, workouts, water, sleep, and weight instantly.
          </p>

          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <Link
              to="/register"
              className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold shadow-xl shadow-emerald-500/25 transition-all transform hover:-translate-y-0.5"
            >
              Start Free Today
            </Link>
            <Link
              to="/login"
              className="px-8 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold border border-slate-700 transition-all"
            >
              Customer Login
            </Link>
          </div>

          {/* Multilingual Examples Carousel / Pills */}
          <div className="mt-12 p-4 rounded-2xl bg-slate-800/60 border border-slate-700/60 backdrop-blur">
            <p className="text-xs uppercase font-semibold text-slate-400 mb-3 tracking-wider">
              Natural Language Examples Understood By AI
            </p>
            <div className="flex flex-wrap justify-center gap-2 text-xs">
              <span className="px-3 py-1.5 rounded-lg bg-slate-900 text-emerald-300 border border-slate-700">
                "Aaje 30 minute walk kari"
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-slate-900 text-teal-300 border border-slate-700">
                "3 khapli rotli and dal khai"
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-slate-900 text-cyan-300 border border-slate-700">
                "Aaje 500ml pani pidhu"
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-slate-900 text-amber-300 border border-slate-700">
                "Weight is 74.5 kg today"
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-slate-900 text-indigo-300 border border-slate-700">
                "Slept 7.5 hours from 11pm"
              </span>
            </div>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 rounded-2xl bg-slate-800/40 border border-slate-800 hover:border-emerald-500/30 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Utensils className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Automated Food Logging</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Calculates authoritative calories, proteins, carbs, and fats mapped against our nutritional master catalog.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-800/40 border border-slate-800 hover:border-teal-500/30 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <Flame className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">MET Calorie Burn</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Standardized MET-based calculations for gym workouts, cardio, walking, yoga, and high-intensity training.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-800/40 border border-slate-800 hover:border-cyan-500/30 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <MessageSquare className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Multi-Provider AI Core</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Seamlessly powered by Cloudflare Workers AI GLM-4.7-Flash, OpenAI, Gemini, or Mistral with zero downtime.
            </p>
          </div>
        </div>

        {/* Backend Status Bar */}
        <div className="mt-16 max-w-xl mx-auto p-4 rounded-xl bg-slate-800/30 border border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${healthStatus?.status === 'ok' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
            <span>Backend Status:</span>
            <span className="font-semibold text-slate-200">
              {healthStatus?.status === 'ok' ? 'Operational' : 'Connecting...'}
            </span>
          </div>
          {healthStatus?.services && (
            <div className="flex items-center gap-2">
              <span>AI Provider:</span>
              <span className="font-mono text-emerald-400 font-medium">
                {healthStatus.services.aiProvider}
              </span>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        <p>&copy; {new Date().getFullYear()} Google Fitbit AI Chatbot. All rights reserved.</p>
      </footer>
    </div>
  );
};
