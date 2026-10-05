"""
Career Transition Pathway Service for AI Career Navigator.

Analyzes career-to-career lateral and vertical transitions (e.g. Software Developer -> Cloud Engineer).
Identifies overlapping skills, transferable skills (using O*NET provenance),
missing competencies, transition difficulty tiers, and explainable guidance.
"""

import os
import csv
from typing import Any, Dict, List, Optional, Set
from models.career import Career
from models.canonical_skill import CanonicalSkill
from utils.normalization import normalize_skill_name


ONET_TRANSFERABLE_CSV = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/processed/onet/transferable_skill_candidates.csv")
)


def load_onet_transferable_set() -> Set[str]:
    """Loads normalized O*NET transferable skill terms from processed dataset."""
    terms = set()
    if os.path.exists(ONET_TRANSFERABLE_CSV):
        try:
            with open(ONET_TRANSFERABLE_CSV, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    norm = row.get("normalized_name")
                    if norm:
                        terms.add(norm.strip().lower())
        except Exception:
            pass
    # Baseline fallback if CSV not reachable
    if not terms:
        terms = {
            "programming", "complex problem solving", "troubleshooting",
            "systems analysis", "technology design", "operations analysis",
            "critical thinking", "mathematics", "active learning"
        }
    return terms


class CareerTransitionService:
    """Service for career-to-career transition analysis."""

    _onet_transferable_terms: Optional[Set[str]] = None

    @classmethod
    def get_onet_transferable_terms(cls) -> Set[str]:
        if cls._onet_transferable_terms is None:
            cls._onet_transferable_terms = load_onet_transferable_set()
        return cls._onet_transferable_terms

    @classmethod
    def is_transferable(cls, skill_name: str, canonical_skill: Optional[CanonicalSkill] = None) -> bool:
        """Determines if a skill is recognized as a transferable competency."""
        norm = normalize_skill_name(skill_name)
        terms = cls.get_onet_transferable_terms()
        if norm in terms:
            return True
        if canonical_skill and canonical_skill.skill_type:
            st = canonical_skill.skill_type.lower()
            if "transferable" in st or "soft" in st or "cross-functional" in st:
                return True
        # Check domain-agnostic foundational programming/data competencies
        foundational = {"python", "git", "sql", "data structures", "linux", "programming"}
        return norm in foundational

    @classmethod
    def analyze_transition(
        cls,
        source_career_id: int,
        target_career_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Performs in-depth comparative transition analysis between two careers.
        """
        source_career = Career.query.get(source_career_id)
        target_career = Career.query.get(target_career_id)

        if not source_career or not target_career:
            return None

        # Index source career skills by canonical_skill_id and normalized name
        source_by_canonical = {}
        source_by_name = {}

        for cs in source_career.skills:
            if cs.canonical_skill_id:
                source_by_canonical[cs.canonical_skill_id] = cs
            norm = normalize_skill_name(cs.skill_name)
            source_by_name[norm] = cs

        target_skills = target_career.skills
        total_target_req_points = sum(cs.required_level for cs in target_skills) or 1.0

        overlapping_skills: List[Dict[str, Any]] = []
        transferable_skills: List[Dict[str, Any]] = []
        additional_skills: List[Dict[str, Any]] = []
        achieved_points = 0.0

        target_matched_source_ids = set()

        for t_cs in target_skills:
            t_req = t_cs.required_level
            t_imp = t_cs.importance
            t_norm = normalize_skill_name(t_cs.skill_name)

            # Match in source
            matched_src = None
            if t_cs.canonical_skill_id and t_cs.canonical_skill_id in source_by_canonical:
                matched_src = source_by_canonical[t_cs.canonical_skill_id]
            elif t_norm in source_by_name:
                matched_src = source_by_name[t_norm]

            is_trans = cls.is_transferable(t_cs.skill_name, t_cs.canonical_skill)

            if matched_src:
                target_matched_source_ids.add(matched_src.id)
                s_req = matched_src.required_level
                transfer_level = min(s_req, t_req)
                achieved_points += transfer_level

                level_gap = max(0, t_req - s_req)
                if s_req >= t_req:
                    status = "DIRECT_TRANSFER"
                    desc = f"Direct transfer: Source proficiency level {s_req}/5 satisfies target role requirement ({t_req}/5)."
                else:
                    status = "SKILL_UPGRADE_NEEDED"
                    desc = f"Proficiency upgrade needed: Source requires level {s_req}/5, but target requires level {t_req}/5 (gap: {level_gap})."

                item = {
                    "skill_name": t_cs.skill_name,
                    "canonical_skill_id": t_cs.canonical_skill_id,
                    "source_required_level": s_req,
                    "target_required_level": t_req,
                    "target_importance": t_imp,
                    "level_gap": level_gap,
                    "status": status,
                    "is_onet_transferable": is_trans,
                    "description": desc
                }
                overlapping_skills.append(item)

                if is_trans:
                    transferable_skills.append(item)
            else:
                # Skill is missing from source career
                add_item = {
                    "skill_name": t_cs.skill_name,
                    "canonical_skill_id": t_cs.canonical_skill_id,
                    "target_required_level": t_req,
                    "target_importance": t_imp,
                    "status": "NEW_SKILL_REQUIRED",
                    "is_onet_transferable": is_trans,
                    "description": f"New competency required: '{t_cs.skill_name}' is required at level {t_req}/5 (importance: {t_imp}/5)."
                }
                additional_skills.append(add_item)

        # Identify surplus skills in source that are not in target
        surplus_skills = [
            {
                "skill_name": cs.skill_name,
                "canonical_skill_id": cs.canonical_skill_id,
                "source_level": cs.required_level,
                "importance_in_source": cs.importance,
                "note": "Complementary domain knowledge from source career."
            }
            for cs in source_career.skills
            if cs.id not in target_matched_source_ids
        ]

        # Calculate metrics
        total_target_count = len(target_skills) or 1
        overlap_count = len(overlapping_skills)
        missing_count = len(additional_skills)

        overlap_percentage = round((overlap_count / float(total_target_count)) * 100.0, 1)
        estimated_readiness = round((achieved_points / float(total_target_req_points)) * 100.0, 1)

        # Transition Difficulty tiering
        if estimated_readiness >= 65.0 and missing_count <= 1:
            difficulty = "LOW"
            difficulty_label = "Smooth Lateral Transition"
        elif estimated_readiness >= 35.0 and missing_count <= 3:
            difficulty = "MODERATE"
            difficulty_label = "Moderate Upskilling Transition"
        else:
            difficulty = "HIGH"
            difficulty_label = "Significant Cross-Domain Pivot"

        # Generate human-readable explainable summary
        overlap_names = [o["skill_name"] for o in overlapping_skills]
        additional_names = [a["skill_name"] for a in additional_skills]

        summary_parts = []
        if overlap_names:
            summary_parts.append(
                f"Transitioning from {source_career.title} to {target_career.title} benefits from "
                f"{len(overlap_names)} overlapping competency area(s): {', '.join(overlap_names)} "
                f"({overlap_percentage}% requirement overlap, estimated readiness: {estimated_readiness}%)."
            )
        else:
            summary_parts.append(
                f"There is minimal direct skill overlap between {source_career.title} and {target_career.title}."
            )

        if additional_names:
            summary_parts.append(
                f"The primary transition hurdles involve acquiring {len(additional_names)} new skill(s): "
                f"{', '.join(additional_names)}."
            )

        summary_parts.append(f"Overall transition difficulty is evaluated as {difficulty} ({difficulty_label}).")
        explanation = " ".join(summary_parts)

        return {
            "source_career": {
                "id": source_career.id,
                "title": source_career.title,
                "domain": source_career.domain
            },
            "target_career": {
                "id": target_career.id,
                "title": target_career.title,
                "domain": target_career.domain
            },
            "transition_summary": {
                "overlap_percentage": overlap_percentage,
                "estimated_readiness_percentage": estimated_readiness,
                "transition_difficulty": difficulty,
                "difficulty_label": difficulty_label,
                "total_target_skills": len(target_skills),
                "overlapping_skills_count": overlap_count,
                "additional_skills_count": missing_count,
                "explanation": explanation
            },
            "overlapping_skills": overlapping_skills,
            "transferable_skills": transferable_skills,
            "additional_skills_required": additional_skills,
            "surplus_source_skills": surplus_skills
        }
