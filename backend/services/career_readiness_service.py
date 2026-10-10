"""
Career Readiness & Personalized Action Plan Engine.
Phase 12 Module 12.5.

Orchestrates cross-module intelligence across:
1. Career competencies & target proficiency (models.career)
2. Student skill gap analysis (Phase 10: SkillGapService)
3. Explainable Skill ROI (Phase 11.1: SkillRoiService)
4. Portfolio capstone projects (Phase 11.2: PortfolioProjectService)
5. Academic curriculum benchmarks (Phase 11.3: AcademicBenchmarkService)
6. Industry demand growth signals (Phase 11.4: IndustryDemandService)
7. Multi-hop career trajectories (Phase 11.5: CareerTrajectoryService)
8. AI interview simulations (Phase 11.6: InterviewSimulationService)
9. Live job vacancy intelligence (Phase 12.2: JobActionCenterService)
10. Practical task assessments (Phase 12.3: PracticalTaskService)
11. Adaptive skill learning curriculum (Phase 12.4: AdaptiveLearningService)

Answers four fundamental student questions:
1. What should I do TODAY? (Single highest-leverage atomic action)
2. What should I do NEXT? (4-pillar progression: LEARN -> PRACTICE -> BUILD -> PREPARE)
3. What is blocking me? (7-dimension deterministic root-cause diagnosis)
4. Am I becoming job-ready? (Multi-evidence triangulation, readiness band, milestone state)

SAFETY & DESIGN GUARANTEES:
- Pure in-memory computation. ZERO database writes, ZERO schema mutations.
- Exactly 11 PostgreSQL tables preserved.
- Formative educational guidance only; non-predictive decision support.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import math

from extensions import db
from models.career import Career
from models.career_skill import CareerSkill
from models.canonical_skill import CanonicalSkill
from models.skill import Skill
from services.skill_gap_service import SkillGapService
from services.skill_roi_service import SkillRoiService
from services.academic_benchmark_service import AcademicBenchmarkService
from services.industry_demand_service import IndustryDemandService
from services.portfolio_project_service import PortfolioProjectService
from services.career_trajectory_service import CareerTrajectoryService
from services.practical_task_service import PracticalTaskService
from services.interview_simulation_service import QUESTION_BANK
from services.adaptive_learning_service import AdaptiveLearningService
from services.job_action_center_service import JobActionCenterService
from utils.normalization import normalize_skill_name, strip_parenthetical_qualifiers


class CareerReadinessService:
    """
    Orchestration and decision layer for career readiness and personalized action plans.
    """

    SAFETY_DISCLAIMER = (
        "Educational Decision Support: Deterministic career readiness assessments provide "
        "formative guidance and do not represent employment prediction, placement guarantees, "
        "or recruiter certification."
    )

    PROVENANCE_NOTICES = {
        "industry_data": "DEMO / SAMPLE / PROTOTYPE — NOT LIVE LABOR MARKET DATA",
        "learning_effort": "ESTIMATED / HEURISTIC — NOT GUARANTEED COMPLETION TIME",
        "academic_data": "DEMO / SAMPLE / PROTOTYPE — NOT OFFICIAL UNIVERSITY CURRICULUM DATA",
        "readiness_scores": "FORMATIVE COMPOSITE SIGNAL — NOT STANDARDIZED EMPLOYMENT BENCHMARK",
    }

    # Base evidence weighting when all layers are established
    BASE_EVIDENCE_WEIGHTS = {
        "skill_coverage": 0.40,
        "practical_evidence": 0.25,
        "portfolio_evidence": 0.20,
        "interview_evidence": 0.15,
    }

    # Educational Readiness Bands
    BAND_FOUNDATION_REQUIRED = "FOUNDATION_REQUIRED"  # < 50.0
    BAND_DEVELOPING = "DEVELOPING"                    # 50.0 - 74.9
    BAND_PLACEMENT_READY = "PLACEMENT_READY"          # >= 75.0

    # 5-Tier Milestone States
    STATE_NOT_READY = "NOT_READY"                      # < 40.0 or critical blocker
    STATE_FOUNDATION_BUILDING = "FOUNDATION_BUILDING"  # 40.0 - 59.9
    STATE_PROJECT_APPLICATION = "PROJECT_APPLICATION"  # 60.0 - 74.9
    STATE_INTERVIEW_ACTIVE = "INTERVIEW_ACTIVE"        # 75.0 - 84.9
    STATE_PLACEMENT_READY = "PLACEMENT_READY"          # >= 85.0 and no critical blocker

    # 7 Blocker Taxonomy Types
    BLOCKER_PREREQUISITE = "PREREQUISITE_BLOCKER"
    BLOCKER_CRITICAL_SKILL_GAP = "CRITICAL_SKILL_GAP"
    BLOCKER_PRACTICAL_EVIDENCE = "PRACTICAL_EVIDENCE_GAP"
    BLOCKER_PORTFOLIO_EVIDENCE = "PORTFOLIO_EVIDENCE_GAP"
    BLOCKER_INTERVIEW_EVIDENCE = "INTERVIEW_EVIDENCE_GAP"
    BLOCKER_ACADEMIC_BLIND_SPOT = "ACADEMIC_BLIND_SPOT"
    BLOCKER_JOB_SPECIFIC_GAP = "JOB_SPECIFIC_GAP"

    @classmethod
    def get_readiness_assessment(
        cls,
        career_id: int,
        user_id: Optional[int] = None,
        user_skills_payload: Optional[List[Dict[str, Any]]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Master orchestration pipeline synthesizing multi-dimensional readiness,
        immediate actions, weekly plan, blockers, critical path, and next milestones.
        """
        opts = options or {}
        career = Career.query.get(career_id)
        if not career:
            return {
                "error": "CAREER_NOT_FOUND",
                "message": f"Career with id {career_id} not found",
                "status": "error"
            }

        hours_per_week = opts.get("hours_per_week") or opts.get("learning_pace") or 10
        try:
            hours_per_week = max(5, min(40, int(hours_per_week)))
        except (ValueError, TypeError):
            hours_per_week = 10

        from_career_id = opts.get("from_career_id")
        raw_vacancy_skills = opts.get("vacancy_skills") or []
        vacancy_skills = {normalize_skill_name(s) for s in raw_vacancy_skills if s}

        # 1. Resolve student skills
        student_skills: List[Skill] = []
        if user_skills_payload is not None:
            for item in user_skills_payload:
                s_name = item.get("skill_name") or item.get("name")
                s_prof = float(item.get("proficiency") if item.get("proficiency") is not None else item.get("level", 0))
                if s_name:
                    # Scale 1-5 scale to 1-10 raw scale for Skill model if needed
                    raw_p = int(round(s_prof * 2.0)) if (0 < s_prof <= 5.0) else int(round(s_prof))
                    raw_p = max(0, min(10, raw_p))
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
            try:
                student_skills = Skill.query.filter_by(user_id=user_id).all()
            except Exception:
                student_skills = []

        # 2. Evaluate skill gap
        gap_eval = SkillGapService.evaluate_career_gap(career, student_skills)
        current_readiness = float(gap_eval["summary"]["readiness_percentage"])

        # 3. Query cross-module intelligence layers
        # 3a. Adaptive Learning Plan (Phase 12.4)
        adaptive_plan = AdaptiveLearningService.get_learning_plan(
            career_id=career.id,
            user_id=user_id,
            user_skills_payload=user_skills_payload,
            options={
                "learning_pace": hours_per_week,
                "from_career_id": from_career_id,
                "vacancy_skills": list(vacancy_skills)
            }
        )
        priority_skills = adaptive_plan.get("priority_skills", [])

        # 3b. Academic Benchmark (Phase 11.3)
        academic_breakdown = {}
        academic_industry_gaps = []
        try:
            acad_res = AcademicBenchmarkService.benchmark_career_curriculum(career_id=career.id, user_id=user_id)
            if "industry_gaps" in acad_res:
                academic_industry_gaps = acad_res["industry_gaps"]
            if "curriculum_breakdown" in acad_res:
                for ab in acad_res["curriculum_breakdown"]:
                    academic_breakdown[normalize_skill_name(ab["skill_name"])] = ab
        except Exception:
            pass

        # 3c. Live Jobs / Vacancies (Phase 12.2)
        if not vacancy_skills:
            try:
                action_center = JobActionCenterService.get_action_center_data(career_id=career.id, user_id=user_id)
                top_skills = action_center.get("job_readiness", {}).get("top_in_demand_skills", [])
                for ts in top_skills:
                    if isinstance(ts, dict) and "skill" in ts:
                        vacancy_skills.add(normalize_skill_name(ts["skill"]))
                    elif isinstance(ts, str):
                        vacancy_skills.add(normalize_skill_name(ts))
            except Exception:
                pass

        # 3d. Career Trajectory (Phase 11.5)
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

        # 4. Multi-Evidence Collection & Dynamic Weight Redistribution
        evidence_breakdown, dynamic_weights, overall_score = cls.collect_evidence(
            career=career,
            student_skills=student_skills,
            gap_eval=gap_eval,
            user_id=user_id,
            options=opts
        )

        # 5. Determine Educational Readiness Band
        if overall_score >= 75.0:
            readiness_band = cls.BAND_PLACEMENT_READY
        elif overall_score >= 50.0:
            readiness_band = cls.BAND_DEVELOPING
        else:
            readiness_band = cls.BAND_FOUNDATION_REQUIRED

        # 6. Blocker Diagnosis (7 Dimensions)
        blockers = cls.diagnose_blockers(
            career=career,
            gap_eval=gap_eval,
            priority_skills=priority_skills,
            academic_breakdown=academic_breakdown,
            vacancy_skills=vacancy_skills,
            evidence_breakdown=evidence_breakdown,
            academic_industry_gaps=academic_industry_gaps
        )

        # 7. Milestone State
        milestone_state = cls.determine_milestone_state(
            overall_score=overall_score,
            blockers=blockers
        )

        # 8. What should I do TODAY? (Single atomic high-leverage action)
        today_action = cls.select_today_action(
            blockers=blockers,
            priority_skills=priority_skills,
            career=career
        )

        # 9. What should I do NEXT? (4-Pillar progression)
        next_actions = cls.build_next_actions(
            priority_skills=priority_skills,
            career=career,
            blockers=blockers
        )

        # 10. Weekly Action Plan (Structured by hours_per_week)
        weekly_plan = cls.build_weekly_plan(
            priority_skills=priority_skills,
            hours_per_week=hours_per_week,
            career=career
        )

        # 11. Critical Path Sequence
        critical_path = cls.build_critical_path(
            blockers=blockers,
            priority_skills=priority_skills,
            milestone_state=milestone_state
        )

        # 12. Next Milestone
        next_milestone = cls.determine_next_milestone(
            current_state=milestone_state,
            overall_score=overall_score,
            blockers=blockers,
            hours_per_week=hours_per_week
        )

        # 13. Velocity Projection
        target_placement_score = 85.0
        remaining_gap = max(0.0, target_placement_score - overall_score)
        total_remaining_hours = sum(p.get("estimated_hours", 10) for p in priority_skills)
        projected_weeks = round(total_remaining_hours / max(1, hours_per_week), 1)

        velocity_projection = {
            "current_score": overall_score,
            "target_score": target_placement_score,
            "hours_per_week": hours_per_week,
            "total_estimated_hours": total_remaining_hours,
            "projected_weeks_to_placement_ready": projected_weeks,
            "trajectory_speed": "STEADY" if hours_per_week >= 10 else "MODERATE"
        }

        # 14. Human-readable Narrative Explanation
        narrative = cls.generate_explanation(
            career_title=career.title,
            overall_score=overall_score,
            band=readiness_band,
            milestone_state=milestone_state,
            today_action=today_action,
            blockers_count=len(blockers)
        )

        return {
            "status": "success",
            "career": {
                "id": career.id,
                "title": career.title,
                "domain": career.domain
            },
            "readiness": {
                "overall_score": overall_score,
                "readiness_band": readiness_band,
                "milestone_state": milestone_state,
                "evidence_breakdown": evidence_breakdown,
                "dynamic_weighting": dynamic_weights,
                "velocity_projection": velocity_projection
            },
            "today": today_action,
            "next_actions": next_actions,
            "weekly_plan": weekly_plan,
            "blockers": blockers,
            "critical_path": critical_path,
            "next_milestone": next_milestone,
            "trajectory_context": trajectory_info,
            "explanation": narrative,
            "provenance": cls.PROVENANCE_NOTICES,
            "safety_disclaimer": cls.SAFETY_DISCLAIMER
        }

    # =========================================================================
    # Multi-Evidence Collection & Dynamic Weight Redistribution
    # =========================================================================

    @classmethod
    def collect_evidence(
        cls,
        career: Career,
        student_skills: List[Skill],
        gap_eval: Dict[str, Any],
        user_id: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, float], float]:
        """
        Gathers evidence across 4 layers:
        1. Skill Coverage (Deterministic gap analysis, 0-100)
        2. Practical Evidence (Hands-on tasks, 0-100 or None)
        3. Portfolio Evidence (Capstone projects, 0-100 or None)
        4. Interview Evidence (AI interview evaluations, 0-100 or None)

        Dynamically normalizes weights across established layers to prevent
        penalizing students who have not yet undertaken mock tests.
        """
        opts = options or {}
        summary = gap_eval["summary"]
        skill_coverage_score = float(summary["readiness_percentage"])

        total_skills_count = summary.get("total_required_skills", summary.get("total_career_skills", 0))
        evidence_breakdown: Dict[str, Any] = {
            "skill_coverage": {
                "score": round(skill_coverage_score, 1),
                "status": "VERIFIED",
                "matched_count": summary.get("matched_skills", 0),
                "missing_count": summary.get("missing_skills", 0),
                "weak_count": summary.get("weak_skills", 0),
                "total_skills": total_skills_count,
                "description": f"Verified competency across {summary.get('matched_skills', 0)}/{total_skills_count} required career skills."
            }
        }

        # Layer 2: Practical Evidence (Phase 12.3)
        # Check if caller passed simulated/evaluated practical scores or if user has records
        sim_practical = opts.get("practical_score")
        if sim_practical is not None:
            p_score = max(0.0, min(100.0, float(sim_practical)))
            evidence_breakdown["practical_evidence"] = {
                "score": round(p_score, 1),
                "status": "EVALUATED",
                "description": f"Hands-on diagnostic assessment score: {round(p_score, 1)}/100."
            }
        else:
            evidence_breakdown["practical_evidence"] = {
                "score": None,
                "status": "NOT_ESTABLISHED",
                "description": "No verified hands-on diagnostic submission recorded in Practical Task Engine."
            }

        # Layer 3: Portfolio Evidence (Phase 11.2)
        sim_portfolio = opts.get("portfolio_score")
        if sim_portfolio is not None:
            port_score = max(0.0, min(100.0, float(sim_portfolio)))
            evidence_breakdown["portfolio_evidence"] = {
                "score": round(port_score, 1),
                "status": "EVALUATED",
                "description": f"Capstone portfolio artifact verification: {round(port_score, 1)}/100."
            }
        else:
            evidence_breakdown["portfolio_evidence"] = {
                "score": None,
                "status": "NOT_ESTABLISHED",
                "description": "No production-grade capstone project repository linked or evaluated."
            }

        # Layer 4: Interview Evidence (Phase 11.6)
        sim_interview = opts.get("interview_score")
        if sim_interview is not None:
            int_score = max(0.0, min(100.0, float(sim_interview)))
            evidence_breakdown["interview_evidence"] = {
                "score": round(int_score, 1),
                "status": "EVALUATED",
                "description": f"AI Interview Simulator technical articulation score: {round(int_score, 1)}/100."
            }
        else:
            evidence_breakdown["interview_evidence"] = {
                "score": None,
                "status": "NOT_ESTABLISHED",
                "description": "No technical interview simulation attempt recorded for target track."
            }

        # Dynamic Weight Redistribution Algorithm
        established_weights = {}
        for layer_key, base_w in cls.BASE_EVIDENCE_WEIGHTS.items():
            if evidence_breakdown[layer_key]["score"] is not None:
                established_weights[layer_key] = base_w

        total_est_weight = sum(established_weights.values())
        if total_est_weight <= 0.0:
            total_est_weight = 1.0
            established_weights = {"skill_coverage": 1.0}

        dynamic_weights = {}
        composite_score = 0.0

        for layer_key in cls.BASE_EVIDENCE_WEIGHTS:
            if layer_key in established_weights:
                norm_w = round(established_weights[layer_key] / total_est_weight, 3)
                dynamic_weights[layer_key] = norm_w
                layer_score = evidence_breakdown[layer_key]["score"]
                composite_score += norm_w * layer_score
            else:
                dynamic_weights[layer_key] = 0.0

        overall_score = round(min(100.0, max(0.0, composite_score)), 1)
        return evidence_breakdown, dynamic_weights, overall_score

    # =========================================================================
    # 7-Dimension Root Cause Blocker Diagnosis
    # =========================================================================

    @classmethod
    def diagnose_blockers(
        cls,
        career: Career,
        gap_eval: Dict[str, Any],
        priority_skills: List[Dict[str, Any]],
        academic_breakdown: Dict[str, Any],
        vacancy_skills: Set[str],
        evidence_breakdown: Dict[str, Any],
        academic_industry_gaps: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Identifies root-cause blockers across 7 deterministic dimensions:
        1. PREREQUISITE_BLOCKER: Unmet foundational prerequisites
        2. CRITICAL_SKILL_GAP: High-importance skill deficit
        3. PRACTICAL_EVIDENCE_GAP: Core competency unverified hands-on
        4. PORTFOLIO_EVIDENCE_GAP: Absence of capstone artifact
        5. INTERVIEW_EVIDENCE_GAP: Unvalidated technical articulation
        6. ACADEMIC_BLIND_SPOT: Deficits absent in academic syllabi
        7. JOB_SPECIFIC_GAP: Skills required by active job market vacancies
        """
        blockers: List[Dict[str, Any]] = []
        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

        # Index student skills and gaps
        gap_skills_by_norm = {}
        for item in gap_eval.get("prioritized_skill_gaps", []):
            gap_skills_by_norm[normalize_skill_name(item["skill_name"])] = item

        # 1. PREREQUISITE_BLOCKER
        for p_skill in priority_skills:
            target_norm = normalize_skill_name(p_skill["skill_name"])
            prereqs = p_skill.get("prerequisites", [])
            for pr in prereqs:
                pr_norm = normalize_skill_name(pr)
                # Check if prerequisite is satisfied or missing/weak
                pr_gap = gap_skills_by_norm.get(pr_norm)
                if pr_gap and (pr_gap.get("status") in ["MISSING", "WEAK"] or float(pr_gap.get("current_proficiency", 0)) < 2.0):
                    blockers.append({
                        "id": f"blocker-prereq-{pr_norm}-{target_norm}",
                        "blocker_type": cls.BLOCKER_PREREQUISITE,
                        "skill_name": pr.title(),
                        "severity": "CRITICAL" if p_skill.get("career_importance", 0) >= 80 else "HIGH",
                        "title": f"Unmet Prerequisite: {pr.title()} Blocks {p_skill['skill_name']}",
                        "description": f"Foundational mastery of {pr.title()} is required before progressing into {p_skill['skill_name']}.",
                        "impact": f"Prevents core competency closure in {p_skill['skill_name']}.",
                        "resolution_action": f"Complete introductory modules for {pr.title()} prior to advanced practice.",
                        "estimated_effort_hours": 10
                    })

        # 2. CRITICAL_SKILL_GAP
        for item in gap_eval.get("prioritized_skill_gaps", []):
            s_name = item["skill_name"]
            s_norm = normalize_skill_name(s_name)
            importance = int(item.get("importance", 3))
            status = item.get("status", "MISSING")
            curr_prof = float(item.get("current_proficiency", 0.0))

            if importance >= 4 and (status == "MISSING" or curr_prof <= 1.0):
                blockers.append({
                    "id": f"blocker-gap-{s_norm}",
                    "blocker_type": cls.BLOCKER_CRITICAL_SKILL_GAP,
                    "skill_name": s_name,
                    "severity": "CRITICAL" if importance == 5 else "HIGH",
                    "title": f"Critical Skill Deficit: {s_name}",
                    "description": f"{s_name} is a high-importance competency (Level {importance}/5) currently missing or unestablished in your profile.",
                    "impact": f"Lowers primary technical coverage for {career.title}.",
                    "resolution_action": f"Dedicate structured study to core {s_name} syntax, concepts, and exercises.",
                    "estimated_effort_hours": int(round(12 + importance * 2))
                })

        # 3. PRACTICAL_EVIDENCE_GAP
        if evidence_breakdown.get("practical_evidence", {}).get("status") == "NOT_ESTABLISHED":
            top_skill_name = priority_skills[0]["skill_name"] if priority_skills else "Core Competency"
            blockers.append({
                "id": f"blocker-practical-{career.id}",
                "blocker_type": cls.BLOCKER_PRACTICAL_EVIDENCE,
                "skill_name": top_skill_name,
                "severity": "HIGH",
                "title": f"Missing Practical Evidence for {career.title}",
                "description": f"No hands-on diagnostic task submissions have verified applied problem solving in {career.title}.",
                "impact": "Leaves technical execution unvalidated on coding diagnostic benchmarks.",
                "resolution_action": "Complete a hands-on technical task in the Practical Task Engine.",
                "estimated_effort_hours": 2
            })

        # 4. PORTFOLIO_EVIDENCE_GAP
        if evidence_breakdown.get("portfolio_evidence", {}).get("status") == "NOT_ESTABLISHED":
            blockers.append({
                "id": f"blocker-portfolio-{career.id}",
                "blocker_type": cls.BLOCKER_PORTFOLIO_EVIDENCE,
                "skill_name": career.title,
                "severity": "MEDIUM",
                "title": f"Absence of Production-Grade Capstone Artifact",
                "description": f"No end-to-end repository artifact currently showcases integrated {career.title} technologies.",
                "impact": "Recruiters cannot verify architectural design and systems-level coding proficiency.",
                "resolution_action": "Build and publish a recommended capstone project from the Portfolio Engine.",
                "estimated_effort_hours": 25
            })

        # 5. INTERVIEW_EVIDENCE_GAP
        if evidence_breakdown.get("interview_evidence", {}).get("status") == "NOT_ESTABLISHED":
            blockers.append({
                "id": f"blocker-interview-{career.id}",
                "blocker_type": cls.BLOCKER_INTERVIEW_EVIDENCE,
                "skill_name": career.title,
                "severity": "MEDIUM",
                "title": f"Unvalidated Technical Articulation & Defense",
                "description": "Mock interview evaluations have not yet verified verbal explanation of trade-offs and concepts.",
                "impact": "Risk of stumbling during live technical screening interviews.",
                "resolution_action": "Simulate technical interview questions in the AI Interview Simulator.",
                "estimated_effort_hours": 3
            })

        # 6. ACADEMIC_BLIND_SPOT
        for ig in (academic_industry_gaps or []):
            ig_name = ig if isinstance(ig, str) else ig.get("skill_name", str(ig))
            ig_norm = normalize_skill_name(ig_name)
            blockers.append({
                "id": f"blocker-acad-{ig_norm}",
                "blocker_type": cls.BLOCKER_ACADEMIC_BLIND_SPOT,
                "skill_name": ig_name,
                "severity": "MEDIUM",
                "title": f"Academic Blind-Spot: {ig_name}",
                "description": f"{ig_name} is demanded in industry for {career.title} but absent from typical university degree curricula.",
                "impact": "Underrepresented in academic degree programs and coursework transcripts.",
                "resolution_action": f"Supplement university coursework with targeted industry documentation and practical labs for {ig_name}.",
                "estimated_effort_hours": 10
            })

        for s_norm, ab in academic_breakdown.items():
            b_status = str(ab.get("benchmark_status") or ab.get("curriculum_status") or "")
            if "INDUSTRY_GAP" in b_status or ("NEEDS_REINFORCEMENT" in b_status and ab.get("student_status") == "MISSING"):
                s_name = ab.get("skill_name", s_norm.title())
                blockers.append({
                    "id": f"blocker-acad-{s_norm}",
                    "blocker_type": cls.BLOCKER_ACADEMIC_BLIND_SPOT,
                    "skill_name": s_name,
                    "severity": "MEDIUM",
                    "title": f"Academic Blind-Spot: {s_name}",
                    "description": f"{s_name} is covered in academic curriculum but requires practical reinforcement to meet industry benchmarks.",
                    "impact": "Theoretical academic coverage without verified hands-on execution.",
                    "resolution_action": f"Complete hands-on coding exercises and practical labs in {s_name}.",
                    "estimated_effort_hours": 10
                })

        # 7. JOB_SPECIFIC_GAP
        for v_skill in vacancy_skills:
            if v_skill in gap_skills_by_norm:
                gap_item = gap_skills_by_norm[v_skill]
                if gap_item.get("status") in ["MISSING", "WEAK"]:
                    blockers.append({
                        "id": f"blocker-job-{v_skill}",
                        "blocker_type": cls.BLOCKER_JOB_SPECIFIC_GAP,
                        "skill_name": gap_item["skill_name"],
                        "severity": "HIGH",
                        "title": f"Active Market Vacancy Skill Gap: {gap_item['skill_name']}",
                        "description": f"{gap_item['skill_name']} is explicitly demanded in current employer job postings for {career.title}.",
                        "impact": "Limits immediate applicant qualification matching on live job vacancies.",
                        "resolution_action": f"Prioritize {gap_item['skill_name']} in upcoming weekly sprints to match employer requirements.",
                        "estimated_effort_hours": 8
                    })

        # Deterministic deduplication by blocker id
        seen_ids = set()
        deduped = []
        for b in blockers:
            if b["id"] not in seen_ids:
                seen_ids.add(b["id"])
                deduped.append(b)

        # Deterministic sorting: Highest severity first, then blocker_type, then skill_name
        deduped.sort(
            key=lambda x: (-severity_rank.get(x["severity"], 0), x["blocker_type"], x["skill_name"])
        )
        return deduped

    # =========================================================================
    # What should I do TODAY? (Single Highest-Leverage Action)
    # =========================================================================

    @classmethod
    def select_today_action(
        cls,
        blockers: List[Dict[str, Any]],
        priority_skills: List[Dict[str, Any]],
        career: Career
    ) -> Dict[str, Any]:
        """
        Determines the single most impactful, atomic, actionable step for TODAY.
        Prioritizes:
        1. Unmet prerequisite resolution (if blocking critical downstream skills)
        2. Foundation / Core Skill study on the #1 priority skill
        3. Practical task diagnostic validation
        """
        # Case 1: Check for critical prerequisite blockers
        prereq_blockers = [b for b in blockers if b["blocker_type"] == cls.BLOCKER_PREREQUISITE]
        if prereq_blockers:
            pb = prereq_blockers[0]
            return {
                "action_type": "RESOLVE_PREREQUISITE",
                "pillar": "LEARN",
                "title": f"Resolve Prerequisite: Study {pb['skill_name']} Fundamentals",
                "skill_name": pb["skill_name"],
                "estimated_minutes": 60,
                "why_now": f"Highest leverage immediate action: Unblocks downstream progression into core {career.title} competencies.",
                "stage": "FOUNDATION",
                "resource_or_task": {
                    "type": "Prerequisite Foundation",
                    "topic": pb["skill_name"],
                    "action": "Complete introductory syntax, core concepts, and environment setup."
                }
            }

        # Case 2: Priority skills from Adaptive Learning
        if priority_skills:
            top = priority_skills[0]
            stage = top.get("learning_stage", "FOUNDATION")
            skill_name = top["skill_name"]

            if stage in ["FOUNDATION", "CORE_SKILL"]:
                res = top.get("recommended_resources", [])
                resource_item = res[0] if res else None
                return {
                    "action_type": "LEARN",
                    "pillar": "LEARN",
                    "title": f"Master {skill_name} Fundamentals: Core Syntax & Primitives",
                    "skill_name": skill_name,
                    "estimated_minutes": 60,
                    "why_now": f"Offers highest marginal ROI (+{round(top.get('roi_score', 50) * 0.12, 1)}% readiness velocity) addressing your primary career gap.",
                    "stage": stage,
                    "resource_or_task": resource_item
                }
            elif stage == "APPLIED_PRACTICE":
                pt = top.get("practical_task", {})
                task_title = pt.get("title") if pt.get("available") else f"Solve {skill_name} Practical Task"
                return {
                    "action_type": "PRACTICE",
                    "pillar": "PRACTICE",
                    "title": f"Solve Practical Task: {task_title}",
                    "skill_name": skill_name,
                    "estimated_minutes": pt.get("estimated_minutes", 45),
                    "why_now": f"Validates hands-on implementation ability for {skill_name} with automated diagnostic rubrics.",
                    "stage": "APPLIED_PRACTICE",
                    "resource_or_task": pt
                }
            elif stage == "PROJECT_APPLICATION":
                pp = top.get("portfolio_project", {})
                proj_title = pp.get("title") if pp.get("available") else f"Build {skill_name} Capstone Project"
                return {
                    "action_type": "BUILD",
                    "pillar": "BUILD",
                    "title": f"Start Capstone Implementation: {proj_title}",
                    "skill_name": skill_name,
                    "estimated_minutes": 90,
                    "why_now": f"Produces tangible portfolio evidence proving end-to-end implementation of {skill_name}.",
                    "stage": "PROJECT_APPLICATION",
                    "resource_or_task": pp
                }
            else:
                ip = top.get("interview_preparation", {})
                return {
                    "action_type": "PREPARE",
                    "pillar": "PREPARE",
                    "title": f"Simulate Interview Defense: {skill_name} Scenarios",
                    "skill_name": skill_name,
                    "estimated_minutes": 30,
                    "why_now": f"Reinforces conceptual trade-offs and verbal articulation for technical interviews in {skill_name}.",
                    "stage": "INTERVIEW_READINESS",
                    "resource_or_task": ip
                }

        # Case 3: Complete profile / no gaps
        return {
            "action_type": "PREPARE",
            "pillar": "PREPARE",
            "title": f"Conduct Final Mock Technical Screen for {career.title}",
            "skill_name": career.title,
            "estimated_minutes": 45,
            "why_now": "All core competencies satisfied! Polish interview articulation and scenario defense.",
            "stage": "PLACEMENT_READY",
            "resource_or_task": {
                "type": "Comprehensive Mock Screen",
                "career": career.title
            }
        }

    # =========================================================================
    # What should I do NEXT? (4-Pillar Progression)
    # =========================================================================

    @classmethod
    def build_next_actions(
        cls,
        priority_skills: List[Dict[str, Any]],
        career: Career,
        blockers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Builds the next actions across the 4 pedagogical pillars:
        Pillar 1: LEARN (Conceptual / Resource)
        Pillar 2: PRACTICE (Hands-on diagnostic task)
        Pillar 3: BUILD (Portfolio capstone project)
        Pillar 4: PREPARE (Interview scenario / defense)
        """
        actions = []
        top_skill = priority_skills[0] if priority_skills else None
        second_skill = priority_skills[1] if len(priority_skills) > 1 else top_skill

        # Pillar 1: LEARN
        if top_skill:
            actions.append({
                "pillar": "LEARN",
                "title": f"Study {top_skill['skill_name']} Core Architecture",
                "skill_name": top_skill["skill_name"],
                "estimated_hours": 3.0,
                "rationale": f"Establishes theoretical foundation and best practices in {top_skill['skill_name']}.",
                "target_outcome": f"Proficiency Level 3+ understanding of {top_skill['skill_name']} concepts."
            })
        else:
            actions.append({
                "pillar": "LEARN",
                "title": f"Review Advanced Patterns in {career.title}",
                "skill_name": career.title,
                "estimated_hours": 2.0,
                "rationale": "Keep abreast of emerging frameworks and architecture guidelines.",
                "target_outcome": "Maintain sharp domain knowledge."
            })

        # Pillar 2: PRACTICE
        practice_target = top_skill or second_skill
        if practice_target and practice_target.get("practical_task", {}).get("available"):
            pt = practice_target["practical_task"]
            actions.append({
                "pillar": "PRACTICE",
                "title": f"Solve Task: {pt['title']}",
                "skill_name": practice_target["skill_name"],
                "estimated_hours": round(pt.get("estimated_minutes", 45) / 60.0, 1),
                "rationale": f"Diagnostic hands-on task evaluating error handling and edge cases in {practice_target['skill_name']}.",
                "target_outcome": "Verified score >= 70 on automated rubric."
            })
        elif practice_target:
            actions.append({
                "pillar": "PRACTICE",
                "title": f"Complete Diagnostic Exercise in {practice_target['skill_name']}",
                "skill_name": practice_target["skill_name"],
                "estimated_hours": 1.5,
                "rationale": "Applied problem-solving and coding exercises.",
                "target_outcome": "Functional script or module passed without runtime errors."
            })
        else:
            actions.append({
                "pillar": "PRACTICE",
                "title": "Solve Code Refactoring Exercise",
                "skill_name": career.title,
                "estimated_hours": 1.0,
                "rationale": "Maintain code speed and clarity.",
                "target_outcome": "Clean modular codebase."
            })

        # Pillar 3: BUILD
        build_target = top_skill
        if build_target and build_target.get("portfolio_project", {}).get("available"):
            pp = build_target["portfolio_project"]
            actions.append({
                "pillar": "BUILD",
                "title": f"Implement Milestone for '{pp['title']}'",
                "skill_name": build_target["skill_name"],
                "estimated_hours": 5.0,
                "rationale": f"Builds production-grade capstone demonstrating {build_target['skill_name']} in real-world context.",
                "target_outcome": "Committed repository with clean README and tests."
            })
        else:
            actions.append({
                "pillar": "BUILD",
                "title": f"Construct End-to-End {career.title} Capstone Project",
                "skill_name": career.title,
                "estimated_hours": 6.0,
                "rationale": "Tangible public proof of full lifecycle project development.",
                "target_outcome": "Deployable project live demo."
            })

        # Pillar 4: PREPARE
        prep_target = top_skill
        if prep_target and prep_target.get("interview_preparation", {}).get("available"):
            ip = prep_target["interview_preparation"]
            actions.append({
                "pillar": "PREPARE",
                "title": f"Defend Technical Questions on {prep_target['skill_name']}",
                "skill_name": prep_target["skill_name"],
                "estimated_hours": 1.0,
                "rationale": f"Practice answering system design and trade-off questions for {prep_target['skill_name']}.",
                "target_outcome": "Rubric score >= 75 in AI Interview Simulator."
            })
        else:
            actions.append({
                "pillar": "PREPARE",
                "title": f"Mock Behavioral & Technical Interview Round",
                "skill_name": career.title,
                "estimated_hours": 1.0,
                "rationale": "Sharpen STAR-format answers and architectural defense.",
                "target_outcome": "Interview confidence and fluency."
            })

        return actions

    # =========================================================================
    # Weekly Action Plan (Structured by hours_per_week)
    # =========================================================================

    @classmethod
    def build_weekly_plan(
        cls,
        priority_skills: List[Dict[str, Any]],
        hours_per_week: int,
        career: Career
    ) -> List[Dict[str, Any]]:
        """
        Creates a 5-day structured weekly schedule matching the student's study pace.
        Guarantees that the sum of allocated hours equals hours_per_week.
        """
        hpw = float(hours_per_week)
        # Ratios across 5 days: Day 1 (20%), Day 2 (20%), Day 3 (25%), Day 4 (15%), Day 5 (20%)
        # Calculate daily allocations and round cleanly, ensuring exact sum
        d1 = round(hpw * 0.20, 1)
        d2 = round(hpw * 0.20, 1)
        d3 = round(hpw * 0.25, 1)
        d4 = round(hpw * 0.15, 1)
        d5 = round(hpw - (d1 + d2 + d3 + d4), 1)

        skill_1 = priority_skills[0]["skill_name"] if priority_skills else career.title
        skill_2 = priority_skills[1]["skill_name"] if len(priority_skills) > 1 else skill_1

        schedule = [
            {
                "day": "Day 1 (Monday)",
                "pillar": "LEARN",
                "skill_name": skill_1,
                "title": f"Foundational Theory & Environment Setup for {skill_1}",
                "allocated_hours": d1,
                "outcome": f"Understand core principles and establish development tooling for {skill_1}."
            },
            {
                "day": "Day 2 (Tuesday)",
                "pillar": "PRACTICE",
                "skill_name": skill_1,
                "title": f"Diagnostic Coding Tasks & Edge-Case Handling in {skill_1}",
                "allocated_hours": d2,
                "outcome": f"Pass unit tests and validate error handling on hands-on {skill_1} exercises."
            },
            {
                "day": "Day 3 (Wednesday)",
                "pillar": "BUILD",
                "skill_name": skill_1,
                "title": f"Capstone Architecture & Project Module Implementation",
                "allocated_hours": d3,
                "outcome": "Complete core business logic component in capstone portfolio repository."
            },
            {
                "day": "Day 4 (Thursday)",
                "pillar": "LEARN",
                "skill_name": skill_2,
                "title": f"Curriculum Reinforcement & Advanced Patterns in {skill_2}",
                "allocated_hours": d4,
                "outcome": f"Close curriculum blind-spots and review official specifications for {skill_2}."
            },
            {
                "day": "Day 5 (Friday)",
                "pillar": "PREPARE",
                "skill_name": skill_1,
                "title": f"Technical Mock Interview Defense & Weekly Review",
                "allocated_hours": d5,
                "outcome": f"Articulate trade-offs and score >= 75 in mock interview evaluation for {skill_1}."
            }
        ]
        return schedule

    # =========================================================================
    # Milestone States & Critical Path
    # =========================================================================

    @classmethod
    def determine_milestone_state(
        cls,
        overall_score: float,
        blockers: List[Dict[str, Any]]
    ) -> str:
        """
        Evaluates current 5-tier milestone state based on score and critical blockers:
        1. NOT_READY (< 40.0 or critical prerequisite blocker)
        2. FOUNDATION_BUILDING (40.0 - 59.9)
        3. PROJECT_APPLICATION (60.0 - 74.9)
        4. INTERVIEW_ACTIVE (75.0 - 84.9)
        5. PLACEMENT_READY (>= 85.0 and no critical blockers)
        """
        has_critical_prereq = any(
            b["blocker_type"] == cls.BLOCKER_PREREQUISITE and b["severity"] == "CRITICAL"
            for b in blockers
        )

        if overall_score < 40.0 or has_critical_prereq:
            return cls.STATE_NOT_READY
        elif overall_score < 60.0:
            return cls.STATE_FOUNDATION_BUILDING
        elif overall_score < 75.0:
            return cls.STATE_PROJECT_APPLICATION
        elif overall_score < 85.0:
            return cls.STATE_INTERVIEW_ACTIVE
        else:
            return cls.STATE_PLACEMENT_READY

    @classmethod
    def determine_next_milestone(
        cls,
        current_state: str,
        overall_score: float,
        blockers: List[Dict[str, Any]],
        hours_per_week: int
    ) -> Dict[str, Any]:
        """
        Calculates the immediate next milestone, score target, required actions,
        and estimated time to achieve it.
        """
        transitions = {
            cls.STATE_NOT_READY: {
                "target_milestone": cls.STATE_FOUNDATION_BUILDING,
                "target_score": 40.0,
                "required_actions": [
                    "Resolve critical prerequisite blockers",
                    "Complete basic syntax and conceptual modules for core skills"
                ],
                "effort_hours": 20
            },
            cls.STATE_FOUNDATION_BUILDING: {
                "target_milestone": cls.STATE_PROJECT_APPLICATION,
                "target_score": 60.0,
                "required_actions": [
                    "Complete hands-on practical diagnostic tasks",
                    "Elevate core competency gap coverage above 60%"
                ],
                "effort_hours": 30
            },
            cls.STATE_PROJECT_APPLICATION: {
                "target_milestone": cls.STATE_INTERVIEW_ACTIVE,
                "target_score": 75.0,
                "required_actions": [
                    "Ship production-grade capstone project artifact",
                    "Attain placement-ready skill coverage across required competencies"
                ],
                "effort_hours": 35
            },
            cls.STATE_INTERVIEW_ACTIVE: {
                "target_milestone": cls.STATE_PLACEMENT_READY,
                "target_score": 85.0,
                "required_actions": [
                    "Score >= 75 across technical interview simulations",
                    "Refine live market vacancy alignment"
                ],
                "effort_hours": 20
            },
            cls.STATE_PLACEMENT_READY: {
                "target_milestone": "CAREER_PLACEMENT",
                "target_score": 100.0,
                "required_actions": [
                    "Submit applications to matched live job vacancies",
                    "Engage in direct recruiter screenings"
                ],
                "effort_hours": 15
            }
        }

        trans = transitions.get(current_state, transitions[cls.STATE_NOT_READY])
        target_score = trans["target_score"]
        score_gap = max(0.0, round(target_score - overall_score, 1))
        est_weeks = round(trans["effort_hours"] / max(1, hours_per_week), 1)

        return {
            "current_state": current_state,
            "target_milestone": trans["target_milestone"],
            "target_score": target_score,
            "score_gap": score_gap,
            "required_actions": trans["required_actions"],
            "estimated_effort_hours": trans["effort_hours"],
            "estimated_weeks": est_weeks
        }

    @classmethod
    def build_critical_path(
        cls,
        blockers: List[Dict[str, Any]],
        priority_skills: List[Dict[str, Any]],
        milestone_state: str
    ) -> List[Dict[str, Any]]:
        """
        Creates an ordered sequence of critical milestones that must be resolved
        to unblock placement readiness.
        """
        critical_path = []
        step = 1

        # Step 1: Prerequisite resolution
        prereqs = [b for b in blockers if b["blocker_type"] == cls.BLOCKER_PREREQUISITE]
        if prereqs:
            critical_path.append({
                "step": step,
                "type": "UNBLOCK_PREREQUISITE",
                "title": f"Resolve Prerequisite: {prereqs[0]['skill_name']}",
                "status": "IMMEDIATE_ACTION",
                "description": f"Must be completed before advanced modules in {prereqs[0]['title']} can be undertaken."
            })
            step += 1

        # Step 2: High Severity Skill Gaps
        critical_gaps = [b for b in blockers if b["blocker_type"] == cls.BLOCKER_CRITICAL_SKILL_GAP]
        if critical_gaps:
            top_gap = critical_gaps[0]
            critical_path.append({
                "step": step,
                "type": "CLOSE_COMPETENCY_GAP",
                "title": f"Establish Mastery in {top_gap['skill_name']}",
                "status": "PENDING" if step > 1 else "IMMEDIATE_ACTION",
                "description": f"Elevate proficiency in {top_gap['skill_name']} to meet career benchmark levels."
            })
            step += 1

        # Step 3: Practical Diagnostic Evidence
        practical_blocker = any(b["blocker_type"] == cls.BLOCKER_PRACTICAL_EVIDENCE for b in blockers)
        if practical_blocker:
            critical_path.append({
                "step": step,
                "type": "PRACTICAL_EVIDENCE",
                "title": "Validate Hands-On Technical Execution",
                "status": "LOCKED" if step > 2 else "PENDING",
                "description": "Submit code implementation to Practical Task Engine and score >= 70."
            })
            step += 1

        # Step 4: Capstone Portfolio Build
        critical_path.append({
            "step": step,
            "type": "BUILD_CAPSTONE",
            "title": "Publish Capstone Portfolio Artifact",
            "status": "LOCKED" if step > 2 else "PENDING",
            "description": "Construct, document, and deploy production-grade project demonstrating career skills."
        })
        step += 1

        # Step 5: Interview Defense
        critical_path.append({
            "step": step,
            "type": "INTERVIEW_DEFENSE",
            "title": "Pass Technical Screen Interview Simulation",
            "status": "LOCKED",
            "description": "Demonstrate verbal clarity, architecture justification, and problem-solving defense."
        })

        return critical_path

    # =========================================================================
    # Narrative Explanation
    # =========================================================================

    @classmethod
    def generate_explanation(
        cls,
        career_title: str,
        overall_score: float,
        band: str,
        milestone_state: str,
        today_action: Dict[str, Any],
        blockers_count: int
    ) -> str:
        """
        Synthesizes human-readable pedagogical justification explaining current readiness,
        why today's action was selected, and how following the plan moves the student
        toward placement readiness.
        """
        band_descriptions = {
            cls.BAND_FOUNDATION_REQUIRED: "foundational concepts require reinforcement before project application",
            cls.BAND_DEVELOPING: "substantial progress has been demonstrated with remaining applied competencies to close",
            cls.BAND_PLACEMENT_READY: "strong alignment with industry hiring criteria across core competencies"
        }
        band_text = band_descriptions.get(band, "developing track alignment")

        narrative = (
            f"Your current readiness for {career_title} is evaluated at {overall_score}/100 "
            f"({band.replace('_', ' ').title()} band), indicating that {band_text}. "
            f"You are currently situated in the '{milestone_state.replace('_', ' ').title()}' milestone state with "
            f"{blockers_count} identified readiness blocker{'s' if blockers_count != 1 else ''}. "
            f"Today's recommended highest-leverage focus is '{today_action.get('title')}' because "
            f"{today_action.get('why_now', 'it directly closes your highest priority gap')}. "
            f"Consistent execution through the 4-pillar progression (Learn -> Practice -> Build -> Prepare) "
            f"will systematically eliminate technical blockers and advance you toward placement readiness."
        )
        return narrative
