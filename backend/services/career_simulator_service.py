"""
Interactive Career Skill Simulator Service for AI Career Navigator.
Phase 9 Module 9.4: "What If I Learn Skill X?" Interactive Career Simulator.

Provides:
- In-memory hypothetical simulation of acquiring or upgrading a skill.
- Deterministic calculation of current state vs simulated state (readiness, missing skills, study timeline).
- Cross-pathway impact analysis reflecting Module 9.3 specialization tracks.
- Explainable, transparent impact narrative and newly satisfied competency detection.
- Strict safety guarantee: ZERO modifications to database, student profile, or career requirements.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func

from extensions import db
from models.canonical_skill import CanonicalSkill
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from models.skill_alias import SkillAlias
from services.career_pathway_service import CareerPathwayService
from services.roadmap_service import RoadmapService
from services.skill_gap_service import SkillGapService, SkillGapStatus
from utils.normalization import normalize_skill_name


class CareerSimulatorService:
    """Service providing in-memory deterministic simulation of skill acquisition impacts."""

    @classmethod
    def resolve_skill(
        cls,
        skill_id: Optional[Any] = None,
        skill_name: Optional[str] = None,
        career_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Resolves a skill by canonical ID, canonical name, recognized alias, or career skill ID.
        Returns a dictionary with canonical ID, resolved canonical name, and normalized name,
        or None if resolution fails.
        """
        # 1. Resolve by numeric skill_id
        if skill_id is not None:
            try:
                sid = int(skill_id)
                # Check CanonicalSkill by primary key
                cs = CanonicalSkill.query.get(sid)
                if cs:
                    return {
                        "id": cs.id,
                        "canonical_skill_id": cs.id,
                        "name": cs.canonical_name,
                        "normalized_name": cs.normalized_name,
                        "skill_type": cs.skill_type
                    }

                # Check CareerSkill by ID if career_id provided or directly
                c_skill = CareerSkill.query.get(sid)
                if c_skill:
                    c_id = c_skill.canonical_skill_id
                    if c_id:
                        cs = CanonicalSkill.query.get(c_id)
                        if cs:
                            return {
                                "id": cs.id,
                                "canonical_skill_id": cs.id,
                                "name": cs.canonical_name,
                                "normalized_name": cs.normalized_name,
                                "skill_type": cs.skill_type
                            }
                    norm = normalize_skill_name(c_skill.skill_name)
                    return {
                        "id": sid,
                        "canonical_skill_id": None,
                        "name": c_skill.skill_name,
                        "normalized_name": norm,
                        "skill_type": "Career Competency"
                    }
            except (ValueError, TypeError):
                pass

        # 2. Resolve by skill_name string
        if skill_name:
            norm_query = normalize_skill_name(str(skill_name).strip())

            # Check CanonicalSkill exact normalized match
            cs = CanonicalSkill.query.filter_by(normalized_name=norm_query).first()
            if cs:
                return {
                    "id": cs.id,
                    "canonical_skill_id": cs.id,
                    "name": cs.canonical_name,
                    "normalized_name": cs.normalized_name,
                    "skill_type": cs.skill_type
                }

            # Check SkillAlias exact normalized alias match
            alias = SkillAlias.query.filter_by(normalized_alias=norm_query).first()
            if alias and alias.canonical_skill:
                cs = alias.canonical_skill
                return {
                    "id": cs.id,
                    "canonical_skill_id": cs.id,
                    "name": cs.canonical_name,
                    "normalized_name": cs.normalized_name,
                    "skill_type": cs.skill_type
                }

            # Check career skills for this specific career
            if career_id:
                career_match = CareerSkill.query.filter(
                    CareerSkill.career_id == career_id,
                    func.lower(CareerSkill.skill_name) == norm_query
                ).first()
                if career_match:
                    c_id = career_match.canonical_skill_id
                    if c_id:
                        cs = CanonicalSkill.query.get(c_id)
                        if cs:
                            return {
                                "id": cs.id,
                                "canonical_skill_id": cs.id,
                                "name": cs.canonical_name,
                                "normalized_name": cs.normalized_name,
                                "skill_type": cs.skill_type
                            }
                    return {
                        "id": career_match.id,
                        "canonical_skill_id": None,
                        "name": career_match.skill_name,
                        "normalized_name": norm_query,
                        "skill_type": "Career Competency"
                    }

        return None

    @classmethod
    def normalize_proficiency_inputs(
        cls,
        simulated_level_raw: Any
    ) -> Tuple[float, int]:
        """
        Normalizes simulated proficiency input into:
        - normalized_level (1.0 to 5.0 scale)
        - raw_proficiency (1 to 10 scale)
        Raises ValueError if outside valid range.
        """
        try:
            val = float(simulated_level_raw)
        except (ValueError, TypeError):
            raise ValueError("simulated_level must be a numeric value")

        if val < 1.0 or val > 10.0:
            raise ValueError("simulated_level must be between 1 and 5 (career scale) or 1 and 10 (raw scale)")

        if val <= 5.0:
            # 1 to 5 career scale
            norm_level = round(val, 1)
            raw_prof = int(round(val * 2.0))
        else:
            # 6 to 10 student raw scale
            raw_prof = int(round(val))
            norm_level = round(val / 2.0, 1)

        return norm_level, raw_prof

    @classmethod
    def simulate_skill_impact(
        cls,
        career_id: int,
        skill_id: Optional[Any] = None,
        skill_name: Optional[str] = None,
        simulated_level: Optional[Any] = None,
        user_id: Optional[int] = None,
        hours_per_week: int = 10
    ) -> Dict[str, Any]:
        """
        Executes in-memory what-if simulation for a candidate skill improvement.
        Strictly immutable with zero database persistence.
        """
        # 1. Validate career
        career = Career.query.get(career_id)
        if not career:
            return {"error": "CAREER_NOT_FOUND", "message": f"Career with ID {career_id} not found"}

        # 2. Resolve skill
        resolved_skill = cls.resolve_skill(skill_id=skill_id, skill_name=skill_name, career_id=career_id)
        if not resolved_skill:
            return {
                "error": "SKILL_NOT_FOUND",
                "message": "Skill could not be resolved. Please provide a valid skill ID, canonical name, or recognized alias."
            }

        # 3. Validate and normalize simulated proficiency
        if simulated_level is None:
            return {"error": "INVALID_PROFICIENCY", "message": "simulated_level is required"}

        try:
            sim_norm_level, sim_raw_prof = cls.normalize_proficiency_inputs(simulated_level)
        except ValueError as e:
            return {"error": "INVALID_PROFICIENCY", "message": str(e)}

        # 4. Fetch current student skills (read-only)
        student_skills: List[Skill] = []
        if user_id:
            student_skills = Skill.query.filter_by(user_id=user_id).all()

        # Find student's current proficiency in this skill
        target_canonical_id = resolved_skill.get("canonical_skill_id")
        target_norm_name = resolved_skill["normalized_name"]

        current_raw_prof = 0
        current_skill_obj: Optional[Skill] = None

        for s in student_skills:
            if target_canonical_id and s.canonical_skill_id == target_canonical_id:
                current_skill_obj = s
                current_raw_prof = s.proficiency or 0
                break
            elif normalize_skill_name(s.skill_name) == target_norm_name:
                current_skill_obj = s
                current_raw_prof = s.proficiency or 0
                break

        current_norm_level = round(current_raw_prof / 2.0, 1)

        # 5. Evaluate CURRENT state for career
        curr_gap_analysis = SkillGapService.evaluate_career_gap(career, student_skills)
        curr_summary = curr_gap_analysis["summary"]
        curr_readiness = curr_summary["readiness_percentage"]
        curr_gaps = curr_gap_analysis["prioritized_skill_gaps"]

        curr_missing = [g["skill_name"] for g in curr_gaps if g["status"] == SkillGapStatus.MISSING]
        curr_weak = [g["skill_name"] for g in curr_gaps if g["status"] == SkillGapStatus.WEAK]

        curr_roadmap = RoadmapService.generate_roadmap(career.title, curr_gaps, hours_per_week=hours_per_week)
        curr_study_plan = curr_roadmap.get("study_plan") or {}
        curr_study_hours = curr_study_plan.get("estimated_total_hours", 0)
        curr_study_weeks = curr_study_plan.get("estimated_weeks", 0)

        # 6. Build in-memory SIMULATED skills list (immutable copy)
        # Note: We do NOT add or commit to db.session!
        simulated_skills: List[Skill] = []
        skill_updated = False

        for s in student_skills:
            if (target_canonical_id and s.canonical_skill_id == target_canonical_id) or (
                normalize_skill_name(s.skill_name) == target_norm_name
            ):
                # Update proficiency in memory only
                simulated_skills.append(
                    Skill(
                        user_id=s.user_id,
                        skill_name=s.skill_name,
                        canonical_skill_id=s.canonical_skill_id,
                        proficiency=sim_raw_prof
                    )
                )
                skill_updated = True
            else:
                simulated_skills.append(
                    Skill(
                        user_id=s.user_id,
                        skill_name=s.skill_name,
                        canonical_skill_id=s.canonical_skill_id,
                        proficiency=s.proficiency
                    )
                )

        if not skill_updated:
            # Add new skill to simulated list in memory
            simulated_skills.append(
                Skill(
                    user_id=user_id or 0,
                    skill_name=resolved_skill["name"],
                    canonical_skill_id=target_canonical_id,
                    proficiency=sim_raw_prof
                )
            )

        # 7. Evaluate SIMULATED state for career
        sim_gap_analysis = SkillGapService.evaluate_career_gap(career, simulated_skills)
        sim_summary = sim_gap_analysis["summary"]
        sim_readiness = sim_summary["readiness_percentage"]
        sim_gaps = sim_gap_analysis["prioritized_skill_gaps"]

        sim_missing = [g["skill_name"] for g in sim_gaps if g["status"] == SkillGapStatus.MISSING]
        sim_weak = [g["skill_name"] for g in sim_gaps if g["status"] == SkillGapStatus.WEAK]

        sim_roadmap = RoadmapService.generate_roadmap(career.title, sim_gaps, hours_per_week=hours_per_week)
        sim_study_plan = sim_roadmap.get("study_plan") or {}
        sim_study_hours = sim_study_plan.get("estimated_total_hours", 0)
        sim_study_weeks = sim_study_plan.get("estimated_weeks", 0)

        # 8. Compute Impact Differentials
        readiness_gain = round(max(0.0, sim_readiness - curr_readiness), 1)
        hours_saved = max(0, curr_study_hours - sim_study_hours)
        weeks_saved = max(0, curr_study_weeks - sim_study_weeks)

        # Check if the skill is actually required by this career
        career_req_skills = {normalize_skill_name(cs.skill_name): cs for cs in career.skills}
        is_required_by_career = target_norm_name in career_req_skills
        career_req_level = career_req_skills[target_norm_name].required_level if is_required_by_career else None
        career_importance = career_req_skills[target_norm_name].importance if is_required_by_career else None

        # Detect newly satisfied skills (changed from MISSING/WEAK to MATCHED/EXCEEDS)
        curr_status_by_name = {g["skill_name"]: g["status"] for g in curr_gaps}
        sim_status_by_name = {g["skill_name"]: g["status"] for g in sim_gaps}

        newly_satisfied_skills = []
        for sname, s_curr_st in curr_status_by_name.items():
            s_sim_st = sim_status_by_name.get(sname)
            if s_curr_st in [SkillGapStatus.MISSING, SkillGapStatus.WEAK] and s_sim_st in [
                SkillGapStatus.MATCHED, SkillGapStatus.EXCEEDS
            ]:
                newly_satisfied_skills.append({
                    "skill_name": sname,
                    "previous_status": s_curr_st,
                    "simulated_status": s_sim_st
                })

        remaining_gaps = [
            {
                "skill_name": g["skill_name"],
                "required_level": g["required_level"],
                "simulated_proficiency": g["current_proficiency"],
                "status": g["status"],
                "priority_level": g["priority_level"]
            }
            for g in sim_gaps
            if g["status"] in [SkillGapStatus.MISSING, SkillGapStatus.WEAK]
        ]

        # 9. Evaluate Specialization Pathway Impacts (Module 9.3 Integration)
        pathway_impacts = []
        curr_pathways_data = CareerPathwayService.evaluate_career_pathways(
            career_id=career.id, user_id=user_id, hours_per_week=hours_per_week
        )
        if curr_pathways_data and curr_pathways_data.get("pathways"):
            config = CareerPathwayService.get_pathway_configuration(career)
            raw_pathways = config.get("pathways", [])

            for pdef in raw_pathways:
                p_id = pdef["id"]
                curr_p = next((p for p in curr_pathways_data["pathways"] if p["id"] == p_id), None)
                sim_p = CareerPathwayService.evaluate_pathway_for_student(
                    career=career,
                    pathway_def=pdef,
                    student_skills=simulated_skills,
                    hours_per_week=hours_per_week
                )

                if curr_p and sim_p:
                    c_p_readiness = curr_p["readiness_percentage"]
                    s_p_readiness = sim_p["readiness_percentage"]
                    p_gain = round(max(0.0, s_p_readiness - c_p_readiness), 1)

                    # Check if the simulated skill is part of this pathway
                    p_core = [normalize_skill_name(x) for x in pdef.get("core_skill_names", [])]
                    p_elective = [normalize_skill_name(x) for x in pdef.get("elective_skill_names", [])]
                    is_in_pathway = (target_norm_name in p_core) or (target_norm_name in p_elective)

                    pathway_impacts.append({
                        "pathway_id": p_id,
                        "pathway_name": pdef["name"],
                        "specialization_focus": pdef.get("specialization_focus", ""),
                        "is_relevant_to_pathway": is_in_pathway,
                        "current_readiness": c_p_readiness,
                        "simulated_readiness": s_p_readiness,
                        "readiness_gain": p_gain,
                        "current_weeks": curr_p["estimated_weeks"],
                        "simulated_weeks": sim_p["estimated_weeks"],
                        "weeks_saved": max(0, curr_p["estimated_weeks"] - sim_p["estimated_weeks"]),
                        "simulated_effort_tier": sim_p["effort_tier_label"]
                    })

        # 10. Generate Transparent, Explainable Explanation
        if not is_required_by_career:
            explanation = (
                f"The skill '{resolved_skill['name']}' is not a mandatory or elective requirement "
                f"for the {career.title} track. While valuable for general development, simulating an "
                f"increase to Level {sim_norm_level} yields no direct readiness increase for this role."
            )
        elif readiness_gain > 0:
            explanation = (
                f"Advancing '{resolved_skill['name']}' from Level {current_norm_level}/5 to Level {sim_norm_level}/5 "
                f"improves your overall readiness for {career.title} by +{readiness_gain} percentage points "
                f"(from {curr_readiness}% to {sim_readiness}%). This reduces your remaining study workload by "
                f"~{weeks_saved} study week(s) ({hours_saved} hours) at {hours_per_week} hrs/week."
            )
        else:
            if current_norm_level >= (career_req_level or 5):
                explanation = (
                    f"Your current proficiency in '{resolved_skill['name']}' ({current_norm_level}/5) "
                    f"already satisfies the role requirement ({career_req_level}/5). "
                    f"Simulating an upgrade to Level {sim_norm_level}/5 demonstrates extra mastery but does not "
                    f"change your baseline career readiness percentage."
                )
            elif sim_norm_level <= current_norm_level:
                explanation = (
                    f"The simulated proficiency of Level {sim_norm_level}/5 is not higher than your "
                    f"current proficiency of Level {current_norm_level}/5, resulting in zero readiness gain."
                )
            else:
                explanation = (
                    f"Simulating '{resolved_skill['name']}' at Level {sim_norm_level}/5 narrows your competency gap, "
                    f"but remains below the role requirement of Level {career_req_level}/5, yielding 0 percentage points gain in full readiness."
                )

        return {
            "career_id": career.id,
            "career_title": career.title,
            "career_domain": career.domain,
            "hours_per_week": hours_per_week,
            "skill": {
                "id": resolved_skill["id"],
                "canonical_skill_id": resolved_skill["canonical_skill_id"],
                "name": resolved_skill["name"],
                "is_required_by_career": is_required_by_career,
                "career_required_level": career_req_level,
                "career_importance": career_importance,
                "current_level": current_norm_level,
                "current_raw_proficiency": current_raw_prof,
                "simulated_level": sim_norm_level,
                "simulated_raw_proficiency": sim_raw_prof,
            },
            "current_state": {
                "readiness_percentage": curr_readiness,
                "matched_skills_count": curr_summary["matched_skills"],
                "weak_skills_count": curr_summary["weak_skills"],
                "missing_skills_count": curr_summary["missing_skills"],
                "missing_skills": curr_missing,
                "weak_skills": curr_weak,
                "estimated_total_hours": curr_study_hours,
                "estimated_weeks": curr_study_weeks,
            },
            "simulated_state": {
                "readiness_percentage": sim_readiness,
                "matched_skills_count": sim_summary["matched_skills"],
                "weak_skills_count": sim_summary["weak_skills"],
                "missing_skills_count": sim_summary["missing_skills"],
                "missing_skills": sim_missing,
                "weak_skills": sim_weak,
                "estimated_total_hours": sim_study_hours,
                "estimated_weeks": sim_study_weeks,
            },
            "impact": {
                "readiness_gain": readiness_gain,
                "hours_saved": hours_saved,
                "weeks_saved": weeks_saved,
                "newly_satisfied_skills": newly_satisfied_skills,
                "remaining_gaps": remaining_gaps,
                "pathway_impacts": pathway_impacts,
            },
            "explanation": explanation,
        }
