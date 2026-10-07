/**
 * Centralized API client service for AI Career Navigator.
 * Connects React frontend directly to Flask REST API backend.
 */

const API_BASE = '/api';

function getToken() {
  try {
    return localStorage.getItem('career_navigator_token');
  } catch (e) {
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
  } catch (e) {
    console.warn('LocalStorage access restricted', e);
  }
}

async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = options.headers ? { ...options.headers } : {};

  // Don't set Content-Type for FormData (browser sets boundary automatically)
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, config);

    let data;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      data = { message: text };
    }

    if (!response.ok) {
      const errorMsg = data?.message || data?.error || `HTTP ${response.status} Error`;
      const error = new Error(errorMsg);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    // Re-throw with consistent shape so UI try/catch can display friendly messages
    if (!err.status && err.name === 'TypeError') {
      const networkError = new Error('Network error: Unable to connect to backend server.');
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

  getCareerDetail: (careerId) => request(`/careers/${careerId}`),

  getCareerRecommendations: (domain = null, limit = null) => {
    let query = '';
    const params = new URLSearchParams();
    if (domain) params.append('domain', domain);
    if (limit) params.append('limit', limit);
    if (params.toString()) query = `?${params.toString()}`;
    return request(`/careers/recommendations${query}`);
  },

  getSkillGap: (careerId) => request(`/careers/${careerId}/skill-gap`),

  getRoadmap: (careerId, hoursPerWeek = null) => {
    const query = hoursPerWeek ? `?hours_per_week=${hoursPerWeek}` : '';
    return request(`/careers/${careerId}/roadmap${query}`);
  },

  compareCareers: (careerAId, careerBId) =>
    request(`/careers/compare?career_a_id=${careerAId}&career_b_id=${careerBId}`),

  getCareerPathways: (careerId, options = {}) => {
    const { hoursPerWeek = 10, userId = null } = options;
    const params = new URLSearchParams();
    if (hoursPerWeek) params.append('hours_per_week', hoursPerWeek);
    if (userId) params.append('user_id', userId);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/careers/${careerId}/pathways${query}`);
  },

  simulateSkillImpact: (careerId, options = {}) => {
    const { skillId, skillName, simulatedLevel, hoursPerWeek = 10, userId = null } = options;
    return request(`/careers/${careerId}/simulate-skill`, {
      method: 'POST',
      body: JSON.stringify({
        skill_id: skillId,
        skill_name: skillName,
        simulated_level: simulatedLevel,
        hours_per_week: hoursPerWeek,
        user_id: userId,
      }),
    });
  },

  getCareerSkillRoi: (careerId, options = {}) => {
    const { hoursPerWeek = 10, userId = null } = options;
    const params = new URLSearchParams();
    if (hoursPerWeek) params.append('hours_per_week', hoursPerWeek);
    if (userId) params.append('user_id', userId);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/careers/${careerId}/skill-roi${query}`);
  },

  runCounterfactualAnalysis: (careerId, options = {}) => {
    const { skillId, skillName, targetLevel = null, hoursPerWeek = 10, userId = null } = options;
    return request(`/careers/${careerId}/counterfactual`, {
      method: 'POST',
      body: JSON.stringify({
        skill_id: skillId,
        skill_name: skillName,
        target_level: targetLevel,
        hours_per_week: hoursPerWeek,
        user_id: userId,
      }),
    });
  },

  getPortfolioProjectRecommendations: (careerId, options = {}) => {
    const { difficulty = null, limit = null, userId = null } = options;
    const params = new URLSearchParams();
    if (difficulty) params.append('difficulty', difficulty);
    if (limit) params.append('limit', limit);
    if (userId) params.append('user_id', userId);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/careers/${careerId}/portfolio-recommendations${query}`);
  },

  getCareerAcademicBenchmark: (careerId, options = {}) => {
    const { program = null, userId = null } = options;
    const params = new URLSearchParams();
    if (program) params.append('program', program);
    if (userId) params.append('user_id', userId);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/careers/${careerId}/academic-benchmark${query}`);
  },

  getCareerIndustryDemand: (careerId, options = {}) => {
    const { trend = null, demandLevel = null, limit = null, userId = null } = options;
    const params = new URLSearchParams();
    if (trend) params.append('trend', trend);
    if (demandLevel) params.append('demand_level', demandLevel);
    if (limit) params.append('limit', limit);
    if (userId) params.append('user_id', userId);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/careers/${careerId}/industry-demand${query}`);
  },

  getCareerTrajectory: (careerId, options = {}) => {
    const { fromCareerId = null, objective = 'BEST_FIT', maxHops = 3, limit = 3, userId = null } = options;
    const params = new URLSearchParams();
    if (fromCareerId) params.append('from_career_id', fromCareerId);
    if (objective) params.append('objective', objective);
    if (maxHops) params.append('max_hops', maxHops);
    if (limit) params.append('limit', limit);
    if (userId) params.append('user_id', userId);
    const query = params.toString() ? `?${params.toString()}` : '';
    return request(`/careers/${careerId}/trajectory${query}`);
  },



  getCareerAnalytics: (careerId) => request(`/careers/${careerId}/analytics`),

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
    const query = hoursPerWeek ? `?hours_per_week=${hoursPerWeek}` : '';
    return request(`/careers/${careerId}/readiness-summary${query}`);
  },

  // Career Market Outlook
  getCareerMarketOutlook: (careerId) => request(`/careers/${careerId}/market-outlook`),
  listMarketOutlooks: () => request('/careers/market-outlook'),
  compareMarketOutlooks: (careerIds) =>
    request('/careers/market-outlook/compare', {
      method: 'POST',
      body: JSON.stringify({ career_ids: careerIds }),
    }),

  // Learning Resources & Progress
  listLearningResources: (params = {}) => {
    const q = new URLSearchParams();
    if (params.canonical_skill_id) q.append('canonical_skill_id', params.canonical_skill_id);
    if (params.difficulty) q.append('difficulty', params.difficulty);
    if (params.type) q.append('type', params.type);
    if (params.q) q.append('q', params.q);
    const queryString = q.toString() ? `?${q.toString()}` : '';
    return request(`/learning-resources${queryString}`);
  },

  startLearningResource: (resourceId) =>
    request(`/learning-resources/${resourceId}/start`, { method: 'POST' }),

  updateLearningProgress: (resourceId, progress_percentage, notes = null) =>
    request(`/learning-resources/${resourceId}/progress`, {
      method: 'PUT',
      body: JSON.stringify({ progress_percentage, notes }),
    }),

  completeLearningResource: (resourceId) =>
    request(`/learning-resources/${resourceId}/complete`, { method: 'POST' }),

  getUserLearningProgress: (status = null) => {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return request(`/learning-resources/progress${query}`);
  },

  getSkillProgress: (skillId) =>
    request(`/skills/canonical/${skillId}/progress`),

  // Live Job Opportunities & Career Action Center
  listLiveJobs: (params = {}) => {
    const q = new URLSearchParams();
    if (params.q || params.query) q.append('q', params.q || params.query);
    if (params.location) q.append('location', params.location);
    if (params.work_mode) q.append('work_mode', params.work_mode);
    if (params.experience) q.append('experience', params.experience);
    if (params.technology || params.tech) q.append('technology', params.technology || params.tech);
    if (params.provider) q.append('provider', params.provider);
    if (params.source_key) q.append('source_key', params.source_key);
    if (params.page) q.append('page', params.page);
    if (params.page_size) q.append('page_size', params.page_size);
    const queryString = q.toString() ? `?${q.toString()}` : '';
    return request(`/jobs${queryString}`);
  },

  getLiveJobSources: () => request('/jobs/sources'),

  getLiveJobDetails: (sourceKey, providerId) =>
    request(`/jobs/${encodeURIComponent(sourceKey)}/${encodeURIComponent(providerId)}`),

  matchLiveJob: (sourceKey, providerId, payload = {}) =>
    request(`/jobs/${encodeURIComponent(sourceKey)}/${encodeURIComponent(providerId)}/match`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  matchCustomJob: (payload) =>
    request('/jobs/match-custom', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getJobActionCenter: (sourceKey, providerId, options = {}) => {
    const { fromCareerId = null, skills = null } = options;
    const q = new URLSearchParams();
    if (fromCareerId) q.append('from_career_id', fromCareerId);
    const queryString = q.toString() ? `?${q.toString()}` : '';

    if (skills && Array.isArray(skills)) {
      return request(`/jobs/${encodeURIComponent(sourceKey)}/${encodeURIComponent(providerId)}/action-center${queryString}`, {
        method: 'POST',
        body: JSON.stringify({ skills }),
      });
    }
    return request(`/jobs/${encodeURIComponent(sourceKey)}/${encodeURIComponent(providerId)}/action-center${queryString}`);
  },

  getSqlDiagnostic: () => request('/jobs/diagnostics/sql'),

  evaluateSqlDiagnostic: (answers) =>
    request('/jobs/diagnostics/sql/evaluate', {
      method: 'POST',
      body: JSON.stringify({ answers }),
    }),

  // Practical Skill Assessment & Hands-On Task Engine
  listPracticalTasks: (params = {}) => {
    const q = new URLSearchParams();
    if (params.career_id || params.careerId) q.append('career_id', params.career_id || params.careerId);
    if (params.difficulty) q.append('difficulty', params.difficulty);
    if (params.skill) q.append('skill', params.skill);
    if (params.category) q.append('category', params.category);
    if (params.job_source || params.jobSource) q.append('job_source', params.job_source || params.jobSource);
    if (params.job_id || params.jobId) q.append('job_id', params.job_id || params.jobId);
    if (params.limit) q.append('limit', params.limit);
    const queryString = q.toString() ? `?${q.toString()}` : '';
    return request(`/practical-tasks${queryString}`);
  },

  getPracticalTask: (taskId) =>
    request(`/practical-tasks/${encodeURIComponent(taskId)}`),

  evaluatePracticalTask: (payload) =>
    request('/practical-tasks/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getCareerPracticalTasks: (careerId, params = {}) => {
    const q = new URLSearchParams();
    if (params.difficulty) q.append('difficulty', params.difficulty);
    if (params.skill) q.append('skill', params.skill);
    if (params.category) q.append('category', params.category);
    if (params.job_source || params.jobSource) q.append('job_source', params.job_source || params.jobSource);
    if (params.job_id || params.jobId) q.append('job_id', params.job_id || params.jobId);
    if (params.limit) q.append('limit', params.limit);
    const queryString = q.toString() ? `?${q.toString()}` : '';
    return request(`/careers/${careerId}/practical-tasks${queryString}`);
  },
};
