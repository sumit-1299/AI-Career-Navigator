const API_BASE = '/api';

function getToken() {
  try {
    return localStorage.getItem('career_navigator_token');
  } catch {
    return null;
  }
}

async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await response.json()
    : { message: await response.text() };

  if (!response.ok) {
    const error = new Error(data?.message || `HTTP ${response.status} Error`);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

function queryString(params = {}) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      q.append(key, value);
    }
  });
  return q.toString() ? `?${q.toString()}` : '';
}

export const jobApi = {
  listJobs: (filters = {}) =>
    request(`/jobs${queryString({
      q: filters.q,
      location: filters.location,
      work_mode: filters.work_mode,
      experience: filters.experience,
      technology: filters.technology,
      provider: filters.provider,
      page: filters.page || 1,
    })}`),

  getJob: (sourceKey, providerId) =>
    request(`/jobs/${encodeURIComponent(sourceKey)}/${encodeURIComponent(providerId)}`),

  compareJob: (sourceKey, providerId, mode = 'semantic') =>
    request(
      `/jobs/${encodeURIComponent(sourceKey)}/${encodeURIComponent(providerId)}/compare`,
      {
        method: 'POST',
        body: JSON.stringify({
          submission_id: crypto.randomUUID(),
          mode,
        }),
      }
    ),

  getComparison: (comparisonId) =>
    request(`/job-matches/${encodeURIComponent(comparisonId)}`),

  getRecentComparisons: () =>
    request('/job-matches'),
};
