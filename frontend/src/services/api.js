const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function get(path) {
  const response = await fetch(`${BASE_URL}${path}`);
  if (!response.ok) { const error = new Error(`API request failed: ${response.status}`); error.status = response.status; throw error; }
  return response.json();
}

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  if (!response.ok) {
    let message = `API request failed: ${response.status}`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
      else if (Array.isArray(body.detail)) message = body.detail.map((item) => item.msg).join(', ');
    } catch { /* Response was not JSON. */ }
    throw new Error(message);
  }
  return response.json();
}

export const api = {
  history: (slug, city, days = 30) => get(`/api/materials/${slug}/history?city=${encodeURIComponent(city)}&days=${days}`),
  overview: (city) => get(`/api/v1/market/overview?city=${encodeURIComponent(city)}`),
  detail: (slug, city = 'delhi') => get(`/api/v1/prices/${encodeURIComponent(slug)}/detail?city=${encodeURIComponent(city)}`),
};

export const adminPriceApi = {
  options: () => get('/api/v1/admin/prices/options'),
  list: (filters = {}) => {
    const query = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== '' && value !== null && value !== undefined) query.set(key, value);
    });
    return get(`/api/v1/admin/prices?${query.toString()}`);
  },
  create: (payload) => request('/api/v1/admin/prices', { method: 'POST', body: JSON.stringify(payload) }),
  replace: (id, payload) => request(`/api/v1/admin/prices/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
};

export const adminImportApi = {
  preview: async (file) => {
    const body = new FormData();
    body.append('file', file);
    const response = await fetch(`${BASE_URL}/api/v1/admin/prices/import/preview`, { method: 'POST', body });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Preview failed: ${response.status}`);
    }
    return response.json();
  },
  commit: (rows) => request('/api/v1/admin/prices/import/commit', {
    method: 'POST',
    body: JSON.stringify({ rows }),
  }),
};

export const submissionApi = {
  options: () => get('/api/v1/price-submissions/options'),
  create: (payload) => request('/api/v1/price-submissions', { method: 'POST', body: JSON.stringify(payload) }),
  list: (filters = {}) => {
    const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value !== '' && value != null));
    return get(`/api/v1/admin/price-submissions?${query}`);
  },
  approve: (id, notes = null) => request(`/api/v1/admin/price-submissions/${id}/approve`, { method: 'POST', body: JSON.stringify({ notes }) }),
  reject: (id, notes = null) => request(`/api/v1/admin/price-submissions/${id}/reject`, { method: 'POST', body: JSON.stringify({ notes }) }),
};

export const dataSourceApi = {
  list: () => get('/api/v1/admin/data-sources'),
  run: (id) => request(`/api/v1/admin/data-sources/${id}/run`, { method: 'POST' }),
};
