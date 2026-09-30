import React from 'react';
import { Clock, Pencil, Trash2 } from 'lucide-react';

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
  hasExplicitTime?: boolean;
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
  onEdit?: (entry: FoodLogEntryData) => void;
  onDelete?: (entry: FoodLogEntryData) => void;
}

export const FoodLogEntry: React.FC<FoodLogEntryProps> = ({
  entry,
  onEdit,
  onDelete,
}) => {
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

  const hasExplicitTime = Boolean(
    entry.hasExplicitTime !== undefined
      ? entry.hasExplicitTime
      : entry.timeFormatted && entry.timeFormatted.trim().length > 0
  );
  const displayMealType = entry.mealType || '—';

  return (
    <div className="py-2.5 px-3 rounded-lg bg-slate-900/40 hover:bg-slate-800/40 transition-colors border border-slate-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs w-full min-w-0">
      <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
        {hasExplicitTime && (
          <div className="flex items-center space-x-1 text-slate-400 font-medium shrink-0">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{entry.timeFormatted}</span>
          </div>
        )}

        <span
          className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold border ${getMealBadgeStyle(
            displayMealType,
          )}`}
        >
          {displayMealType}
        </span>

        <span className="text-slate-200 font-medium">
          {formattedQuantity}
        </span>

        {hasExplicitTime && onEdit && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onEdit(entry);
            }}
            className="flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 transition-colors border border-emerald-500/20 cursor-pointer ml-1"
            title="Edit explicit time"
          >
            <Clock className="w-2.5 h-2.5 text-emerald-400" />
            <span>Edit Time</span>
          </button>
        )}
      </div>

      <div className="flex items-center justify-between sm:justify-end space-x-3 shrink-0">
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

        {(onEdit || onDelete) && (
          <div className="flex items-center space-x-1 pl-1 border-l border-slate-800">
            {onEdit && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(entry);
                }}
                className="p-1 rounded text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition-colors"
                title="Edit food log"
              >
                <Pencil className="w-3.5 h-3.5" />
              </button>
            )}
            {onDelete && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(entry);
                }}
                className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                title="Delete food log"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

