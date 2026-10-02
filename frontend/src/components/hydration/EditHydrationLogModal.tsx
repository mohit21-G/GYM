import React, { useState, useEffect } from 'react';
import { X, Save, Droplets } from 'lucide-react';
import { HydrationEntryItem } from './DailyHydrationSummary';

interface EditHydrationLogModalProps {
  isOpen: boolean;
  entry: HydrationEntryItem | null;
  onClose: () => void;
  onSave: (updatedData: {
    amountMl: number;
    beverageName: string;
    loggedAt?: string;
  }) => Promise<void>;
}

export const EditHydrationLogModal: React.FC<EditHydrationLogModalProps> = ({
  isOpen,
  entry,
  onClose,
  onSave,
}) => {
  const [amountMl, setAmountMl] = useState<number>(250);
  const [beverageName, setBeverageName] = useState('Water');
  const [timeFormatted, setTimeFormatted] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (entry) {
      setAmountMl(Number(entry.amountMl ?? entry.amount_ml ?? entry.amount ?? 250));
      setBeverageName(entry.beverageName || entry.beverage_name || entry.beverage || 'Water');
      setTimeFormatted(entry.time || entry.timeFormatted || '');
      setError(null);
    }
  }, [entry, isOpen]);

  if (!isOpen || !entry) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!beverageName.trim()) {
      setError('Beverage name is required');
      return;
    }
    if (amountMl <= 0) {
      setError('Amount must be greater than 0');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await onSave({
        amountMl: Number(amountMl),
        beverageName: beverageName.trim(),
        loggedAt: timeFormatted.trim() ? timeFormatted.trim() : undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to save changes. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div
        className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-scaleIn"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
              <Droplets className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Edit Hydration Log</h3>
              <p className="text-xs text-slate-400">Update the amount or beverage logged</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Beverage Name
            </label>
            <input
              type="text"
              value={beverageName}
              onChange={(e) => setBeverageName(e.target.value)}
              placeholder="e.g. Water, Lemon Water, Coconut Water"
              required
              className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Amount (ml)
            </label>
            <input
              type="number"
              step="any"
              min="1"
              value={amountMl}
              onChange={(e) => setAmountMl(parseFloat(e.target.value) || 0)}
              required
              className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center justify-between">
              <span>Time</span>
              <span className="text-[10px] text-slate-400">e.g. 7:00 AM, 16:30</span>
            </label>
            <input
              type="text"
              value={timeFormatted}
              onChange={(e) => setTimeFormatted(e.target.value)}
              placeholder="e.g. 7:00 AM"
              className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="pt-2 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white text-xs font-semibold rounded-xl shadow-lg shadow-cyan-500/20 transition-all flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{saving ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
