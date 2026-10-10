"""
Adaptive Skill Learning & Resource Recommendation Engine.
Phase 12 Module 12.4.

Consolidates:
1. Career target competencies & proficiency levels (1-5 scale)
2. Student skill gaps (Missing, Weak, Matched)
3. Skill ROI rankings (Phase 11.1)
4. Industry demand growth signals (Phase 11.4)
5. Academic benchmark curriculum deficits (Phase 11.3)
6. Practical assessment task bank (Phase 12.3)
7. Portfolio capstone recommendations (Phase 11.2)
8. AI interview simulation questions (Phase 11.6)
9. Multi-hop career trajectory transitions (Phase 11.5)
10. Live job market vacancies (Phase 12.2)

Produces an explainable, deterministic curriculum sequence:
Formula:
    PriorityScore = 0.30 * GapSeverity + 0.20 * SkillROI + 0.15 * CareerImportance +
                    0.15 * IndustryDemand + 0.10 * AcademicDeficit + 0.10 * JobRelevance
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from extensions import db
from models.career import Career
from models.career_skill import CareerSkill
from models.canonical_skill import CanonicalSkill
from models.skill import Skill
from models.learning_resource import LearningResource
from services.skill_gap_service import SkillGapService, SkillGapStatus
from services.skill_roi_service import SkillRoiService
from services.industry_demand_service import IndustryDemandService
from services.academic_benchmark_service import AcademicBenchmarkService
from services.portfolio_project_service import PortfolioProjectService
from services.career_trajectory_service import CareerTrajectoryService
from services.practical_task_service import PracticalTaskService
from services.interview_simulation_service import QUESTION_BANK
from utils.normalization import normalize_skill_name, strip_parenthetical_qualifiers


class AdaptiveLearningService:
    """
    Deterministic, explainable career-gap-closure engine for AI Career Navigator.
    """

    SAFETY_DISCLAIMER = (
        "Educational Decision Support: Deterministic adaptive skill learning recommendations provide formative "
        "guidance and do not represent employment prediction, placement guarantees, or recruiter certification."
    )

    PROVENANCE_NOTICES = {
        "industry_data": "DEMO / SAMPLE / PROTOTYPE — NOT LIVE LABOR MARKET DATA",
        "learning_effort": "ESTIMATED / HEURISTIC — NOT GUARANTEED COMPLETION TIME",
        "academic_data": "DEMO / SAMPLE / PROTOTYPE — NOT OFFICIAL UNIVERSITY CURRICULUM DATA",
    }

    WEIGHTS: Dict[str, float] = {
        "gap_severity": 0.30,
        "skill_roi": 0.20,
        "career_importance": 0.15,
        "industry_demand": 0.15,
        "academic_deficit": 0.10,
        "job_relevance": 0.10,
    }

    # Deterministic skill prerequisite map based on canonical skills
    PREREQUISITE_MAP: Dict[str, List[str]] = {
        # Data & AI Track
        "pandas": ["python"],
        "machine learning": ["python", "data structures", "statistics"],
        "deep learning": ["machine learning", "python"],
        "tensorflow": ["python", "machine learning"],
        "data structures": ["python"],
        # Web & Fullstack Track
        "react": ["javascript", "html", "css"],
        "javascript": ["html", "css"],
        # Database Track
        "postgresql": ["sql"],
        "mysql": ["sql"],
        "database security": ["sql"],
        # Cloud & Infrastructure Track
        "aws": ["linux", "networking"],
        "docker": ["linux"],
        "kubernetes": ["docker", "linux"],
        "ci/cd": ["git", "linux"],
        "siem": ["linux", "networking", "cybersecurity"],
        "routing and switching": ["networking"],
        "ccna": ["networking"],
        "network security": ["networking"],
    }

    # Progression stage definitions
    STAGES = [
        {"id": "FOUNDATION", "label": "Stage 1: Foundation", "description": "Syntax, core concepts, setup, and fundamentals."},
        {"id": "CORE_SKILL", "label": "Stage 2: Core Skill", "description": "Functions, design patterns, architecture, and idioms."},
        {"id": "APPLIED_PRACTICE", "label": "Stage 3: Applied Practice", "description": "Targeted diagnostic tasks, problem solving, and exercises."},
        {"id": "PROJECT_APPLICATION", "label": "Stage 4: Project Application", "description": "Hands-on capstone project implementing a real-world system."},
        {"id": "INTERVIEW_READINESS", "label": "Stage 5: Interview Readiness", "description": "Technical interview rubrics, system design, and concept explanations."},
    ]

    # Heuristic effort formulas
    STAGE_EFFORT_BASE: Dict[str, Tuple[int, float]] = {
        "FOUNDATION": (10, 3.0),
        "CORE_SKILL": (8, 2.5),
        "APPLIED_PRACTICE": (6, 2.0),
        "PROJECT_APPLICATION": (10, 2.0),
        "INTERVIEW_READINESS": (4, 1.0),
    }

    # Backward-compatible effort bands (hours)
    STAGE_EFFORT_HOURS: Dict[str, Tuple[int, int]] = {
        "FOUNDATION": (5, 15),
        "CORE_SKILL": (10, 30),
        "APPLIED_PRACTICE": (5, 20),
        "PROJECT_APPLICATION": (10, 40),
        "INTERVIEW_READINESS": (3, 10),
    }

    @classmethod
    def resolve_prerequisites(cls, skill_name: str) -> Tuple[List[str], str]:
        """
        Deterministically resolves prerequisite skill requirements.
        Returns a tuple of (prerequisites_list, explanation_note).
        """
        norm = normalize_skill_name(strip_parenthetical_qualifiers(skill_name))
        prereqs = cls.PREREQUISITE_MAP.get(norm, [])
        if prereqs:
            formatted = [p.title() if len(p) > 3 else p.upper() for p in prereqs]
            return formatted, f"Requires foundational understanding of {', '.join(formatted)} prior to advanced study."
        return [], "No prerequisite relationship was established."

    @classmethod
    def determine_learning_stage(cls, current_proficiency: float, target_proficiency: float = 4.0) -> str:
        """
        Determines current pedagogical stage based on student proficiency (1.0 to 5.0 scale).
        """
        if current_proficiency <= 0.0 or current_proficiency < 2.0:
            return "FOUNDATION"
        elif current_proficiency < 3.0:
            return "CORE_SKILL"
        elif current_proficiency >= target_proficiency:
            return "INTERVIEW_READINESS"
        elif current_proficiency < 4.0 and target_proficiency <= 4.0:
            return "APPLIED_PRACTICE"
        else:
            return "PROJECT_APPLICATION"

    @classmethod
    def determine_skill_closure(cls, current_proficiency: float) -> Dict[str, Any]:
        """
        Evaluates educational skill closure status based on verified proficiency.
        """
        if current_proficiency >= 5.0:
            return {"status": "MASTERED", "threshold": 5.0, "label": "Mastered Competency"}
        elif current_proficiency >= 4.0:
            return {"status": "PROJECT_READY", "threshold": 4.0, "label": "Project Ready"}
        elif current_proficiency >= 3.0:
            return {"status": "CORE_READY", "threshold": 3.0, "label": "Core Competency Ready"}
        elif current_proficiency >= 2.0:
            return {"status": "FOUNDATION_COMPLETE", "threshold": 2.0, "label": "Foundation Complete"}
        else:
            return {"status": "NOT_STARTED", "threshold": 0.0, "label": "Learning Pending"}

    @classmethod
    def estimate_learning_effort(cls, stage: str, gap_value: float) -> int:
        """
        Estimates learning effort in hours based on stage and remaining gap value.
        Heuristic, bounded, and conservative.
        """
        base, mult = cls.STAGE_EFFORT_BASE.get(stage, (10, 2.0))
        return int(round(base + max(0.0, float(gap_value)) * mult))

    @classmethod
    def explain_priority(
        cls,
        skill_name: str,
        priority_score: float,
        gap_severity: float,
        roi_score: float,
        importance: float,
        demand: float,
        academic: float,
        job_rel: float,
        is_missing: bool
    ) -> str:
        """
        Generates deterministic natural-language reasoning explaining skill priority.
        """
        reasons = []
        if is_missing or gap_severity >= 90.0:
            reasons.append("is currently missing from your profile")
        elif gap_severity >= 50.0:
            reasons.append("has a substantial proficiency gap")

        if importance >= 80.0:
            reasons.append("is highly critical for the target career track")
        if roi_score >= 70.0:
            reasons.append("offers rapid marginal readiness gain (high ROI)")
        if demand >= 80.0:
            reasons.append("shows strong industry demand in current market indicators")
        if job_rel >= 80.0:
            reasons.append("appears frequently in matched job vacancies")
        if academic >= 75.0:
            reasons.append("represents an industry gap beyond typical academic coursework")

        if not reasons:
            reasons.append("contributes progressively to career competency requirements")

        return f"{skill_name} is prioritized (Score: {priority_score}/100) because it {' and '.join(reasons)}."

    @classmethod
    def rank_resources(
        cls,
        canonical_skill_id: Optional[Any] = None,
        skill_name: Optional[str] = None,
        current_prof: float = 0.0,
        learning_stage: str = "FOUNDATION",
        career_title: str = "",
        limit: int = 3,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Queries existing learning_resources and scores them deterministically:
        Score = 0.35 * skill_match + 0.20 * difficulty_fit + 0.15 * career_relevance +
                0.15 * learning_stage_fit + 0.15 * industry_relevance
        """
        # Flexible argument unpacking:
        if isinstance(canonical_skill_id, str):
            actual_skill = canonical_skill_id
            actual_stage = skill_name if isinstance(skill_name, str) else "FOUNDATION"
            actual_career = str(current_prof) if isinstance(current_prof, (str, int)) else ""
            actual_prof = float(kwargs.get("current_prof", 0.0))
            actual_cid = None
            if "limit" in kwargs:
                limit = kwargs["limit"]
        else:
            actual_cid = canonical_skill_id
            actual_skill = skill_name or ""
            actual_stage = learning_stage or "FOUNDATION"
            actual_career = career_title or ""
            actual_prof = float(current_prof or 0.0)

        db_resources: List[LearningResource] = []
        if actual_cid:
            db_resources = LearningResource.query.filter_by(
                canonical_skill_id=actual_cid,
                status="Active"
            ).all()

        if not db_resources and actual_skill:
            c_skill = CanonicalSkill.query.filter_by(normalized_name=normalize_skill_name(actual_skill)).first()
            if c_skill:
                db_resources = LearningResource.query.filter_by(
                    canonical_skill_id=c_skill.id,
                    status="Active"
                ).all()

        ranked_list = []
        for r in db_resources:
            # 1. Skill Match (Exact canonical match = 100)
            skill_match = 100.0

            # 2. Difficulty Fit (0-100)
            diff = (r.difficulty_level or "Beginner").lower()
            if actual_prof < 2.0:
                diff_fit = 100.0 if diff == "beginner" else (50.0 if diff == "intermediate" else 20.0)
            elif actual_prof < 3.5:
                diff_fit = 100.0 if diff == "intermediate" else (80.0 if diff == "beginner" else 40.0)
            else:
                diff_fit = 100.0 if diff == "advanced" else (80.0 if diff == "intermediate" else 30.0)

            # 3. Career Relevance (0-100)
            career_rel = 90.0 if (r.provider and any(k in r.provider.lower() for k in ["aws", "google", "microsoft", "python", "coursera", "cisco"])) else 80.0

            # 4. Learning Stage Fit (0-100)
            rtype = (r.resource_type or "").lower()
            if actual_stage in ["FOUNDATION", "CORE_SKILL"]:
                stage_fit = 100.0 if rtype in ["course", "documentation", "tutorial"] else 60.0
            elif actual_stage == "APPLIED_PRACTICE":
                stage_fit = 100.0 if rtype in ["practice platform", "interactive", "tutorial"] else 70.0
            elif actual_stage == "PROJECT_APPLICATION":
                stage_fit = 100.0 if rtype in ["project", "lab"] else 65.0
            else:
                stage_fit = 90.0 if rtype in ["certification", "practice platform"] else 70.0

            # 5. Industry Relevance (0-100)
            ind_rel = 100.0 if r.certification_available else 85.0

            composite_score = round(
                0.35 * skill_match +
                0.20 * diff_fit +
                0.15 * career_rel +
                0.15 * stage_fit +
                0.15 * ind_rel,
                1
            )

            reason = (
                f"Selected as a {r.difficulty_level} {r.resource_type} from {r.provider} matching your "
                f"{actual_stage.replace('_', ' ').lower()} learning stage."
            )

            ranked_list.append({
                "resource_id": r.id,
                "title": r.title,
                "provider": r.provider,
                "resource_type": r.resource_type,
                "type": r.resource_type,
                "difficulty_level": r.difficulty_level,
                "difficulty": r.difficulty_level,
                "url": r.url,
                "estimated_duration": r.estimated_duration or "Self-paced",
                "description": r.description,
                "certification_available": r.certification_available,
                "ranking_score": composite_score,
                "selection_reason": reason
            })

        # Fallback if no database resource matched
        if not ranked_list and actual_skill:
            norm_name = normalize_skill_name(actual_skill)
            ranked_list = [
                {
                    "resource_id": f"curated-{norm_name}-1",
                    "title": f"Mastering {actual_skill}: Comprehensive Guide & Curriculum",
                    "provider": "AI Career Navigator Curated Academy",
                    "resource_type": "Course",
                    "type": "Course",
                    "difficulty_level": "Intermediate",
                    "difficulty": "Intermediate",
                    "url": f"https://learning.academics.org/topics/{norm_name}",
                    "estimated_duration": "20 hours",
                    "description": f"Structured modular curriculum covering theoretical foundations and practical patterns in {actual_skill}.",
                    "certification_available": True,
                    "ranking_score": 92.0,
                    "selection_reason": f"Curated high-yield learning resource targeting {actual_skill}."
                },
                {
                    "resource_id": f"curated-{norm_name}-2",
                    "title": f"Official {actual_skill} Documentation & Reference Manual",
                    "provider": f"{actual_skill} Community / Official",
                    "resource_type": "Documentation",
                    "type": "Documentation",
                    "difficulty_level": "Beginner",
                    "difficulty": "Beginner",
                    "url": f"https://docs.standard.org/{norm_name}",
                    "estimated_duration": "10 hours",
                    "description": f"Authoritative documentation, standard specifications, and core APIs for {actual_skill}.",
                    "certification_available": False,
                    "ranking_score": 88.5,
                    "selection_reason": f"Authoritative reference documentation for {actual_skill}."
                }
            ]

        # Sort descending by ranking score
        ranked_list.sort(key=lambda x: x["ranking_score"], reverse=True)
        if limit and limit > 0:
            return ranked_list[:limit]
        return ranked_list

    @classmethod
    def get_learning_plan(
        cls,
        career_id: int,
        user_id: Optional[int] = None,
        user_skills_payload: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive, deterministic Adaptive Skill Learning Plan.
        """
        career = Career.query.get(career_id)
        if not career:
            return {
                "error": "CAREER_NOT_FOUND",
                "message": f"Career with ID {career_id} not found"
            }

        opts = options or {}
        limit = opts.get("limit") if opts.get("limit") is not None else opts.get("max_skills", 10)
        learning_pace = opts.get("learning_pace", 10)
        from_career_id = opts.get("from_career_id")
        vacancy_skills = set(normalize_skill_name(s) for s in opts.get("vacancy_skills", []))

        # 1. Resolve student skills
        student_skills: List[Skill] = []
        if user_skills_payload is not None:
            for item in user_skills_payload:
                s_name = item.get("skill_name") or item.get("name")
                s_prof = float(item.get("proficiency") if item.get("proficiency") is not None else item.get("level", 0))
                if s_name:
                    # If passed on a 1-5 scale, scale to 1-10 raw scale for Skill model
                    raw_p = int(round(s_prof * 2.0)) if (0 < s_prof <= 5.0) else int(round(s_prof))
                    mock_s = Skill(
                        user_id=user_id or 0,
                        skill_name=s_name,
                        proficiency=raw_p
                    )
                    c_lookup = CanonicalSkill.query.filter_by(normalized_name=normalize_skill_name(s_name)).first()
                    if c_lookup:
                        mock_s.canonical_skill_id = c_lookup.id
                    student_skills.append(mock_s)
        elif user_id:
            student_skills = Skill.query.filter_by(user_id=user_id).all()

        # 2. Evaluate skill gap
        gap_eval = SkillGapService.evaluate_career_gap(career, student_skills)
        current_readiness = gap_eval["summary"]["readiness_percentage"]
        gap_items = gap_eval.get("prioritized_skill_gaps", [])

        # 3. Query cross-module intelligence layers safely
        # 3a. Skill ROI
        roi_rankings = {}
        try:
            roi_res = SkillRoiService.rank_career_skill_rois(career_id=career.id, user_id=user_id)
            if "ranked_skills" in roi_res:
                for r in roi_res["ranked_skills"]:
                    roi_rankings[normalize_skill_name(r["skill_name"])] = r
        except Exception:
            pass

        # 3b. Industry Demand
        demand_signals = {}
        try:
            dem_res = IndustryDemandService.evaluate_career_industry_demand(career_id=career.id)
            if "skills" in dem_res:
                for d in dem_res["skills"]:
                    demand_signals[normalize_skill_name(d["skill_name"])] = d
        except Exception:
            pass

        # 3c. Academic Benchmark
        academic_breakdown = {}
        try:
            acad_res = AcademicBenchmarkService.benchmark_career_curriculum(career_id=career.id, user_id=user_id)
            if "curriculum_breakdown" in acad_res:
                for ab in acad_res["curriculum_breakdown"]:
                    academic_breakdown[normalize_skill_name(ab["skill_name"])] = ab
        except Exception:
            pass

        # 3d. Capstone Projects (Phase 11.2)
        portfolio_recs = []
        try:
            port_res = PortfolioProjectService.recommend_projects_for_career(career_id=career.id, user_id=user_id)
            portfolio_recs = port_res.get("recommendations", [])
        except Exception:
            pass

        # 3e. Career Trajectory (Phase 11.5) if transition requested
        trajectory_info = None
        if from_career_id and from_career_id != career_id:
            try:
                traj_res = CareerTrajectoryService.find_trajectory(
                    target_career_id=career_id,
                    from_career_id=from_career_id,
                    user_id=user_id
                )
                if "recommended_trajectory" in traj_res:
                    trajectory_info = traj_res["recommended_trajectory"]
            except Exception:
                pass

        # 4. Compute Adaptive Priority for each career skill
        priority_skills = []
        total_estimated_hours = 0

        for item in gap_items:
            s_name = item["skill_name"]
            s_norm = normalize_skill_name(s_name)
            curr_prof = float(item.get("current_proficiency", 0.0))
            raw_prof = int(item.get("raw_proficiency", 0))
            req_level = float(item.get("required_level", 4.0))
            importance = int(item.get("importance", 3))
            status = item.get("status", "MISSING")
            is_missing = status == "MISSING"

            closure_info = cls.determine_skill_closure(curr_prof)

            # 4a. Component 1: Skill Gap Severity (0-100)
            if is_missing:
                gap_severity = 100.0
            elif curr_prof >= req_level:
                gap_severity = 0.0
            else:
                gap_severity = min(100.0, round(((req_level - curr_prof) / 5.0) * 100.0, 1))

            # 4b. Component 2: Skill ROI (0-100)
            roi_data = roi_rankings.get(s_norm)
            if roi_data and "roi_score" in roi_data:
                roi_norm = float(roi_data["roi_score"])
            else:
                roi_norm = min(100.0, round(importance * 18.0 + 10.0, 1))

            # 4c. Component 3: Career Importance (0-100)
            importance_norm = min(100.0, round((importance / 5.0) * 100.0, 1))

            # 4d. Component 4: Industry Demand (0-100)
            dem_data = demand_signals.get(s_norm)
            if dem_data and "growth_rate_pct" in dem_data:
                demand_norm = min(100.0, max(20.0, round(50.0 + dem_data["growth_rate_pct"] * 1.5, 1)))
            else:
                demand_norm = 75.0 if importance >= 4 else 60.0

            # 4e. Component 5: Academic Deficit (0-100)
            acad_data = academic_breakdown.get(s_norm)
            if acad_data:
                status_str = acad_data.get("curriculum_status", "")
                if "INDUSTRY_GAP" in status_str:
                    academic_deficit = 90.0
                elif "NEEDS_REINFORCEMENT" in status_str:
                    academic_deficit = 65.0
                else:
                    academic_deficit = 25.0
            else:
                academic_deficit = 65.0

            # 4f. Component 6: Job Relevance (0-100)
            if vacancy_skills and s_norm in vacancy_skills:
                job_relevance = 95.0
            else:
                job_relevance = min(100.0, round(demand_norm * 0.85 + 15.0, 1))

            # Composite Priority Formula:
            # 0.30 * Gap + 0.20 * ROI + 0.15 * Importance + 0.15 * Demand + 0.10 * Academic + 0.10 * Job
            priority_score = round(
                0.30 * gap_severity +
                0.20 * roi_norm +
                0.15 * importance_norm +
                0.15 * demand_norm +
                0.10 * academic_deficit +
                0.10 * job_relevance,
                1
            )
            priority_score = min(100.0, max(0.0, priority_score))

            # Priority Band
            if priority_score >= 80.0:
                priority_band = "VERY_HIGH"
            elif priority_score >= 65.0:
                priority_band = "HIGH"
            elif priority_score >= 50.0:
                priority_band = "MEDIUM"
            else:
                priority_band = "LOW"

            # Prerequisites
            prereqs, prereq_note = cls.resolve_prerequisites(s_name)

            # Stage & Effort
            learning_stage = cls.determine_learning_stage(curr_prof, req_level)
            gap_val = float(item.get("gap_value") or (req_level - curr_prof))
            estimated_hours = cls.estimate_learning_effort(learning_stage, gap_val)
            total_estimated_hours += estimated_hours

            # Recommended Resources
            resources = cls.rank_resources(
                canonical_skill_id=item.get("canonical_skill_id"),
                skill_name=s_name,
                current_prof=curr_prof,
                learning_stage=learning_stage,
                career_title=career.title
            )

            # Cross-Module Integration 1: Practical Task (Phase 12.3)
            practical_task = {"available": False, "task_id": None, "title": None}
            for pt in PracticalTaskService.TASK_BANK:
                if normalize_skill_name(pt.get("skill", "")) == s_norm:
                    practical_task = {
                        "available": True,
                        "task_id": pt["id"],
                        "title": pt["title"],
                        "category": pt["category"],
                        "difficulty": pt["difficulty"],
                        "objective": pt.get("objective", ""),
                        "scenario": pt.get("scenario", ""),
                        "estimated_minutes": pt.get("estimated_minutes", 45)
                    }
                    break

            # Cross-Module Integration 2: Portfolio Capstone Project (Phase 11.2)
            portfolio_proj = {"available": False, "project_id": None, "title": None}
            for pp in portfolio_recs:
                addressed = [normalize_skill_name(x) for x in (
                    (pp.get("missing_skills_addressed") or []) +
                    (pp.get("weak_skills_addressed") or []) +
                    (pp.get("covered_career_skills") or []) +
                    (pp.get("demonstrated_skills") or [])
                )]
                if s_norm in addressed:
                    portfolio_proj = {
                        "available": True,
                        "project_id": pp["project_id"],
                        "title": pp["title"],
                        "difficulty": pp["difficulty"],
                        "estimated_hours": pp.get("estimated_hours", 30),
                        "description": pp.get("description", "")
                    }
                    break

            # Cross-Module Integration 3: Interview Preparation (Phase 11.6)
            interview_prep = {"available": False, "sample_question": None, "sample_questions": [], "question_count": 0}
            matched_questions = [
                q for q in QUESTION_BANK
                if normalize_skill_name(q.get("competency", "")) == s_norm
            ]
            if matched_questions:
                sample_qs = [q["question_text"] for q in matched_questions[:3]]
                interview_prep = {
                    "available": True,
                    "competency": s_name,
                    "question_count": len(matched_questions),
                    "sample_question": matched_questions[0]["question_text"],
                    "sample_questions": sample_qs,
                    "difficulty": matched_questions[0]["difficulty"]
                }

            # Human-understandable Explanation
            reason = cls.explain_priority(
                skill_name=s_name,
                priority_score=priority_score,
                gap_severity=gap_severity,
                roi_score=roi_norm,
                importance=importance_norm,
                demand=demand_norm,
                academic=academic_deficit,
                job_rel=job_relevance,
                is_missing=is_missing
            )

            priority_skills.append({
                "skill_id": item.get("canonical_skill_id"),
                "skill_name": s_name,
                "category": item.get("category", "Core Competency"),
                "priority_score": priority_score,
                "priority_band": priority_band,
                "gap_severity": gap_severity,
                "roi_score": round(roi_norm, 1),
                "career_importance": round(importance_norm, 1),
                "industry_demand": round(demand_norm, 1),
                "academic_deficit": round(academic_deficit, 1),
                "job_relevance": round(job_relevance, 1),
                "components": {
                    "gap_severity": gap_severity,
                    "skill_roi": round(roi_norm, 1),
                    "career_importance": round(importance_norm, 1),
                    "industry_demand": round(demand_norm, 1),
                    "academic_deficit": round(academic_deficit, 1),
                    "job_relevance": round(job_relevance, 1),
                },
                "current_proficiency": curr_prof,
                "current_raw_proficiency": raw_prof,
                "target_proficiency": req_level,
                "learning_stage": learning_stage,
                "closure_status": closure_info["status"],
                "closure_label": closure_info["label"],
                "estimated_hours": estimated_hours,
                "prerequisites": prereqs,
                "prerequisite_note": prereq_note,
                "recommended_resources": resources[:3],
                "learning_resources": resources[:3],
                "practical_task": practical_task,
                "portfolio_project": portfolio_proj,
                "interview_preparation": interview_prep,
                "reason": reason
            })

        # 5. Deterministic Ranking
        priority_skills.sort(
            key=lambda x: (-x["priority_score"], -x["gap_severity"], x["skill_name"])
        )

        if limit and limit > 0:
            priority_skills = priority_skills[:limit]

        # 6. Build Structured Sequential Learning Path
        learning_path = []
        learned_or_available = {normalize_skill_name(s.skill_name) for s in student_skills if s.proficiency >= 8}
        stage_idx = 1

        for skill in priority_skills:
            s_norm = normalize_skill_name(skill["skill_name"])
            prereqs_met = all(p in learned_or_available for p in [normalize_skill_name(pr) for pr in skill["prerequisites"]])

            if stage_idx == 1 and prereqs_met:
                step_status = "START_NOW"
            elif prereqs_met:
                step_status = "READY_NEXT"
            else:
                step_status = f"AFTER_{skill['prerequisites'][0].upper() if skill['prerequisites'] else 'FOUNDATION'}"

            learning_path.append({
                "stage": stage_idx,
                "skill": skill["skill_name"],
                "learning_stage": skill["learning_stage"],
                "priority_band": skill["priority_band"],
                "status": step_status,
                "estimated_hours": skill["estimated_hours"],
                "closure_target": f"Level {int(skill['target_proficiency'])}/5"
            })
            learned_or_available.add(s_norm)
            stage_idx += 1

        # 7. Next Best Action Summary
        if priority_skills:
            next_skill = priority_skills[0]["skill_name"]
            next_action = f"Begin with {next_skill} ({priority_skills[0]['learning_stage'].replace('_', ' ').title()})"
        else:
            next_action = "All core competencies satisfied for this career track."

        next_actions = []
        if priority_skills:
            top = priority_skills[0]
            next_actions.append(f"Step 1: Complete foundational study for {top['skill_name']} ({top['estimated_hours']} estimated hours).")
            if top["practical_task"]["available"]:
                next_actions.append(f"Step 2: Solve practical task '{top['practical_task']['title']}' to validate hands-on ability.")
            if top["portfolio_project"]["available"]:
                next_actions.append(f"Step 3: Implement capstone project '{top['portfolio_project']['title']}' for your portfolio.")
            if top["interview_preparation"]["available"]:
                next_actions.append(f"Step 4: Practice interview questions targeting {top['skill_name']} in the Interview Simulator.")

        return {
            "status": "success",
            "career": {
                "id": career.id,
                "title": career.title,
                "domain": career.domain
            },
            "learning_summary": {
                "total_priority_skills": len(priority_skills),
                "estimated_hours": total_estimated_hours,
                "learning_pace_hours_per_week": learning_pace,
                "estimated_weeks": round(total_estimated_hours / max(1, learning_pace), 1),
                "student_readiness_score": current_readiness,
                "current_stage": priority_skills[0]["learning_stage"] if priority_skills else "COMPLETED",
                "next_best_skill": priority_skills[0]["skill_name"] if priority_skills else None,
                "next_best_action": next_action
            },
            "next_best_skill": priority_skills[0]["skill_name"] if priority_skills else None,
            "priority_skills": priority_skills,
            "learning_path": learning_path,
            "trajectory_context": trajectory_info,
            "next_actions": next_actions,
            "provenance": cls.PROVENANCE_NOTICES,
            "safety_disclaimer": cls.SAFETY_DISCLAIMER
        }
