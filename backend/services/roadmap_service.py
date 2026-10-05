"""
Roadmap Recommendation Service for AI Career Navigator.

Deterministic, explainable learning roadmap generator based on identified skill gaps.
Maps prioritized skill gaps to recommended milestones, learning modalities, and industry certification paths.
"""

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from models.canonical_skill import CanonicalSkill


# Defined industry certification reference tracks based on project architecture specifications
INDUSTRY_CERTIFICATIONS_CATALOG = {
    "aws": [
        {
            "certification_name": "AWS Certified Cloud Practitioner (CLF-C02)",
            "provider": "Amazon Web Services",
            "level": "Foundational",
            "url": "https://aws.amazon.com/certification/certified-cloud-practitioner/",
            "description": "Validates overall understanding of AWS Cloud platform and foundational architecture."
        },
        {
            "certification_name": "AWS Certified Solutions Architect – Associate (SAA-C03)",
            "provider": "Amazon Web Services",
            "level": "Associate",
            "url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
            "description": "Showcases knowledge of how to design cost-effective and resilient architectures on AWS."
        }
    ],
    "ccna": [
        {
            "certification_name": "Cisco Certified Network Associate (CCNA 200-301)",
            "provider": "Cisco Systems",
            "level": "Associate",
            "url": "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html",
            "description": "Covers networking fundamentals, IP services, security fundamentals, and network automation."
        }
    ],
    "linux": [
        {
            "certification_name": "Linux Professional Institute Certification (LPIC-1)",
            "provider": "Linux Professional Institute",
            "level": "Professional",
            "url": "https://www.lpi.org/our-certifications/lpic-1-overview/",
            "description": "Validates ability to perform maintenance tasks with the command line, install & configure computers."
        },
        {
            "certification_name": "Red Hat Certified System Administrator (RHCSA EX200)",
            "provider": "Red Hat",
            "level": "Professional",
            "url": "https://www.redhat.com/en/services/certification/rhcsa",
            "description": "Demonstrates core system administration skills across Red Hat Enterprise Linux environments."
        }
    ],
    "kubernetes": [
        {
            "certification_name": "Certified Kubernetes Administrator (CKA)",
            "provider": "Linux Foundation / CNCF",
            "level": "Professional",
            "url": "https://www.cncf.io/certification/cka/",
            "description": "Validates skills, knowledge and competency to perform responsibilities of Kubernetes administrators."
        }
    ],
    "docker": [
        {
            "certification_name": "Docker Certified Associate (DCA)",
            "provider": "Mirantis / Docker",
            "level": "Associate",
            "url": "https://training.mirantis.com/certification/dca-certification-exam/",
            "description": "Validates skills in container orchestration, image creation, security and networking."
        }
    ],
    "cybersecurity": [
        {
            "certification_name": "CompTIA Security+ (SY0-701)",
            "provider": "CompTIA",
            "level": "Entry / Intermediate",
            "url": "https://www.comptia.org/certifications/security",
            "description": "Global certification validating baseline cybersecurity skills to perform core security functions."
        }
    ],
    "python": [
        {
            "certification_name": "Certified Associate in Python Programming (PCAP-31-03)",
            "provider": "Python Institute",
            "level": "Associate",
            "url": "https://pythoninstitute.org/pcap",
            "description": "Demonstrates coding skills, object-oriented concepts, and advanced Python modules."
        }
    ]
}


class RoadmapService:
    """Generates structured, explainable learning roadmap steps."""

    @staticmethod
    def get_certifications_for_skill(skill_name: str, normalized_name: str) -> List[Dict[str, str]]:
        """Retrieves verified industry certification mappings for a skill."""
        key = normalized_name.lower().strip()
        if key in INDUSTRY_CERTIFICATIONS_CATALOG:
            return INDUSTRY_CERTIFICATIONS_CATALOG[key]

        # Check partial key match (e.g. 'networking' -> ccna)
        if "network" in key:
            return INDUSTRY_CERTIFICATIONS_CATALOG.get("ccna", [])
        if "cloud" in key:
            return INDUSTRY_CERTIFICATIONS_CATALOG.get("aws", [])
        if "security" in key:
            return INDUSTRY_CERTIFICATIONS_CATALOG.get("cybersecurity", [])

        return []

    @classmethod
    def calculate_study_plan(
        cls,
        roadmap_steps: List[Dict[str, Any]],
        hours_per_week: int
    ) -> Dict[str, Any]:
        """
        Calculates estimated total hours, weeks to completion, completion date,
        and distributes steps into weekly milestones based on study intensity.
        """
        if hours_per_week <= 0:
            raise ValueError("hours_per_week must be greater than zero")

        total_required_hours = sum(step.get("estimated_hours", 0) for step in roadmap_steps)

        if total_required_hours == 0 or len(roadmap_steps) == 0:
            today_str = datetime.now().date().isoformat()
            return {
                "hours_per_week": hours_per_week,
                "estimated_total_hours": 0,
                "estimated_weeks": 0,
                "estimated_completion_date": today_str,
                "weekly_milestones": []
            }

        estimated_weeks = math.ceil(total_required_hours / hours_per_week)
        completion_date = (datetime.now().date() + timedelta(weeks=estimated_weeks)).isoformat()

        # Build continuous interval for each roadmap step
        step_intervals = []
        current_hr = 0
        for s in roadmap_steps:
            s_hours = s.get("estimated_hours", 0)
            step_intervals.append({
                "step": s,
                "start": current_hr,
                "end": current_hr + s_hours
            })
            current_hr += s_hours

        # Distribute workload across weeks
        weekly_milestones = []
        for w in range(1, estimated_weeks + 1):
            w_start = (w - 1) * hours_per_week
            w_end = min(total_required_hours, w * hours_per_week)
            w_hours = w_end - w_start

            active_skills = []
            active_step_details = []

            for item in step_intervals:
                s_start = item["start"]
                s_end = item["end"]
                # Overlap condition
                if max(w_start, s_start) < min(w_end, s_end):
                    overlap_hrs = min(w_end, s_end) - max(w_start, s_start)
                    step_obj = item["step"]
                    sk_name = step_obj["skill_name"]
                    if sk_name not in active_skills:
                        active_skills.append(sk_name)
                    active_step_details.append({
                        "step_number": step_obj["step_number"],
                        "skill_name": sk_name,
                        "allocated_hours": overlap_hrs,
                        "recommended_action": step_obj.get("recommended_action", "")
                    })

            title_skills = ", ".join(active_skills) if active_skills else "Milestone Consolidation"
            weekly_milestones.append({
                "week": w,
                "target_hours": w_hours,
                "skills": active_skills,
                "milestone_title": f"Week {w}: {title_skills}",
                "steps": active_step_details
            })

        return {
            "hours_per_week": hours_per_week,
            "estimated_total_hours": total_required_hours,
            "estimated_weeks": estimated_weeks,
            "estimated_completion_date": completion_date,
            "weekly_milestones": weekly_milestones
        }

    @classmethod
    def generate_roadmap(
        cls,
        career_title: str,
        skill_gaps: List[Dict[str, Any]],
        hours_per_week: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Creates an actionable sequential roadmap addressing prioritized skill gaps,
        optionally incorporating weekly study intensity and timeline calculation.
        """
        # Filter only items requiring action (MISSING and WEAK)
        actionable_gaps = [
            g for g in skill_gaps if g.get("status") in ["MISSING", "WEAK"]
        ]

        roadmap_steps = []
        phase_groups = {
            "Phase 1: Foundational Blockers (Immediate Focus)": [],
            "Phase 2: Core Competency Reinforcement": [],
            "Phase 3: Role Readiness & Specialization": []
        }

        step_counter = 1
        for gap in actionable_gaps:
            status = gap["status"]
            importance = gap.get("importance", 3)
            skill_name = gap["skill_name"]
            req_level = gap.get("required_level", 3)
            score = gap.get("priority_score", 0.0)
            curr_prof = gap.get("current_proficiency", 0)
            gap_val = gap.get("gap_value", max(1, req_level - curr_prof))

            norm_name = skill_name.lower()
            certs = cls.get_certifications_for_skill(skill_name, norm_name)

            if status == "MISSING":
                estimated_hours = 10 + int(req_level) * 5
                action = f"Complete foundational coursework and build introductory practical projects in {skill_name}."
                modalities = ["Interactive coding courses", "Official documentation quickstarts", "Tutorial repositories"]
            else:  # WEAK
                estimated_hours = max(8, int(gap_val) * 8)
                action = f"Reinforce proficiency from current level to required level {req_level}/5 through advanced lab exercises."
                modalities = ["Hands-on portfolio projects", "Code refactoring & unit testing", "Production scenario drills"]

            step_item = {
                "step_number": step_counter,
                "skill_name": skill_name,
                "gap_status": status,
                "required_level": req_level,
                "current_proficiency": curr_prof,
                "importance": importance,
                "priority_score": score,
                "estimated_hours": estimated_hours,
                "recommended_action": action,
                "learning_modalities": modalities,
                "industry_certifications": certs,
                "reason": (
                    f"Prioritized for Step {step_counter} because {skill_name} is marked as "
                    f"'{status}' with career importance {importance}/5 for the {career_title} pathway."
                )
            }

            if score >= 15.0 or (status == "MISSING" and importance >= 4):
                phase_groups["Phase 1: Foundational Blockers (Immediate Focus)"].append(step_item)
            elif score >= 8.0:
                phase_groups["Phase 2: Core Competency Reinforcement"].append(step_item)
            else:
                phase_groups["Phase 3: Role Readiness & Specialization"].append(step_item)

            roadmap_steps.append(step_item)
            step_counter += 1

        result = {
            "career_target": career_title,
            "total_roadmap_steps": len(roadmap_steps),
            "roadmap_phases": [
                {"phase_name": pname, "steps": psteps}
                for pname, psteps in phase_groups.items() if psteps
            ],
            "sequential_steps": roadmap_steps,
            "external_resources_status": {
                "learning_materials_dataset": "Schema defined; awaiting dedicated repository dataset in data/learning/",
                "certifications_dataset": "Baseline industry vendor certifications mapped; future expansion ready."
            }
        }

        if hours_per_week is not None:
            study_plan = cls.calculate_study_plan(roadmap_steps, hours_per_week)
            result["study_plan"] = study_plan
            result["hours_per_week"] = study_plan["hours_per_week"]
            result["estimated_total_hours"] = study_plan["estimated_total_hours"]
            result["estimated_weeks"] = study_plan["estimated_weeks"]
            result["estimated_completion_date"] = study_plan["estimated_completion_date"]
            result["weekly_milestones"] = study_plan["weekly_milestones"]

        return result


def generate_learning_roadmap(
    career_title: str,
    skill_gaps: List[Dict[str, Any]],
    hours_per_week: Optional[int] = None
) -> Dict[str, Any]:
    """Helper wrapper for roadmap generation."""
    return RoadmapService.generate_roadmap(career_title, skill_gaps, hours_per_week=hours_per_week)
