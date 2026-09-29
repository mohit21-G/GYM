import React, { useState, useEffect } from 'react';
import { apiClient } from '../../config/api';
import {
  Activity,
  Plus,
  Search,
  Trash2,
  RefreshCw,
  FolderPlus,
  CheckCircle2,
} from 'lucide-react';

export const AdminActivitiesPage: React.FC = () => {
  const [activities, setActivities] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Modals
  const [showAddActivity, setShowAddActivity] = useState(false);
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  // Form states
  const [newActivity, setNewActivity] = useState({
    name: '',
    categoryId: '',
    metValue: 3.5,
    description: '',
    synonyms: '',
  });

  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDesc, setNewCategoryDesc] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [actRes, catsRes] = await Promise.all([
        apiClient.get('/admin/activities', {
          params: { page, limit: 15, name: search || undefined, categoryId: selectedCat || undefined },
        }),
        apiClient.get('/admin/activity-categories'),
      ]);
      setActivities(actRes.data.items || []);
      setTotalPages(actRes.data.meta?.totalPages || 1);
      setCategories(catsRes.data || []);
      if (!newActivity.categoryId && catsRes.data?.length > 0) {
        setNewActivity((prev) => ({ ...prev, categoryId: catsRes.data[0].id }));
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, selectedCat]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchData();
  };

  const handleCreateActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/admin/activities', {
        ...newActivity,
        metValue: Number(newActivity.metValue),
      });
      setSuccess(`Activity "${newActivity.name}" added to master database`);
      setShowAddActivity(false);
      setNewActivity({
        name: '',
        categoryId: categories[0]?.id || '',
        metValue: 3.5,
        description: '',
        synonyms: '',
      });
      fetchData();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to create activity item');
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/admin/activity-categories', {
        name: newCategoryName.trim(),
        description: newCategoryDesc.trim(),
      });
      setSuccess(`Category "${newCategoryName}" created`);
      setShowAddCategory(false);
      setNewCategoryName('');
      setNewCategoryDesc('');
      fetchData();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to create activity category');
    }
  };

  const handleDeleteActivity = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) return;
    try {
      await apiClient.delete(`/admin/activities/${id}`);
      setActivities((prev) => prev.filter((a) => a.id !== id));
      setSuccess(`Deleted "${name}"`);
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to delete activity item');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Activity Master Catalog
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Canonical workout registry, MET intensities, and multilingual exercise synonyms
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowAddCategory(true)}
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
          >
            <FolderPlus className="w-4 h-4 text-amber-400" />
            <span>New Category</span>
          </button>
          <button
            onClick={() => setShowAddActivity(true)}
            className="flex items-center space-x-1.5 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-xs font-semibold transition-colors cursor-pointer shadow-lg shadow-amber-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Activity</span>
          </button>
        </div>
      </div>

      {success && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex flex-col md:flex-row gap-4 justify-between items-center shadow-lg">
        <form onSubmit={handleSearchSubmit} className="flex-1 w-full relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search activities by name or alias..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
          />
        </form>

        <div className="flex items-center space-x-3 w-full md:w-auto">
          <select
            value={selectedCat}
            onChange={(e) => {
              setSelectedCat(e.target.value);
              setPage(1);
            }}
            className="bg-slate-800 border border-slate-700 text-xs text-white rounded-xl px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-amber-500"
          >
            <option value="">All Categories ({categories.length})</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c._count?.activities ?? 0})
              </option>
            ))}
          </select>

          <button
            onClick={fetchData}
            className="p-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-slate-300"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Activities Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex items-center justify-center space-x-2">
            <RefreshCw className="w-5 h-5 animate-spin text-amber-400" />
            <span>Loading activities catalog...</span>
          </div>
        ) : activities.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <Activity className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-300">No activities found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Activity Name</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">MET Intensity</th>
                  <th className="py-3.5 px-4">Description</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {activities.map((act) => (
                  <tr key={act.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-200">{act.name}</div>
                      {act.synonyms && (
                        <div className="text-[10px] text-slate-400 mt-0.5 truncate max-w-xs">
                          Aliases: {act.synonyms}
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        {act.category?.name || 'General'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-bold text-amber-400 px-2 py-0.5 bg-amber-500/10 rounded-lg border border-amber-500/20">
                        MET {act.metValue}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 truncate max-w-xs">
                      {act.description || 'Standard metabolic exertion'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleDeleteActivity(act.id, act.name)}
                        className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer"
                        title="Delete activity entry"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add Activity Modal */}
      {showAddActivity && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Add Canonical Activity</h3>
            <form onSubmit={handleCreateActivity} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Activity Name
                </label>
                <input
                  type="text"
                  required
                  value={newActivity.name}
                  onChange={(e) => setNewActivity({ ...newActivity, name: e.target.value })}
                  placeholder="e.g. Surya Namaskar, HIIT Treadmill"
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Category
                  </label>
                  <select
                    value={newActivity.categoryId}
                    onChange={(e) => setNewActivity({ ...newActivity, categoryId: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    MET Value
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    required
                    value={newActivity.metValue}
                    onChange={(e) => setNewActivity({ ...newActivity, metValue: Number(e.target.value) })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={newActivity.description}
                  onChange={(e) => setNewActivity({ ...newActivity, description: e.target.value })}
                  placeholder="Notes on intensity or posture"
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Synonyms / Aliases
                </label>
                <input
                  type="text"
                  value={newActivity.synonyms}
                  onChange={(e) => setNewActivity({ ...newActivity, synonyms: e.target.value })}
                  placeholder="e.g. running, daudvu, jog"
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddActivity(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-xs font-semibold shadow-lg shadow-amber-500/20"
                >
                  Save Activity
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Category Modal */}
      {showAddCategory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Create Activity Category</h3>
            <form onSubmit={handleCreateCategory} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Category Name
                </label>
                <input
                  type="text"
                  required
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  placeholder="e.g. Yoga & Flexibility"
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={newCategoryDesc}
                  onChange={(e) => setNewCategoryDesc(e.target.value)}
                  placeholder="Optional description"
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddCategory(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-xs font-semibold"
                >
                  Create Category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
