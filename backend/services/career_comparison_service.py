"""
Side-by-Side Career Comparison Service for AI Career Navigator.

Compares two target careers against each other and against a student's skill profile.
Distinguishes:
- Common Skills (shared requirements)
- Career A Only
- Career B Only
- Student Already Has (satisfied proficiencies)
- Student Missing (actionable gaps)
Calculates overlap percentages, comparative readiness, and acquisition distances.
"""

from typing import Any, Dict, List, Optional, Set
from models.career import Career
from models.skill import Skill
from services.career_recommendation_service import CareerRecommendationService
from services.skill_gap_service import SkillGapService, SkillGapStatus
from utils.normalization import normalize_skill_name


class CareerComparisonService:
    """Service providing side-by-side comparative analysis of two careers."""

    @classmethod
    def compare_careers(
        cls,
        career_a_id: int,
        career_b_id: int,
        student_skills: List[Skill]
    ) -> Optional[Dict[str, Any]]:
        """
        Executes dual career comparison and student readiness evaluation.
        """
        career_a = Career.query.get(career_a_id)
        career_b = Career.query.get(career_b_id)

        if not career_a or not career_b:
            return None

        # Evaluate individual career gaps for the student
        gap_analysis_a = SkillGapService.evaluate_career_gap(career_a, student_skills)
        gap_analysis_b = SkillGapService.evaluate_career_gap(career_b, student_skills)

        distance_a = CareerRecommendationService.calculate_skill_acquisition_distance(
            gap_analysis_a["prioritized_skill_gaps"]
        )
        distance_b = CareerRecommendationService.calculate_skill_acquisition_distance(
            gap_analysis_b["prioritized_skill_gaps"]
        )

        gaps_a_map = {g["skill_name"].lower(): g for g in gap_analysis_a["prioritized_skill_gaps"]}
        gaps_b_map = {g["skill_name"].lower(): g for g in gap_analysis_b["prioritized_skill_gaps"]}

        # Match by canonical ID where available, otherwise by normalized name
        skills_a_by_key = {}
        for cs in career_a.skills:
            key = f"id_{cs.canonical_skill_id}" if cs.canonical_skill_id else f"name_{normalize_skill_name(cs.skill_name)}"
            skills_a_by_key[key] = cs

        skills_b_by_key = {}
        for cs in career_b.skills:
            key = f"id_{cs.canonical_skill_id}" if cs.canonical_skill_id else f"name_{normalize_skill_name(cs.skill_name)}"
            skills_b_by_key[key] = cs

        all_keys = set(skills_a_by_key.keys()).union(set(skills_b_by_key.keys()))
        common_keys = set(skills_a_by_key.keys()).intersection(set(skills_b_by_key.keys()))
        a_only_keys = set(skills_a_by_key.keys()) - common_keys
        b_only_keys = set(skills_b_by_key.keys()) - common_keys

        common_skills = []
        for k in sorted(common_keys):
            cs_a = skills_a_by_key[k]
            cs_b = skills_b_by_key[k]
            ga = gaps_a_map.get(cs_a.skill_name.lower(), {})
            gb = gaps_b_map.get(cs_b.skill_name.lower(), {})

            common_skills.append({
                "skill_name": cs_a.skill_name,
                "canonical_skill_id": cs_a.canonical_skill_id,
                "career_a": {
                    "required_level": cs_a.required_level,
                    "importance": cs_a.importance,
                    "status": ga.get("status", SkillGapStatus.MISSING)
                },
                "career_b": {
                    "required_level": cs_b.required_level,
                    "importance": cs_b.importance,
                    "status": gb.get("status", SkillGapStatus.MISSING)
                },
                "student_current_proficiency": ga.get("current_proficiency", 0.0)
            })

        career_a_only = []
        for k in sorted(a_only_keys):
            cs = skills_a_by_key[k]
            ga = gaps_a_map.get(cs.skill_name.lower(), {})
            career_a_only.append({
                "skill_name": cs.skill_name,
                "canonical_skill_id": cs.canonical_skill_id,
                "required_level": cs.required_level,
                "importance": cs.importance,
                "student_current_proficiency": ga.get("current_proficiency", 0.0),
                "status": ga.get("status", SkillGapStatus.MISSING)
            })

        career_b_only = []
        for k in sorted(b_only_keys):
            cs = skills_b_by_key[k]
            gb = gaps_b_map.get(cs.skill_name.lower(), {})
            career_b_only.append({
                "skill_name": cs.skill_name,
                "canonical_skill_id": cs.canonical_skill_id,
                "required_level": cs.required_level,
                "importance": cs.importance,
                "student_current_proficiency": gb.get("current_proficiency", 0.0),
                "status": gb.get("status", SkillGapStatus.MISSING)
            })

        # Categorize overall student competencies across both careers
        student_already_has = []
        student_missing = []

        seen_satisfied = set()
        seen_missing = set()

        for g in gap_analysis_a["prioritized_skill_gaps"] + gap_analysis_b["prioritized_skill_gaps"]:
            sname = g["skill_name"]
            st = g["status"]
            if st in [SkillGapStatus.MATCHED, SkillGapStatus.EXCEEDS]:
                if sname not in seen_satisfied:
                    seen_satisfied.add(sname)
                    student_already_has.append({
                        "skill_name": sname,
                        "canonical_skill_id": g["canonical_skill_id"],
                        "current_proficiency": g["current_proficiency"],
                        "status": st
                    })
            else:
                if sname not in seen_missing:
                    seen_missing.add(sname)
                    student_missing.append({
                        "skill_name": sname,
                        "canonical_skill_id": g["canonical_skill_id"],
                        "current_proficiency": g["current_proficiency"],
                        "status": st
                    })

        total_unique = len(all_keys) or 1
        overlap_percentage = round((len(common_keys) / float(total_unique)) * 100.0, 1)

        readiness_a = gap_analysis_a["summary"]["readiness_percentage"]
        readiness_b = gap_analysis_b["summary"]["readiness_percentage"]

        # Comparative narrative
        common_names = [c["skill_name"] for c in common_skills]
        comparison_summary = (
            f"Comparing {career_a.title} (Readiness: {readiness_a}%, Distance: {distance_a}) "
            f"vs {career_b.title} (Readiness: {readiness_b}%, Distance: {distance_b}). "
            f"The two career paths share {len(common_skills)} common skill requirement(s) ({overlap_percentage}% overlap)"
            f"{': ' + ', '.join(common_names) if common_names else ''}."
        )

        return {
            "career_a": {
                "id": career_a.id,
                "title": career_a.title,
                "domain": career_a.domain,
                "readiness_percentage": readiness_a,
                "skill_acquisition_distance": distance_a,
                "total_required_skills": len(career_a.skills),
                "matched_skills_count": gap_analysis_a["summary"]["matched_skills"],
                "missing_skills_count": gap_analysis_a["summary"]["missing_skills"],
                "weak_skills_count": gap_analysis_a["summary"]["weak_skills"],
            },
            "career_b": {
                "id": career_b.id,
                "title": career_b.title,
                "domain": career_b.domain,
                "readiness_percentage": readiness_b,
                "skill_acquisition_distance": distance_b,
                "total_required_skills": len(career_b.skills),
                "matched_skills_count": gap_analysis_b["summary"]["matched_skills"],
                "missing_skills_count": gap_analysis_b["summary"]["missing_skills"],
                "weak_skills_count": gap_analysis_b["summary"]["weak_skills"],
            },
            "comparison_metrics": {
                "overlap_percentage": overlap_percentage,
                "common_skills_count": len(common_skills),
                "career_a_exclusive_count": len(career_a_only),
                "career_b_exclusive_count": len(career_b_only),
                "closer_career": career_a.title if distance_a <= distance_b else career_b.title,
                "summary": comparison_summary,
            },
            "common_skills": common_skills,
            "career_a_only": career_a_only,
            "career_b_only": career_b_only,
            "student_already_has": student_already_has,
            "student_missing": student_missing,
        }
