import { create } from 'zustand';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'CUSTOMER' | 'ADMIN';
  status: 'ACTIVE' | 'INACTIVE';
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: JSON.parse(localStorage.getItem('Fitness_user') || 'null'),
  token: localStorage.getItem('Fitness_token') || null,
  isAuthenticated: !!localStorage.getItem('Fitness_token'),

  setAuth: (user: User, token: string) => {
    localStorage.setItem('Fitness_user', JSON.stringify(user));
    localStorage.setItem('Fitness_token', token);
    set({ user, token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('Fitness_user');
    localStorage.removeItem('Fitness_token');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
