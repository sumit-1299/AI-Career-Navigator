"""
Career Action Center Orchestration Service for AI Career Navigator.
Phase 12 Module 12.2: Live Job Opportunity Intelligence & Career Action Center.

This orchestration service combines outputs from existing, verified intelligence engines:
1. LiveJobsService (listing, parsing, caching, matching)
2. CareerRecommendationService & Career model (deterministic career mapping)
3. SkillRoiService (Phase 11.1 explainable ROI for missing job skills)
4. PortfolioProjectService (Phase 11.2 capstone project recommendations closing gaps)
5. IndustryDemandService (Phase 11.4 dynamic skill demand benchmarks)
6. CareerTrajectoryService (Phase 11.5 multi-hop transition intelligence)
7. InterviewSimulationService (Phase 11.6 interview readiness assessment)

SAFETY & DESIGN GUARANTEES:
- Strictly read-only orchestration. ZERO database writes, ZERO schema mutations.
- Does NOT duplicate job fetching, matching algorithms, or intelligence engines.
- Distinguishes JOB MATCH SCORE (vacancy skill overlap) from CAREER READINESS SCORE (holistic qualification).
- Enforces strict educational tone: NO employment guarantees, NO placement promises.
- Preserves DEMO / SAMPLE / PROTOTYPE research provenance on industry demand benchmarks.
"""

from typing import Any, Dict, List, Optional
import re

from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from services.live_jobs_service import LiveJobsService
from services.skill_roi_service import SkillRoiService
from services.portfolio_project_service import PortfolioProjectService
from services.industry_demand_service import IndustryDemandService
from services.career_trajectory_service import CareerTrajectoryService
from services.interview_simulation_service import InterviewSimulationService
from utils.normalization import normalize_skill_name


class JobActionCenterService:
    """
    Thin orchestration service providing comprehensive Career Action Center intelligence
    for live job opportunities by connecting existing intelligence layers.
    """

    SAFETY_DISCLAIMER = (
        "Educational Decision Support: Job match scores measure direct vacancy skill overlap "
        "and do not constitute employment prediction or placement guarantees. "
        "Industry demand signals reflect DEMO / SAMPLE / PROTOTYPE research benchmarks."
    )

    # Deterministic mapping rules for canonical careers
    CAREER_TITLE_PATTERNS = [
        # Career 2: Web Developer (front-end / web specific)
        (2, re.compile(r"\b(frontend|front-end|web developer|ui engineer|react developer|vue developer|angular developer|design engineer)\b", re.I)),
        # Career 3: Data Analyst
        (3, re.compile(r"\b(data analyst|bi analyst|business intelligence|analytics engineer|data analytics)\b", re.I)),
        # Career 5: AI/ML Engineer (specific AI/ML)
        (5, re.compile(r"\b(ai engineer|machine learning engineer|ml engineer|artificial intelligence|prompt engineer|computer vision|nlp engineer)\b", re.I)),
        # Career 4: Data Scientist
        (4, re.compile(r"\b(data scientist|deep learning scientist|research scientist - ml)\b", re.I)),
        # Career 7: DevOps Engineer
        (7, re.compile(r"\b(devops|site reliability|sre|ci/cd|release engineer)\b", re.I)),
        # Career 6: Cloud Engineer
        (6, re.compile(r"\b(cloud engineer|cloud architect|solutions architect|platform engineer|infrastructure engineer|systems architect)\b", re.I)),
        # Career 8: Cybersecurity Analyst
        (8, re.compile(r"\b(cybersecurity|security engineer|infosec|soc analyst|penetration tester|appsec)\b", re.I)),
        # Career 9: Network Engineer
        (9, re.compile(r"\b(network engineer|network administrator|systems administrator|sysadmin|network operations)\b", re.I)),
        # Career 10: Database Administrator
        (10, re.compile(r"\b(database administrator|dba|database engineer|database reliability)\b", re.I)),
        # Career 2: Fullstack (also Web Developer)
        (2, re.compile(r"\b(full stack|fullstack|full-stack)\b", re.I)),
        # Career 1: Software Developer (broad software/backend/general tech)
        (1, re.compile(r"\b(software engineer|software developer|backend engineer|backend developer|product engineer|developer relations|solutions engineer)\b", re.I)),
    ]

    @classmethod
    def map_job_to_career(cls, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministically maps a live job vacancy to one of the 10 canonical IT career tracks.
        Returns mapped career info or explicit fallback ('Career mapping unavailable').
        """
        if not job or not isinstance(job, dict):
            return {
                "status": "unavailable",
                "career_id": None,
                "career_title": None,
                "domain": None,
                "confidence": "NONE",
                "message": "Career mapping unavailable",
            }

        title = str(job.get("title", "")).strip()
        tags = [t.strip().casefold() for t in job.get("tech_tags", []) if isinstance(t, str)]

        # 1. Check title keyword patterns in prioritized order
        for cid, pattern in cls.CAREER_TITLE_PATTERNS:
            if pattern.search(title):
                career = Career.query.get(cid)
                if career:
                    return {
                        "status": "mapped",
                        "career_id": career.id,
                        "career_title": career.title,
                        "domain": career.domain,
                        "confidence": "HIGH",
                        "message": None,
                    }

        # 2. Check tech tag overlap with CareerSkill if title didn't directly match
        if tags:
            try:
                career_skills = CareerSkill.query.all()
                scores: Dict[int, int] = {}
                for cs in career_skills:
                    cname = cs.canonical_skill.name.casefold() if cs.canonical_skill else ""
                    if cname in tags:
                        scores[cs.career_id] = scores.get(cs.career_id, 0) + 1

                if scores:
                    best_cid = max(scores, key=scores.get)
                    if scores[best_cid] >= 2:  # at least 2 distinct required skills match
                        career = Career.query.get(best_cid)
                        if career:
                            return {
                                "status": "mapped",
                                "career_id": career.id,
                                "career_title": career.title,
                                "domain": career.domain,
                                "confidence": "MEDIUM",
                                "message": None,
                            }
            except Exception:
                pass

        # 3. Explicit fallback when no reliable mapping exists
        return {
            "status": "unavailable",
            "career_id": None,
            "career_title": None,
            "domain": None,
            "confidence": "NONE",
            "message": "Career mapping unavailable",
        }

    @classmethod
    def get_action_center(
        cls,
        source_key: str,
        provider_id: str,
        user_id: Optional[int] = None,
        custom_skills: Optional[List[str]] = None,
        from_career_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates full Career Action Center intelligence for a live job posting.
        Combines job matching, mapped career, Skill ROI, portfolio projects,
        industry demand benchmarks, trajectory intelligence, and interview practice.
        """
        # 1. Validate source and fetch live job posting
        if source_key not in LiveJobsService.get_source_registry():
            return {
                "status": "error",
                "error": "NOT_FOUND",
                "message": f"Source '{source_key}' not found",
            }

        job_data = LiveJobsService.get_job(source_key, provider_id)
        if not job_data or not job_data.get("job"):
            return {
                "status": "error",
                "error": "NOT_FOUND",
                "message": f"Job '{provider_id}' not found in source '{source_key}'",
            }

        job = job_data["job"]
        source_info = job_data.get("source_info", {})

        # 2. Resolve candidate skills
        candidate_skills: List[str] = []
        user_skill_records = []
        if custom_skills and isinstance(custom_skills, list):
            candidate_skills = [str(s).strip() for s in custom_skills if str(s).strip()]
        elif user_id:
            try:
                user_skill_records = Skill.query.filter_by(user_id=int(user_id)).all()
                for s in user_skill_records:
                    if s.skill_name and s.skill_name.strip():
                        candidate_skills.append(s.skill_name.strip())
            except Exception:
                pass

        # 3. Match candidate skills against the job
        match_result = LiveJobsService.match_job_to_skills(job, candidate_skills)
        match_score = match_result.get("match_score", 0.0)
        matched_skills = match_result.get("matched_skills", [])
        missing_skills = match_result.get("missing_skills", [])

        # 4. Deterministic Career Mapping
        career_mapping = cls.map_job_to_career(job)
        mapped_career_id = career_mapping.get("career_id")

        # 5. Connected Intelligence Layers (when career mapping is available)
        skill_actions: List[Dict[str, Any]] = []
        portfolio_recommendations: List[Dict[str, Any]] = []
        industry_demand_context: Optional[Dict[str, Any]] = None
        trajectory_context: Optional[Dict[str, Any]] = None
        interview_context: Optional[Dict[str, Any]] = None

        if mapped_career_id:
            # 5a. Skill ROI Integration (Phase 11.1)
            roi_lookup: Dict[str, Dict[str, Any]] = {}
            try:
                roi_data = SkillRoiService.rank_career_skill_rois(
                    career_id=mapped_career_id,
                    user_id=user_id,
                )
                if isinstance(roi_data, dict) and "ranked_skills" in roi_data:
                    for item in roi_data["ranked_skills"]:
                        sname_norm = normalize_skill_name(item.get("skill_name", ""))
                        roi_lookup[sname_norm] = item
            except Exception:
                pass

            # Build prioritized action items for missing skills
            for sname in missing_skills:
                norm = normalize_skill_name(sname)
                roi_item = roi_lookup.get(norm)
                if roi_item:
                    priority = roi_item.get("roi_tier", "MEDIUM")
                    if roi_item.get("is_quickest_win"):
                        priority = "QUICKEST_WIN"
                    skill_actions.append({
                        "skill_name": sname,
                        "why_it_matters": (
                            f"Core required skill for {career_mapping['career_title']}. "
                            f"Closing this gap provides +{roi_item.get('marginal_readiness_gain', 0.0)}% marginal readiness gain."
                        ),
                        "priority": priority,
                        "roi_score": roi_item.get("roi_score", 0.0),
                        "marginal_readiness_gain": roi_item.get("marginal_readiness_gain", 0.0),
                        "estimated_study_hours": roi_item.get("estimated_study_hours", 20),
                        "suggested_action": f"Focus on {sname} fundamentals and complete an aligned practical exercise.",
                    })
                else:
                    skill_actions.append({
                        "skill_name": sname,
                        "why_it_matters": f"Directly listed requirement in {job.get('employer', 'employer')} vacancy.",
                        "priority": "MEDIUM",
                        "roi_score": 5.0,
                        "marginal_readiness_gain": 4.0,
                        "estimated_study_hours": 15,
                        "suggested_action": f"Study {sname} documentation and build a hands-on verification project.",
                    })

            # Sort skill actions: QUICKEST_WIN and HIGH first
            tier_weights = {"QUICKEST_WIN": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            skill_actions.sort(
                key=lambda x: (tier_weights.get(x["priority"], 0), x.get("roi_score", 0)),
                reverse=True,
            )

            # 5b. Portfolio Project Integration (Phase 11.2)
            try:
                portfolio_data = PortfolioProjectService.recommend_projects_for_career(
                    career_id=mapped_career_id,
                    user_id=user_id,
                    limit=3,
                )
                if isinstance(portfolio_data, dict) and "recommendations" in portfolio_data:
                    for p in portfolio_data["recommendations"]:
                        # Highlight which missing skills this project exercises
                        demonstrated = [d.casefold() for d in p.get("demonstrated_skills", [])]
                        gaps_addressed = [
                            m for m in missing_skills
                            if m.casefold() in demonstrated
                        ]
                        portfolio_recommendations.append({
                            "project_id": p.get("project_id"),
                            "title": p.get("title"),
                            "domain": p.get("domain"),
                            "difficulty": p.get("difficulty"),
                            "estimated_hours": p.get("estimated_hours"),
                            "portfolio_value": p.get("portfolio_value"),
                            "demonstrated_skills": p.get("demonstrated_skills", []),
                            "deliverables": p.get("deliverables", [])[:3],
                            "addresses_missing_skills": gaps_addressed,
                            "recommendation_reason": p.get("explanation"),
                        })
            except Exception:
                pass

            # 5c. Industry Demand Integration (Phase 11.4)
            try:
                ind_data = IndustryDemandService.evaluate_career_industry_demand(
                    career_id=mapped_career_id,
                    user_id=user_id,
                )
                if isinstance(ind_data, dict) and "overall_market_temperature" in ind_data:
                    # Filter demand skills relevant to this job
                    job_tags_set = set(t.casefold() for t in job.get("tech_tags", []))
                    relevant_demand_skills = [
                        s for s in ind_data.get("skills", [])
                        if s.get("skill_name", "").casefold() in job_tags_set
                    ]
                    industry_demand_context = {
                        "overall_market_temperature": ind_data.get("overall_market_temperature"),
                        "market_growth_label": ind_data.get("market_growth_label"),
                        "overlapping_demand_skills": relevant_demand_skills[:5],
                        "provenance_disclaimer": ind_data.get("provenance") or ind_data.get("provenance_disclaimer") or IndustryDemandService.PROVENANCE_NOTICE,
                    }
            except Exception:
                pass

            # 5d. Career Trajectory Integration (Phase 11.5)
            # If student specified a different from_career_id or has a different primary career
            alt_from_cid = from_career_id
            if not alt_from_cid and mapped_career_id != 1:
                alt_from_cid = 1  # Default benchmark transition from Software Developer

            if alt_from_cid and alt_from_cid != mapped_career_id:
                try:
                    traj_data = CareerTrajectoryService.find_trajectory(
                        target_career_id=mapped_career_id,
                        from_career_id=alt_from_cid,
                        user_id=user_id,
                    )
                    if isinstance(traj_data, dict) and "recommended_trajectory" in traj_data:
                        rec_traj = traj_data["recommended_trajectory"]
                        trajectory_context = {
                            "from_career_id": alt_from_cid,
                            "target_career_id": mapped_career_id,
                            "trajectory_type": rec_traj.get("trajectory_type"),
                            "total_hops": rec_traj.get("total_hops"),
                            "feasibility_score": rec_traj.get("feasibility_score"),
                            "bridge_skills": rec_traj.get("bridge_skills", [])[:4],
                            "milestones": [
                                m.get("milestone_title")
                                for m in rec_traj.get("milestones", [])
                            ][:3],
                        }
                except Exception:
                    pass

            # 5e. Interview Readiness Integration (Phase 11.6)
            interview_context = {
                "interview_available": True,
                "career_id": mapped_career_id,
                "career_title": career_mapping["career_title"],
                "target_role": job.get("title"),
                "recommended_practice_action": (
                    f"Test your technical knowledge for {career_mapping['career_title']} "
                    "with career-aligned simulation questions."
                ),
            }

        # 6. Synthesize "What Should I Do Next?" Action Plan
        action_plan = cls._synthesize_action_plan(
            match_score=match_score,
            missing_skills=missing_skills,
            skill_actions=skill_actions,
            portfolio_recs=portfolio_recommendations,
            career_mapping=career_mapping,
            has_interview=interview_context is not None,
        )

        return {
            "status": "success",
            "job": job,
            "source_info": source_info,
            "match": {
                "match_score": match_score,
                "total_target_skills": match_result.get("total_target_skills", 0),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "work_mode": job.get("work_mode"),
                "experience_level": job.get("experience_level"),
                "recommendations": match_result.get("recommendations", []),
                "score_distinction_notice": (
                    "Job Match Score reflects direct keyword and tag overlap with this vacancy. "
                    "Career Readiness Score measures holistic curriculum and track proficiency."
                ),
            },
            "career_connection": career_mapping,
            "skill_actions": skill_actions,
            "portfolio_recommendations": portfolio_recommendations,
            "industry_demand_context": industry_demand_context,
            "career_trajectory": trajectory_context,
            "interview_readiness": interview_context,
            "action_plan": action_plan,
            "safety_disclaimer": cls.SAFETY_DISCLAIMER,
        }

    @staticmethod
    def _synthesize_action_plan(
        match_score: float,
        missing_skills: List[str],
        skill_actions: List[Dict[str, Any]],
        portfolio_recs: List[Dict[str, Any]],
        career_mapping: Dict[str, Any],
        has_interview: bool,
    ) -> Dict[str, Any]:
        """
        Synthesizes a cohesive, advisory action plan combining all available signals.
        Strictly enforces non-deterministic advisory language.
        """
        # 1. Readiness status
        if match_score >= 80:
            readiness_status = "READY_TO_APPLY"
            status_text = "Strong Technical Alignment"
            advice = (
                "Your skills align well with the core requirements of this vacancy. "
                "Consider preparing your application and reviewing company-specific tooling."
            )
        elif match_score >= 50:
            readiness_status = "MODERATE_ALIGNMENT"
            status_text = "Moderate Technical Alignment"
            advice = (
                "You meet a substantial portion of the required tech stack. "
                "Reinforce key missing competencies to increase your technical confidence."
            )
        else:
            readiness_status = "GAPS_IDENTIFIED"
            status_text = "Key Skill Gaps Identified"
            advice = (
                "Significant competencies listed in this posting are currently missing from your profile. "
                "We recommend addressing priority skills and completing portfolio evidence before applying."
            )

        # 2. Priority skills
        priority_skills = [
            {
                "skill_name": item["skill_name"],
                "priority": item["priority"],
                "gain": item.get("marginal_readiness_gain", 0.0),
            }
            for item in skill_actions[:3]
        ]

        # 3. Portfolio recommendation
        portfolio_action = None
        if portfolio_recs:
            top_p = portfolio_recs[0]
            portfolio_action = {
                "project_id": top_p.get("project_id"),
                "title": top_p.get("title"),
                "deliverable_summary": top_p.get("deliverables", ["Build working project"])[0],
            }

        # 4. Next steps checklist
        steps = []
        if priority_skills:
            top_skill = priority_skills[0]["skill_name"]
            steps.append(f"Study priority skill '{top_skill}' to close key technical vacancy gap.")

        if portfolio_action:
            steps.append(f"Build capstone project '{portfolio_action['title']}' to demonstrate practical capability.")

        if has_interview:
            career_title = career_mapping.get("career_title", "target career")
            steps.append(f"Practice technical interview questions for {career_title}.")

        if match_score >= 70:
            steps.append("Tailor your resume highlighting matched skills and relevant deliverables.")

        return {
            "readiness_status": readiness_status,
            "status_headline": status_text,
            "recommended_next_step": advice,
            "priority_skills": priority_skills,
            "portfolio_action": portfolio_action,
            "interview_recommended": has_interview,
            "action_checklist": steps,
        }
