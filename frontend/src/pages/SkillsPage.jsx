import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';
import { ProgressBar } from '../components/common/ProgressBar';
import {
  Sparkles,
  Plus,
  Search,
  CheckCircle,
  BookOpen,
} from 'lucide-react';

export function SkillsPage() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New skill form state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedCanonical, setSelectedCanonical] = useState(null);
  const [proficiency, setProficiency] = useState(5);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadUserSkills();
  }, []);

  async function loadUserSkills() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getUserSkills();
      setSkills(res?.skills || []);
    } catch (err) {
      console.warn('Could not load user skills', err);
    } finally {
      setLoading(false);
    }
  }

  // Canonical skill search debounce
  useEffect(() => {
    if (!searchQuery || searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await api.searchCanonicalSkills(searchQuery.trim());
        const list = Array.isArray(res) ? res : res?.skills || [];
        setSearchResults(list);
      } catch (err) {
        console.warn('Skill autocomplete failed', err);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  async function handleAddSkill(e) {
    e.preventDefault();
    const skillName = selectedCanonical
      ? selectedCanonical.canonical_name || selectedCanonical.skill_name || selectedCanonical.name
      : searchQuery.trim();
    if (!skillName) return;

    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await api.addSkill(skillName, proficiency);
      setSuccessMsg(`Successfully added "${skillName}" (Level ${proficiency}/10)`);
      setSearchQuery('');
      setSelectedCanonical(null);
      setSearchResults([]);
      setProficiency(5);
      await loadUserSkills();
    } catch (err) {
      setError(err.message || 'Failed to add skill');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 md:p-8 shadow-sm border border-slate-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                Student Profile Inventory
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              My Verified Skills
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              Manage your technical & domain competencies. Each skill is mapped to our canonical
              knowledge graph.
            </p>
          </div>
          <span className="text-xs font-semibold px-3 py-1 bg-slate-100 text-slate-700 rounded-full w-fit">
            {skills.length} Skills Logged
          </span>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}
      {successMsg && <Alert type="success" message={successMsg} />}

      {/* Add Skill Form Section */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
        <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-primary-600" />
          <span>Add Skill with Canonical Autocomplete</span>
        </h2>

        <form onSubmit={handleAddSkill} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
            {/* Search Input with dropdown */}
            <div className="md:col-span-2 relative">
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Skill Name (Canonical Search)
              </label>
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="e.g. Python, Machine Learning, React, SQL..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    if (selectedCanonical && e.target.value !== (selectedCanonical.canonical_name || selectedCanonical.name)) {
                      setSelectedCanonical(null);
                    }
                  }}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 text-sm bg-slate-50 focus:bg-white transition"
                  required
                />
                {isSearching && (
                  <div className="absolute right-3.5 top-3.5">
                    <Spinner size="sm" />
                  </div>
                )}
              </div>

              {/* Autocomplete Dropdown */}
              {searchResults.length > 0 && !selectedCanonical && (
                <div className="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-xl shadow-lg max-h-56 overflow-y-auto">
                  <div className="p-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                    Canonical Matches Found
                  </div>
                  {searchResults.map((item) => {
                    const cName = item.canonical_name || item.skill_name || item.name;
                    const cType = item.skill_type || item.category;

                    return (
                      <div
                        key={item.id}
                        onClick={() => {
                          setSelectedCanonical(item);
                          setSearchQuery(cName);
                          setSearchResults([]);
                        }}
                        className="px-3.5 py-2 hover:bg-primary-50 cursor-pointer flex items-center justify-between transition text-sm"
                      >
                        <div>
                          <span className="font-semibold text-slate-800">{cName}</span>
                          {cType && (
                            <span className="text-xs text-slate-400 ml-2">({cType})</span>
                          )}
                        </div>
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">
                          Canonical #{item.id}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}

              {selectedCanonical && (
                <div className="mt-2 text-xs flex items-center gap-1.5 text-emerald-700 font-medium">
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>
                    Linked to Canonical Entity:{' '}
                    <b>
                      {selectedCanonical.canonical_name ||
                        selectedCanonical.skill_name ||
                        selectedCanonical.name}
                    </b>{' '}
                    (ID #{selectedCanonical.id})
                  </span>
                </div>
              )}
            </div>

            {/* Proficiency Slider */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Proficiency: {proficiency}/10
                </label>
                <span className="text-xs font-bold text-primary-600">
                  {proficiency <= 3
                    ? 'Beginner'
                    : proficiency <= 7
                    ? 'Intermediate'
                    : 'Advanced'}
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={proficiency}
                onChange={(e) => setProficiency(Number(e.target.value))}
                className="w-full accent-primary-600 cursor-pointer h-2 bg-slate-200 rounded-lg appearance-none mt-2"
              />
              <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                <span>1 (Novice)</span>
                <span>5 (Competent)</span>
                <span>10 (Expert)</span>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={submitting || !searchQuery.trim()}
              className="px-5 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-md shadow-primary-600/20 transition flex items-center gap-2"
            >
              {submitting ? (
                <span>Adding...</span>
              ) : (
                <>
                  <Plus className="w-4 h-4" />
                  <span>Add to Profile</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Skills Inventory Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16">
          <Spinner size="lg" />
          <p className="mt-3 text-slate-500 text-sm">Loading skills inventory...</p>
        </div>
      ) : skills.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
          <Sparkles className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No skills added yet</h3>
          <p className="text-xs text-slate-500 mt-1">
            Search canonical skills above or upload your resume to populate your profile.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {skills.map((s) => {
            const canonical = s.canonical_skill;
            return (
              <div
                key={s.id}
                className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-base text-slate-900">{s.skill_name}</h3>
                    <Badge variant={s.proficiency >= 7 ? 'success' : s.proficiency >= 4 ? 'info' : 'warning'}>
                      Level {s.proficiency}/10
                    </Badge>
                  </div>

                  {canonical ? (
                    <p className="text-xs text-slate-400">
                      Canonical: <span className="text-slate-600 font-medium">{canonical.name || canonical.canonical_name}</span>
                    </p>
                  ) : (
                    <p className="text-xs text-slate-400">Custom user skill</p>
                  )}

                  <div className="mt-3">
                    <ProgressBar
                      value={s.proficiency}
                      max={10}
                      color={
                        s.proficiency >= 7
                          ? 'bg-emerald-500'
                          : s.proficiency >= 4
                          ? 'bg-primary-500'
                          : 'bg-amber-500'
                      }
                    />
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-400">
                    {s.proficiency >= 8
                      ? 'Advanced Mastery'
                      : s.proficiency >= 5
                      ? 'Workplace Ready'
                      : 'Developing'}
                  </span>
                  {(canonical?.id || s.canonical_skill_id) && (
                    <a
                      href={`/learning?skill_id=${canonical?.id || s.canonical_skill_id}`}
                      className="text-primary-600 font-semibold hover:underline flex items-center gap-1"
                    >
                      <BookOpen className="w-3 h-3" /> Modules
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
