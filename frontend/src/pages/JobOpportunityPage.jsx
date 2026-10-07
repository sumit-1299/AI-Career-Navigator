import React from 'react';
import { JobOpportunityExplorer } from '../components/analytics/JobOpportunityExplorer';
import { Briefcase, Compass, ShieldCheck } from 'lucide-react';

export function JobOpportunityPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <div className="flex items-center gap-2 text-primary-600 font-semibold text-xs tracking-wider uppercase">
            <Compass className="w-4 h-4" />
            <span>Phase 12.2 Intelligence</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            Live Job Opportunities & Career Action Center
          </h1>
          <p className="text-sm text-slate-600 mt-1 max-w-3xl">
            Discover active technology openings from verified employer boards, evaluate personalized vacancy skill match,
            prioritize high-ROI missing competencies, and explore tailored capstone projects and interview readiness actions.
          </p>
        </div>
      </div>

      {/* Main Action Center Experience */}
      <JobOpportunityExplorer />
    </div>
  );
}

export default JobOpportunityPage;
