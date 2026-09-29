import React from 'react';
import { Clock } from 'lucide-react';

export interface FoodLogEntryData {
  id: string;
  foodMasterId?: string | null;
  foodName: string;
  quantity: number;
  unit: string;
  calories: number;
  mealType: string;
  loggedAt: string;
  timeFormatted: string;
  macros?: {
    proteinG: number;
    carbsG: number;
    fatG: number;
    fiberG: number;
  };
}

interface FoodLogEntryProps {
  entry: FoodLogEntryData;
  index?: number;
}

export const FoodLogEntry: React.FC<FoodLogEntryProps> = ({ entry }) => {
  const getMealBadgeStyle = (mealType: string) => {
    switch (mealType?.toUpperCase()) {
      case 'BREAKFAST':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'LUNCH':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'SNACK':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/20';
      case 'DINNER':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      default:
        return 'bg-slate-700/50 text-slate-300 border-slate-600/30';
    }
  };

  const formattedQuantity =
    entry.quantity === 1
      ? `1 ${entry.unit}`
      : `${entry.quantity} ${entry.unit}`;

  return (
    <div className="py-2.5 px-3 rounded-lg bg-slate-900/40 hover:bg-slate-800/40 transition-colors border border-slate-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
      <div className="flex items-center space-x-2.5">
        <div className="flex items-center space-x-1 text-slate-400 font-medium shrink-0">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{entry.timeFormatted || 'Today'}</span>
        </div>

        <span
          className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold border ${getMealBadgeStyle(
            entry.mealType,
          )}`}
        >
          {entry.mealType || 'SNACK'}
        </span>

        <span className="text-slate-200 font-medium">
          {formattedQuantity}
        </span>
      </div>

      <div className="flex items-center justify-between sm:justify-end space-x-3">
        {entry.macros && (
          <div className="flex items-center space-x-2 text-[11px] text-slate-400">
            <span title="Protein">
              P: <span className="text-blue-400 font-semibold">{entry.macros.proteinG}g</span>
            </span>
            <span className="text-slate-600">·</span>
            <span title="Carbs">
              C: <span className="text-amber-400 font-semibold">{entry.macros.carbsG}g</span>
            </span>
            <span className="text-slate-600">·</span>
            <span title="Fat">
              F: <span className="text-rose-400 font-semibold">{entry.macros.fatG}g</span>
            </span>
          </div>
        )}

        <div className="text-emerald-400 font-bold text-xs bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 shrink-0">
          {Math.round(entry.calories)} kcal
        </div>
      </div>
    </div>
  );
};
