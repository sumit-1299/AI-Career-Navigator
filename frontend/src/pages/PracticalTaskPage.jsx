import React from 'react';
import { PracticalTaskExplorer } from '../components/analytics/PracticalTaskExplorer';
import { CheckSquare, Compass } from 'lucide-react';

export function PracticalTaskPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <div className="flex items-center gap-2 text-primary-600 font-semibold text-xs tracking-wider uppercase">
            <Compass className="w-4 h-4" />
            <span>Phase 12.3 Practical Intelligence</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            Practical Skill Assessment & Hands-On Tasks
          </h1>
          <p className="text-sm text-slate-600 mt-1 max-w-3xl">
            Tackle concrete technical tasks covering real-world scenarios across the 10 canonical IT career tracks.
            Receive immediate, deterministic educational evaluation, concept coverage diagnostics, and skill evidence.
          </p>
        </div>
      </div>

      {/* Main Practical Tasks Experience */}
      <PracticalTaskExplorer />
    </div>
  );
}

export default PracticalTaskPage;
