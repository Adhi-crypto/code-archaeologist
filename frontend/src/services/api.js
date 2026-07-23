import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export const repoApi = {
  ingest: (data) => api.post('/api/repo/ingest', data),
  status: (repoId) => api.get(`/api/repo/status/${repoId}`),
  list: () => api.get('/api/repo/list'),
};

export const chatApi = {
  query: (data) => api.post('/api/chat/query', data),
};

export const evolutionApi = {
  analyze: (data) => api.post('/api/evolution/analyze', data),
};

export const bugOriginApi = {
  analyze: (data) => api.post('/api/bug-origin/analyze', data),
};

export const repoIntelligenceApi = {
  analyze: (data) => api.post('/api/repository/intelligence', data),
};

export default api;