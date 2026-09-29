import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api/v1';

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
    // If backend returns standard NestJS TransformInterceptor envelope: { success, statusCode, data }
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

