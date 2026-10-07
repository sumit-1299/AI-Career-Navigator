const API_BASE = '/api';

function getToken() {
  try {
    return localStorage.getItem('career_navigator_token');
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) {
      localStorage.setItem('career_navigator_token', token);
    } else {
      localStorage.removeItem('career_navigator_token');
    }
  } catch {}
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

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json')
      ? await response.json()
      : { message: await response.text() };

    if (!response.ok) {
      if (response.status === 401 && token) {
        try {
          localStorage.removeItem('career_navigator_token');
          localStorage.removeItem('career_navigator_user');
        } catch {}
        window.dispatchEvent(new CustomEvent('career-navigator:unauthorized'));
      }

      const error = new Error(
        data?.message || data?.error || `HTTP ${response.status} Error`
      );
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    if (!err.status && err.name === 'TypeError') {
      const networkError = new Error(
        'Unable to reach the Career Navigator server.'
      );
      networkError.status = 0;
      throw networkError;
    }
    throw err;
  }
}

export const api = {
  // Authentication
  login: (email, password) =>
    request('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (name, email, password) =>
    request('/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),

  forgotPassword: (email) =>
    request('/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  resetPassword: (token, password) =>
    request('/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password }),
    }),

  // Student Academic Profile
  getProfile: (userId) =>
    request(userId ? `/profile?user_id=${userId}` : '/profile'),

  createProfile: (profileData) =>
    request('/profile', {
      method: 'POST',
      body: JSON.stringify(profileData),
    }),

  updateProfile: (profileData, userId) =>
    request(userId ? `/profile?user_id=${userId}` : '/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    }),

  // Career Preferences
  getPreferences: () => request('/career-preferences'),

  savePreferences: (preferences) =>
    request('/career-preferences', {
      method: 'POST',
      body: JSON.stringify(preferences),
    }),

  // Skills
  searchCanonicalSkills: (query, limit = 10) =>
    request(`/skills?q=${encodeURIComponent(query)}&limit=${limit}`),

  getUserSkills: () => request('/skills'),

  addSkill: (skill_name, proficiency) =>
    request('/skills', {
      method: 'POST',
      body: JSON.stringify({ skill_name, proficiency }),
    }),

  getCanonicalSkillDetail: (skillId) =>
    request(`/skills/canonical/${skillId}`),

  // Resume Ingestion
  extractResume: (input) => {
    if (input instanceof File) {
      const formData = new FormData();
      formData.append('file', input);
      return request('/skills/extract-resume', {
        method: 'POST',
        body: formData,
      });
    }

    return request('/skills/extract-resume', {
      method: 'POST',
      body: JSON.stringify({ resume_text: input }),
    });
  },

  scoreResume: (careerId, input) => {
    const endpoint = `/skills/extract-resume/score?career_id=${careerId}`;

    if (input instanceof File) {
      const formData = new FormData();
      formData.append('file', input);
      return request(endpoint, {
        method: 'POST',
        body: formData,
      });
    }

    const body = typeof input === 'string' ? { resume_text: input } : input;

    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  applyResumeSkills: (skills, userId) =>
    request('/skills/extract-resume/apply', {
      method: 'POST',
      body: JSON.stringify({ skills, user_id: userId }),
    }),

  // Careers & Intelligence
  listCareers: () => request('/careers'),

  getCareerDetail: (careerId) =>
    request(`/careers/${careerId}`),

  getCareerRecommendations: (domain = null, limit = null) => {
    const params = new URLSearchParams();

    if (domain) params.append('domain', domain);
    if (limit) params.append('limit', limit);

    const query = params.toString() ? `?${params.toString()}` : '';

    return request(`/careers/recommendations${query}`);
  },

  getSkillGap: (careerId) =>
    request(`/careers/${careerId}/skill-gap`),

  getRoadmap: (careerId, hoursPerWeek = null) => {
    const query = hoursPerWeek
      ? `?hours_per_week=${hoursPerWeek}`
      : '';

    return request(`/careers/${careerId}/roadmap${query}`);
  },

  compareCareers: (careerAId, careerBId) =>
    request(
      `/careers/compare?career_a_id=${careerAId}&career_b_id=${careerBId}`
    ),

  getCareerPathways: (careerId, options = {}) => {
    const { hoursPerWeek = 10, userId = null } = options;
    const params = new URLSearchParams();

    if (hoursPerWeek) params.append('hours_per_week', hoursPerWeek);
    if (userId) params.append('user_id', userId);

    const query = params.toString() ? `?${params.toString()}` : '';

    return request(`/careers/${careerId}/pathways${query}`);
  },

  simulateSkillImpact: (careerId, options = {}) =>
    request(`/careers/${careerId}/simulate-skill`, {
      method: 'POST',
      body: JSON.stringify({
        skill_id: options.skillId,
        skill_name: options.skillName,
        simulated_level: options.simulatedLevel,
        hours_per_week: options.hoursPerWeek ?? 10,
        user_id: options.userId ?? null,
      }),
    }),

  getCareerSkillRoi: (careerId, options = {}) => {
    const { hoursPerWeek = 10, userId = null } = options;
    const params = new URLSearchParams();

    if (hoursPerWeek) params.append('hours_per_week', hoursPerWeek);
    if (userId) params.append('user_id', userId);

    const query = params.toString() ? `?${params.toString()}` : '';

    return request(`/careers/${careerId}/skill-roi${query}`);
  },

  runCounterfactualAnalysis: (careerId, options = {}) =>
    request(`/careers/${careerId}/counterfactual`, {
      method: 'POST',
      body: JSON.stringify({
        skill_id: options.skillId,
        skill_name: options.skillName,
        target_level: options.targetLevel ?? null,
        hours_per_week: options.hoursPerWeek ?? 10,
        user_id: options.userId ?? null,
      }),
    }),

  getPortfolioProjectRecommendations: (careerId, options = {}) => {
    const { difficulty = null, limit = null, userId = null } = options;
    const params = new URLSearchParams();

    if (difficulty) params.append('difficulty', difficulty);
    if (limit) params.append('limit', limit);
    if (userId) params.append('user_id', userId);

    const query = params.toString() ? `?${params.toString()}` : '';

    return request(`/careers/${careerId}/portfolio-recommendations${query}`);
  },

  getCareerAnalytics: (careerId) =>
    request(`/careers/${careerId}/analytics`),

  getCareerReadinessSummary: (careerId, options = {}) => {
    const { hoursPerWeek = 10, resumeText = null } = options;

    if (resumeText) {
      return request(`/careers/${careerId}/readiness-summary`, {
        method: 'POST',
        body: JSON.stringify({
          hours_per_week: hoursPerWeek,
          resume_text: resumeText,
        }),
      });
    }

    const query = hoursPerWeek
      ? `?hours_per_week=${hoursPerWeek}`
      : '';

    return request(`/careers/${careerId}/readiness-summary${query}`);
  },

  // Career Market Outlook
  getCareerMarketOutlook: (careerId) =>
    request(`/careers/${careerId}/market-outlook`),

  listMarketOutlooks: () =>
    request('/careers/market-outlook'),

  compareMarketOutlooks: (careerIds) =>
    request('/careers/market-outlook/compare', {
      method: 'POST',
      body: JSON.stringify({ career_ids: careerIds }),
    }),

  // Learning Resources & Progress
  listLearningResources: (params = {}) => {
    const q = new URLSearchParams();

    if (params.canonical_skill_id) {
      q.append('canonical_skill_id', params.canonical_skill_id);
    }

    if (params.difficulty) {
      q.append('difficulty', params.difficulty);
    }

    if (params.type) {
      q.append('type', params.type);
    }

    if (params.q) {
      q.append('q', params.q);
    }

    const queryString = q.toString()
      ? `?${q.toString()}`
      : '';

    return request(`/learning-resources${queryString}`);
  },

  startLearningResource: (resourceId) =>
    request(`/learning-resources/${resourceId}/start`, {
      method: 'POST',
    }),

  updateLearningProgress: (resourceId, progress_percentage, notes = null) =>
    request(`/learning-resources/${resourceId}/progress`, {
      method: 'PUT',
      body: JSON.stringify({
        progress_percentage,
        notes,
      }),
    }),

  completeLearningResource: (resourceId) =>
    request(`/learning-resources/${resourceId}/complete`, {
      method: 'POST',
    }),

  getUserLearningProgress: (status = null) => {
    const query = status
      ? `?status=${encodeURIComponent(status)}`
      : '';

    return request(`/learning-resources/progress${query}`);
  },

  getSkillProgress: (skillId) =>
    request(`/skills/canonical/${skillId}/progress`),
};
