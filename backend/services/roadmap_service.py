"""
Roadmap Recommendation Service for AI Career Navigator.

Deterministic, explainable learning roadmap generator based on identified skill gaps.
Maps prioritized skill gaps to recommended milestones, learning modalities, and industry certification paths.
"""

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
    def generate_roadmap(
        cls,
        career_title: str,
        skill_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Creates an actionable sequential roadmap addressing prioritized skill gaps.
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
            importance = gap["importance"]
            skill_name = gap["skill_name"]
            req_level = gap["required_level"]
            score = gap["priority_score"]

            norm_name = skill_name.lower()
            certs = cls.get_certifications_for_skill(skill_name, norm_name)

            if status == "MISSING":
                action = f"Complete foundational coursework and build introductory practical projects in {skill_name}."
                modalities = ["Interactive coding courses", "Official documentation quickstarts", "Tutorial repositories"]
            else:  # WEAK
                action = f"Reinforce proficiency from current level to required level {req_level}/5 through advanced lab exercises."
                modalities = ["Hands-on portfolio projects", "Code refactoring & unit testing", "Production scenario drills"]

            step_item = {
                "step_number": step_counter,
                "skill_name": skill_name,
                "gap_status": status,
                "required_level": req_level,
                "current_proficiency": gap["current_proficiency"],
                "importance": importance,
                "priority_score": score,
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

        return {
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


def generate_learning_roadmap(career_title: str, skill_gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Helper wrapper for roadmap generation."""
    return RoadmapService.generate_roadmap(career_title, skill_gaps)
