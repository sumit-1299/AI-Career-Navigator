"""
Career Pathway Branching & Elective Specialization Tree Service for AI Career Navigator.
Phase 9 Module 9.3: Interactive Career Pathway Branching & Elective Specialization Tree.

Provides:
- Deterministic career pathway branching for target careers.
- Distinction between core competencies, specialization electives, and common overlapping skills.
- Evaluation of student's current skill readiness, missing skills, and prerequisites per pathway.
- Configurable study intensity (5, 10, 20 hrs/week) and estimated learning effort using existing roadmap calculations.
- Objective pathway suitability scoring and ranking to answer:
  "Which pathway toward this career is most suitable for me?"
- Transparent limitation reporting where existing curriculum only supports a single consolidated pathway.
"""

from typing import Any, Dict, List, Optional, Set
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from services.roadmap_service import RoadmapService
from services.skill_gap_service import SkillGapService, SkillGapStatus
from utils.normalization import normalize_skill_name


# Deterministic skill prerequisite dependencies based on canonical skill relationships
PREREQUISITE_DEPENDENCIES: Dict[str, List[str]] = {
    "react": ["javascript", "html", "css"],
    "pandas": ["python"],
    "machine learning": ["python", "statistics"],
    "deep learning": ["machine learning", "python"],
    "tensorflow": ["python", "machine learning"],
    "aws": ["linux", "networking"],
    "docker": ["linux"],
    "kubernetes": ["docker", "linux"],
    "ci/cd": ["git", "linux"],
    "siem": ["linux", "networking", "cybersecurity"],
    "routing and switching": ["networking"],
    "ccna": ["networking"],
    "network security": ["networking"],
    "postgresql": ["sql"],
    "mysql": ["sql"],
    "database security": ["sql"],
}


# Curated pathway registry strictly referencing existing career skills in database
CAREER_PATHWAYS_CONFIG: Dict[int, Dict[str, Any]] = {
    # Career 1: Software Developer (Skills: Python, Java, Data Structures, Git, SQL)
    1: {
        "has_multiple_pathways": True,
        "limitation_note": None,
        "pathways": [
            {
                "id": "sw-dev-python",
                "name": "Python Backend & Systems Track",
                "specialization_focus": "Python & Backend Systems",
                "description": "Emphasizes modern Python backend services, asynchronous architecture, and relational querying.",
                "is_primary": True,
                "core_skill_names": ["Data Structures", "Git", "SQL"],
                "elective_skill_names": ["Python"],
            },
            {
                "id": "sw-dev-java",
                "name": "Enterprise Java Architecture Track",
                "specialization_focus": "Enterprise Java & High-Throughput Services",
                "description": "Focuses on robust enterprise architectures, JVM design patterns, and distributed services.",
                "is_primary": False,
                "core_skill_names": ["Data Structures", "Git", "SQL"],
                "elective_skill_names": ["Java"],
            },
            {
                "id": "sw-dev-polyglot",
                "name": "Full-Stack Polyglot Engineering Track",
                "specialization_focus": "Multi-Language Full-Stack Engineering",
                "description": "Comprehensive engineering track mastering both Python and Java paradigms for maximum versatility.",
                "is_primary": False,
                "core_skill_names": ["Data Structures", "Git"],
                "elective_skill_names": ["Python", "Java", "SQL"],
            },
        ],
    },

    # Career 2: Web Developer (Skills: HTML, CSS, JavaScript, React, Git)
    2: {
        "has_multiple_pathways": True,
        "limitation_note": None,
        "pathways": [
            {
                "id": "web-dev-react",
                "name": "Modern Component & React Engineering Track",
                "specialization_focus": "Single-Page Applications & React Ecosystem",
                "description": "Focuses on component-driven web application architecture, state management, and modern React workflows.",
                "is_primary": True,
                "core_skill_names": ["HTML", "CSS", "JavaScript"],
                "elective_skill_names": ["React", "Git"],
            },
            {
                "id": "web-dev-standards",
                "name": "Core Frontend & Web Standards Track",
                "specialization_focus": "Semantic Web & Vanilla JavaScript Performance",
                "description": "Focuses on lightweight, standards-compliant web development with minimal runtime overhead.",
                "is_primary": False,
                "core_skill_names": ["HTML", "CSS", "JavaScript"],
                "elective_skill_names": ["Git"],
            },
        ],
    },

    # Career 3: Data Analyst (Skills: SQL, Power BI, Python, Statistics, Excel)
    3: {
        "has_multiple_pathways": False,
        "limitation_note": "Single consolidated pathway supported by current curriculum: analytics curriculum consolidates BI tooling, SQL querying, and descriptive statistics.",
        "pathways": [
            {
                "id": "data-analyst-bi",
                "name": "Business Intelligence & Quantitative Analytics Track",
                "specialization_focus": "BI Reporting, SQL Warehousing & Statistical Analytics",
                "description": "Consolidates relational database querying, interactive dashboards, and business performance metrics into a unified track.",
                "is_primary": True,
                "core_skill_names": ["SQL", "Excel", "Statistics", "Power BI"],
                "elective_skill_names": ["Python"],
            },
        ],
    },

    # Career 4: Data Scientist (Skills: Python, SQL, Statistics, Machine Learning, Pandas)
    4: {
        "has_multiple_pathways": True,
        "limitation_note": None,
        "pathways": [
            {
                "id": "data-sci-statistical",
                "name": "Statistical Analytics & Exploratory Modeling Track",
                "specialization_focus": "Statistical Inference & Tabular Data Science",
                "description": "Focuses on deep exploratory data analysis, hypothesis testing, and quantitative reporting using Pandas and SQL.",
                "is_primary": True,
                "core_skill_names": ["Python", "SQL", "Pandas"],
                "elective_skill_names": ["Statistics"],
            },
            {
                "id": "data-sci-ml",
                "name": "Machine Learning & Predictive Systems Track",
                "specialization_focus": "Algorithmic Modeling & Predictive Pipelines",
                "description": "Targets machine learning model training, hyperparameter optimization, and predictive analytics.",
                "is_primary": False,
                "core_skill_names": ["Python", "Pandas"],
                "elective_skill_names": ["Machine Learning", "Statistics", "SQL"],
            },
        ],
    },

    # Career 5: AI/ML Engineer (Skills: Python, Machine Learning, Deep Learning, TensorFlow, Statistics)
    5: {
        "has_multiple_pathways": True,
        "limitation_note": None,
        "pathways": [
            {
                "id": "ai-ml-applied",
                "name": "Applied Machine Learning Specialist Track",
                "specialization_focus": "Feature Engineering & Supervised Learning",
                "description": "Focuses on practical machine learning pipelines, statistical feature selection, and model validation.",
                "is_primary": True,
                "core_skill_names": ["Python", "Statistics", "Machine Learning"],
                "elective_skill_names": ["TensorFlow"],
            },
            {
                "id": "ai-ml-deep-learning",
                "name": "Deep Learning & Neural Architectures Track",
                "specialization_focus": "Deep Neural Networks & Tensor Computation",
                "description": "Targets multi-layer neural networks, backpropagation optimization, and computational graphs with TensorFlow.",
                "is_primary": False,
                "core_skill_names": ["Python", "Machine Learning"],
                "elective_skill_names": ["Deep Learning", "TensorFlow", "Statistics"],
            },
        ],
    },

    # Career 6: Cloud Engineer (Skills: Linux, Networking, AWS, Python, Docker)
    6: {
        "has_multiple_pathways": True,
        "limitation_note": None,
        "pathways": [
            {
                "id": "cloud-infra",
                "name": "Cloud Infrastructure & Systems Operations Track",
                "specialization_focus": "VPC Networking, Server Virtualization & Cloud Security",
                "description": "Focuses on foundational Linux system administration, VPC networks, and core AWS infrastructure provisioning.",
                "is_primary": True,
                "core_skill_names": ["Linux", "Networking", "AWS"],
                "elective_skill_names": ["Docker"],
            },
            {
                "id": "cloud-devops-automation",
                "name": "Cloud Automation & Containerization Track",
                "specialization_focus": "Containerized Workloads & Cloud Scripting",
                "description": "Targets containerized microservice deployments, Docker runtime management, and automated Python infrastructure scripts.",
                "is_primary": False,
                "core_skill_names": ["Linux", "AWS"],
                "elective_skill_names": ["Python", "Docker", "Networking"],
            },
        ],
    },

    # Career 7: DevOps Engineer (Skills: Linux, Docker, Kubernetes, Git, CI/CD)
    7: {
        "has_multiple_pathways": False,
        "limitation_note": "Single consolidated pathway supported by current curriculum: all competencies are mandatory core requirements without elective branching.",
        "pathways": [
            {
                "id": "devops-core",
                "name": "Standard DevOps Automation & Delivery Track",
                "specialization_focus": "Infrastructure as Code, CI/CD & Container Orchestration",
                "description": "All competencies are essential core requirements for modern continuous integration, delivery pipelines, and Kubernetes management.",
                "is_primary": True,
                "core_skill_names": ["Linux", "Docker", "Kubernetes", "Git", "CI/CD"],
                "elective_skill_names": [],
            },
        ],
    },

    # Career 8: Cybersecurity Analyst (Skills: Linux, Networking, Cybersecurity, Python, SIEM)
    8: {
        "has_multiple_pathways": False,
        "limitation_note": "Single consolidated pathway supported by current curriculum: defense monitoring requirements follow a unified SOC operational track.",
        "pathways": [
            {
                "id": "cyber-soc",
                "name": "Security Operations Center (SOC) Defense Track",
                "specialization_focus": "Incident Detection, Threat Hunting & SIEM Telemetry",
                "description": "Focuses on intrusion detection, packet inspection, network defense, and SIEM security incident monitoring.",
                "is_primary": True,
                "core_skill_names": ["Linux", "Networking", "Cybersecurity", "SIEM"],
                "elective_skill_names": ["Python"],
            },
        ],
    },

    # Career 9: Network Engineer (Skills: Networking, Linux, Routing and Switching, CCNA, Network Security)
    9: {
        "has_multiple_pathways": False,
        "limitation_note": "Single consolidated pathway supported by current curriculum: networking infrastructure requirements follow a standardized linear certification track.",
        "pathways": [
            {
                "id": "net-eng-core",
                "name": "Core Enterprise Network Engineering Track",
                "specialization_focus": "Routing, Switching Protocols & Enterprise Security",
                "description": "Structured enterprise networking track covering CCNA fundamentals, routers, switches, and edge firewall defense.",
                "is_primary": True,
                "core_skill_names": ["Networking", "Routing and Switching", "CCNA", "Network Security"],
                "elective_skill_names": ["Linux"],
            },
        ],
    },

    # Career 10: Database Administrator (Skills: SQL, PostgreSQL, MySQL, Linux, Database Security)
    10: {
        "has_multiple_pathways": False,
        "limitation_note": "Single consolidated pathway supported by current curriculum: unified DBA track covering open-source RDBMS engines and access security.",
        "pathways": [
            {
                "id": "dba-relational",
                "name": "Relational Database Administration & Security Track",
                "specialization_focus": "PostgreSQL/MySQL Management, Backup & Access Security",
                "description": "Unified DBA track covering open-source relational DBMS engines, maintenance routines, failover, and role-based security.",
                "is_primary": True,
                "core_skill_names": ["SQL", "PostgreSQL", "MySQL", "Database Security"],
                "elective_skill_names": ["Linux"],
            },
        ],
    },
}


class CareerPathwayService:
    """Service providing interactive career pathway branching and elective specialization analysis."""

    @staticmethod
    def get_pathway_configuration(career: Career) -> Dict[str, Any]:
        """
        Retrieves the pathway configuration for a career.
        If not in the pre-configured registry, deterministically generates a baseline pathway
        based on the career's existing career_skills.
        """
        if career.id in CAREER_PATHWAYS_CONFIG:
            return CAREER_PATHWAYS_CONFIG[career.id]

        # Dynamic fallback for any additional career tracks
        skills = sorted(career.skills, key=lambda s: (-s.importance, -s.required_level))
        core_skills = [s.skill_name for s in skills if s.importance >= 4]
        elective_skills = [s.skill_name for s in skills if s.importance < 4]

        # If all are high importance or empty
        if not core_skills:
            core_skills = [s.skill_name for s in skills]
            elective_skills = []

        return {
            "has_multiple_pathways": False,
            "limitation_note": "Single default pathway generated from career competency requirements.",
            "pathways": [
                {
                    "id": f"career-{career.id}-standard",
                    "name": f"Standard {career.title} Track",
                    "specialization_focus": f"Core Competencies in {career.domain or career.title}",
                    "description": f"Standard linear preparation track for {career.title}.",
                    "is_primary": True,
                    "core_skill_names": core_skills,
                    "elective_skill_names": elective_skills,
                }
            ],
        }

    @staticmethod
    def check_prerequisites(
        skill_name: str,
        student_skills_map: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluates whether prerequisites for a given skill are satisfied by student proficiency.
        Returns prerequisites list and boolean satisfaction flag.
        """
        norm = normalize_skill_name(skill_name)
        prereqs = PREREQUISITE_DEPENDENCIES.get(norm, [])
        if not prereqs:
            return {
                "prerequisites": [],
                "prerequisites_satisfied": True,
                "missing_prerequisites": []
            }

        missing = []
        for p in prereqs:
            # Check if student has prerequisite at proficiency >= 2.5 (level 5/10)
            p_prof = student_skills_map.get(p, 0.0)
            if p_prof < 2.5:
                missing.append(p.title())

        return {
            "prerequisites": [p.title() for p in prereqs],
            "prerequisites_satisfied": len(missing) == 0,
            "missing_prerequisites": missing
        }

    @classmethod
    def evaluate_pathway_for_student(
        cls,
        career: Career,
        pathway_def: Dict[str, Any],
        student_skills: List[Skill],
        hours_per_week: int = 10
    ) -> Dict[str, Any]:
        """
        Evaluates a specific pathway against a student's skills profile.
        Calculates:
        - Core vs elective skill requirements
        - Student matches, gaps, and prerequisites
        - Readiness percentage and remaining study hours/weeks
        - Effort tier (LOW, MODERATE, HIGH)
        """
        # Map student skills by normalized name and canonical ID
        student_map_by_id: Dict[int, Skill] = {}
        student_map_by_name: Dict[str, Skill] = {}
        student_prof_by_norm: Dict[str, float] = {}

        for s in student_skills:
            if s.canonical_skill_id:
                student_map_by_id[s.canonical_skill_id] = s
            norm_name = normalize_skill_name(s.skill_name)
            student_map_by_name[norm_name] = s
            student_prof_by_norm[norm_name] = (s.proficiency or 0) / 2.0

        # Index career skills by normalized name
        career_skills_by_norm: Dict[str, CareerSkill] = {}
        for cs in career.skills:
            career_skills_by_norm[normalize_skill_name(cs.skill_name)] = cs

        core_names: List[str] = pathway_def.get("core_skill_names", [])
        elective_names: List[str] = pathway_def.get("elective_skill_names", [])

        core_skills_data: List[Dict[str, Any]] = []
        elective_skills_data: List[Dict[str, Any]] = []
        actionable_gaps: List[Dict[str, Any]] = []

        total_req_points = 0.0
        achieved_points = 0.0

        matched_count = 0
        weak_count = 0
        missing_count = 0

        def process_skill_item(sname: str, is_core: bool) -> Optional[Dict[str, Any]]:
            nonlocal total_req_points, achieved_points, matched_count, weak_count, missing_count

            norm = normalize_skill_name(sname)
            cs = career_skills_by_norm.get(norm)
            if not cs:
                # Skill does not belong to this career in database
                return None

            req_level = cs.required_level or 1
            importance = cs.importance or 1
            total_req_points += req_level

            # Lookup student skill
            matched_s = None
            if cs.canonical_skill_id and cs.canonical_skill_id in student_map_by_id:
                matched_s = student_map_by_id[cs.canonical_skill_id]
            elif norm in student_map_by_name:
                matched_s = student_map_by_name[norm]

            raw_prof = matched_s.proficiency if matched_s else 0
            gap_metrics = SkillGapService.calculate_gap(req_level, raw_prof)
            priority_metrics = SkillGapService.calculate_priority(
                importance,
                gap_metrics["gap_value"],
                gap_metrics["status"]
            )

            clamped_achieved = min(gap_metrics["current_proficiency"], float(req_level))
            achieved_points += clamped_achieved

            st = gap_metrics["status"]
            if st == SkillGapStatus.MISSING:
                missing_count += 1
            elif st == SkillGapStatus.WEAK:
                weak_count += 1
            else:
                matched_count += 1

            prereq_info = cls.check_prerequisites(cs.skill_name, student_prof_by_norm)

            item = {
                "career_skill_id": cs.id,
                "canonical_skill_id": cs.canonical_skill_id,
                "skill_name": cs.skill_name,
                "required_level": req_level,
                "importance": importance,
                "current_proficiency": gap_metrics["current_proficiency"],
                "raw_proficiency": gap_metrics["raw_proficiency"],
                "gap_value": gap_metrics["gap_value"],
                "status": st,
                "priority_score": priority_metrics["priority_score"],
                "priority_level": priority_metrics["priority_level"],
                "is_core": is_core,
                "prerequisites": prereq_info["prerequisites"],
                "prerequisites_satisfied": prereq_info["prerequisites_satisfied"],
                "missing_prerequisites": prereq_info["missing_prerequisites"]
            }

            if st in [SkillGapStatus.MISSING, SkillGapStatus.WEAK]:
                actionable_gaps.append({
                    "skill_name": cs.skill_name,
                    "canonical_skill_id": cs.canonical_skill_id,
                    "required_level": req_level,
                    "importance": importance,
                    "current_proficiency": gap_metrics["current_proficiency"],
                    "gap_value": gap_metrics["gap_value"],
                    "status": st,
                    "priority_score": priority_metrics["priority_score"],
                })

            return item

        for name in core_names:
            processed = process_skill_item(name, is_core=True)
            if processed:
                core_skills_data.append(processed)

        for name in elective_names:
            processed = process_skill_item(name, is_core=False)
            if processed:
                elective_skills_data.append(processed)

        readiness_pct = (
            round((achieved_points / total_req_points) * 100.0, 1)
            if total_req_points > 0
            else 0.0
        )

        # Generate roadmap and study plan for this specific pathway
        roadmap = RoadmapService.generate_roadmap(
            pathway_def["name"], actionable_gaps, hours_per_week=hours_per_week
        )
        study_plan = roadmap.get("study_plan") or {}

        est_hours = study_plan.get("estimated_total_hours", 0)
        est_weeks = study_plan.get("estimated_weeks", 0)
        completion_date = study_plan.get("estimated_completion_date")
        milestones = study_plan.get("weekly_milestones", [])

        # Effort tier classification
        if est_weeks <= 4 or readiness_pct >= 75.0:
            effort_tier = "LOW"
            effort_label = "Fast Track"
        elif est_weeks <= 12 or readiness_pct >= 40.0:
            effort_tier = "MODERATE"
            effort_label = "Moderate Upskilling"
        else:
            effort_tier = "HIGH"
            effort_label = "Extensive Skill Build"

        # Deterministic suitability score for ranking pathways:
        # 70% Readiness + 30% Effort efficiency + Primary track tie-breaker
        readiness_component = 0.70 * readiness_pct
        effort_component = 0.30 * max(0.0, 100.0 - (est_hours * 0.5))
        primary_tiebreak = 1.0 if pathway_def.get("is_primary") else 0.0

        suitability_score = round(readiness_component + effort_component + primary_tiebreak, 1)

        total_skills_count = len(core_skills_data) + len(elective_skills_data)

        return {
            "id": pathway_def["id"],
            "name": pathway_def["name"],
            "specialization_focus": pathway_def.get("specialization_focus", ""),
            "description": pathway_def.get("description", ""),
            "is_primary": pathway_def.get("is_primary", False),
            "suitability_score": suitability_score,
            "readiness_percentage": readiness_pct,
            "effort_tier": effort_tier,
            "effort_tier_label": effort_label,
            "estimated_total_hours": est_hours,
            "estimated_weeks": est_weeks,
            "estimated_completion_date": completion_date,
            "total_skills_count": total_skills_count,
            "matched_skills_count": matched_count,
            "weak_skills_count": weak_count,
            "missing_skills_count": missing_count,
            "core_skills": core_skills_data,
            "elective_skills": elective_skills_data,
            "all_skills": core_skills_data + elective_skills_data,
            "actionable_skill_gaps": actionable_gaps,
            "study_milestones": milestones,
        }

    @classmethod
    def evaluate_career_pathways(
        cls,
        career_id: int,
        user_id: Optional[int] = None,
        hours_per_week: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates all available pathways for a career track.
        Personalizes results if user_id or student skills exist, otherwise evaluates
        neutral baseline pathways.
        """
        career = Career.query.get(career_id)
        if not career:
            return None

        # Fetch student skills if user_id is provided
        student_skills: List[Skill] = []
        is_personalized = False
        if user_id:
            student_skills = Skill.query.filter_by(user_id=user_id).all()
            if student_skills:
                is_personalized = True

        config = cls.get_pathway_configuration(career)
        has_multiple = config.get("has_multiple_pathways", False)
        limitation_note = config.get("limitation_note")
        raw_pathways = config.get("pathways", [])

        # Handle empty skills edge-case
        if not career.skills:
            return {
                "career": {
                    "id": career.id,
                    "title": career.title,
                    "domain": career.domain,
                    "description": career.description,
                    "total_skills": 0,
                },
                "hours_per_week": hours_per_week,
                "is_personalized": False,
                "user_id": user_id,
                "has_multiple_pathways": False,
                "limitation_note": "No curriculum skills defined for this career track.",
                "overlapping_skills": [],
                "pathways_count": 0,
                "recommended_pathway_id": None,
                "recommended_pathway_name": None,
                "recommendation_summary": "No pathway data available.",
                "pathways": [],
            }

        # Evaluate each pathway
        evaluated_pathways: List[Dict[str, Any]] = []
        for pdef in raw_pathways:
            eval_p = cls.evaluate_pathway_for_student(
                career=career,
                pathway_def=pdef,
                student_skills=student_skills,
                hours_per_week=hours_per_week
            )
            evaluated_pathways.append(eval_p)

        # Sort pathways by suitability_score descending, then readiness descending, then est_weeks ascending
        evaluated_pathways.sort(
            key=lambda p: (
                -p["suitability_score"],
                -p["readiness_percentage"],
                p["estimated_weeks"],
                -int(p["is_primary"])
            )
        )

        # Assign ranks and generate explainable justifications
        for idx, p in enumerate(evaluated_pathways):
            rank = idx + 1
            p["rank"] = rank
            p["is_recommended"] = (rank == 1)

            if rank == 1:
                if is_personalized:
                    p["recommendation_reason"] = (
                        f"Top Recommended Pathway: Best alignment with your current background. "
                        f"You have a {p['readiness_percentage']}% readiness match ({p['matched_skills_count']}/{p['total_skills_count']} skills satisfied) "
                        f"with an estimated completion time of ~{p['estimated_weeks']} weeks at {hours_per_week} hrs/week."
                    )
                else:
                    p["recommendation_reason"] = (
                        f"Primary Recommended Pathway: Standard foundational curriculum for {p['name']}, "
                        f"requiring ~{p['estimated_weeks']} study weeks ({p['estimated_total_hours']} total hours) at {hours_per_week} hrs/week."
                    )
            else:
                p["recommendation_reason"] = (
                    f"Alternative Specialization Track: Requires ~{p['estimated_weeks']} weeks ({p['estimated_total_hours']} hours) "
                    f"to master {p['missing_skills_count']} additional specialization competencies (Readiness: {p['readiness_percentage']}%)."
                )

        recommended_p = evaluated_pathways[0] if evaluated_pathways else None
        rec_id = recommended_p["id"] if recommended_p else None
        rec_name = recommended_p["name"] if recommended_p else None

        if is_personalized and recommended_p:
            recommendation_summary = (
                f"Based on your current skill profile, the '{rec_name}' is your most suitable pathway "
                f"with {recommended_p['readiness_percentage']}% current readiness and ~{recommended_p['estimated_weeks']} weeks to completion."
            )
        elif recommended_p:
            recommendation_summary = (
                f"The '{rec_name}' represents the foundational preparation pathway toward {career.title}."
            )
        else:
            recommendation_summary = "No pathways evaluated."

        # Compute overlapping competencies across pathways
        # A skill is overlapping if it is required by all pathways
        overlapping_skills: List[Dict[str, Any]] = []
        if evaluated_pathways:
            # Gather set of skill names present in each pathway
            pathway_skill_sets: List[Set[str]] = [
                {normalize_skill_name(s["skill_name"]) for s in p["all_skills"]}
                for p in evaluated_pathways
            ]
            common_norms = set.intersection(*pathway_skill_sets) if pathway_skill_sets else set()

            # Find representative skill details from first pathway
            first_p_skills = {
                normalize_skill_name(s["skill_name"]): s
                for s in evaluated_pathways[0]["all_skills"]
            }

            for cnorm in sorted(common_norms):
                sdata = first_p_skills.get(cnorm)
                if sdata:
                    overlapping_skills.append({
                        "skill_name": sdata["skill_name"],
                        "canonical_skill_id": sdata["canonical_skill_id"],
                        "required_level": sdata["required_level"],
                        "importance": sdata["importance"],
                        "current_proficiency": sdata["current_proficiency"],
                        "status": sdata["status"],
                        "is_shared_across_all_pathways": True
                    })

        return {
            "career": {
                "id": career.id,
                "title": career.title,
                "domain": career.domain,
                "description": career.description,
                "total_skills": len(career.skills),
            },
            "hours_per_week": hours_per_week,
            "is_personalized": is_personalized,
            "user_id": user_id,
            "has_multiple_pathways": has_multiple,
            "limitation_note": limitation_note,
            "overlapping_skills": overlapping_skills,
            "pathways_count": len(evaluated_pathways),
            "recommended_pathway_id": rec_id,
            "recommended_pathway_name": rec_name,
            "recommendation_summary": recommendation_summary,
            "pathways": evaluated_pathways,
        }
