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
  user: JSON.parse(localStorage.getItem('fitbit_user') || 'null'),
  token: localStorage.getItem('fitbit_token') || null,
  isAuthenticated: !!localStorage.getItem('fitbit_token'),

  setAuth: (user: User, token: string) => {
    localStorage.setItem('fitbit_user', JSON.stringify(user));
    localStorage.setItem('fitbit_token', token);
    set({ user, token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('fitbit_user');
    localStorage.removeItem('fitbit_token');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
