"""
Side-by-Side Career Comparison & Transition Pathway Service for AI Career Navigator.
Phase 9 Module 9.2: Market-Augmented Dual Career Comparison & Transition Pathway Explorer.

Provides:
- Career A vs Career B skill and competency comparison (common, exclusive, student readiness).
- Labor market demand comparison and demand delta.
- Salary differential comparison (entry, median, senior bands) and percentage deltas.
- Weekly study intensity and roadmap completion timeline comparison.
- Estimated study weeks difference.
- Career transition pathway analysis, difficulty classification, and O*NET transferable skills matrix.
"""

import re
from typing import Any, Dict, List, Optional, Set

from models.career import Career
from models.skill import Skill
from services.career_market_service import CareerMarketService
from services.career_recommendation_service import CareerRecommendationService
from services.career_transition_service import CareerTransitionService
from services.roadmap_service import RoadmapService
from services.skill_gap_service import SkillGapService, SkillGapStatus
from utils.normalization import normalize_skill_name


def parse_salary_amount(val: Optional[str]) -> Optional[int]:
    """
    Parses formatted salary strings like '$115,000 / yr', '$78,000', or '$120k' into an integer.
    Returns integer value or None if parsing fails.
    """
    if not val:
        return None
    cleaned = str(val).lower().replace(",", "").replace("$", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(k)?", cleaned)
    if match:
        num = float(match.group(1))
        if match.group(2) == "k":
            num *= 1000.0
        return int(num)
    return None


class CareerComparisonService:
    """Service providing side-by-side comparative analysis of two careers with market and transition intelligence."""

    @staticmethod
    def calculate_salary_differential(
        career_a_title: str,
        career_b_title: str,
        market_a: Dict[str, Any],
        market_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculates salary differences across entry, median, and senior bands."""
        bands_a = market_a.get("salary_bands", {})
        bands_b = market_b.get("salary_bands", {})

        entry_a = parse_salary_amount(bands_a.get("entry_level"))
        entry_b = parse_salary_amount(bands_b.get("entry_level"))
        entry_delta = (entry_b - entry_a) if (entry_a is not None and entry_b is not None) else None

        median_a = parse_salary_amount(bands_a.get("median"))
        median_b = parse_salary_amount(bands_b.get("median"))
        median_delta = (median_b - median_a) if (median_a is not None and median_b is not None) else None
        median_pct = (
            round(((median_b - median_a) / float(median_a)) * 100.0, 1)
            if (median_a and median_b is not None)
            else 0.0
        )

        senior_a = parse_salary_amount(bands_a.get("senior"))
        senior_b = parse_salary_amount(bands_b.get("senior"))
        senior_delta = (senior_b - senior_a) if (senior_a is not None and senior_b is not None) else None

        def format_delta(d: Optional[int]) -> str:
            if d is None:
                return "N/A"
            prefix = "+" if d >= 0 else ""
            return f"{prefix}${d:,} / yr"

        higher_career = "Equal"
        if median_delta is not None:
            if median_delta > 0:
                higher_career = career_b_title
            elif median_delta < 0:
                higher_career = career_a_title

        return {
            "career_a_salary_bands": bands_a,
            "career_b_salary_bands": bands_b,
            "entry_level": {
                "career_a": bands_a.get("entry_level", "N/A"),
                "career_b": bands_b.get("entry_level", "N/A"),
                "delta_amount": entry_delta,
                "formatted_delta": format_delta(entry_delta)
            },
            "median": {
                "career_a": bands_a.get("median", "N/A"),
                "career_b": bands_b.get("median", "N/A"),
                "delta_amount": median_delta,
                "delta_percentage": median_pct,
                "formatted_delta": format_delta(median_delta),
                "higher_salary_career": higher_career
            },
            "senior": {
                "career_a": bands_a.get("senior", "N/A"),
                "career_b": bands_b.get("senior", "N/A"),
                "delta_amount": senior_delta,
                "formatted_delta": format_delta(senior_delta)
            },
            "median_delta": median_delta,
            "median_percentage_delta": median_pct
        }

    @staticmethod
    def calculate_market_comparison(
        career_a: Career,
        career_b: Career,
        market_a: Dict[str, Any],
        market_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculates market demand metrics and demand differential between two careers."""
        demand_a = int(market_a.get("demand_score", 70))
        demand_b = int(market_b.get("demand_score", 70))
        demand_delta = demand_b - demand_a

        higher_demand = "Equal"
        if demand_delta > 0:
            higher_demand = career_b.title
        elif demand_delta < 0:
            higher_demand = career_a.title

        summary = (
            f"{career_b.title} has a market demand score of {demand_b}/100 compared to "
            f"{career_a.title} with {demand_a}/100 (delta: {'+' if demand_delta >= 0 else ''}{demand_delta} points)."
        )

        return {
            "career_a": {
                "id": career_a.id,
                "title": career_a.title,
                "demand_score": demand_a,
                "demand_level": market_a.get("demand_level", "High"),
                "five_year_growth_rate": market_a.get("five_year_growth_rate", "+18%"),
                "top_hiring_sectors": market_a.get("top_hiring_sectors", [])
            },
            "career_b": {
                "id": career_b.id,
                "title": career_b.title,
                "demand_score": demand_b,
                "demand_level": market_b.get("demand_level", "High"),
                "five_year_growth_rate": market_b.get("five_year_growth_rate", "+18%"),
                "top_hiring_sectors": market_b.get("top_hiring_sectors", [])
            },
            "demand_delta": demand_delta,
            "higher_demand_career": higher_demand,
            "summary": summary
        }

    @staticmethod
    def calculate_timeline_comparison(
        career_a: Career,
        career_b: Career,
        gaps_a: List[Dict[str, Any]],
        gaps_b: List[Dict[str, Any]],
        hours_per_week: int = 10
    ) -> Dict[str, Any]:
        """Calculates study workload and weeks-to-completion differential between two roadmaps."""
        roadmap_a = RoadmapService.generate_roadmap(career_a.title, gaps_a, hours_per_week=hours_per_week)
        roadmap_b = RoadmapService.generate_roadmap(career_b.title, gaps_b, hours_per_week=hours_per_week)

        study_a = roadmap_a.get("study_plan") or {}
        study_b = roadmap_b.get("study_plan") or {}

        hours_a = study_a.get("estimated_total_hours", 0)
        hours_b = study_b.get("estimated_total_hours", 0)

        weeks_a = study_a.get("estimated_weeks", 0)
        weeks_b = study_b.get("estimated_weeks", 0)

        weeks_diff = weeks_b - weeks_a
        hours_diff = hours_b - hours_a

        faster_career = career_a.title if weeks_a <= weeks_b else career_b.title
        summary = (
            f"At {hours_per_week} hours/week, {career_a.title} requires ~{weeks_a} weeks ({hours_a} hrs) "
            f"vs {career_b.title} requiring ~{weeks_b} weeks ({hours_b} hrs). "
            f"Difference: {'+' if weeks_diff >= 0 else ''}{weeks_diff} study week(s)."
        )

        return {
            "hours_per_week": hours_per_week,
            "career_a": {
                "id": career_a.id,
                "title": career_a.title,
                "estimated_total_hours": hours_a,
                "estimated_weeks": weeks_a,
                "estimated_completion_date": study_a.get("estimated_completion_date"),
                "milestones_count": len(study_a.get("weekly_milestones", []))
            },
            "career_b": {
                "id": career_b.id,
                "title": career_b.title,
                "estimated_total_hours": hours_b,
                "estimated_weeks": weeks_b,
                "estimated_completion_date": study_b.get("estimated_completion_date"),
                "milestones_count": len(study_b.get("weekly_milestones", []))
            },
            "estimated_study_weeks_difference": weeks_diff,
            "estimated_study_hours_difference": hours_diff,
            "faster_career": faster_career,
            "summary": summary
        }

    @classmethod
    def compare_careers(
        cls,
        career_a_id: int,
        career_b_id: int,
        student_skills: Optional[List[Skill]] = None,
        hours_per_week: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Executes comprehensive dual career comparison with market intelligence,
        salary differential, study timeline delta, and career transition pathway analysis.
        """
        if student_skills is None:
            student_skills = []

        career_a = Career.query.get(career_a_id)
        career_b = Career.query.get(career_b_id)

        if not career_a or not career_b:
            return None

        # 1. Evaluate individual career gaps for the student
        gap_analysis_a = SkillGapService.evaluate_career_gap(career_a, student_skills)
        gap_analysis_b = SkillGapService.evaluate_career_gap(career_b, student_skills)

        gaps_a = gap_analysis_a["prioritized_skill_gaps"]
        gaps_b = gap_analysis_b["prioritized_skill_gaps"]

        distance_a = CareerRecommendationService.calculate_skill_acquisition_distance(gaps_a)
        distance_b = CareerRecommendationService.calculate_skill_acquisition_distance(gaps_b)

        gaps_a_map = {g["skill_name"].lower(): g for g in gaps_a}
        gaps_b_map = {g["skill_name"].lower(): g for g in gaps_b}

        # 2. Match by canonical ID where available, otherwise by normalized name
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

        for g in gaps_a + gaps_b:
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

        # 3. Market demand & salary intelligence (Phase 7 / Module 9.2)
        market_a = CareerMarketService.get_market_outlook_by_career_id(career_a.id) or {}
        market_b = CareerMarketService.get_market_outlook_by_career_id(career_b.id) or {}

        market_comparison = cls.calculate_market_comparison(career_a, career_b, market_a, market_b)
        salary_differential = cls.calculate_salary_differential(career_a.title, career_b.title, market_a, market_b)

        # 4. Study timeline & workload comparison (Module 8.3 / Module 9.2)
        timeline_comparison = cls.calculate_timeline_comparison(
            career_a, career_b, gaps_a, gaps_b, hours_per_week=hours_per_week
        )

        # 5. Career transition analysis (Module 9.2)
        transition_analysis = CareerTransitionService.analyze_transition(career_a.id, career_b.id)
        transition_difficulty = (
            transition_analysis["transition_summary"]["transition_difficulty"]
            if transition_analysis
            else "MODERATE"
        )
        transition_difficulty_label = (
            transition_analysis["transition_summary"]["difficulty_label"]
            if transition_analysis
            else "Moderate Upskilling Transition"
        )
        transferable_skills = (
            transition_analysis.get("transferable_skills", [])
            if transition_analysis
            else []
        )

        # Comparative narrative
        common_names = [c["skill_name"] for c in common_skills]
        comparison_summary = (
            f"Comparing {career_a.title} (Readiness: {readiness_a}%, Distance: {distance_a}) "
            f"vs {career_b.title} (Readiness: {readiness_b}%, Distance: {distance_b}). "
            f"The two career paths share {len(common_skills)} common skill requirement(s) ({overlap_percentage}% overlap)"
            f"{': ' + ', '.join(common_names) if common_names else ''}. "
            f"Transition difficulty from {career_a.title} to {career_b.title} is classified as {transition_difficulty} ({transition_difficulty_label})."
        )

        return {
            # Legacy structures preserved 100%
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

            # Module 9.2 Additive Enhancements
            "market_comparison": market_comparison,
            "demand_delta": market_comparison["demand_delta"],
            "salary_differential": salary_differential,
            "salary_delta": salary_differential["median_delta"],
            "timeline_comparison": timeline_comparison,
            "estimated_study_weeks_difference": timeline_comparison["estimated_study_weeks_difference"],
            "transition_analysis": transition_analysis,
            "transition_difficulty": transition_difficulty,
            "transition_difficulty_label": transition_difficulty_label,
            "transferable_skills": transferable_skills,
        }
