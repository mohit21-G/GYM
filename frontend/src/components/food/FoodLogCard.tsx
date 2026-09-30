import React from 'react';
import {
  ChevronDown,
  Wheat,
  Milk,
  Apple,
  Egg,
  Carrot,
  Cookie,
  Droplets,
  Utensils,
  History,
  Pencil,
  Trash2,
} from 'lucide-react';
import { FoodLogEntry, FoodLogEntryData } from './FoodLogEntry';

export interface GroupedFoodCardData {
  foodKey: string;
  foodMasterId?: string | null;
  foodName: string;
  categoryName?: string;
  icon?: string;
  imageUrl?: string;
  totalQuantity: number;
  unit: string;
  totalCalories: number;
  entryCount: number;
  macros?: {
    proteinG: number;
    carbsG: number;
    fatG: number;
    fiberG: number;
  };
  entries: FoodLogEntryData[];
}

interface FoodLogCardProps {
  card: GroupedFoodCardData;
  isExpanded?: boolean;
  onToggle?: () => void;
  onEditEntry?: (entry: FoodLogEntryData) => void;
  onDeleteEntry?: (entry: FoodLogEntryData) => void;
}

export const FoodLogCard: React.FC<FoodLogCardProps> = ({
  card,
  isExpanded = false,
  onToggle,
  onEditEntry,
  onDeleteEntry,
}) => {
  // Select icon based on category or food keyword
  const renderFoodIcon = () => {
    if (card.imageUrl) {
      return (
        <img
          src={card.imageUrl}
          alt={card.foodName}
          className="w-10 h-10 rounded-xl object-cover border border-slate-700/60 shadow-inner"
          onError={(e) => {
            (e.target as HTMLElement).style.display = 'none';
          }}
        />
      );
    }

    const iconType = card.icon?.toLowerCase() || '';
    const nameLower = card.foodName.toLowerCase();

    if (iconType === 'wheat' || nameLower.includes('roti') || nameLower.includes('rotli') || nameLower.includes('thepla') || nameLower.includes('bhakhri') || nameLower.includes('bread') || nameLower.includes('paratha')) {
      return (
        <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-sm shrink-0">
          <Wheat className="w-5 h-5" />
        </div>
      );
    }
    if (iconType === 'milk' || nameLower.includes('milk') || nameLower.includes('doodh') || nameLower.includes('curd') || nameLower.includes('dahi') || nameLower.includes('paneer') || nameLower.includes('yogurt')) {
      return (
        <div className="w-10 h-10 rounded-xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-sm shrink-0">
          <Milk className="w-5 h-5" />
        </div>
      );
    }
    if (iconType === 'apple' || nameLower.includes('banana') || nameLower.includes('kela') || nameLower.includes('apple') || nameLower.includes('fruit')) {
      return (
        <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-sm shrink-0">
          <Apple className="w-5 h-5" />
        </div>
      );
    }
    if (iconType === 'egg' || nameLower.includes('egg') || nameLower.includes('chicken') || nameLower.includes('meat') || nameLower.includes('protein')) {
      return (
        <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center text-rose-400 shadow-sm shrink-0">
          <Egg className="w-5 h-5" />
        </div>
      );
    }
    if (iconType === 'carrot' || nameLower.includes('sabzi') || nameLower.includes('salad') || nameLower.includes('vegetable')) {
      return (
        <div className="w-10 h-10 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center text-teal-400 shadow-sm shrink-0">
          <Carrot className="w-5 h-5" />
        </div>
      );
    }
    if (iconType === 'cookie' || nameLower.includes('khakhra') || nameLower.includes('snack') || nameLower.includes('nuts')) {
      return (
        <div className="w-10 h-10 rounded-xl bg-orange-500/15 border border-orange-500/30 flex items-center justify-center text-orange-400 shadow-sm shrink-0">
          <Cookie className="w-5 h-5" />
        </div>
      );
    }
    if (iconType === 'cup-soda' || nameLower.includes('water') || nameLower.includes('juice') || nameLower.includes('tea')) {
      return (
        <div className="w-10 h-10 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-sm shrink-0">
          <Droplets className="w-5 h-5" />
        </div>
      );
    }

    return (
      <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-sm shrink-0">
        <Utensils className="w-5 h-5" />
      </div>
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onToggle?.();
    }
  };

  const entryLabel = card.entryCount === 1 ? '1 entry' : `${card.entryCount} entries`;
  const formattedSummary = `${card.totalQuantity} ${card.unit} · ${card.totalCalories} kcal · ${entryLabel}`;

  return (
    <div
      className={`group transition-all duration-200 bg-slate-900/90 rounded-2xl border ${
        isExpanded
          ? 'border-emerald-500/40 shadow-lg shadow-emerald-950/20'
          : 'border-slate-800 hover:border-slate-700/80 shadow-md'
      } backdrop-blur-sm overflow-hidden w-full max-w-full box-border`}
    >
      {/* Clickable Header (Summary) */}
      <div
        role="button"
        tabIndex={0}
        onClick={onToggle}
        onKeyDown={handleKeyDown}
        aria-expanded={isExpanded}
        aria-controls={`entries-${card.foodKey}`}
        className="w-full text-left p-3.5 sm:p-4 flex items-center justify-between gap-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50 rounded-2xl cursor-pointer select-none transition-colors hover:bg-slate-800/40 min-w-0"
      >
        <div className="flex items-center space-x-3 min-w-0 flex-1">
          {renderFoodIcon()}

          <div className="min-w-0 flex-1">
            <h4 className="text-sm font-semibold text-slate-100 truncate group-hover:text-emerald-300 transition-colors">
              {card.foodName}
            </h4>
            <p className="text-xs text-slate-400 mt-0.5 truncate font-medium">
              {formattedSummary}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <div className="text-right hidden sm:block">
            <div className="text-xs font-bold text-emerald-400">
              {card.totalCalories} kcal
            </div>
            <div className="text-[11px] text-slate-500">
              {card.totalQuantity} {card.unit}
            </div>
          </div>

          {card.entryCount === 1 && card.entries && card.entries.length === 1 && (onEditEntry || onDeleteEntry) && (
            <div
              className="flex items-center space-x-1 pl-1 border-l border-slate-800"
              onClick={(e) => e.stopPropagation()}
            >
              {onEditEntry && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEditEntry(card.entries[0]);
                  }}
                  className="p-1 rounded text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition-colors"
                  title="Edit food log"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
              )}
              {onDeleteEntry && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteEntry(card.entries[0]);
                  }}
                  className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                  title="Delete food log"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          )}

          <div
            className={`w-7 h-7 rounded-lg flex items-center justify-center transition-transform duration-300 text-slate-400 group-hover:text-slate-200 ${
              isExpanded
                ? 'rotate-180 bg-emerald-500/10 text-emerald-400'
                : 'bg-slate-800/60'
            }`}
          >
            <ChevronDown className="w-4 h-4" />
          </div>
        </div>
      </div>

      {/* Expanded State (Individual History & Nutrition Totals) */}
      {isExpanded && (
        <div
          id={`entries-${card.foodKey}`}
          className="border-t border-slate-800/80 px-3.5 sm:px-4 py-3 bg-slate-950/40 animate-fadeIn w-full box-border"
        >
          {/* History Header */}
          <div className="flex items-center justify-between mb-2.5 text-xs text-slate-400 font-medium">
            <div className="flex items-center space-x-1.5 text-slate-300">
              <History className="w-3.5 h-3.5 text-emerald-400" />
              <span>Today's Log Entries ({card.entryCount})</span>
            </div>
            <span className="text-[11px] text-slate-500">
              Click header to collapse
            </span>
          </div>

          {/* List of Entries */}
          <div className="space-y-1.5 mb-3 w-full">
            {card.entries.map((entry, index) => (
              <FoodLogEntry
                key={entry.id || `${card.foodKey}-entry-${index}`}
                entry={entry}
                index={index}
                onEdit={onEditEntry}
                onDelete={onDeleteEntry}
              />
            ))}
          </div>

          {/* Expanded Summary Totals Footer */}
          <div className="pt-2.5 border-t border-slate-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <div className="text-slate-300 font-medium">
              Total:{' '}
              <span className="text-slate-100 font-semibold">
                {card.totalQuantity} {card.unit}
              </span>{' '}
              ·{' '}
              <span className="text-emerald-400 font-bold">
                {card.totalCalories} kcal
              </span>
            </div>

            {card.macros && (
              <div className="flex items-center space-x-2 text-[11px]">
                <span className="bg-slate-800/70 border border-slate-700/50 px-2 py-0.5 rounded text-slate-300">
                  P: <span className="text-blue-400 font-semibold">{card.macros.proteinG ?? (card.macros as any)?.protein ?? 0}g</span>
                </span>
                <span className="bg-slate-800/70 border border-slate-700/50 px-2 py-0.5 rounded text-slate-300">
                  C: <span className="text-amber-400 font-semibold">{card.macros.carbsG ?? (card.macros as any)?.carbs ?? 0}g</span>
                </span>
                <span className="bg-slate-800/70 border border-slate-700/50 px-2 py-0.5 rounded text-slate-300">
                  F: <span className="text-rose-400 font-semibold">{card.macros.fatG ?? (card.macros as any)?.fat ?? 0}g</span>
                </span>
                {(card.macros.fiberG > 0 || (card.macros as any)?.fiber > 0) && (
                  <span className="bg-slate-800/70 border border-slate-700/50 px-2 py-0.5 rounded text-slate-300">
                    Fib: <span className="text-emerald-400 font-semibold">{card.macros.fiberG ?? (card.macros as any)?.fiber ?? 0}g</span>
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
