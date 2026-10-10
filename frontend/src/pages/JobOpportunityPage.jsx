import React from 'react';
import { JobOpportunityExplorer } from '../components/analytics/JobOpportunityExplorer';
import { SectionHeader } from '../components/common/SectionHeader';
import { Badge } from '../components/common/Badge';

export function JobOpportunityPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        badge="Live Job Market Intelligence"
        title="Live Job Opportunities & Career Action Center"
        subtitle="Discover active technology openings from verified employer boards, evaluate personalized vacancy skill match, prioritize high-ROI missing competencies, and explore tailored capstone projects and interview readiness actions."
        action={
          <Badge variant="primary" size="md">
            Phase 12.2 Action Center
          </Badge>
        }
      />
      <JobOpportunityExplorer />
    </div>
  );
}

export default JobOpportunityPage;
