"""
Multi-Career Recommendation Service for AI Career Navigator.
Phase 9 Module 9.1: Multi-Factor Personalized Career Recommendation & Explainability Engine.

Scoring Model:
- Skill Fit: 50%
  (Blends readiness percentage, coverage, proximity, and optional ATS match)
- Preference Fit: 20%
  (Role alignment and domain preference matching)
- Market Demand: 15%
  (Labor market intelligence industry demand score)
- Academic Fit: 15%
  (Degree specialization, CGPA standing, and education level)

Formula:
  Final Score = 0.50 * Skill Fit + 0.20 * Preference Fit + 0.15 * Market Demand + 0.15 * Academic Fit
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from models.career import Career
from models.career_preference import CareerPreference
from models.student_profile import StudentProfile
from models.skill import Skill
from services.career_market_service import CareerMarketService
from services.skill_gap_service import SkillGapService, SkillGapStatus
from services.resume_extraction_service import ResumeExtractionService


class CareerRecommendationService:
    """Service for ranking and explaining career pathway recommendations."""

    # Module 9.1 Standard Multi-Factor Weights
    WEIGHT_SKILL = 0.50
    WEIGHT_PREFERENCE = 0.20
    WEIGHT_MARKET = 0.15
    WEIGHT_ACADEMIC = 0.15

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

    @classmethod
    def calculate_skill_fit(
        cls,
        readiness_pct: float,
        matched_count: int,
        weak_count: int,
        total_required: int,
        distance: float,
        ats_score: Optional[float] = None
    ) -> float:
        """
        Computes the normalized Skill Fit factor score (0.0 to 100.0).
        Blends proficiency readiness, skill coverage, acquisition proximity, and optional ATS match.
        """
        base_skill_score = cls.calculate_recommendation_score(
            readiness_pct, matched_count, weak_count, total_required, distance
        )
        if ats_score is not None:
            clamped_ats = max(0.0, min(100.0, float(ats_score)))
            blended = (0.85 * base_skill_score) + (0.15 * clamped_ats)
            return round(max(0.0, min(100.0, blended)), 1)
        return round(base_skill_score, 1)

    @classmethod
    def calculate_preference_fit(
        cls,
        career: Career,
        preference: Optional[CareerPreference]
    ) -> float:
        """
        Computes the normalized Preference Fit factor score (0.0 to 100.0).
        Evaluates student's target role and preferred domain against candidate career.
        Defaults to neutral 50.0 if no preference record is set.
        """
        if not preference:
            return 50.0

        pref_role = (preference.target_role or "").strip().lower()
        pref_domain = (preference.preferred_domain or "").strip().lower()
        career_title = (career.title or "").strip().lower()
        career_domain = (career.domain or "").strip().lower()

        # Role Alignment (weight: 55% of preference fit)
        if not pref_role:
            role_score = 50.0
        elif pref_role == career_title:
            role_score = 100.0
        elif pref_role in career_title or career_title in pref_role:
            role_score = 85.0
        else:
            pref_role_words = {w for w in re.findall(r"\w+", pref_role) if len(w) > 2}
            career_title_words = {w for w in re.findall(r"\w+", career_title) if len(w) > 2}
            if pref_role_words & career_title_words:
                role_score = 70.0
            else:
                role_score = 30.0

        # Domain Alignment (weight: 45% of preference fit)
        if not pref_domain:
            domain_score = 50.0
        elif pref_domain == career_domain:
            domain_score = 100.0
        elif pref_domain in career_domain or career_domain in pref_domain:
            domain_score = 80.0
        else:
            pref_dom_words = {w for w in re.findall(r"\w+", pref_domain) if len(w) > 2}
            career_dom_words = {w for w in re.findall(r"\w+", career_domain) if len(w) > 2}
            if pref_dom_words & career_dom_words:
                domain_score = 65.0
            else:
                domain_score = 25.0

        pref_score = (0.55 * role_score) + (0.45 * domain_score)
        return round(max(0.0, min(100.0, pref_score)), 1)

    @classmethod
    def calculate_market_demand(cls, career_id: int) -> float:
        """
        Computes the normalized Market Demand factor score (0.0 to 100.0).
        Reads labor market intelligence demand score (e.g., 92, 89, 95).
        """
        outlook = CareerMarketService.get_market_outlook_by_career_id(career_id)
        if outlook and "demand_score" in outlook:
            demand = float(outlook["demand_score"])
        else:
            demand = 70.0
        return round(max(0.0, min(100.0, demand)), 1)

    @classmethod
    def calculate_academic_fit(
        cls,
        career: Career,
        profile: Optional[StudentProfile]
    ) -> float:
        """
        Computes the normalized Academic Fit factor score (0.0 to 100.0).
        Evaluates student's degree specialization, academic standing (CGPA), and education level.
        Defaults to neutral 50.0 if no profile is set.
        """
        if not profile:
            return 50.0

        spec = (profile.specialization or "").strip().lower()
        edu = (profile.education or "").strip().lower()
        combined_academic = f"{spec} {edu}".strip()
        career_title = (career.title or "").strip().lower()
        career_domain = (career.domain or "").strip().lower()
        career_desc = (career.description or "").strip().lower()

        # Specialization Match (weight: 60% of academic fit)
        if not combined_academic:
            spec_score = 65.0
        elif spec and (spec == career_title or spec == career_domain):
            spec_score = 100.0
        elif spec and (spec in career_title or spec in career_domain or career_title in spec or career_domain in spec):
            spec_score = 95.0
        else:
            academic_tokens = {w for w in re.findall(r"\w+", combined_academic) if len(w) > 2}
            career_tokens = {w for w in re.findall(r"\w+", f"{career_title} {career_domain} {career_desc}") if len(w) > 2}

            direct_overlap = academic_tokens & career_tokens
            
            stem_matches = 0
            for a_tok in academic_tokens:
                for c_tok in career_tokens:
                    if a_tok == c_tok:
                        stem_matches += 1
                        break
                    elif len(a_tok) >= 4 and len(c_tok) >= 4 and (a_tok[:4] == c_tok[:4] or a_tok in c_tok or c_tok in a_tok):
                        stem_matches += 1
                        break

            is_computing_bg = any(k in combined_academic for k in ["computer", "computing", "software", "information technology"])

            if len(direct_overlap) >= 2 or stem_matches >= 2:
                spec_score = 92.0
            elif len(direct_overlap) == 1 or stem_matches == 1:
                spec_score = 88.0 if is_computing_bg else 75.0
            elif is_computing_bg:
                spec_score = 80.0
            else:
                spec_score = 45.0

        # CGPA Standing (weight: 25% of academic fit)
        cgpa = profile.cgpa
        if cgpa is not None and cgpa > 0:
            if cgpa > 4.0:
                # 10-point scale
                if cgpa >= 8.5:
                    cgpa_score = 95.0
                elif cgpa >= 7.5:
                    cgpa_score = 85.0
                elif cgpa >= 6.5:
                    cgpa_score = 75.0
                else:
                    cgpa_score = 60.0
            else:
                # 4-point scale
                if cgpa >= 3.7:
                    cgpa_score = 95.0
                elif cgpa >= 3.2:
                    cgpa_score = 85.0
                elif cgpa >= 2.8:
                    cgpa_score = 75.0
                else:
                    cgpa_score = 60.0
        else:
            cgpa_score = 75.0

        # Education Level (weight: 15% of academic fit)
        if any(deg in edu for deg in ["master", "m.tech", "ms", "phd", "postgraduate"]):
            edu_score = 95.0
        elif any(deg in edu for deg in ["bachelor", "b.tech", "bs", "be", "undergraduate", "b.sc"]):
            edu_score = 85.0
        elif edu:
            edu_score = 75.0
        else:
            edu_score = 70.0

        acad_fit = (0.60 * spec_score) + (0.25 * cgpa_score) + (0.15 * edu_score)
        return round(max(0.0, min(100.0, acad_fit)), 1)

    @classmethod
    def calculate_multi_factor_score(
        cls,
        skill_fit: float,
        preference_fit: float,
        market_demand: float,
        academic_fit: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates deterministic multi-factor recommendation score using the approved Phase 9 formula:
            Final Score = 0.50 * Skill Fit + 0.20 * Preference Fit + 0.15 * Market Demand + 0.15 * Academic Fit
        Returns final score and factor breakdown dictionary.
        """
        skill_contrib = round(cls.WEIGHT_SKILL * skill_fit, 1)
        pref_contrib = round(cls.WEIGHT_PREFERENCE * preference_fit, 1)
        market_contrib = round(cls.WEIGHT_MARKET * market_demand, 1)
        academic_contrib = round(cls.WEIGHT_ACADEMIC * academic_fit, 1)

        final_score = round(skill_contrib + pref_contrib + market_contrib + academic_contrib, 1)
        final_score = max(0.0, min(100.0, final_score))

        factor_breakdown = {
            "skill_fit": {
                "score": skill_fit,
                "weight": cls.WEIGHT_SKILL,
                "weighted_contribution": skill_contrib
            },
            "preference_fit": {
                "score": preference_fit,
                "weight": cls.WEIGHT_PREFERENCE,
                "weighted_contribution": pref_contrib
            },
            "market_demand": {
                "score": market_demand,
                "weight": cls.WEIGHT_MARKET,
                "weighted_contribution": market_contrib
            },
            "academic_fit": {
                "score": academic_fit,
                "weight": cls.WEIGHT_ACADEMIC,
                "weighted_contribution": academic_contrib
            }
        }
        return final_score, factor_breakdown

    @staticmethod
    def generate_multi_factor_justification(
        career_title: str,
        final_score: float,
        skill_fit: float,
        preference_fit: float,
        market_demand: float,
        academic_fit: float
    ) -> str:
        """Generates an explainable justification for the multi-factor recommendation score."""
        factors = [
            ("Skill Match", skill_fit, 0.50),
            ("Career Preference", preference_fit, 0.20),
            ("Market Demand", market_demand, 0.15),
            ("Academic Foundation", academic_fit, 0.15),
        ]
        sorted_factors = sorted(factors, key=lambda f: f[1], reverse=True)
        top_factor_name = sorted_factors[0][0]
        top_factor_score = sorted_factors[0][1]

        parts = [
            f"Overall recommendation score for {career_title} is {final_score}/100, combining: "
            f"Skill Fit ({skill_fit}/100 @ 50%), "
            f"Preference Fit ({preference_fit}/100 @ 20%), "
            f"Market Demand ({market_demand}/100 @ 15%), and "
            f"Academic Fit ({academic_fit}/100 @ 15%)."
        ]
        if top_factor_score >= 80.0:
            parts.append(f"Strongest alignment is in {top_factor_name} ({top_factor_score}/100).")
        return " ".join(parts)

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
        student_skills: Optional[List[Skill]] = None,
        domain_filter: Optional[str] = None,
        limit: Optional[int] = None,
        user_id: Optional[int] = None,
        is_personalized: bool = False,
        resume_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluates and ranks all available careers for a student.
        - When is_personalized=True: Computes multi-factor score (Skill Fit 50%, Preference Fit 20%,
          Market Demand 15%, Academic Fit 15%), along with factor breakdown and explainability justification.
        - When is_personalized=False: Falls back to baseline skill-only recommendation score.
        """
        if student_skills is None:
            student_skills = []

        query = Career.query
        if domain_filter:
            query = query.filter(Career.domain.ilike(f"%{domain_filter}%"))

        careers = query.all()
        ranked_results = []

        # Load user context if personalized
        preference = None
        profile = None
        if is_personalized and user_id:
            preference = CareerPreference.query.filter_by(user_id=user_id).first()
            profile = StudentProfile.query.filter_by(user_id=user_id).first()

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

            # Skill Fit / Legacy recommendation score
            ats_score = None
            if resume_text and resume_text.strip():
                try:
                    ats_res = ResumeExtractionService.score_resume_against_career(resume_text, career.id)
                    if ats_res:
                        ats_score = float(ats_res.get("ats_score", 0.0))
                except Exception:
                    ats_score = None

            skill_fit = cls.calculate_skill_fit(
                readiness_pct,
                len(matched_skills),
                len(weak_skills),
                total_req,
                distance,
                ats_score=ats_score
            )

            explanation = cls.generate_recommendation_explanation(
                career.title,
                readiness_pct,
                matched_skills,
                weak_skills,
                missing_skills,
                high_priority_missing
            )

            if is_personalized:
                preference_fit = cls.calculate_preference_fit(career, preference)
                market_demand = cls.calculate_market_demand(career.id)
                academic_fit = cls.calculate_academic_fit(career, profile)

                final_score, factor_breakdown = cls.calculate_multi_factor_score(
                    skill_fit=skill_fit,
                    preference_fit=preference_fit,
                    market_demand=market_demand,
                    academic_fit=academic_fit
                )

                multi_justification = cls.generate_multi_factor_justification(
                    career_title=career.title,
                    final_score=final_score,
                    skill_fit=skill_fit,
                    preference_fit=preference_fit,
                    market_demand=market_demand,
                    academic_fit=academic_fit
                )

                ranked_results.append({
                    "career_id": career.id,
                    "career_title": career.title,
                    "domain": career.domain,
                    "description": career.description,
                    "recommendation_score": final_score,
                    "final_score": final_score,
                    "is_personalized": True,
                    "factor_breakdown": factor_breakdown,
                    "multi_factor_justification": multi_justification,
                    "readiness_percentage": readiness_pct,
                    "skill_acquisition_distance": distance,
                    "total_required_skills": total_req,
                    "matched_skills": matched_skills,
                    "weak_skills": weak_skills,
                    "missing_skills": missing_skills,
                    "high_priority_missing_skills": high_priority_missing,
                    "explanation": explanation
                })
            else:
                # Unauthenticated / skill-only baseline mode
                market_demand = cls.calculate_market_demand(career.id)
                factor_breakdown = {
                    "skill_fit": {
                        "score": skill_fit,
                        "weight": 1.0,
                        "weighted_contribution": skill_fit
                    },
                    "preference_fit": {
                        "score": None,
                        "weight": 0.0,
                        "weighted_contribution": 0.0
                    },
                    "market_demand": {
                        "score": market_demand,
                        "weight": 0.0,
                        "weighted_contribution": 0.0
                    },
                    "academic_fit": {
                        "score": None,
                        "weight": 0.0,
                        "weighted_contribution": 0.0
                    }
                }

                ranked_results.append({
                    "career_id": career.id,
                    "career_title": career.title,
                    "domain": career.domain,
                    "description": career.description,
                    "recommendation_score": skill_fit,
                    "final_score": skill_fit,
                    "is_personalized": False,
                    "factor_breakdown": factor_breakdown,
                    "multi_factor_justification": None,
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
