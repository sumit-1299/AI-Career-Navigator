"""
Student Analytics and Career Readiness Velocity Service for AI Career Navigator.

Tracks student progress over time, calculates baseline vs current readiness,
computes readiness improvement, learning velocity, and estimates time to target career readiness.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from models.career import Career
from models.canonical_skill import CanonicalSkill
from models.learning_resource import LearningResource
from models.skill import Skill
from models.user import User
from models.user_learning_progress import UserLearningProgress
from services.skill_gap_service import SkillGapService, SkillGapStatus
from utils.normalization import normalize_skill_name


class StudentAnalyticsService:
    """Service providing career readiness analytics, velocity metrics, and learning timeline."""

    @classmethod
    def get_student_career_analytics(
        cls,
        user_id: int,
        career_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates comprehensive career readiness analytics and velocity for a student
        targeting a specific career track.
        """
        career = Career.query.get(career_id)
        if not career:
            return None

        user = User.query.get(user_id)
        if not user:
            return None

        # Fetch student current skills and learning progress records
        current_skills = Skill.query.filter_by(user_id=user_id).all()
        progress_records = (
            UserLearningProgress.query.filter_by(user_id=user_id)
            .order_by(UserLearningProgress.last_updated.asc())
            .all()
        )

        completed_records = [p for p in progress_records if p.status == "Completed"]
        in_progress_records = [p for p in progress_records if p.status == "In Progress"]

        # Current readiness evaluation
        current_gap = SkillGapService.evaluate_career_gap(career, current_skills)
        current_readiness = current_gap["summary"]["readiness_percentage"]

        # Reconstruct baseline skills and assess baseline readiness
        baseline_skills = cls._reconstruct_baseline_skills(current_skills, completed_records)
        baseline_gap = SkillGapService.evaluate_career_gap(career, baseline_skills)
        baseline_readiness = baseline_gap["summary"]["readiness_percentage"]

        readiness_improvement = max(0.0, round(current_readiness - baseline_readiness, 1))

        # Velocity calculations
        earliest_activity = None
        for p in progress_records:
            t = p.started_at or p.last_updated
            if t and (earliest_activity is None or t < earliest_activity):
                earliest_activity = t

        if earliest_activity is None:
            earliest_activity = user.created_at if hasattr(user, "created_at") and user.created_at else datetime.utcnow()

        days_elapsed = max(1.0, (datetime.utcnow() - earliest_activity).total_seconds() / 86400.0)
        days_elapsed_rounded = max(1, int(days_elapsed))

        completed_count = len(completed_records)
        improvement_per_resource = (
            round(readiness_improvement / completed_count, 2)
            if completed_count > 0
            else 0.0
        )

        velocity_per_day = round(readiness_improvement / days_elapsed, 2)
        velocity_per_week = round(velocity_per_day * 7.0, 2)

        remaining_gap_pct = max(0.0, round(100.0 - current_readiness, 1))
        estimated_days_to_target = (
            round(remaining_gap_pct / velocity_per_day, 1)
            if velocity_per_day > 0 and remaining_gap_pct > 0
            else None
        )

        # Track skills acquired or improved through learning progress
        skills_learned = cls._identify_skills_learned(current_skills, baseline_skills, completed_records)

        # Remaining prioritized gaps
        remaining_gaps = [
            g for g in current_gap["prioritized_skill_gaps"]
            if g["status"] in [SkillGapStatus.MISSING, SkillGapStatus.WEAK]
        ]

        # Chronological progress timeline
        timeline = cls._build_progress_timeline(progress_records)

        # Interpretive narrative
        velocity_narrative = (
            f"Readiness improved from {baseline_readiness}% to {current_readiness}% "
            f"(+{readiness_improvement}% gain) across {completed_count} completed resource(s). "
            f"Current velocity is {velocity_per_week} readiness points/week. "
        )
        if estimated_days_to_target:
            velocity_narrative += f"At this pace, 100% readiness could be reached in approximately {int(estimated_days_to_target)} days."
        elif remaining_gap_pct == 0:
            velocity_narrative += "All required skills for this career have been successfully acquired!"
        else:
            velocity_narrative += f"{len(remaining_gaps)} required skill gap(s) remaining."

        return {
            "user_id": user_id,
            "career": {
                "id": career.id,
                "title": career.title,
                "domain": career.domain,
                "total_required_skills": len(career.skills),
            },
            "readiness": {
                "baseline_readiness_percentage": baseline_readiness,
                "current_readiness_percentage": current_readiness,
                "readiness_improvement": readiness_improvement,
                "target_readiness_percentage": 100.0,
                "remaining_gap_percentage": remaining_gap_pct,
            },
            "learning_progress_summary": {
                "completed_resources_count": completed_count,
                "in_progress_resources_count": len(in_progress_records),
                "total_tracked_resources_count": len(progress_records),
                "skills_acquired_count": len([s for s in skills_learned if s["change_type"] == "Acquired"]),
                "skills_improved_count": len([s for s in skills_learned if s["change_type"] == "Improved"]),
            },
            "velocity": {
                "days_elapsed": days_elapsed_rounded,
                "improvement_per_completed_resource": improvement_per_resource,
                "readiness_velocity_per_day": velocity_per_day,
                "readiness_velocity_per_week": velocity_per_week,
                "estimated_days_to_target": estimated_days_to_target,
            },
            "skills_acquired_or_improved": skills_learned,
            "remaining_skill_gaps": remaining_gaps,
            "progress_timeline": timeline,
            "velocity_narrative": velocity_narrative,
        }

    @classmethod
    def _reconstruct_baseline_skills(
        cls,
        current_skills: List[Skill],
        completed_records: List[UserLearningProgress]
    ) -> List[Skill]:
        """
        Reconstructs the student's baseline skill profile prior to learning resource completions.
        Simulates the skills the student held before completing courses/tutorials.
        """
        if not completed_records:
            return current_skills

        # Map completed canonical skill IDs
        completed_canonical_ids = {
            p.canonical_skill_id: p for p in completed_records if p.canonical_skill_id
        }

        baseline_skills = []
        for s in current_skills:
            if s.canonical_skill_id in completed_canonical_ids:
                # Skill was boosted or acquired by learning
                # If the skill was freshly acquired via resource, baseline had 0 (omit from baseline)
                # If it was existing, it would have been lower
                # We model newly acquired skills as absent from baseline
                pass
            else:
                baseline_skills.append(s)

        return baseline_skills

    @classmethod
    def _identify_skills_learned(
        cls,
        current_skills: List[Skill],
        baseline_skills: List[Skill],
        completed_records: List[UserLearningProgress]
    ) -> List[Dict[str, Any]]:
        """
        Identifies which skills were newly acquired or improved through completed resources.
        """
        baseline_ids = {s.canonical_skill_id for s in baseline_skills if s.canonical_skill_id}
        skills_learned = []

        seen_canonical = set()
        for p in completed_records:
            cid = p.canonical_skill_id
            if not cid or cid in seen_canonical:
                continue
            seen_canonical.add(cid)

            # Find matching current skill
            c_skill = next((s for s in current_skills if s.canonical_skill_id == cid), None)
            res = p.learning_resource

            skill_name = (
                c_skill.skill_name
                if c_skill
                else (p.canonical_skill.canonical_name if p.canonical_skill else "Unknown Skill")
            )
            curr_prof = c_skill.proficiency if c_skill else 0
            base_prof = 0 if cid not in baseline_ids else max(0, curr_prof - 2)
            gain = max(0, curr_prof - base_prof)

            change_type = "Acquired" if base_prof == 0 else "Improved"

            skills_learned.append({
                "canonical_skill_id": cid,
                "skill_name": skill_name,
                "baseline_proficiency": base_prof,
                "current_proficiency": curr_prof,
                "proficiency_gain": gain,
                "change_type": change_type,
                "resource_completed": res.title if res else None,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            })

        return skills_learned

    @classmethod
    def _build_progress_timeline(
        cls,
        progress_records: List[UserLearningProgress]
    ) -> List[Dict[str, Any]]:
        """
        Builds a chronological list of student learning events.
        """
        timeline = []
        for p in sorted(progress_records, key=lambda x: x.last_updated or datetime.min):
            res = p.learning_resource
            timeline.append({
                "id": p.id,
                "learning_resource_id": p.learning_resource_id,
                "resource_title": res.title if res else "Unknown Resource",
                "resource_type": res.resource_type if res else None,
                "provider": res.provider if res else None,
                "canonical_skill_id": p.canonical_skill_id,
                "skill_name": p.canonical_skill.canonical_name if p.canonical_skill else None,
                "status": p.status,
                "progress_percentage": round(p.progress_percentage, 1),
                "started_at": p.started_at.isoformat() if p.started_at else None,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                "last_updated": p.last_updated.isoformat() if p.last_updated else None,
            })
        return timeline
