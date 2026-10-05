import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import {
  GraduationCap,
  Briefcase,
  Save,
} from 'lucide-react';

export function ProfilePage() {
  const { user, profile, setProfile, preferences, setPreferences } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Profile fields
  const [educationLevel, setEducationLevel] = useState('');
  const [major, setMajor] = useState('');
  const [graduationYear, setGraduationYear] = useState('');
  const [interests, setInterests] = useState('');

  // Career Preferences fields
  const [targetRole, setTargetRole] = useState('');
  const [preferredDomain, setPreferredDomain] = useState('');
  const [experienceLevel, setExperienceLevel] = useState('Entry-Level');

  useEffect(() => {
    loadUserData();
  }, []);

  async function loadUserData() {
    setLoading(true);
    setError(null);
    try {
      try {
        const profRes = await api.getProfile();
        if (profRes?.profile) {
          const p = profRes.profile;
          setEducationLevel(p.education || p.education_level || '');
          setMajor(p.specialization || p.major || '');
          setGraduationYear(p.graduation_year || '');
          setInterests(Array.isArray(p.interests) ? p.interests.join(', ') : p.interests || '');
          setProfile(p);
        }
      } catch (err) {
        // Profile not created yet
      }

      try {
        const prefRes = await api.getPreferences();
        if (prefRes?.career_preferences) {
          const cp = prefRes.career_preferences;
          setTargetRole(cp.target_role || '');
          setPreferredDomain(cp.preferred_domain || '');
          setExperienceLevel(cp.experience_level || 'Entry-Level');
          setPreferences(cp);
        }
      } catch (err) {
        // Preferences not set yet
      }
    } catch (err) {
      console.warn('Error loading profile', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const profileData = {
        education: educationLevel,
        education_level: educationLevel,
        specialization: major,
        major: major,
        graduation_year: graduationYear ? Number(graduationYear) : null,
        interests: interests.split(',').map((s) => s.trim()).filter(Boolean),
      };

      try {
        const pRes = await api.updateProfile(profileData);
        if (pRes?.profile) setProfile(pRes.profile);
      } catch (err) {
        const pRes = await api.createProfile(profileData);
        if (pRes?.profile) setProfile(pRes.profile);
      }

      const prefData = {
        target_role: targetRole,
        preferred_domain: preferredDomain,
        experience_level: experienceLevel,
      };
      const prefRes = await api.savePreferences(prefData);
      if (prefRes?.career_preferences) setPreferences(prefRes.career_preferences);

      setSuccessMsg('Academic profile and career preferences saved successfully!');
    } catch (err) {
      setError(err.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
                User Credentials & Objectives
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              Student Profile & Career Preferences
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              Configure your academic background and desired career trajectory.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold">
              {user?.name ? user.name[0].toUpperCase() : 'U'}
            </div>
            <div>
              <p className="font-bold text-sm text-slate-800">{user?.name || 'Student'}</p>
              <p className="text-xs text-slate-400">{user?.email}</p>
            </div>
          </div>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}
      {successMsg && <Alert type="success" message={successMsg} />}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Spinner size="lg" />
          <p className="mt-4 text-slate-500 font-medium">Loading student credentials...</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Section 1: Academic Background */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
              <GraduationCap className="w-5 h-5 text-primary-600" />
              <h2 className="text-base font-bold text-slate-900">Academic Background</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Degree / Education Level
                </label>
                <select
                  value={educationLevel}
                  onChange={(e) => setEducationLevel(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white text-sm"
                >
                  <option value="">Select Level</option>
                  <option value="High School">High School</option>
                  <option value="Associate">Associate Degree</option>
                  <option value="Bachelor's">Bachelor's Degree</option>
                  <option value="Master's">Master's Degree</option>
                  <option value="PhD">Doctorate / PhD</option>
                  <option value="Self-Taught">Self-Taught / Bootcamp</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Academic Major / Specialization
                </label>
                <input
                  type="text"
                  placeholder="e.g. Computer Science, Information Systems"
                  value={major}
                  onChange={(e) => setMajor(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Expected Graduation Year
                </label>
                <input
                  type="number"
                  placeholder="2026"
                  min="1990"
                  max="2035"
                  value={graduationYear}
                  onChange={(e) => setGraduationYear(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Academic Interests (Comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Artificial Intelligence, Distributed Systems, Cloud"
                  value={interests}
                  onChange={(e) => setInterests(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white text-sm"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Career Preferences */}
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
              <Briefcase className="w-5 h-5 text-indigo-600" />
              <h2 className="text-base font-bold text-slate-900">Career Preferences & Objectives</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Target Role Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Machine Learning Engineer"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Preferred Industry Domain
                </label>
                <select
                  value={preferredDomain}
                  onChange={(e) => setPreferredDomain(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white text-sm"
                >
                  <option value="">Any Domain</option>
                  <option value="Data Science & AI">Data Science & AI</option>
                  <option value="Software Engineering">Software Engineering</option>
                  <option value="Cloud & DevOps">Cloud & DevOps</option>
                  <option value="Cybersecurity">Cybersecurity</option>
                  <option value="Product & Analytics">Product & Analytics</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Current Experience Level
                </label>
                <select
                  value={experienceLevel}
                  onChange={(e) => setExperienceLevel(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white text-sm"
                >
                  <option value="Student">Student / Intern</option>
                  <option value="Entry-Level">Entry-Level (0–2 yrs)</option>
                  <option value="Mid-Level">Mid-Level (3–5 yrs)</option>
                  <option value="Senior">Senior (5+ yrs)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Submit Action */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-md shadow-primary-600/20 transition flex items-center gap-2"
            >
              {saving ? (
                <>
                  <Spinner size="sm" />
                  <span>Saving Profile...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save All Changes</span>
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
