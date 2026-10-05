"""
Multi-Career Recommendation Service for AI Career Navigator.

Evaluates student skill profile across all standardized career pathways.
Calculates deterministic recommendation scores, skill acquisition distances,
readiness percentages, and human-explainable rationales.
"""

from typing import Any, Dict, List, Optional
from models.career import Career
from models.skill import Skill
from services.skill_gap_service import SkillGapService, SkillGapStatus


class CareerRecommendationService:
    """Service for ranking and explaining career pathway recommendations."""

    @staticmethod
    def calculate_skill_acquisition_distance(gaps: List[Dict[str, Any]]) -> float:
        """
        Calculates the normalized skill acquisition distance from 0.0 (ready) to 100.0 (maximum gap).
        
        Formula:
            distance = (sum(gap_value * importance) / sum(required_level * importance)) * 100.0
        """
        total_required_weighted = 0.0
        total_gap_weighted = 0.0

        for g in gaps:
            req = float(g.get("required_level", 1))
            imp = float(g.get("importance", 1))
            gap = float(g.get("gap_value", 0.0))

            total_required_weighted += (req * imp)
            total_gap_weighted += (gap * imp)

        if total_required_weighted <= 0.0:
            return 0.0

        ratio = min(1.0, max(0.0, total_gap_weighted / total_required_weighted))
        return round(ratio * 100.0, 1)

    @staticmethod
    def calculate_recommendation_score(
        readiness_pct: float,
        matched_count: int,
        weak_count: int,
        total_required: int,
        distance: float
    ) -> float:
        """
        Computes a composite, explainable recommendation score (0.0 to 100.0).
        
        Components:
        1. Readiness Percentage (weight: 60%): Overall proficiency achievement.
        2. Skill Coverage Ratio (weight: 25%): Proportion of required skills possessed.
        3. Acquisition Proximity (weight: 15%): Inverted skill acquisition distance.
        """
        if total_required <= 0:
            return 0.0

        coverage_ratio = (matched_count + (0.5 * weak_count)) / float(total_required)
        coverage_score = min(100.0, max(0.0, coverage_ratio * 100.0))
        proximity_score = max(0.0, 100.0 - distance)

        composite = (
            (0.60 * readiness_pct) +
            (0.25 * coverage_score) +
            (0.15 * proximity_score)
        )
        return round(composite, 1)

    @staticmethod
    def generate_recommendation_explanation(
        career_title: str,
        readiness_pct: float,
        matched_names: List[str],
        weak_names: List[str],
        missing_names: List[str],
        high_priority_missing: List[str]
    ) -> str:
        """Generates a human-friendly, transparent justification for the recommendation."""
        # 1. 100% Achieved
        if readiness_pct >= 100.0 and not missing_names and not weak_names:
            return (
                f"You meet or exceed all required competencies for {career_title} (readiness: 100%). "
                f"Your profile is fully aligned and ready for this career pathway."
            )

        # 2. 0% Baseline
        if not matched_names and not weak_names:
            top_missing = ", ".join(missing_names[:3]) if missing_names else "prerequisite skills"
            return (
                f"You currently have no recorded prerequisites for {career_title} (readiness: 0%). "
                f"Foundational skills including {top_missing} should be prioritized first."
            )

        # 3. Partial Foundation
        matched_str = ", ".join(matched_names) if matched_names else "None"
        parts = []

        if matched_names:
            parts.append(
                f"Your existing {matched_str} skills provide a strong foundation for {career_title} "
                f"(readiness: {readiness_pct}%)."
            )
        elif weak_names:
            parts.append(
                f"You possess introductory background in {', '.join(weak_names)} (readiness: {readiness_pct}%)."
            )

        if high_priority_missing:
            parts.append(
                f"{', '.join(high_priority_missing)} are the highest-priority gaps for this pathway."
            )
        elif missing_names:
            parts.append(
                f"{', '.join(missing_names[:3])} are remaining skill gaps to acquire."
            )

        if weak_names and matched_names:
            parts.append(
                f"Reinforcing proficiency in {', '.join(weak_names)} will further accelerate role readiness."
            )

        return " ".join(parts)

    @classmethod
    def recommend_careers(
        cls,
        student_skills: List[Skill],
        domain_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluates and ranks all available careers for a student.
        """
        query = Career.query
        if domain_filter:
            query = query.filter(Career.domain.ilike(f"%{domain_filter}%"))

        careers = query.all()
        ranked_results = []

        for career in careers:
            gap_analysis = SkillGapService.evaluate_career_gap(career, student_skills)
            summary = gap_analysis["summary"]
            gaps = gap_analysis["prioritized_skill_gaps"]

            matched_skills = [
                g["skill_name"] for g in gaps
                if g["status"] in [SkillGapStatus.MATCHED, SkillGapStatus.EXCEEDS]
            ]
            weak_skills = [
                g["skill_name"] for g in gaps
                if g["status"] == SkillGapStatus.WEAK
            ]
            missing_skills = [
                g["skill_name"] for g in gaps
                if g["status"] == SkillGapStatus.MISSING
            ]
            high_priority_missing = [
                g["skill_name"] for g in gaps
                if g["status"] == SkillGapStatus.MISSING and (g["importance"] >= 4 or g["priority_score"] >= 15.0)
            ]

            readiness_pct = summary["readiness_percentage"]
            total_req = summary["total_required_skills"]
            distance = cls.calculate_skill_acquisition_distance(gaps)
            rec_score = cls.calculate_recommendation_score(
                readiness_pct,
                len(matched_skills),
                len(weak_skills),
                total_req,
                distance
            )

            explanation = cls.generate_recommendation_explanation(
                career.title,
                readiness_pct,
                matched_skills,
                weak_skills,
                missing_skills,
                high_priority_missing
            )

            ranked_results.append({
                "career_id": career.id,
                "career_title": career.title,
                "domain": career.domain,
                "description": career.description,
                "recommendation_score": rec_score,
                "readiness_percentage": readiness_pct,
                "skill_acquisition_distance": distance,
                "total_required_skills": total_req,
                "matched_skills": matched_skills,
                "weak_skills": weak_skills,
                "missing_skills": missing_skills,
                "high_priority_missing_skills": high_priority_missing,
                "explanation": explanation
            })

        # Rank deterministically: score desc, readiness desc, distance asc, title asc
        ranked_results.sort(
            key=lambda x: (
                -x["recommendation_score"],
                -x["readiness_percentage"],
                x["skill_acquisition_distance"],
                x["career_title"]
            )
        )

        if limit and limit > 0:
            return ranked_results[:limit]
        return ranked_results
