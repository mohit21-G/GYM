import React from 'react';
import { Droplets, GlassWater, Clock, Sparkles } from 'lucide-react';

export interface HydrationEntryItem {
  id?: string;
  time?: string;
  timeFormatted?: string;
  amountMl?: number;
  amount_ml?: number;
  amount?: number;
  beverageName?: string;
  beverage_name?: string;
  beverage?: string;
  portion?: string;
  rawText?: string;
  notes?: string;
  loggedAt?: string;
}

export interface DailyHydrationSummaryData {
  totalMl: number;
  targetMl?: number | null;
  hasTarget?: boolean;
  remainingMl?: number | null;
  percent?: number | null;
  entries?: HydrationEntryItem[];
  amountMl?: number;
  title?: string;
  subtitle?: string;
  log?: {
    amountMl?: number;
    beverageName?: string;
  };
  dailySummary?: {
    totalMl?: number;
    targetMl?: number | null;
    hasTarget?: boolean;
    remainingMl?: number | null;
  };
}

interface DailyHydrationSummaryProps {
  data: DailyHydrationSummaryData;
  className?: string;
}

export const DailyHydrationSummary: React.FC<DailyHydrationSummaryProps> = ({
  data,
  className = '',
}) => {
  if (!data) return null;

  const rawEntries: HydrationEntryItem[] = Array.isArray(data.entries)
    ? data.entries
    : Array.isArray((data as any).details)
    ? (data as any).details
    : [];

  const singleAmt = data.amountMl ?? data.log?.amountMl ?? (data as any).amount ?? 0;
  const singleBev = data.log?.beverageName ?? (data as any).beverageName ?? (data as any).beverage_name ?? 'Water';

  // If no entries array was passed but a single amount was logged, build a single item
  const entries: HydrationEntryItem[] =
    rawEntries.length > 0
      ? rawEntries
      : singleAmt > 0
      ? [{ amountMl: singleAmt, beverageName: singleBev }]
      : [];

  const totalMl =
    data.dailySummary?.totalMl ??
    data.totalMl ??
    (entries.length > 0
      ? entries.reduce((acc, e) => acc + (Number(e.amountMl ?? e.amount_ml ?? e.amount) || 0), 0)
      : singleAmt);

  // Target handling: only show if explicitly configured
  const hasExplicitTarget = Boolean(
    data.hasTarget ||
    data.dailySummary?.hasTarget ||
    (data.targetMl && data.targetMl > 0 && data.targetMl !== 2500)
  );
  const targetMl = hasExplicitTarget ? (data.targetMl ?? data.dailySummary?.targetMl ?? null) : null;

  const percent =
    hasExplicitTarget && targetMl && targetMl > 0
      ? Math.min(100, Math.round((totalMl / targetMl) * 100))
      : null;

  const remainingMl =
    hasExplicitTarget && targetMl && targetMl > 0
      ? Math.max(0, targetMl - totalMl)
      : null;

  const entryCount = entries.length;

  // Compute breakdown by beverage type for pills
  const bevTotals: Record<string, number> = {};
  for (const e of entries) {
    const bName = e.beverageName || e.beverage_name || e.beverage || 'Water';
    const amt = Number(e.amountMl ?? e.amount_ml ?? e.amount) || 0;
    bevTotals[bName] = (bevTotals[bName] || 0) + amt;
  }
  const bevList = Object.entries(bevTotals);

  return (
    <div
      className={`bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-cyan-500/25 rounded-2xl p-4 shadow-lg backdrop-blur-sm w-full ${className}`}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Droplets className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-200">
              Daily Hydration Progress
            </h3>
            <p className="text-[10px] text-slate-400">
              {entryCount} {entryCount === 1 ? 'entry' : 'entries'} logged today
            </p>
          </div>
        </div>

        <div className="text-right">
          {hasExplicitTarget && targetMl ? (
            <>
              <span className="text-xs font-bold text-cyan-400">{totalMl}</span>
              <span className="text-[11px] text-slate-400"> / {targetMl} ml</span>
            </>
          ) : (
            <>
              <span className="text-xs font-bold text-cyan-400">{totalMl} ml</span>
              <div className="text-[10px] text-slate-400 font-medium">Today's Total</div>
            </>
          )}
        </div>
      </div>

      {/* Progress Bar (ONLY if user has an explicit target) */}
      {hasExplicitTarget && targetMl && percent !== null && (
        <div className="mt-3 space-y-1.5">
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>{percent}% of daily goal</span>
            <span className="text-slate-300 font-medium">
              {remainingMl !== null && remainingMl > 0
                ? `${remainingMl} ml remaining`
                : 'Daily goal reached!'}
            </span>
          </div>

          <div className="w-full bg-slate-800/80 rounded-full h-2.5 overflow-hidden border border-slate-700/40">
            <div
              className="bg-gradient-to-r from-cyan-500 to-teal-400 h-2.5 rounded-full transition-all duration-700 ease-out shadow-sm shadow-cyan-500/30"
              style={{ width: `${percent}%` }}
            />
          </div>
        </div>
      )}

      {/* Prominent Today's Total Hydration Banner */}
      <div className="mt-3.5 bg-slate-800/60 rounded-xl p-3 border border-slate-700/40 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-6 h-6 rounded-md bg-cyan-500/10 flex items-center justify-center text-cyan-400">
            <GlassWater className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-medium">Today's Total Hydration</div>
            <div className="text-[10px] text-slate-500">
              Sum of all logged water & beverages today
            </div>
          </div>
        </div>
        <div className="text-right">
          <span className="text-sm font-bold text-cyan-400">{totalMl}</span>
          <span className="text-xs text-slate-400 ml-1">ml</span>
        </div>
      </div>

      {/* Beverage Breakdown Pills (Matching Nutrition Macro Pills aesthetic) */}
      {bevList.length > 0 && (
        <div
          className={`mt-2.5 grid gap-1.5 text-center text-xs ${
            bevList.length === 1
              ? 'grid-cols-1'
              : bevList.length === 2
              ? 'grid-cols-2'
              : bevList.length === 3
              ? 'grid-cols-3'
              : 'grid-cols-4'
          }`}
        >
          {bevList.map(([bName, bAmt], idx) => (
            <div
              key={idx}
              className="bg-slate-800/60 rounded-xl p-2 border border-slate-700/40"
            >
              <div className="text-[10px] text-slate-400 font-medium truncate">
                {bName}
              </div>
              <div className="text-cyan-400 font-bold mt-0.5 text-xs">
                {bAmt} ml
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Itemized Logged Entries Timeline / List */}
      {entries.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            <span>Logged Today</span>
            <span className="text-slate-500 lowercase">
              {entries.length} {entries.length === 1 ? 'record' : 'records'}
            </span>
          </div>

          <div className="space-y-1.5">
            {entries.map((item, idx) => {
              const timeStr = item.time || item.timeFormatted || '';
              const amt = item.amountMl ?? item.amount_ml ?? item.amount ?? 0;
              const bev = item.beverageName || item.beverage_name || item.beverage || 'Water';
              const rawPortion = item.portion || item.rawText;

              return (
                <div
                  key={idx}
                  className="flex items-center justify-between bg-slate-800/40 hover:bg-slate-800/60 rounded-xl px-3 py-2 border border-slate-700/30 transition-colors text-xs"
                >
                  <div className="flex items-center space-x-2.5 truncate flex-1">
                    <Droplets className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                    <span className="text-slate-200 font-medium truncate">
                      {rawPortion ? (
                        <span>
                          {rawPortion} {bev !== 'Water' ? `(${bev})` : ''}{' '}
                          <span className="text-slate-400 font-normal">— {amt} ml</span>
                        </span>
                      ) : (
                        <span>
                          {bev}{' '}
                          <span className="text-cyan-400 font-bold">— {amt} ml</span>
                        </span>
                      )}
                    </span>
                  </div>
                  {timeStr && (
                    <div className="flex items-center space-x-1 text-[10px] text-slate-400 font-medium flex-shrink-0 ml-2">
                      <Clock className="w-3 h-3 text-slate-500" />
                      <span>{timeStr}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
