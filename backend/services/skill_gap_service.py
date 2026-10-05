"""
Deterministic Skill-Gap Assessment Engine for AI Career Navigator.

Compares a student's current skill profile against a target career's requirements.
Calculates deterministic proficiency gaps, classifies status (MISSING, WEAK, MATCHED, EXCEEDS),
weights by career importance, and computes explainable priority rankings.
"""

from typing import Any, Dict, List, Optional
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from utils.normalization import normalize_skill_name


class SkillGapStatus:
    MISSING = "MISSING"
    WEAK = "WEAK"
    MATCHED = "MATCHED"
    EXCEEDS = "EXCEEDS"


class SkillGapService:
    """Service for deterministic skill gap analysis."""

    @staticmethod
    def calculate_gap(
        required_level: int,
        student_raw_proficiency: int
    ) -> Dict[str, Any]:
        """
        Calculates proficiency gap and classifies status.
        
        Proficiency Scaling:
        - Career requirements use a 1 to 5 scale (required_level).
        - Student skills use a 1 to 10 scale (raw_proficiency).
        - Normalized current proficiency is scaled to 1.0 - 5.0 (raw_proficiency / 2.0).
        """
        if student_raw_proficiency <= 0:
            return {
                "current_proficiency": 0.0,
                "raw_proficiency": 0,
                "gap_value": float(required_level),
                "status": SkillGapStatus.MISSING
            }

        normalized_curr = round(student_raw_proficiency / 2.0, 2)
        diff = round(required_level - normalized_curr, 2)

        if diff > 0:
            status = SkillGapStatus.WEAK
            gap_value = diff
        elif diff == 0:
            status = SkillGapStatus.MATCHED
            gap_value = 0.0
        else:
            status = SkillGapStatus.EXCEEDS
            gap_value = 0.0

        return {
            "current_proficiency": normalized_curr,
            "raw_proficiency": student_raw_proficiency,
            "gap_value": gap_value,
            "status": status
        }

    @staticmethod
    def calculate_priority(
        importance: int,
        gap_value: float,
        status: str
    ) -> Dict[str, Any]:
        """
        Deterministic, explainable prioritization formula:
        
        Formula:
            urgency_factor = 1.25 if MISSING else (1.0 if WEAK else 0.0)
            priority_score = round(importance * gap_value * urgency_factor, 2)
        
        Priority Levels:
            - HIGH: score >= 15.0
            - MEDIUM: 6.0 <= score < 15.0
            - LOW: 0.0 < score < 6.0
            - NONE: score == 0.0 (Satisfied competencies)
        """
        if status in [SkillGapStatus.MATCHED, SkillGapStatus.EXCEEDS]:
            return {
                "priority_score": 0.0,
                "priority_level": "NONE"
            }

        urgency_factor = 1.25 if status == SkillGapStatus.MISSING else 1.0
        score = round(importance * gap_value * urgency_factor, 2)

        if score >= 15.0:
            level = "HIGH"
        elif score >= 6.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "priority_score": score,
            "priority_level": level
        }

    @staticmethod
    def generate_explanation(
        skill_name: str,
        required_level: int,
        importance: int,
        raw_proficiency: int,
        normalized_curr: float,
        gap_value: float,
        status: str,
        priority_level: str
    ) -> str:
        """Generates clear, human-understandable explanation for the skill gap status."""
        if status == SkillGapStatus.MISSING:
            return (
                f"High-priority missing skill: '{skill_name}' is required at proficiency level "
                f"{required_level}/5 with high career importance ({importance}/5). You currently have "
                f"no experience or certification recorded for this skill. Prioritized for immediate learning."
            )
        elif status == SkillGapStatus.WEAK:
            return (
                f"Proficiency gap: '{skill_name}' requires level {required_level}/5 (importance: {importance}/5). "
                f"Your current proficiency is {raw_proficiency}/10 ({normalized_curr}/5), leaving a gap of "
                f"{gap_value} level(s). Skill reinforcement and hands-on projects are recommended."
            )
        elif status == SkillGapStatus.MATCHED:
            return (
                f"Target achieved: Your current proficiency in '{skill_name}' ({raw_proficiency}/10) "
                f"meets the role requirement of level {required_level}/5 (importance: {importance}/5)."
            )
        else:  # EXCEEDS
            return (
                f"Core competency: Your proficiency in '{skill_name}' ({raw_proficiency}/10) "
                f"exceeds the required threshold of level {required_level}/5. This is a competitive strength."
            )

    @classmethod
    def evaluate_career_gap(
        cls,
        career: Career,
        student_skills: List[Skill]
    ) -> Dict[str, Any]:
        """
        Evaluates a complete career against a student's skills list.
        """
        # Map student skills by canonical_skill_id and normalized_name for fast lookup
        student_map_by_id = {}
        student_map_by_name = {}

        for s in student_skills:
            if s.canonical_skill_id:
                student_map_by_id[s.canonical_skill_id] = s
            norm_name = normalize_skill_name(s.skill_name)
            student_map_by_name[norm_name] = s

        career_skills = career.skills if hasattr(career, "skills") and career.skills else (
            CareerSkill.query.filter_by(career_id=career.id).all()
        )

        total_required = len(career_skills)
        matched_count = 0
        weak_count = 0
        missing_count = 0

        total_required_points = 0.0
        total_achieved_points = 0.0

        gap_items: List[Dict[str, Any]] = []

        for cs in career_skills:
            req_level = cs.required_level or 1
            importance = cs.importance or 1
            total_required_points += req_level

            # Attempt lookup by canonical_skill_id first, then fallback to normalized name
            matched_student_skill = None
            if cs.canonical_skill_id and cs.canonical_skill_id in student_map_by_id:
                matched_student_skill = student_map_by_id[cs.canonical_skill_id]
            else:
                cs_norm = normalize_skill_name(cs.skill_name)
                if cs_norm in student_map_by_name:
                    matched_student_skill = student_map_by_name[cs_norm]

            raw_prof = matched_student_skill.proficiency if matched_student_skill else 0
            gap_metrics = cls.calculate_gap(req_level, raw_prof)
            priority_metrics = cls.calculate_priority(
                importance,
                gap_metrics["gap_value"],
                gap_metrics["status"]
            )

            # Accumulate readiness score
            clamped_achieved = min(gap_metrics["current_proficiency"], float(req_level))
            total_achieved_points += clamped_achieved

            if gap_metrics["status"] == SkillGapStatus.MISSING:
                missing_count += 1
            elif gap_metrics["status"] == SkillGapStatus.WEAK:
                weak_count += 1
            else:
                matched_count += 1

            explanation = cls.generate_explanation(
                cs.skill_name,
                req_level,
                importance,
                gap_metrics["raw_proficiency"],
                gap_metrics["current_proficiency"],
                gap_metrics["gap_value"],
                gap_metrics["status"],
                priority_metrics["priority_level"]
            )

            gap_items.append({
                "career_skill_id": cs.id,
                "canonical_skill_id": cs.canonical_skill_id,
                "skill_name": cs.skill_name,
                "required_level": req_level,
                "importance": importance,
                "current_proficiency": gap_metrics["current_proficiency"],
                "raw_proficiency": gap_metrics["raw_proficiency"],
                "gap_value": gap_metrics["gap_value"],
                "status": gap_metrics["status"],
                "priority_score": priority_metrics["priority_score"],
                "priority_level": priority_metrics["priority_level"],
                "explanation": explanation
            })

        # Sort gaps deterministically by priority_score descending, then importance descending, then gap_value descending
        prioritized_gaps = sorted(
            gap_items,
            key=lambda x: (-x["priority_score"], -x["importance"], -x["gap_value"], x["skill_name"])
        )

        readiness_pct = (
            round((total_achieved_points / total_required_points) * 100.0, 1)
            if total_required_points > 0 else 0.0
        )

        return {
            "career": {
                "id": career.id,
                "title": career.title,
                "domain": career.domain,
                "description": career.description
            },
            "summary": {
                "total_required_skills": total_required,
                "matched_skills": matched_count,
                "weak_skills": weak_count,
                "missing_skills": missing_count,
                "readiness_percentage": readiness_pct
            },
            "prioritized_skill_gaps": prioritized_gaps
        }


def assess_career_skill_gap(career_id: int, student_skills: List[Skill]) -> Optional[Dict[str, Any]]:
    """Helper wrapper for evaluating career skill gap."""
    career = Career.query.get(career_id)
    if not career:
        return None
    return SkillGapService.evaluate_career_gap(career, student_skills)
