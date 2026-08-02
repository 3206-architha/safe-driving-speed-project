import axios from 'axios';
import type {
  AuthResponse, Prediction, PredictionRequest,
} from '../types';

const api = axios.create({ baseURL: '/api' });

// Attach the JWT to every request automatically once logged in
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the token expires, bounce back to login instead of showing broken data
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export const authApi = {
  register: (name: string, email: string, password: string) =>
    api.post<AuthResponse>('/auth/register', { name, email, password }),
  login: (email: string, password: string) =>
    api.post<AuthResponse>('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
};

export const predictionApi = {
  predict: (payload: PredictionRequest) =>
    api.post<Prediction>('/predict', payload),
  history: (params?: { risk_level?: string; skip?: number; limit?: number }) =>
    api.get<Prediction[]>('/predictions', { params }),
};

export const weatherApi = {
  current: (lat: number, lng: number) =>
    api.get('/weather/current', { params: { lat, lng } }),
};

export const analyticsApi = {
  trends: () => api.get('/analytics/trends'),
  riskDistribution: () => api.get('/analytics/risk-distribution'),
};

export default api;
