"""
Explainable Skill ROI & Counterfactual Analysis Engine for AI Career Navigator.
Phase 11 Module 11.1: Explainable AI Counterfactuals & Skill ROI Engine.

Provides:
- In-memory counterfactual skill analysis ("What happens if student improves skill X?").
- Marginal readiness gain and multi-factor recommendation score impact calculation.
- Skill ROI (Marginal Readiness Gain / Estimated Learning Effort).
- Deterministic ranking of missing and weak skills by learning efficiency.
- Explainable natural-language reasoning derived strictly from scoring inputs.
- Strict safety guarantee: ZERO database modifications or persistent mutations.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from extensions import db
from models.canonical_skill import CanonicalSkill
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from services.career_simulator_service import CareerSimulatorService
from services.skill_gap_service import SkillGapService, SkillGapStatus
from utils.normalization import normalize_skill_name


class SkillRoiService:
    """Service providing deterministic counterfactual analysis and skill ROI calculations."""

    DEFAULT_HOURS_PER_WEEK = 10

    @staticmethod
    def normalize_proficiency_inputs(simulated_level_raw: Any) -> Tuple[float, int]:
        """
        Normalizes proficiency input into:
        - normalized_level (1.0 to 5.0 career scale)
        - raw_proficiency (1 to 10 student scale)
        Raises ValueError if out of bounds.
        """
        return CareerSimulatorService.normalize_proficiency_inputs(simulated_level_raw)

    @classmethod
    def calculate_learning_effort(
        cls,
        current_norm_level: float,
        target_norm_level: float,
        is_missing: bool,
        required_level: int,
        hours_per_week: int = DEFAULT_HOURS_PER_WEEK
    ) -> Tuple[int, int]:
        """
        Calculates estimated learning hours and weeks based on the project's
        established roadmap study model.
        - Missing skill: base 10 hours + (required_level * 5 hours)
        - Weak skill: base 5 hours + (level_delta * 8 hours)
        """
        safe_hours_per_week = max(1, int(hours_per_week))

        if is_missing or current_norm_level <= 0.0:
            target_pts = int(round(target_norm_level)) if target_norm_level > 0 else int(required_level)
            estimated_hours = 10 + target_pts * 5
        else:
            level_delta = max(0.0, target_norm_level - current_norm_level)
            estimated_hours = max(5, int(round(5 + level_delta * 8)))

        estimated_weeks = max(1, math.ceil(estimated_hours / safe_hours_per_week))
        return estimated_hours, estimated_weeks

    @classmethod
    def calculate_counterfactual(
        cls,
        career_id: int,
        skill_id: Optional[Any] = None,
        skill_name: Optional[str] = None,
        target_level: Optional[Any] = None,
        user_id: Optional[int] = None,
        hours_per_week: int = DEFAULT_HOURS_PER_WEEK
    ) -> Dict[str, Any]:
        """
        Performs an in-memory counterfactual analysis for improving a specific skill.
        Answers: 'What happens to career readiness if the student reaches target_level in this skill?'
        Strictly read-only; does not mutate student records.
        """
        # 1. Validate career
        career = Career.query.get(career_id)
        if not career:
            return {
                "error": "CAREER_NOT_FOUND",
                "message": f"Career with ID {career_id} not found"
            }

        # 2. Resolve target skill
        resolved_skill = CareerSimulatorService.resolve_skill(
            skill_id=skill_id,
            skill_name=skill_name,
            career_id=career_id
        )
        if not resolved_skill:
            return {
                "error": "SKILL_NOT_FOUND",
                "message": "Skill could not be resolved. Please provide a valid skill ID, canonical name, or recognized alias."
            }

        resolved_canonical_id = resolved_skill.get("canonical_skill_id")
        resolved_norm_name = resolved_skill["normalized_name"]
        display_skill_name = resolved_skill["name"]

        # 3. Retrieve student's current skills (read-only)
        student_skills: List[Skill] = []
        if user_id:
            student_skills = Skill.query.filter_by(user_id=user_id).all()

        current_raw_prof = 0
        for s in student_skills:
            if resolved_canonical_id and s.canonical_skill_id == resolved_canonical_id:
                current_raw_prof = s.proficiency or 0
                break
            elif normalize_skill_name(s.skill_name) == resolved_norm_name:
                current_raw_prof = s.proficiency or 0
                break

        current_norm_level = round(current_raw_prof / 2.0, 1)

        # 4. Check if skill is required by the career
        career_skills: List[CareerSkill] = (
            career.skills if hasattr(career, "skills") and career.skills else
            CareerSkill.query.filter_by(career_id=career.id).all()
        )

        matched_career_skill: Optional[CareerSkill] = None
        for cs in career_skills:
            if resolved_canonical_id and cs.canonical_skill_id == resolved_canonical_id:
                matched_career_skill = cs
                break
            elif normalize_skill_name(cs.skill_name) == resolved_norm_name:
                matched_career_skill = cs
                break

        # Calculate current baseline readiness for this career
        current_gap_analysis = SkillGapService.evaluate_career_gap(career, student_skills)
        current_readiness = current_gap_analysis["summary"]["readiness_percentage"]

        # Case A: Skill is UNRELATED to target career
        if not matched_career_skill:
            explanation = (
                f"Skill '{display_skill_name}' is not an established competency requirement for "
                f"'{career.title}'. While building domain versatility, improving this skill produces "
                f"0.0% marginal readiness gain toward this specific career specification."
            )
            return {
                "career_id": career.id,
                "career_title": career.title,
                "skill_name": display_skill_name,
                "is_required": False,
                "current_proficiency": current_norm_level,
                "current_raw_proficiency": current_raw_prof,
                "target_proficiency": current_norm_level,
                "target_raw_proficiency": current_raw_prof,
                "required_level": None,
                "importance": None,
                "before_readiness": current_readiness,
                "after_readiness": current_readiness,
                "readiness_gain": 0.0,
                "before_gap": 0.0,
                "after_gap": 0.0,
                "estimated_hours": 0,
                "estimated_weeks": 0,
                "roi_score": 0.0,
                "roi_per_10h": 0.0,
                "explanation": explanation
            }

        # Case B: Skill IS REQUIRED by the target career
        required_level = matched_career_skill.required_level or 1
        importance = matched_career_skill.importance or 1

        # Determine target proficiency: if not provided, default to meeting the required level
        if target_level is not None:
            try:
                target_norm_level, target_raw_prof = cls.normalize_proficiency_inputs(target_level)
            except ValueError as e:
                return {
                    "error": "INVALID_PROFICIENCY",
                    "message": str(e)
                }
        else:
            target_norm_level = float(required_level)
            target_raw_prof = int(required_level * 2)

        # Clamped effective target level (cannot exceed 5.0 career scale)
        clamped_target_norm = min(5.0, max(1.0, target_norm_level))

        # Check if skill is already fully satisfied
        before_gap = max(0.0, round(required_level - current_norm_level, 2))
        after_gap = max(0.0, round(required_level - clamped_target_norm, 2))

        # Calculate marginal readiness gain
        total_required_points = sum((cs.required_level or 1) for cs in career_skills)
        if total_required_points <= 0:
            total_required_points = 1.0

        current_achieved_point = min(current_norm_level, float(required_level))
        hypothetical_achieved_point = min(clamped_target_norm, float(required_level))
        point_delta = max(0.0, hypothetical_achieved_point - current_achieved_point)

        readiness_gain = round((point_delta / total_required_points) * 100.0, 1)
        after_readiness = min(100.0, round(current_readiness + readiness_gain, 1))

        is_missing = (current_raw_prof == 0)
        hours, weeks = cls.calculate_learning_effort(
            current_norm_level=current_norm_level,
            target_norm_level=clamped_target_norm,
            is_missing=is_missing,
            required_level=required_level,
            hours_per_week=hours_per_week
        )

        roi_score = round(readiness_gain / max(1, weeks), 2)
        roi_per_10h = round((readiness_gain * 10.0) / max(1, hours), 2)

        # Generate explainable natural-language justification
        if before_gap <= 0.0:
            explanation = (
                f"Competency already satisfied: Your current proficiency in '{display_skill_name}' "
                f"({current_raw_prof}/10, {current_norm_level}/5) already meets or exceeds the career benchmark "
                f"of Level {required_level}/5 (importance: {importance}/5). Advancing this skill produces "
                f"0.0% marginal readiness gain for this role."
            )
        elif point_delta <= 0.0:
            explanation = (
                f"Limited return: Simulated level {clamped_target_norm}/5 does not exceed your current "
                f"proficiency of {current_norm_level}/5 in '{display_skill_name}', resulting in 0.0% readiness gain."
            )
        else:
            gap_reduction = round(before_gap - after_gap, 2)
            explanation = (
                f"High-impact return: '{display_skill_name}' is a required competency for '{career.title}' "
                f"with career importance {importance}/5. Raising proficiency from Level {current_norm_level}/5 "
                f"({current_raw_prof}/10) to Level {clamped_target_norm}/5 reduces the competency gap by "
                f"{gap_reduction} level(s), boosting readiness from {current_readiness}% to {after_readiness}% "
                f"(+{readiness_gain}%). With an estimated {hours} hours ({weeks} weeks at {hours_per_week}h/week), "
                f"this achieves a Skill ROI of {roi_score} readiness points per study week."
            )

        return {
            "career_id": career.id,
            "career_title": career.title,
            "skill_name": display_skill_name,
            "is_required": True,
            "current_proficiency": current_norm_level,
            "current_raw_proficiency": current_raw_prof,
            "target_proficiency": clamped_target_norm,
            "target_raw_proficiency": target_raw_prof,
            "required_level": required_level,
            "importance": importance,
            "before_readiness": current_readiness,
            "after_readiness": after_readiness,
            "readiness_gain": readiness_gain,
            "before_gap": before_gap,
            "after_gap": after_gap,
            "estimated_hours": hours,
            "estimated_weeks": weeks,
            "roi_score": roi_score,
            "roi_per_10h": roi_per_10h,
            "explanation": explanation
        }

    @classmethod
    def rank_career_skill_rois(
        cls,
        career_id: int,
        user_id: Optional[int] = None,
        hours_per_week: int = DEFAULT_HOURS_PER_WEEK
    ) -> Dict[str, Any]:
        """
        Deterministically evaluates and ranks all missing and weak skills for a career by ROI.
        Prioritizes:
        1. ROI Score descending (readiness gain per study week)
        2. Absolute Readiness Gain descending
        3. Career Importance descending
        4. Current Gap descending
        5. Skill Name ascending (deterministic tie-breaker)
        """
        career = Career.query.get(career_id)
        if not career:
            return {
                "error": "CAREER_NOT_FOUND",
                "message": f"Career with ID {career_id} not found"
            }

        student_skills: List[Skill] = []
        if user_id:
            student_skills = Skill.query.filter_by(user_id=user_id).all()

        gap_analysis = SkillGapService.evaluate_career_gap(career, student_skills)
        current_readiness = gap_analysis["summary"]["readiness_percentage"]
        prioritized_gaps = gap_analysis["prioritized_skill_gaps"]

        candidate_analyses = []
        for gap in prioritized_gaps:
            status = gap["status"]
            # Only evaluate actionable skills (MISSING or WEAK)
            if status not in [SkillGapStatus.MISSING, SkillGapStatus.WEAK]:
                continue

            analysis = cls.calculate_counterfactual(
                career_id=career.id,
                skill_id=gap.get("canonical_skill_id") or gap.get("career_skill_id"),
                skill_name=gap["skill_name"],
                target_level=gap["required_level"],  # Target full satisfaction
                user_id=user_id,
                hours_per_week=hours_per_week
            )

            if "error" not in analysis:
                analysis["status"] = status
                candidate_analyses.append(analysis)

        # Deterministic sorting
        candidate_analyses.sort(
            key=lambda x: (
                -x["roi_score"],
                -x["readiness_gain"],
                -x["importance"],
                -x["before_gap"],
                x["skill_name"]
            )
        )

        quickest_win = candidate_analyses[0] if candidate_analyses else None
        highest_gain = (
            max(candidate_analyses, key=lambda x: (x["readiness_gain"], x["roi_score"], x["skill_name"]))
            if candidate_analyses else None
        )

        total_potential_gain = round(sum(x["readiness_gain"] for x in candidate_analyses), 1)
        total_estimated_hours = sum(x["estimated_hours"] for x in candidate_analyses)

        return {
            "career_id": career.id,
            "career_title": career.title,
            "domain": career.domain,
            "current_readiness": current_readiness,
            "hours_per_week": hours_per_week,
            "candidate_skills_count": len(candidate_analyses),
            "total_potential_gain": total_potential_gain,
            "total_estimated_hours": total_estimated_hours,
            "quickest_win": quickest_win,
            "highest_gain": highest_gain,
            "ranked_skills": candidate_analyses
        }
