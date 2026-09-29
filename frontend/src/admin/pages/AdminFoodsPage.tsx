import React, { useState, useEffect } from 'react';
import { apiClient } from '../../config/api';
import {
  UtensilsCrossed,
  Plus,
  Search,
  Trash2,
  RefreshCw,
  FolderPlus,
  Tag,
  CheckCircle2,
} from 'lucide-react';

export const AdminFoodsPage: React.FC = () => {
  const [foods, setFoods] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Modals
  const [showAddFood, setShowAddFood] = useState(false);
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  // New Food Form State
  const [newFood, setNewFood] = useState({
    name: '',
    categoryId: '',
    caloriesPerServing: 100,
    standardServingSize: 100,
    standardServingUnit: 'g',
    proteinG: 0,
    carbsG: 0,
    fatG: 0,
    fiberG: 0,
    synonyms: '',
  });

  // New Category Form State
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDesc, setNewCategoryDesc] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [foodsRes, catsRes] = await Promise.all([
        apiClient.get('/admin/foods', {
          params: { page, limit: 15, name: search || undefined, categoryId: selectedCat || undefined },
        }),
        apiClient.get('/admin/food-categories'),
      ]);
      setFoods(foodsRes.data.items || []);
      setTotalPages(foodsRes.data.meta?.totalPages || 1);
      setCategories(catsRes.data || []);
      if (!newFood.categoryId && catsRes.data?.length > 0) {
        setNewFood((prev) => ({ ...prev, categoryId: catsRes.data[0].id }));
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

  const handleCreateFood = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/admin/foods', {
        ...newFood,
        caloriesPerServing: Number(newFood.caloriesPerServing),
        standardServingSize: Number(newFood.standardServingSize),
        proteinG: Number(newFood.proteinG),
        carbsG: Number(newFood.carbsG),
        fatG: Number(newFood.fatG),
        fiberG: Number(newFood.fiberG),
      });
      setSuccess(`Food "${newFood.name}" added to master database`);
      setShowAddFood(false);
      setNewFood({
        name: '',
        categoryId: categories[0]?.id || '',
        caloriesPerServing: 100,
        standardServingSize: 100,
        standardServingUnit: 'g',
        proteinG: 0,
        carbsG: 0,
        fatG: 0,
        fiberG: 0,
        synonyms: '',
      });
      fetchData();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to create food item');
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/admin/food-categories', {
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
      alert(err.response?.data?.message || 'Failed to create food category');
    }
  };

  const handleDeleteFood = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}" from the canonical database?`))
      return;
    try {
      await apiClient.delete(`/admin/foods/${id}`);
      setFoods((prev) => prev.filter((f) => f.id !== id));
      setSuccess(`Deleted "${name}"`);
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to delete food item');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Food Master Catalog
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Canonical nutrition profiles, Indian foods, serving units, and synonym lookup
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowAddCategory(true)}
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
          >
            <FolderPlus className="w-4 h-4 text-emerald-400" />
            <span>New Category</span>
          </button>
          <button
            onClick={() => setShowAddFood(true)}
            className="flex items-center space-x-1.5 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-xs font-semibold transition-colors cursor-pointer shadow-lg shadow-emerald-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Food Item</span>
          </button>
        </div>
      </div>

      {success && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Search and Category Filter */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex flex-col md:flex-row gap-4 justify-between items-center shadow-lg">
        <form onSubmit={handleSearchSubmit} className="flex-1 w-full relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search foods by name or synonym..."
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
                {c.name} ({c._count?.foods ?? 0})
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

      {/* Foods Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex items-center justify-center space-x-2">
            <RefreshCw className="w-5 h-5 animate-spin text-amber-400" />
            <span>Loading food catalog...</span>
          </div>
        ) : foods.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <UtensilsCrossed className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-300">No food items found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Food Item</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Standard Serving</th>
                  <th className="py-3.5 px-4">Calories</th>
                  <th className="py-3.5 px-4">Macros (P / C / F)</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {foods.map((food) => (
                  <tr key={food.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-200">{food.name}</div>
                      {food.synonyms && (
                        <div className="text-[10px] text-slate-400 mt-0.5 truncate max-w-xs">
                          Aliases: {food.synonyms}
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        {food.category?.name || 'Uncategorized'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {food.standardServingSize} {food.standardServingUnit}
                    </td>
                    <td className="py-3.5 px-4 font-bold text-emerald-400">
                      {food.caloriesPerServing} kcal
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      <span className="text-blue-400 font-medium">{food.proteinG}g</span> /{' '}
                      <span className="text-amber-400 font-medium">{food.carbsG}g</span> /{' '}
                      <span className="text-rose-400 font-medium">{food.fatG}g</span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleDeleteFood(food.id, food.name)}
                        className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer"
                        title="Delete food entry"
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

      {/* Add Food Modal */}
      {showAddFood && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-bold text-white">Add Canonical Food Entry</h3>
            <form onSubmit={handleCreateFood} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Food Item Name
                </label>
                <input
                  type="text"
                  required
                  value={newFood.name}
                  onChange={(e) => setNewFood({ ...newFood, name: e.target.value })}
                  placeholder="e.g. Masala Dosa, Dal Makhani"
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Category
                  </label>
                  <select
                    value={newFood.categoryId}
                    onChange={(e) => setNewFood({ ...newFood, categoryId: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-emerald-500"
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
                    Calories (kcal)
                  </label>
                  <input
                    type="number"
                    required
                    value={newFood.caloriesPerServing}
                    onChange={(e) => setNewFood({ ...newFood, caloriesPerServing: Number(e.target.value) })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Serving Size
                  </label>
                  <input
                    type="number"
                    value={newFood.standardServingSize}
                    onChange={(e) => setNewFood({ ...newFood, standardServingSize: Number(e.target.value) })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                    Serving Unit
                  </label>
                  <input
                    type="text"
                    value={newFood.standardServingUnit}
                    onChange={(e) => setNewFood({ ...newFood, standardServingUnit: e.target.value })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-4 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">Protein (g)</label>
                  <input
                    type="number"
                    value={newFood.proteinG}
                    onChange={(e) => setNewFood({ ...newFood, proteinG: Number(e.target.value) })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-2.5"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">Carbs (g)</label>
                  <input
                    type="number"
                    value={newFood.carbsG}
                    onChange={(e) => setNewFood({ ...newFood, carbsG: Number(e.target.value) })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-2.5"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">Fat (g)</label>
                  <input
                    type="number"
                    value={newFood.fatG}
                    onChange={(e) => setNewFood({ ...newFood, fatG: Number(e.target.value) })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-2.5"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">Fiber (g)</label>
                  <input
                    type="number"
                    value={newFood.fiberG}
                    onChange={(e) => setNewFood({ ...newFood, fiberG: Number(e.target.value) })}
                    className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-2.5"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
                  Synonyms / Aliases (Comma-separated)
                </label>
                <input
                  type="text"
                  value={newFood.synonyms}
                  onChange={(e) => setNewFood({ ...newFood, synonyms: e.target.value })}
                  placeholder="e.g. chapati, phulka, rotli"
                  className="w-full bg-slate-800 border border-slate-700 text-xs text-white rounded-xl p-3"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddFood(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-xs font-semibold shadow-lg shadow-emerald-500/20"
                >
                  Save Food
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
            <h3 className="text-base font-bold text-white">Create Food Category</h3>
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
                  placeholder="e.g. Gujarati Snacks"
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
                  className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-xs font-semibold"
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
