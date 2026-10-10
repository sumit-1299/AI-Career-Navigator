import React from 'react';
import { PracticalTaskExplorer } from '../components/analytics/PracticalTaskExplorer';
import { SectionHeader } from '../components/common/SectionHeader';
import { Badge } from '../components/common/Badge';

export function PracticalTaskPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <SectionHeader
        badge="Hands-On Skill Engine"
        title="Practical Skill Assessment & Tasks"
        subtitle="Tackle concrete technical tasks covering real-world scenarios across the 10 canonical IT career tracks. Receive immediate, deterministic educational evaluation, concept coverage diagnostics, and verified skill evidence."
        action={
          <Badge variant="success" size="md">
            Phase 12.3 Task Engine
          </Badge>
        }
      />
      <PracticalTaskExplorer />
    </div>
  );
}

export default PracticalTaskPage;
