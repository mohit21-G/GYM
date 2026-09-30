import React, { useState } from 'react';
import { Utensils } from 'lucide-react';
import { FoodLogCard, GroupedFoodCardData } from './FoodLogCard';
import { FoodLogEntryData } from './FoodLogEntry';
import { DailyNutritionSummary, DailyNutritionSummaryData } from './DailyNutritionSummary';

interface FoodLogListProps {
  cards: GroupedFoodCardData[];
  dailySummary?: DailyNutritionSummaryData;
  showDailySummary?: boolean;
  className?: string;
  emptyMessage?: string;
  onEditEntry?: (entry: FoodLogEntryData) => void;
  onDeleteEntry?: (entry: FoodLogEntryData) => void;
}

export const FoodLogList: React.FC<FoodLogListProps> = ({
  cards,
  dailySummary,
  showDailySummary = true,
  className = '',
  emptyMessage = 'No food logged for this date.',
  onEditEntry,
  onDeleteEntry,
}) => {
  // Independent expand/collapse state keyed by card.foodKey
  // By default (initial state), cards remain collapsed
  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>({});

  const handleToggleCard = (foodKey: string) => {
    setExpandedKeys((prev) => ({
      ...prev,
      [foodKey]: !prev[foodKey],
    }));
  };

  if (!cards || cards.length === 0) {
    return (
      <div className={`p-4 bg-slate-900/60 rounded-2xl border border-slate-800 text-center ${className}`}>
        <Utensils className="w-8 h-8 text-slate-500 mx-auto mb-2" />
        <p className="text-xs text-slate-400">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`space-y-3 w-full ${className}`}>
      {/* List of distinct food cards */}
      <div className="space-y-2.5 w-full">
        {cards.map((card) => (
          <FoodLogCard
            key={card.foodKey}
            card={card}
            isExpanded={!!expandedKeys[card.foodKey]}
            onToggle={() => handleToggleCard(card.foodKey)}
            onEditEntry={onEditEntry}
            onDeleteEntry={onDeleteEntry}
          />
        ))}
      </div>

      {/* Daily Nutrition Summary (authoritative totals) */}
      {showDailySummary && dailySummary && (
        <DailyNutritionSummary summary={dailySummary} className="mt-3" />
      )}
    </div>
  );
};

