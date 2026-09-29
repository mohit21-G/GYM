import axios from 'axios';

/**
 * Resolves the backend API base URL:
 * - Reads import.meta.env.VITE_API_URL or import.meta.env.VITE_API_BASE_URL.
 * - If not provided:
 *     - Production (import.meta.env.PROD or running on non-localhost domain): 'https://gym-ikjt.onrender.com'
 *     - Local development: 'http://localhost:3000'
 * - Strips trailing slashes and guarantees the '/api/v1' path without duplicating it.
 */
function resolveApiBaseUrl(): string {
  const envUrl = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').trim();

  let base = envUrl;
  if (!base) {
    const isLocalhost =
      typeof window !== 'undefined' &&
      (window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1' ||
        window.location.hostname === '0.0.0.0');

    if (import.meta.env.DEV || isLocalhost) {
      base = 'http://localhost:3000';
    } else {
      base = 'https://gym-ikjt.onrender.com';
    }
  }

  // Strip trailing slashes
  base = base.replace(/\/+$/, '');

  // Ensure /api/v1 prefix without duplication
  if (!base.endsWith('/api/v1')) {
    if (base.endsWith('/api')) {
      base = `${base}/v1`;
    } else {
      base = `${base}/api/v1`;
    }
  }

  return base;
}

export const API_BASE_URL = resolveApiBaseUrl();

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach Bearer token if present
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('Fitness_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor to handle and unwrap responses
apiClient.interceptors.response.use(
  (response) => {
    // If backend returns standard TransformInterceptor envelope: { success, statusCode, data }
    if (
      response.data &&
      typeof response.data === 'object' &&
      'success' in response.data &&
      'data' in response.data
    ) {
      response.data = response.data.data;
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('Fitness_token');
      localStorage.removeItem('Fitness_user');
      // redirect or state change can trigger here if not on auth page
    }
    return Promise.reject(error);
  },
);
