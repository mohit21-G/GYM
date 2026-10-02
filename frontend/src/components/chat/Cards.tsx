import React from 'react';
import {
  Utensils,
  Flame,
  Scale,
  Moon,
  Droplets,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  Minus,
  Sparkles,
  HelpCircle,
  Pencil,
  Trash2,
} from 'lucide-react';
import { FoodLogList } from '../food/FoodLogList';
import { FoodLogCard } from '../food/FoodLogCard';
import { FoodLogEntryData } from '../food/FoodLogEntry';
import { DailyHydrationSummary, HydrationEntryItem } from '../hydration/DailyHydrationSummary';
import { ActivityEntryData } from '../activity/EditActivityLogModal';

interface CardProps {
  cardType?: string;
  data: any;
  onSelectOption?: (text: string) => void;
  onEditEntry?: (entry: FoodLogEntryData) => void;
  onDeleteEntry?: (entry: FoodLogEntryData) => void;
  onEditHydrationEntry?: (entry: HydrationEntryItem) => void;
  onDeleteHydrationEntry?: (entry: HydrationEntryItem) => void;
  onEditActivityEntry?: (entry: ActivityEntryData) => void;
  onDeleteActivityEntry?: (entry: ActivityEntryData) => void;
}

export const StructuredCard: React.FC<CardProps> = ({
  cardType,
  data,
  onSelectOption,
  onEditEntry,
  onDeleteEntry,
  onEditHydrationEntry,
  onDeleteHydrationEntry,
  onEditActivityEntry,
  onDeleteActivityEntry,
}) => {
  if (!data) return null;

  // 1. Grouped Food Cards (Fitbit-style with expandable history)
  if (data.groupedFoodCards && Array.isArray(data.groupedFoodCards) && data.groupedFoodCards.length > 0) {
    // If there are other non-food cards (e.g. from multi-log), extract them
    const otherCards = Array.isArray(data.cards)
      ? data.cards.filter((c: any) => c.type !== 'FOOD' && c.type !== 'FOOD_GROUP')
      : [];

    return (
      <div className="mt-3 space-y-3 w-full">
        <FoodLogList
          cards={data.groupedFoodCards}
          dailySummary={data.dailyNutritionSummary}
          onEditEntry={onEditEntry}
          onDeleteEntry={onDeleteEntry}
        />
        {otherCards.length > 0 && (
          <div className="space-y-2 w-full">
            {otherCards.map((c: any, i: number) => (
              <StructuredCard
                key={i}
                cardType="LOG_RESULT"
                data={c}
                onSelectOption={onSelectOption}
                onEditEntry={onEditEntry}
                onDeleteEntry={onDeleteEntry}
                onEditHydrationEntry={onEditHydrationEntry}
                onDeleteHydrationEntry={onDeleteHydrationEntry}
                onEditActivityEntry={onEditActivityEntry}
                onDeleteActivityEntry={onDeleteActivityEntry}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // 2. Direct array of GroupedFoodCards with cardType === 'FOOD_LOG_CARDS'
  if (cardType === 'FOOD_LOG_CARDS' && Array.isArray(data)) {
    return (
      <div className="mt-3 w-full">
        <FoodLogList
          cards={data}
          onEditEntry={onEditEntry}
          onDeleteEntry={onDeleteEntry}
        />
      </div>
    );
  }

  // 3. Single Grouped Food Card
  if (data.foodKey && data.entries && data.totalQuantity !== undefined) {
    return (
      <div className="mt-3 w-full">
        <FoodLogCard
          card={data}
          onEditEntry={onEditEntry}
          onDeleteEntry={onDeleteEntry}
        />
      </div>
    );
  }

  // 4. Handle generic array of cards
  if (Array.isArray(data)) {
    // Check if array elements are grouped food cards
    const isGroupedList = data.length > 0 && data[0]?.foodKey && data[0]?.entries;
    if (isGroupedList) {
      return (
        <div className="mt-3">
          <FoodLogList cards={data} />
        </div>
      );
    }

    return (
      <div className="mt-3 space-y-2.5">
        {data.map((item, idx) => (
          <StructuredCard
            key={idx}
            cardType={item.type ? 'LOG_RESULT' : cardType}
            data={item}
            onSelectOption={onSelectOption}
            onEditEntry={onEditEntry}
            onDeleteEntry={onDeleteEntry}
            onEditHydrationEntry={onEditHydrationEntry}
            onDeleteHydrationEntry={onDeleteHydrationEntry}
            onEditActivityEntry={onEditActivityEntry}
            onDeleteActivityEntry={onDeleteActivityEntry}
          />
        ))}
      </div>
    );
  }

  // Food Card (Legacy or Single Food Object)
  if (cardType === 'LOG_RESULT' && data.type === 'FOOD') {
    const food = data.food || data;
    const calculatedNutrition = data.calculatedNutrition || data.nutrition;
    const foodName = food?.name || food?.foodName || data?.foodName || 'Food Item';
    const mealType = food?.mealType || data?.mealType || 'SNACK';
    const quantity = food?.quantity ?? data?.quantity ?? 1;
    const unit = food?.unit || data?.unit || 'serving';
    const calories = calculatedNutrition?.calories ?? food?.calories ?? data?.calories ?? 0;
    return (
      <div className="mt-3 bg-slate-900/90 border border-emerald-500/30 rounded-xl p-4 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
          <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-sm">
            <Utensils className="w-4 h-4" />
            <span>Food Logged: {foodName}</span>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium uppercase">
            {mealType}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs mb-3">
          <div>
            <span className="text-slate-400">Portion:</span>{' '}
            <span className="text-slate-200 font-medium">
              {quantity} {unit}
            </span>
          </div>
          <div>
            <span className="text-slate-400">Calories:</span>{' '}
            <span className="text-emerald-400 font-bold text-sm">
              {calories} kcal
            </span>
          </div>
        </div>

        {/* Macro Pill breakdown */}
        <div className="grid grid-cols-4 gap-1.5 text-center text-[11px]">
          <div className="bg-slate-800/80 rounded-lg p-1.5 border border-slate-700/50">
            <div className="text-slate-400">Protein</div>
            <div className="text-blue-400 font-semibold mt-0.5">
              {calculatedNutrition?.proteinG ?? food?.proteinG ?? 0}g
            </div>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-1.5 border border-slate-700/50">
            <div className="text-slate-400">Carbs</div>
            <div className="text-amber-400 font-semibold mt-0.5">
              {calculatedNutrition?.carbsG ?? food?.carbsG ?? 0}g
            </div>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-1.5 border border-slate-700/50">
            <div className="text-slate-400">Fat</div>
            <div className="text-rose-400 font-semibold mt-0.5">
              {calculatedNutrition?.fatG ?? food?.fatG ?? 0}g
            </div>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-1.5 border border-slate-700/50">
            <div className="text-slate-400">Fiber</div>
            <div className="text-emerald-400 font-semibold mt-0.5">
              {calculatedNutrition?.fiberG ?? food?.fiberG ?? 0}g
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Activity Card
  if (cardType === 'LOG_RESULT' && data.type === 'ACTIVITY') {
    const activity = data.activity || data;
    const calculation = data.calculation;
    const activityName = activity?.name || activity?.activityName || data?.title || data?.name || data?.activityName || 'Activity';
    const met = calculation?.metValue ?? activity?.metValue ?? data?.metValue ?? 3.5;
    const duration = calculation?.durationMinutes ?? activity?.durationMinutes ?? data?.durationMinutes ?? 0;
    const burned = calculation?.caloriesBurned ?? activity?.caloriesBurned ?? data?.caloriesBurned ?? (data.metric ? data.metric : 0);
    const burnedDisplay = typeof burned === 'string' ? burned : `${burned} kcal`;
    const canEditDelete = Boolean(data.id) && (onEditActivityEntry || onDeleteActivityEntry);
    return (
      <div className="mt-3 bg-slate-900/90 border border-amber-500/30 rounded-xl p-4 shadow-lg backdrop-blur-sm w-full">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
          <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm">
            <Flame className="w-4 h-4" />
            <span>Activity Logged: {activityName}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
              {data.subtitle || `MET ${met}`}
            </span>
            {canEditDelete && (
              <div className="flex items-center space-x-1 pl-1.5 border-l border-slate-800">
                {onEditActivityEntry && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditActivityEntry(data as ActivityEntryData);
                    }}
                    className="p-1 rounded text-slate-400 hover:text-amber-400 hover:bg-slate-800 transition-colors"
                    title="Edit activity log"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                )}
                {onDeleteActivityEntry && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteActivityEntry(data as ActivityEntryData);
                    }}
                    className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                    title="Delete activity log"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-slate-400">Duration:</span>{' '}
            <span className="text-slate-200 font-medium">
              {duration ? `${duration} mins` : (data.subtitle || 'Completed')}
            </span>
          </div>
          <div>
            <span className="text-slate-400">Burned:</span>{' '}
            <span className="text-amber-400 font-bold text-sm">
              {burnedDisplay}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Hydration Card (Daily Hydration Progress Card matching Daily Nutrition style)
  if (cardType === 'LOG_RESULT' && (data.type === 'HYDRATION' || data.totalMl !== undefined || data.dailySummary?.totalMl !== undefined)) {
    return (
      <div className="mt-3 w-full">
        <DailyHydrationSummary
          data={data}
          onEditEntry={onEditHydrationEntry}
          onDeleteEntry={onDeleteHydrationEntry}
        />
      </div>
    );
  }

  // Sleep Card
  if (cardType === 'LOG_RESULT' && data.type === 'SLEEP') {
    const log = data.log || data;
    const analysis = data.analysis;
    const quality = analysis?.quality || log?.quality || data?.quality || 'GOOD';
    const durationMinutes = log?.durationMinutes ?? data?.durationMinutes ?? 0;
    const hours = analysis?.hours ?? Math.floor(durationMinutes / 60);
    const mins = analysis?.remainingMinutes ?? (durationMinutes % 60);
    return (
      <div className="mt-3 bg-slate-900/90 border border-indigo-500/30 rounded-xl p-4 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
          <div className="flex items-center space-x-2 text-indigo-400 font-semibold text-sm">
            <Moon className="w-4 h-4" />
            <span>Sleep Recorded</span>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-medium">
            {quality}
          </span>
        </div>

        <div className="text-xs text-slate-300 flex justify-between items-center mt-2">
          <span>Duration:</span>
          <span className="text-sm font-bold text-indigo-300">
            {hours}h {mins}m
          </span>
        </div>
      </div>
    );
  }

  // Weight Card
  if (cardType === 'LOG_RESULT' && data.type === 'WEIGHT') {
    const log = data.log || data;
    const trend = data.trend;
    const weightKg = log?.weightKg ?? data?.weightKg ?? data?.weight ?? 0;
    return (
      <div className="mt-3 bg-slate-900/90 border border-emerald-500/30 rounded-xl p-4 shadow-lg backdrop-blur-sm">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
          <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-sm">
            <Scale className="w-4 h-4" />
            <span>Weight Logged</span>
          </div>
          <div className="flex items-center space-x-1 text-xs">
            {trend?.direction === 'DOWN' && <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />}
            {trend?.direction === 'UP' && <TrendingUp className="w-3.5 h-3.5 text-rose-400" />}
            {(!trend || trend?.direction === 'STABLE') && <Minus className="w-3.5 h-3.5 text-slate-400" />}
            <span className="font-medium text-slate-200">{trend?.deltaKg ? `${trend.deltaKg} kg` : 'Recorded'}</span>
          </div>
        </div>

        <div className="text-xs text-slate-300 flex justify-between items-center mt-2">
          <span>Current Weight:</span>
          <span className="text-sm font-bold text-emerald-400">{weightKg} kg</span>
        </div>
      </div>
    );
  }

  // Summary Card (Today / Weekly)
  if (cardType === 'SUMMARY') {
    return (
      <div className="mt-3 bg-slate-900/90 border border-slate-700 rounded-xl p-4 shadow-lg">
        <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-sm border-b border-slate-800 pb-2 mb-3">
          <Sparkles className="w-4 h-4" />
          <span>Health & Fitness Summary</span>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center text-xs mb-3">
          <div className="bg-slate-800/80 rounded-lg p-2 border border-slate-700/50">
            <div className="text-slate-400 text-[10px]">Calories In</div>
            <div className="text-emerald-400 font-bold text-sm mt-0.5">
              {data.caloriesConsumed ?? data.calories?.consumed ?? 0}
            </div>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-2 border border-slate-700/50">
            <div className="text-slate-400 text-[10px]">Calories Out</div>
            <div className="text-amber-400 font-bold text-sm mt-0.5">
              {data.caloriesBurned ?? data.calories?.burned ?? 0}
            </div>
          </div>
          <div className="bg-slate-800/80 rounded-lg p-2 border border-slate-700/50">
            <div className="text-slate-400 text-[10px]">Net</div>
            <div className="text-blue-400 font-bold text-sm mt-0.5">
              {(data.caloriesConsumed ?? data.calories?.consumed ?? 0) -
                (data.caloriesBurned ?? data.calories?.burned ?? 0)}
            </div>
          </div>
        </div>

        {/* Macros if present */}
        {data.macros && (
          <div className="grid grid-cols-4 gap-1.5 text-center text-[11px] mb-2">
            <div className="bg-slate-800/50 rounded p-1 text-slate-300">
              P: <span className="text-blue-400 font-semibold">{data.macros.proteinG}g</span>
            </div>
            <div className="bg-slate-800/50 rounded p-1 text-slate-300">
              C: <span className="text-amber-400 font-semibold">{data.macros.carbsG}g</span>
            </div>
            <div className="bg-slate-800/50 rounded p-1 text-slate-300">
              F: <span className="text-rose-400 font-semibold">{data.macros.fatG}g</span>
            </div>
            <div className="bg-slate-800/50 rounded p-1 text-slate-300">
              Fib: <span className="text-emerald-400 font-semibold">{data.macros.fiberG}g</span>
            </div>
          </div>
        )}

        {/* Hydration progress if present */}
        {data.hydration && (
          <div className="mt-3 pt-3 border-t border-slate-800/80">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="text-cyan-400 font-semibold flex items-center space-x-1">
                <Droplets className="w-3.5 h-3.5" />
                <span>Water Intake</span>
              </span>
              <span className="text-slate-300 font-medium">
                {data.hydration.amountMl ?? data.hydration.consumedMl ?? 0} / {data.hydration.targetMl ?? 2500} ml ({data.hydration.percentTarget ?? data.hydration.percent ?? 0}%)
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-cyan-400 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, data.hydration.percentTarget ?? data.hydration.percent ?? 0)}%` }}
              />
            </div>
          </div>
        )}
      </div>
    );
  }

  // Clarification Pills
  if (cardType === 'CLARIFICATION' && data.options && data.options.length > 0) {
    return (
      <div className="mt-3">
        <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-2">
          <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
          <span>Quick choices:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {data.options.map((opt: string, i: number) => (
            <button
              key={i}
              onClick={() => onSelectOption && onSelectOption(opt)}
              className="text-xs bg-slate-800 hover:bg-emerald-500/20 text-slate-200 hover:text-emerald-300 border border-slate-700 hover:border-emerald-500/40 px-3 py-1.5 rounded-lg transition-all cursor-pointer"
            >
              {opt}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return null;
};
