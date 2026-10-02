import React, { useState, useEffect } from 'react';
import { X, Save, Flame } from 'lucide-react';

export interface ActivityEntryData {
  id: string;
  title?: string;
  activity?: string;
  activityName?: string;
  subtitle?: string;
  metric?: string;
  durationMinutes?: number;
  reps?: number | null;
  sets?: number | null;
  caloriesBurned?: number;
  metValue?: number;
  intensity?: string;
  loggedAt?: string;
  timeFormatted?: string;
}

interface EditActivityLogModalProps {
  isOpen: boolean;
  entry: ActivityEntryData | null;
  onClose: () => void;
  onSave: (updatedData: {
    activity: string;
    durationMinutes?: number;
    reps?: number;
    sets?: number;
    intensity?: string;
  }) => Promise<void>;
}

export const EditActivityLogModal: React.FC<EditActivityLogModalProps> = ({
  isOpen,
  entry,
  onClose,
  onSave,
}) => {
  const [activity, setActivity] = useState('');
  const [durationMinutes, setDurationMinutes] = useState<number>(30);
  const [reps, setReps] = useState<number | ''>('');
  const [sets, setSets] = useState<number | ''>('');
  const [intensity, setIntensity] = useState('MEDIUM');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (entry) {
      setActivity(entry.title || entry.activity || entry.activityName || '');
      setDurationMinutes(Number(entry.durationMinutes) || 30);
      setReps(entry.reps != null ? Number(entry.reps) : '');
      setSets(entry.sets != null ? Number(entry.sets) : '');
      setIntensity(entry.intensity || 'MEDIUM');
      setError(null);
    }
  }, [entry, isOpen]);

  if (!isOpen || !entry) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activity.trim()) {
      setError('Exercise name is required');
      return;
    }
    if (durationMinutes <= 0 && !reps) {
      setError('Enter a duration or reps');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      await onSave({
        activity: activity.trim(),
        durationMinutes: durationMinutes > 0 ? Number(durationMinutes) : undefined,
        reps: reps !== '' ? Number(reps) : undefined,
        sets: sets !== '' ? Number(sets) : undefined,
        intensity,
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
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Flame className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Edit Activity Log</h3>
              <p className="text-xs text-slate-400">Calories burned will automatically recalculate</p>
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
              Exercise Name
            </label>
            <input
              type="text"
              value={activity}
              onChange={(e) => setActivity(e.target.value)}
              placeholder="e.g. Walking, Gym Workout, Push-ups"
              required
              className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Duration (minutes)
              </label>
              <input
                type="number"
                step="any"
                min="0"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Intensity
              </label>
              <select
                value={intensity}
                onChange={(e) => setIntensity(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
              >
                <option value="LOW">LOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="HIGH">HIGH</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Reps <span className="text-slate-500">(optional)</span>
              </label>
              <input
                type="number"
                step="1"
                min="0"
                value={reps}
                onChange={(e) => setReps(e.target.value === '' ? '' : parseInt(e.target.value, 10) || 0)}
                placeholder="—"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Sets <span className="text-slate-500">(optional)</span>
              </label>
              <input
                type="number"
                step="1"
                min="0"
                value={sets}
                onChange={(e) => setSets(e.target.value === '' ? '' : parseInt(e.target.value, 10) || 0)}
                placeholder="—"
                className="w-full bg-slate-800/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all"
              />
            </div>
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
              className="px-5 py-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-xs font-semibold rounded-xl shadow-lg shadow-amber-500/20 transition-all flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{saving ? 'Saving...' : 'Save & Recalculate'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
