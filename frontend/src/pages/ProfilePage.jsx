import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import { SectionHeader } from '../components/common/SectionHeader';
import {
  GraduationCap,
  Briefcase,
  Save,
  User,
  Sparkles,
  Target,
  CheckCircle2,
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
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Modernized Header */}
      <SectionHeader
        badge="User Credentials & Objectives"
        title="Student Profile & Career Preferences"
        subtitle="Configure your academic credentials, specialization, and desired career trajectory."
        action={
          <div className="flex items-center gap-3 bg-white p-2 pr-4 rounded-2xl border border-slate-200/90 shadow-subtle">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-xs">
              {user?.name ? user.name[0].toUpperCase() : 'U'}
            </div>
            <div>
              <p className="font-bold text-sm text-slate-800 leading-tight">{user?.name || 'Student'}</p>
              <p className="text-xs text-slate-400">{user?.email}</p>
            </div>
          </div>
        }
      />

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {successMsg && <Alert type="success" message={successMsg} onClose={() => setSuccessMsg(null)} />}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Spinner size="lg" />
          <p className="mt-4 text-slate-500 font-medium">Loading student credentials...</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Section 1: Academic Background */}
          <Card className="p-6 md:p-8 shadow-card">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100">
              <div className="p-2.5 rounded-xl bg-primary-50 text-primary-600">
                <GraduationCap className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Academic Background</h2>
                <p className="text-xs text-slate-500">Your degree level, institution focus, and specialization</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Degree / Education Level
                </label>
                <select
                  value={educationLevel}
                  onChange={(e) => setEducationLevel(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm font-medium transition"
                >
                  <option value="">Select Education Level</option>
                  <option value="High School">High School</option>
                  <option value="Associate">Associate Degree</option>
                  <option value="Bachelor's">Bachelor's Degree</option>
                  <option value="Master's">Master's Degree</option>
                  <option value="PhD">Doctorate / PhD</option>
                  <option value="Self-Taught">Self-Taught / Bootcamp</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Academic Major / Specialization
                </label>
                <input
                  type="text"
                  placeholder="e.g. Computer Science, Information Systems, Software Eng"
                  value={major}
                  onChange={(e) => setMajor(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Expected Graduation Year
                </label>
                <input
                  type="number"
                  placeholder="2026"
                  min="1990"
                  max="2035"
                  value={graduationYear}
                  onChange={(e) => setGraduationYear(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Academic Interests (Comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Artificial Intelligence, Distributed Systems, Cloud"
                  value={interests}
                  onChange={(e) => setInterests(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm transition"
                />
              </div>
            </div>
          </Card>

          {/* Section 2: Career Preferences */}
          <Card className="p-6 md:p-8 shadow-card">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100">
              <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
                <Briefcase className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Career Preferences & Objectives</h2>
                <p className="text-xs text-slate-500">Tailors multi-hop recommendations and job matching to your target path</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Target Role Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Machine Learning Engineer"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Preferred Industry Domain
                </label>
                <select
                  value={preferredDomain}
                  onChange={(e) => setPreferredDomain(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm font-medium transition"
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
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Current Experience Level
                </label>
                <select
                  value={experienceLevel}
                  onChange={(e) => setExperienceLevel(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm font-medium transition"
                >
                  <option value="Student">Student / Intern</option>
                  <option value="Entry-Level">Entry-Level (0–2 yrs)</option>
                  <option value="Mid-Level">Mid-Level (3–5 yrs)</option>
                  <option value="Senior">Senior (5+ yrs)</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Submit Action */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-subtle hover:shadow transition flex items-center gap-2"
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

export default ProfilePage;
