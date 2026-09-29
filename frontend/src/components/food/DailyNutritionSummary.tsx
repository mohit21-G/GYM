import React from 'react';
import { Flame, PieChart, Sparkles } from 'lucide-react';

export interface DailyNutritionSummaryData {
  date: string;
  totalCalories: number;
  targetCalories: number;
  remainingCalories: number;
  percentOfTarget: number;
  macros: {
    proteinG: number;
    carbsG: number;
    fatG: number;
    fiberG: number;
  };
  totalEntries: number;
  distinctFoodsCount: number;
}

interface DailyNutritionSummaryProps {
  summary: DailyNutritionSummaryData;
  className?: string;
}

export const DailyNutritionSummary: React.FC<DailyNutritionSummaryProps> = ({
  summary,
  className = '',
}) => {
  const percent = Math.min(
    100,
    summary.targetCalories > 0
      ? Math.round((summary.totalCalories / summary.targetCalories) * 100)
      : 0,
  );

  return (
    <div
      className={`bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-emerald-500/25 rounded-2xl p-4 shadow-lg backdrop-blur-sm ${className}`}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Flame className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-200">
              Daily Nutrition Progress
            </h3>
            <p className="text-[10px] text-slate-400">
              {summary.totalEntries} {summary.totalEntries === 1 ? 'entry' : 'entries'} logged today
            </p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-xs font-bold text-emerald-400">
            {summary.totalCalories}
          </span>
          <span className="text-[11px] text-slate-400"> / {summary.targetCalories} kcal</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-3 space-y-1.5">
        <div className="flex justify-between text-[11px] text-slate-400">
          <span>{percent}% of daily goal</span>
          <span className="text-slate-300 font-medium">
            {summary.remainingCalories > 0
              ? `${summary.remainingCalories} kcal remaining`
              : 'Daily goal reached!'}
          </span>
        </div>

        <div className="w-full bg-slate-800/80 rounded-full h-2.5 overflow-hidden border border-slate-700/40">
          <div
            className="bg-gradient-to-r from-emerald-500 to-teal-400 h-2.5 rounded-full transition-all duration-700 ease-out shadow-sm shadow-emerald-500/30"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      {/* Macro Pills Breakdown */}
      <div className="mt-3.5 grid grid-cols-4 gap-1.5 text-center text-xs">
        <div className="bg-slate-800/60 rounded-xl p-2 border border-slate-700/40">
          <div className="text-[10px] text-slate-400 font-medium">Protein</div>
          <div className="text-blue-400 font-bold mt-0.5">
            {summary.macros?.proteinG ?? 0}g
          </div>
        </div>

        <div className="bg-slate-800/60 rounded-xl p-2 border border-slate-700/40">
          <div className="text-[10px] text-slate-400 font-medium">Carbs</div>
          <div className="text-amber-400 font-bold mt-0.5">
            {summary.macros?.carbsG ?? 0}g
          </div>
        </div>

        <div className="bg-slate-800/60 rounded-xl p-2 border border-slate-700/40">
          <div className="text-[10px] text-slate-400 font-medium">Fat</div>
          <div className="text-rose-400 font-bold mt-0.5">
            {summary.macros?.fatG ?? 0}g
          </div>
        </div>

        <div className="bg-slate-800/60 rounded-xl p-2 border border-slate-700/40">
          <div className="text-[10px] text-slate-400 font-medium">Fiber</div>
          <div className="text-emerald-400 font-bold mt-0.5">
            {summary.macros?.fiberG ?? 0}g
          </div>
        </div>
      </div>
    </div>
  );
};
