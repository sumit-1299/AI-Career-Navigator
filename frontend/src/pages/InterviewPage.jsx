import React from 'react';
import { CareerInterviewSimulator } from '../components/analytics/CareerInterviewSimulator';
import { SectionHeader } from '../components/common/SectionHeader';
import { Badge } from '../components/common/Badge';

export function InterviewPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        badge="Career Readiness Simulation"
        title="AI Interview Simulation & Rubric Assessment"
        subtitle="Practice role-specific technical, system architecture, and scenario-based interview questions with deterministic multi-criteria rubric evaluation."
        action={
          <Badge variant="primary" size="md">
            Phase 11.6 Assessment Engine
          </Badge>
        }
      />
      <CareerInterviewSimulator />
    </div>
  );
}

export default InterviewPage;
