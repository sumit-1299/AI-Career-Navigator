import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Spinner, Alert } from '../components/common/UIFeedback';
import { Badge } from '../components/common/Badge';
import { Card, MetricCard } from '../components/common/Card';
import { SectionHeader } from '../components/common/SectionHeader';
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Check,
  Target,
  Award,
  XCircle,
  ArrowLeft,
  ChevronRight,
  Sliders,
} from 'lucide-react';

export function ResumePage() {
  const { targetCareerId } = useAuth();
  const [careers, setCareers] = useState([]);
  const [selectedCareerId, setSelectedCareerId] = useState(targetCareerId || 1);

  const [inputMode, setInputMode] = useState('file'); // 'file' | 'text'
  const [selectedFile, setSelectedFile] = useState(null);
  const [rawText, setRawText] = useState('');
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState(null);

  // ATS scoring state
  const [atsResult, setAtsResult] = useState(null);
  const [atsLoading, setAtsLoading] = useState(false);
  const [atsError, setAtsError] = useState(null);

  // Extraction results
  const [results, setResults] = useState(null);
  const [selectedProficiencies, setSelectedProficiencies] = useState({});
  const [resolvedAmbiguous, setResolvedAmbiguous] = useState({});
  const [applying, setApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState(null);

  useEffect(() => {
    api.listCareers().then((res) => {
      if (res?.careers) setCareers(res.careers);
    }).catch(() => {});
  }, []);

  async function handleExtract(e) {
    e.preventDefault();
    setExtractError(null);
    setResults(null);
    setApplySuccess(null);
    setAtsResult(null);
    setAtsError(null);

    const input = inputMode === 'file' ? selectedFile : rawText;
    if (!input) {
      setExtractError('Please provide a file or resume text');
      return;
    }

    setExtracting(true);
    try {
      const data = await api.extractResume(input);
      setResults(data);

      const profs = {};
      (data?.matched_canonical_skills || []).forEach((m) => {
        profs[m.canonical_id] = 5;
      });
      setSelectedProficiencies(profs);

      // Automatically trigger ATS score for target career
      handleScoreResume(selectedCareerId);
    } catch (err) {
      setExtractError(err.message || 'Failed to extract resume skills');
    } finally {
      setExtracting(false);
    }
  }

  async function handleScoreResume(careerIdToScore) {
    const input = inputMode === 'file' ? selectedFile : rawText;
    if (!input) return;
    const cid = careerIdToScore || selectedCareerId;
    setAtsLoading(true);
    setAtsError(null);
    try {
      const scoreData = await api.scoreResume(cid, input);
      setAtsResult(scoreData);
    } catch (err) {
      setAtsError(err.message || 'Failed to calculate ATS score');
    } finally {
      setAtsLoading(false);
    }
  }

  async function handleApplyToProfile() {
    if (!results) return;
    setApplying(true);
    setExtractError(null);
    try {
      const skillsToApply = [];

      (results.matched_canonical_skills || []).forEach((m) => {
        skillsToApply.push({
          canonical_id: m.canonical_id,
          skill_name: m.canonical_name,
          proficiency: selectedProficiencies[m.canonical_id] || 5,
        });
      });

      (results.ambiguous_skills || []).forEach((amb, idx) => {
        const chosenId = resolvedAmbiguous[idx];
        if (chosenId) {
          const candidate = amb.candidates?.find((c) => c.canonical_id === Number(chosenId));
          if (candidate) {
            skillsToApply.push({
              canonical_id: candidate.canonical_id,
              skill_name: candidate.canonical_name,
              proficiency: selectedProficiencies[candidate.canonical_id] || 5,
            });
          }
        }
      });

      const res = await api.applyResumeSkills(skillsToApply);
      setApplySuccess(
        `Applied ${res?.applied_count ?? skillsToApply.length} skills directly to your profile!`
      );
    } catch (err) {
      setExtractError(err.message || 'Failed to apply skills to profile');
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Modernized Header */}
      <SectionHeader
        badge="Resume Intelligence & Extraction"
        title="Multi-Format Resume Ingestion"
        subtitle="Upload your resume (.PDF, .DOCX, or .TXT) to automatically extract, canonicalize, and link competencies to your career profile."
      />

      {extractError && <Alert type="error" message={extractError} onClose={() => setExtractError(null)} />}
      {applySuccess && <Alert type="success" message={applySuccess} onClose={() => setApplySuccess(null)} />}

      {/* Upload Box */}
      {!results && (
        <Card className="p-6 md:p-8 shadow-card">
          <div className="flex bg-slate-100/80 p-1 rounded-xl w-fit mb-6">
            <button
              type="button"
              onClick={() => setInputMode('file')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                inputMode === 'file'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Upload Document (.pdf, .docx, .txt)
            </button>
            <button
              type="button"
              onClick={() => setInputMode('text')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition ${
                inputMode === 'text'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Paste Resume Text
            </button>
          </div>

          <form onSubmit={handleExtract} className="space-y-6">
            {inputMode === 'file' ? (
              <div className="border-2 border-dashed border-slate-200 hover:border-primary-400 rounded-2xl p-10 text-center bg-slate-50/40 hover:bg-slate-50 transition">
                <div className="w-16 h-16 rounded-2xl bg-primary-50 text-primary-600 flex items-center justify-center mx-auto mb-4">
                  <UploadCloud className="w-8 h-8" />
                </div>
                <h3 className="text-base font-bold text-slate-900">
                  {selectedFile ? selectedFile.name : 'Select or drop your resume document'}
                </h3>
                <p className="text-xs text-slate-500 mt-1 mb-5">
                  Supported formats: PDF (.pdf), Microsoft Word (.docx), Plain Text (.txt)
                </p>
                <input
                  type="file"
                  id="resume-file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setSelectedFile(e.target.files[0])}
                  className="hidden"
                />
                <label
                  htmlFor="resume-file"
                  className="cursor-pointer inline-flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-subtle hover:shadow transition"
                >
                  <FileText className="w-4 h-4 text-primary-600" />
                  <span>{selectedFile ? 'Change File' : 'Browse Files'}</span>
                </label>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Paste Resume Content
                </label>
                <textarea
                  rows={9}
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  placeholder="Paste work experience, skills inventory, projects, education..."
                  className="w-full p-4 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 font-mono bg-slate-50/50 focus:bg-white transition"
                  required
                />
              </div>
            )}

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={extracting || (inputMode === 'file' ? !selectedFile : !rawText.trim())}
                className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-subtle hover:shadow transition flex items-center gap-2"
              >
                {extracting ? (
                  <>
                    <Spinner size="sm" />
                    <span>Parsing & Canonicalizing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Extract & Match Skills</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </Card>
      )}

      {/* Review Screen */}
      {results && (
        <div className="space-y-6 animate-fadeIn">
          {/* Summary Metric Strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="Extracted Terms"
              value={results.summary?.total_extracted ?? results.extracted_skills?.length ?? 0}
              subtext="Raw tokens parsed"
            />
            <MetricCard
              label="Auto-Matched Canonical"
              value={results.summary?.exact_matches ?? results.matched_canonical_skills?.length ?? 0}
              subtext="Mapped to knowledge base"
              trend={{ positive: true, label: 'High confidence' }}
            />
            <MetricCard
              label="Ambiguous Candidates"
              value={results.summary?.ambiguous_matches ?? results.ambiguous_skills?.length ?? 0}
              subtext="Needs user confirmation"
              trend={{ positive: false, label: 'Requires review' }}
            />
            <MetricCard
              label="Unmatched Terms"
              value={results.summary?.unmatched ?? results.unmatched_skills?.length ?? 0}
              subtext="Domain non-specific"
            />
          </div>

          {/* Section 0: Target Career ATS Alignment & Match Score */}
          <Card className="p-6 md:p-7 shadow-card">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
                  <Target className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Target Career ATS Match & Keyword Alignment
                  </h3>
                  <p className="text-xs text-slate-500">
                    Compare resume keywords directly against your target career's required competencies.
                  </p>
                </div>
              </div>

              {/* Career Selector & Rescore Button */}
              <div className="flex items-center gap-2">
                <select
                  value={selectedCareerId}
                  onChange={(e) => {
                    const cid = Number(e.target.value);
                    setSelectedCareerId(cid);
                    handleScoreResume(cid);
                  }}
                  className="px-3.5 py-2 rounded-xl border border-slate-300 text-xs font-semibold text-slate-800 bg-white"
                >
                  {careers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.career_name || c.title}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => handleScoreResume(selectedCareerId)}
                  disabled={atsLoading}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-subtle transition"
                >
                  {atsLoading ? 'Scoring...' : 'Score ATS'}
                </button>
              </div>
            </div>

            {atsError && (
              <div className="mt-4">
                <Alert type="error" message={atsError} />
              </div>
            )}

            {atsLoading && (
              <div className="py-8 flex flex-col items-center justify-center">
                <Spinner size="md" />
                <p className="text-xs text-slate-500 mt-2 font-medium">Computing ATS keyword alignment...</p>
              </div>
            )}

            {atsResult && !atsLoading && (
              <div className="mt-5 space-y-5">
                {/* Score & Alignment Banner */}
                <div className="p-4 bg-gradient-to-r from-slate-50 to-indigo-50/40 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="text-center sm:text-left">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                        ATS Match Score
                      </span>
                      <div className="text-3xl font-black text-indigo-600">
                        {atsResult.ats_score}%
                      </div>
                    </div>
                    <div className="h-10 w-px bg-slate-200 hidden sm:block" />
                    <div>
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                        Alignment Level
                      </span>
                      <Badge
                        variant={
                          atsResult.alignment_level === 'Excellent'
                            ? 'success'
                            : atsResult.alignment_level === 'Strong'
                            ? 'primary'
                            : atsResult.alignment_level === 'Moderate'
                            ? 'warning'
                            : 'error'
                        }
                        size="md"
                      >
                        <Award className="w-3.5 h-3.5 mr-1" />
                        {atsResult.alignment_level} Alignment
                      </Badge>
                    </div>
                  </div>

                  <div className="text-xs text-slate-600 font-medium">
                    Target: <span className="font-bold text-slate-900">{atsResult.career_title}</span> •{' '}
                    {atsResult.matched_count} of {atsResult.total_required_skills} required skills matched
                  </div>
                </div>

                {/* Matched vs Missing Keywords Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Matched Keywords */}
                  <div className="p-4 bg-emerald-50/40 rounded-xl border border-emerald-200">
                    <div className="flex items-center justify-between mb-2.5">
                      <span className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        Matched Required Keywords ({atsResult.matched_keywords?.length || 0})
                      </span>
                    </div>
                    {atsResult.matched_keywords?.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {atsResult.matched_keywords.map((kw, i) => (
                          <span
                            key={i}
                            className="px-2.5 py-1 bg-white text-emerald-800 border border-emerald-200 rounded-lg text-xs font-medium shadow-xs"
                          >
                            ✓ {kw}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-emerald-700 italic">No direct required keywords matched yet.</p>
                    )}
                  </div>

                  {/* Missing Keywords */}
                  <div className="p-4 bg-rose-50/40 rounded-xl border border-rose-200">
                    <div className="flex items-center justify-between mb-2.5">
                      <span className="text-xs font-bold text-rose-900 flex items-center gap-1.5">
                        <XCircle className="w-4 h-4 text-rose-600" />
                        Missing Role Keywords ({atsResult.missing_keywords?.length || 0})
                      </span>
                    </div>
                    {atsResult.missing_keywords?.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {atsResult.missing_keywords.map((kw, i) => (
                          <span
                            key={i}
                            className="px-2.5 py-1 bg-white text-rose-800 border border-rose-200 rounded-lg text-xs font-medium shadow-xs"
                          >
                            ✕ {kw}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-emerald-700 font-medium">
                        All required keywords for this role are covered!
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </Card>

          {/* Section 1: Auto-Matched Canonical Skills */}
          <Card className="p-6 md:p-7 shadow-card">
            <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span>
                Canonical Matches ({results.matched_canonical_skills?.length || 0})
              </span>
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              These skills were matched to the knowledge base with high confidence. Adjust
              self-assessed proficiency before saving.
            </p>

            <div className="space-y-3">
              {results.matched_canonical_skills?.map((item) => (
                <div
                  key={item.canonical_id}
                  className="p-4 bg-slate-50/60 hover:bg-slate-50 rounded-xl border border-slate-200/80 flex flex-col md:flex-row md:items-center justify-between gap-3 transition"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-sm text-slate-900">{item.canonical_name}</h4>
                      <Badge variant="success" size="xs">
                        {Math.round((item.confidence || 1) * 100)}% Match
                      </Badge>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Extracted from: "{item.source_skill}" • Match type: {item.match_type || 'exact'}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <label className="text-xs font-semibold text-slate-600 shrink-0">
                      Proficiency: {selectedProficiencies[item.canonical_id] || 5}/10
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={selectedProficiencies[item.canonical_id] || 5}
                      onChange={(e) =>
                        setSelectedProficiencies((prev) => ({
                          ...prev,
                          [item.canonical_id]: Number(e.target.value),
                        }))
                      }
                      className="accent-primary-600 w-32 cursor-pointer h-2 bg-slate-200 rounded-lg appearance-none"
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Section 2: Ambiguous Skills Needing Review */}
          {results.ambiguous_skills?.length > 0 && (
            <Card className="p-6 md:p-7 shadow-card">
              <h3 className="text-base font-bold text-slate-900 mb-1 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-amber-600" />
                <span>Review Ambiguous Skills ({results.ambiguous_skills.length})</span>
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Select the intended canonical skill entity from candidates:
              </p>

              <div className="space-y-3">
                {results.ambiguous_skills.map((amb, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-amber-50/40 rounded-xl border border-amber-200/80 flex flex-col md:flex-row md:items-center justify-between gap-3"
                  >
                    <div>
                      <p className="font-bold text-sm text-slate-900">"{amb.source_skill}"</p>
                      <p className="text-[11px] text-amber-700">Multiple entity candidates identified</p>
                    </div>

                    <div className="flex items-center gap-2">
                      <select
                        value={resolvedAmbiguous[idx] || ''}
                        onChange={(e) =>
                          setResolvedAmbiguous((prev) => ({
                            ...prev,
                            [idx]: e.target.value,
                          }))
                        }
                        className="px-3.5 py-2 rounded-xl border border-slate-300 text-xs bg-white font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                      >
                        <option value="">-- Choose Canonical Skill --</option>
                        {amb.candidates?.map((c) => (
                          <option key={c.canonical_id} value={c.canonical_id}>
                            {c.canonical_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Action Bar */}
          <Card className="p-4 shadow-card flex items-center justify-between">
            <button
              onClick={() => {
                setResults(null);
                setSelectedFile(null);
                setRawText('');
              }}
              className="px-4 py-2.5 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl flex items-center gap-1.5 transition"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Upload Another Resume</span>
            </button>

            <button
              onClick={handleApplyToProfile}
              disabled={applying}
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-subtle hover:shadow transition flex items-center gap-2"
            >
              {applying ? (
                <>
                  <Spinner size="sm" />
                  <span>Applying to Profile...</span>
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>Apply Skills to My Profile</span>
                </>
              )}
            </button>
          </Card>
        </div>
      )}
    </div>
  );
}

export default ResumePage;
