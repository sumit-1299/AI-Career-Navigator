"""
Placement-Ready Career Readiness Summary & Report Service for AI Career Navigator.
Phase 8 Module 8.4.

Consolidates:
1. Overall readiness score and percentage
2. Target career and category/domain
3. Verified/matched skills
4. Remaining skill gaps (missing + weak)
5. ATS / Resume alignment score
6. Study intensity (5, 10, 20 hrs/wk) & completion timeline
7. Practical portfolio/project recommendations from learning catalog
8. Labor-market salary bands & demand outlook
9. Placement-readiness executive summary, tier, and action plan
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from models.career import Career
from models.canonical_skill import CanonicalSkill
from models.learning_resource import LearningResource
from models.skill import Skill
from models.student_profile import StudentProfile
from models.user import User
from services.career_market_service import CareerMarketService
from services.resume_extraction_service import ResumeExtractionService
from services.roadmap_service import RoadmapService
from services.skill_gap_service import SkillGapService


class ReadinessSummaryService:
    """Consolidated Career Readiness Report Generator."""

    VALID_HOURS_PER_WEEK = [5, 10, 20]

    @classmethod
    def generate_readiness_summary(
        cls,
        career_id: int,
        user_id: Optional[int] = None,
        hours_per_week: int = 10,
        resume_text: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generates a placement-ready career readiness summary report.
        """
        if hours_per_week not in cls.VALID_HOURS_PER_WEEK:
            raise ValueError(
                f"Invalid study intensity: {hours_per_week}. Supported values are 5, 10, or 20 hours per week."
            )

        career = Career.query.get(career_id)
        if not career:
            return None

        # 1. User & Profile Context
        user = None
        profile = None
        student_skills: List[Skill] = []
        if user_id:
            user = User.query.get(int(user_id))
            profile = StudentProfile.query.filter_by(user_id=int(user_id)).first()
            student_skills = Skill.query.filter_by(user_id=int(user_id)).all()

        # 2. Skill Gap & Readiness Calculation
        gap_analysis = SkillGapService.evaluate_career_gap(career, student_skills)
        summary_stats = gap_analysis["summary"]
        readiness_pct = summary_stats.get("readiness_percentage", 0.0)
        readiness_score = round(readiness_pct / 10.0, 1)
        if readiness_pct >= 80.0:
            readiness_category = "Ready"
        elif readiness_pct >= 50.0:
            readiness_category = "Developing"
        else:
            readiness_category = "Not Ready"

        prioritized_gaps = gap_analysis["prioritized_skill_gaps"]
        matched_skills = [
            g for g in prioritized_gaps
            if g.get("status") in ["MATCHED", "EXCEEDS"]
        ]
        missing_skills = [
            g for g in prioritized_gaps
            if g.get("status") == "MISSING"
        ]
        weak_skills = [
            g for g in prioritized_gaps
            if g.get("status") == "WEAK"
        ]

        # 3. Weekly Study Intensity & Completion Timeline (Module 8.3)
        roadmap = RoadmapService.generate_roadmap(
            career.title,
            prioritized_gaps,
            hours_per_week=hours_per_week
        )
        study_plan = roadmap.get("study_plan") or {}

        # 4. Labor Market Intelligence Outlook (Phase 7 / Module 8.1)
        market_record = CareerMarketService.get_market_outlook_by_career_id(career_id)
        if not market_record:
            # Fallback outlook if missing
            market_record = {
                "demand_level": "High",
                "demand_score": 85,
                "salary_bands": {
                    "entry_level": "$75,000 / yr",
                    "median": "$110,000 / yr",
                    "senior": "$155,000 / yr"
                },
                "five_year_growth_rate": "+18%",
                "top_hiring_sectors": ["Technology", "Finance", "Healthcare"],
                "key_trends": ["Increasing automation", "Cloud adoption"]
            }

        # 5. Portfolio / Project Recommendations (from learning_resources)
        career_canonical_ids = {
            cs.canonical_skill_id
            for cs in career.skills
            if cs.canonical_skill_id is not None
        }

        project_resources = (
            LearningResource.query
            .filter_by(resource_type="Project", status="Active")
            .all()
        )

        relevant_projects = [
            p for p in project_resources
            if p.canonical_skill_id in career_canonical_ids
        ]

        # Supplement with general projects if fewer than 3
        if len(relevant_projects) < 3:
            for p in project_resources:
                if p not in relevant_projects:
                    relevant_projects.append(p)
                if len(relevant_projects) >= 3:
                    break

        # Map canonical skill names for clarity
        canonical_map = {
            cs.id: cs.name
            for cs in CanonicalSkill.query.all()
        }

        portfolio_projects = [
            {
                "id": p.id,
                "title": p.title,
                "provider": p.provider,
                "difficulty_level": p.difficulty_level,
                "estimated_duration": p.estimated_duration,
                "description": p.description,
                "url": p.url,
                "targeted_skill": canonical_map.get(p.canonical_skill_id, "Core Technical Skill")
            }
            for p in relevant_projects[:4]
        ]

        # 6. ATS Resume Alignment (Module 8.2)
        ats_alignment: Dict[str, Any] = {}
        if resume_text and resume_text.strip():
            score_data = ResumeExtractionService.score_resume_against_career(
                resume_text=resume_text,
                career_id=career_id
            )
            if score_data:
                ats_alignment = {
                    "ats_score": score_data.get("ats_score", 0),
                    "alignment_level": score_data.get("alignment_level", "Moderate"),
                    "matched_keywords": score_data.get("matched_keywords", []),
                    "missing_keywords": score_data.get("missing_keywords", []),
                    "is_scored": True
                }
            else:
                ats_alignment = {
                    "ats_score": None,
                    "alignment_level": "Pending Ingestion",
                    "matched_keywords": [],
                    "missing_keywords": [g["skill_name"] for g in missing_skills[:6]],
                    "is_scored": False
                }
        else:
            # Fallback if no resume provided
            ats_alignment = {
                "ats_score": None,
                "alignment_level": "Pending Ingestion",
                "matched_keywords": [s["skill_name"] for s in matched_skills[:4]],
                "missing_keywords": [g["skill_name"] for g in missing_skills[:6]],
                "is_scored": False,
                "note": "Upload or paste your resume in Resume Ingestion to calculate verified ATS alignment."
            }

        # 7. Placement Readiness Tier & Summary Analysis
        if readiness_pct >= 80.0:
            placement_tier = "Placement-Ready"
            tier_badge = "emerald"
            verdict = (
                f"Candidate exhibits strong technical readiness ({readiness_pct}%) across core "
                f"competencies for {career.title}. Profile is competitive for entry-level and junior placement interviews."
            )
        elif readiness_pct >= 50.0:
            placement_tier = "Interview-Ready Track"
            tier_badge = "indigo"
            verdict = (
                f"Candidate demonstrates steady progress ({readiness_pct}%) with foundational competencies in place. "
                f"Targeted completion of the remaining {len(missing_skills) + len(weak_skills)} gaps will elevate candidate to full interview competitiveness."
            )
        else:
            placement_tier = "Foundational Upskilling"
            tier_badge = "amber"
            verdict = (
                f"Candidate is in the foundational phase of technical preparation ({readiness_pct}%). "
                f"Structured weekly study ({hours_per_week} hrs/week) across high-priority missing skills is strongly recommended."
            )

        top_strengths = [s["skill_name"] for s in matched_skills[:5]]
        critical_priorities = [g["skill_name"] for g in prioritized_gaps[:4]]

        action_plan = [
            f"Dedicate {hours_per_week} hours/week toward closing priority skill gaps: {', '.join(critical_priorities[:2]) if critical_priorities else 'advanced system topics'}.",
            "Build and document 1-2 practical portfolio projects demonstrating end-to-end technical implementation.",
            "Incorporate target ATS keywords into your resume to ensure automated parser alignment.",
            f"Target estimated roadmap completion date: {study_plan.get('estimated_completion_date', 'Upcoming')}."
        ]

        # 8. Consolidated Result
        return {
            "status": "success",
            "career_id": career.id,
            "career_title": career.title,
            "career_category": career.domain,
            "generated_at": datetime.now().strftime("%B %d, %Y"),
            "student_info": {
                "name": user.name if user else "Student Candidate",
                "email": user.email if user else "candidate@example.com",
                "education": profile.education if profile else "Undergraduate",
                "specialization": profile.specialization if profile else "Computer Science & Engineering",
                "graduation_year": profile.graduation_year if profile else 2026,
                "cgpa": profile.cgpa if profile else None
            },
            "overall_readiness": {
                "percentage": readiness_pct,
                "score": readiness_score,
                "category": readiness_category,
                "total_required_skills": len(career.skills),
                "matched_count": len(matched_skills),
                "missing_count": len(missing_skills),
                "weak_count": len(weak_skills)
            },
            "verified_skills": [
                {
                    "skill_name": s["skill_name"],
                    "current_proficiency": s["current_proficiency"],
                    "required_level": s["required_level"],
                    "status": "Verified"
                }
                for s in matched_skills
            ],
            "remaining_skill_gaps": {
                "missing": [
                    {
                        "skill_name": s["skill_name"],
                        "required_level": s["required_level"],
                        "importance": s.get("importance", 3),
                        "priority_score": s.get("priority_score", 0.0),
                        "gap_status": "MISSING"
                    }
                    for s in missing_skills
                ],
                "weak": [
                    {
                        "skill_name": s["skill_name"],
                        "current_proficiency": s["current_proficiency"],
                        "required_level": s["required_level"],
                        "importance": s.get("importance", 3),
                        "priority_score": s.get("priority_score", 0.0),
                        "gap_status": "WEAK"
                    }
                    for s in weak_skills
                ],
                "total_gaps": len(missing_skills) + len(weak_skills)
            },
            "ats_alignment": ats_alignment,
            "study_timeline": {
                "hours_per_week": study_plan.get("hours_per_week", hours_per_week),
                "estimated_total_hours": study_plan.get("estimated_total_hours", 0),
                "estimated_weeks": study_plan.get("estimated_weeks", 0),
                "estimated_completion_date": study_plan.get("estimated_completion_date"),
                "milestones_count": len(study_plan.get("weekly_milestones", []))
            },
            "portfolio_recommendations": portfolio_projects,
            "market_outlook": {
                "demand_level": market_record.get("demand_level", "High"),
                "demand_score": market_record.get("demand_score", 85),
                "salary_bands": market_record.get("salary_bands", {}),
                "five_year_growth_rate": market_record.get("five_year_growth_rate", "+18%"),
                "top_hiring_sectors": market_record.get("top_hiring_sectors", []),
                "key_trends": market_record.get("key_trends", [])
            },
            "placement_summary": {
                "tier": placement_tier,
                "tier_badge": tier_badge,
                "verdict": verdict,
                "strengths": top_strengths,
                "critical_priorities": critical_priorities,
                "estimated_timeline": f"{study_plan.get('estimated_weeks', 0)} weeks at {hours_per_week} hrs/week",
                "action_plan": action_plan
            }
        }
