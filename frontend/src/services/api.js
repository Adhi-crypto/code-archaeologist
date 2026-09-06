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
  queryStream: async (data, { onStatus, onMetadata, onToken, onDone, signal }) => {
    const response = await fetch(`${API_BASE}/api/chat/query-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal,
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Streaming query failed');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // Keep unfinished trailing chunk

      for (const block of lines) {
        if (!block.trim()) continue;
        const eventMatch = block.match(/^event:\s*(.+)$/m);
        const dataMatch = block.match(/^data:\s*(.+)$/m);

        if (eventMatch && dataMatch) {
          const eventType = eventMatch[1].trim();
          try {
            const parsed = JSON.parse(dataMatch[1]);
            if (eventType === 'status' && onStatus) onStatus(parsed.message);
            else if (eventType === 'metadata' && onMetadata) onMetadata(parsed);
            else if (eventType === 'token' && onToken) onToken(parsed.token);
            else if (eventType === 'done' && onDone) onDone(parsed);
          } catch (e) {
            console.warn('SSE parse warning:', e, block);
          }
        }
      }
    }
  },
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