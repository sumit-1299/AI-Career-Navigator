"""
Industry Demand & Dynamic Skill Weighting Service for AI Career Navigator.
Phase 11 Module 11.4: Real-Time Industry Trends & Dynamic Skill Demand Weighting.

Integrates real-world market intelligence into career requirements and skill gap analysis.
Four strictly separated concepts:
1. MARKET EVIDENCE:
   Normalized demand score [0.0 - 1.0], demand tier, and growth trend.
2. STATIC CAREER REQUIREMENT:
   The career track's baseline importance [1 - 5] and required proficiency [1 - 5].
3. DYNAMIC DEMAND WEIGHT:
   Dynamic Priority = Career Importance * Market Demand Factor
   where Factor = 0.80 + 0.40 * demand_score.
4. STUDENT PROFICIENCY:
   The user's actual demonstrated proficiency level [0 - 5].

DATA PROVENANCE & TRANSPARENCY:
Sample benchmark data is explicitly labeled:
"DEMO / SAMPLE / PROTOTYPE MARKET BENCHMARK — NOT LIVE LABOR MARKET DATA".
Provides deterministic, verifiable market baselines without live web scraping.
"""

from typing import Any, Dict, List, Optional, Tuple
from models.career import Career
from models.career_skill import CareerSkill
from models.canonical_skill import CanonicalSkill
from models.skill_alias import SkillAlias
from models.student_profile import StudentProfile
from services.skill_gap_service import SkillGapService
from services.skill_roi_service import SkillRoiService
from services.portfolio_project_service import PortfolioProjectService
from services.academic_benchmark_service import AcademicBenchmarkService
from utils.normalization import normalize_skill_name, strip_parenthetical_qualifiers


INDUSTRY_DEMAND_PROVENANCE = (
    "DEMO / SAMPLE / PROTOTYPE MARKET BENCHMARK — NOT LIVE LABOR MARKET DATA. "
    "Calculated from normalized industry survey baselines."
)


# ==============================================================================
# CANONICAL SKILL MARKET DEMAND CATALOG
# ==============================================================================
# Covers all 30 canonical skills and aliases across all 10 career paths.
# Scores are normalized between 0.00 and 1.00.
# ==============================================================================

SKILL_MARKET_DEMAND_CATALOG: Dict[str, Dict[str, Any]] = {
    "python": {
        "canonical_name": "Python",
        "demand_score": 0.95,
        "trend": "GROWING",
        "growth_rate_pct": 26.4,
        "sample_job_openings_k": 165,
        "confidence_score": 0.95,
        "top_industries": ["AI & Machine Learning", "Cloud & Backend", "Fintech", "Data Analytics"],
        "market_context": "Dominant language for AI/ML, backend microservices, data science pipelines, and enterprise automation.",
    },
    "docker": {
        "canonical_name": "Docker",
        "demand_score": 0.92,
        "trend": "GROWING",
        "growth_rate_pct": 28.1,
        "sample_job_openings_k": 120,
        "confidence_score": 0.93,
        "top_industries": ["DevOps", "Cloud Native", "Full Stack", "Enterprise Infrastructure"],
        "market_context": "Foundational standard for containerization, local development parity, and modern microservice deployments.",
    },
    "aws": {
        "canonical_name": "AWS",
        "demand_score": 0.93,
        "trend": "GROWING",
        "growth_rate_pct": 25.0,
        "sample_job_openings_k": 140,
        "confidence_score": 0.94,
        "top_industries": ["Cloud Computing", "DevOps", "Enterprise IT", "SaaS Infrastructure"],
        "market_context": "Industry-leading cloud platform with extensive hiring requirements across compute, storage, and serverless.",
    },
    "kubernetes": {
        "canonical_name": "Kubernetes",
        "demand_score": 0.89,
        "trend": "GROWING",
        "growth_rate_pct": 32.5,
        "sample_job_openings_k": 85,
        "confidence_score": 0.92,
        "top_industries": ["Cloud Native", "DevOps / SRE", "Enterprise Architecture"],
        "market_context": "Standard container orchestration engine for scalable distributed systems, high availability, and hybrid cloud.",
    },
    "machine learning": {
        "canonical_name": "Machine Learning",
        "demand_score": 0.92,
        "trend": "GROWING",
        "growth_rate_pct": 34.0,
        "sample_job_openings_k": 95,
        "confidence_score": 0.94,
        "top_industries": ["AI/ML Engineering", "Fintech", "Healthtech", "Autonomous Systems"],
        "market_context": "High-velocity demand driven by predictive modeling, recommendation engines, generative AI, and automation.",
    },
    "deep learning": {
        "canonical_name": "Deep Learning",
        "demand_score": 0.86,
        "trend": "GROWING",
        "growth_rate_pct": 36.2,
        "sample_job_openings_k": 65,
        "confidence_score": 0.91,
        "top_industries": ["AI Research", "Computer Vision", "NLP / LLMs", "Robotics"],
        "market_context": "Specialized high-demand capability required for foundational models, transformers, perception, and neural networks.",
    },
    "react": {
        "canonical_name": "React",
        "demand_score": 0.88,
        "trend": "GROWING",
        "growth_rate_pct": 19.5,
        "sample_job_openings_k": 110,
        "confidence_score": 0.92,
        "top_industries": ["Frontend Web", "Full Stack Development", "B2B SaaS", "Mobile (React Native)"],
        "market_context": "Preeminent JavaScript library for interactive web UIs, single-page applications, and responsive dashboards.",
    },
    "sql": {
        "canonical_name": "SQL",
        "demand_score": 0.87,
        "trend": "STABLE",
        "growth_rate_pct": 8.2,
        "sample_job_openings_k": 175,
        "confidence_score": 0.96,
        "top_industries": ["Data Engineering", "Backend Development", "Business Analytics", "Database Ops"],
        "market_context": "Universal standard across all technical disciplines for relational data querying, aggregation, and persistence.",
    },
    "ci/cd": {
        "canonical_name": "CI/CD",
        "demand_score": 0.84,
        "trend": "GROWING",
        "growth_rate_pct": 22.0,
        "sample_job_openings_k": 78,
        "confidence_score": 0.90,
        "top_industries": ["DevOps", "Platform Engineering", "Software Quality", "Cloud Delivery"],
        "market_context": "Critical workflow requirement for automated build pipelines, unit testing gates, and continuous delivery.",
    },
    "linux": {
        "canonical_name": "Linux",
        "demand_score": 0.82,
        "trend": "STABLE",
        "growth_rate_pct": 11.5,
        "sample_job_openings_k": 130,
        "confidence_score": 0.93,
        "top_industries": ["Server Administration", "DevOps", "Embedded Systems", "Cloud Infrastructure"],
        "market_context": "Fundamental operating system for servers, container runtimes, cloud virtualization, and edge computing.",
    },
    "cybersecurity": {
        "canonical_name": "Cybersecurity",
        "demand_score": 0.87,
        "trend": "GROWING",
        "growth_rate_pct": 29.8,
        "sample_job_openings_k": 92,
        "confidence_score": 0.93,
        "top_industries": ["Information Security", "Defense", "Fintech", "Enterprise Compliance"],
        "market_context": "High-priority corporate imperative facing acute talent shortages across threat defense, compliance, and zero trust.",
    },
    "javascript": {
        "canonical_name": "JavaScript",
        "demand_score": 0.85,
        "trend": "STABLE",
        "growth_rate_pct": 10.0,
        "sample_job_openings_k": 155,
        "confidence_score": 0.95,
        "top_industries": ["Web Development", "Full Stack", "Node.js Microservices", "Front-end"],
        "market_context": "Universal language of the web with pervasive hiring across client browsers, server runtimes, and tooling.",
    },
    "pandas": {
        "canonical_name": "Pandas",
        "demand_score": 0.80,
        "trend": "GROWING",
        "growth_rate_pct": 20.4,
        "sample_job_openings_k": 72,
        "confidence_score": 0.90,
        "top_industries": ["Data Analysis", "Financial Analytics", "Data Science", "Machine Learning"],
        "market_context": "De facto Python library for dataframe manipulation, exploratory analysis, and data feature preparation.",
    },
    "postgresql": {
        "canonical_name": "PostgreSQL",
        "demand_score": 0.78,
        "trend": "GROWING",
        "growth_rate_pct": 18.7,
        "sample_job_openings_k": 80,
        "confidence_score": 0.91,
        "top_industries": ["Backend Engineering", "Open Source DBs", "Fintech", "Data Management"],
        "market_context": "Most beloved open-source relational database, expanding rapidly due to extensibility, JSON support, and pgvector.",
    },
    "java": {
        "canonical_name": "Java",
        "demand_score": 0.76,
        "trend": "STABLE",
        "growth_rate_pct": 6.5,
        "sample_job_openings_k": 145,
        "confidence_score": 0.94,
        "top_industries": ["Enterprise Systems", "Banking / Finance", "Android", "Large-Scale Microservices"],
        "market_context": "Robust enterprise workhorse with deep legacy presence, high-performance JVM execution, and Spring Boot adoption.",
    },
    "git": {
        "canonical_name": "Git",
        "demand_score": 0.77,
        "trend": "STABLE",
        "growth_rate_pct": 7.8,
        "sample_job_openings_k": 160,
        "confidence_score": 0.96,
        "top_industries": ["Software Engineering", "DevOps", "Open Source Collaboration"],
        "market_context": "Essential prerequisite for code versioning, team pull requests, branch protection, and CI integration.",
    },
    "tensorflow": {
        "canonical_name": "TensorFlow",
        "demand_score": 0.74,
        "trend": "GROWING",
        "growth_rate_pct": 15.3,
        "sample_job_openings_k": 45,
        "confidence_score": 0.88,
        "top_industries": ["Deep Learning", "Edge AI (TF Lite)", "Computer Vision", "Production ML"],
        "market_context": "Widely deployed deep learning framework for production inference, mobile model deployment, and distributed training.",
    },
    "data structures": {
        "canonical_name": "Data Structures",
        "demand_score": 0.73,
        "trend": "STABLE",
        "growth_rate_pct": 5.0,
        "sample_job_openings_k": 150,
        "confidence_score": 0.95,
        "top_industries": ["Technical Interviews", "Core Engineering", "High-Performance Systems"],
        "market_context": "Foundational bedrock for technical hiring interviews, algorithmic efficiency, and memory-conscious software design.",
    },
    "network security": {
        "canonical_name": "Network Security",
        "demand_score": 0.74,
        "trend": "GROWING",
        "growth_rate_pct": 21.0,
        "sample_job_openings_k": 58,
        "confidence_score": 0.89,
        "top_industries": ["Infosec", "SOC Defense", "Enterprise Firewalls", "VPN / Zero Trust"],
        "market_context": "Critical perimeter and internal segmentation defense against ransomware, data exfiltration, and unauthorized ingress.",
    },
    "siem": {
        "canonical_name": "SIEM",
        "demand_score": 0.71,
        "trend": "GROWING",
        "growth_rate_pct": 23.5,
        "sample_job_openings_k": 42,
        "confidence_score": 0.88,
        "top_industries": ["SOC Operations", "Threat Intelligence", "Incident Response"],
        "market_context": "Central operational platform for log aggregation, anomaly correlation, alert triage, and incident detection.",
    },
    "database security": {
        "canonical_name": "Database Security",
        "demand_score": 0.69,
        "trend": "GROWING",
        "growth_rate_pct": 16.0,
        "sample_job_openings_k": 38,
        "confidence_score": 0.87,
        "top_industries": ["Data Governance", "SecOps", "Compliance (GDPR/HIPAA)", "DBA"],
        "market_context": "Essential data protection specialty protecting against SQL injection, data leakage, and unencrypted store vulnerabilities.",
    },
    "networking": {
        "canonical_name": "Networking",
        "demand_score": 0.67,
        "trend": "STABLE",
        "growth_rate_pct": 7.0,
        "sample_job_openings_k": 75,
        "confidence_score": 0.90,
        "top_industries": ["Network Administration", "Cloud VPC", "Telecom", "Hardware Infrastructure"],
        "market_context": "Underlying understanding of TCP/IP, DNS, subnetting, and latency required across systems and cloud architecture.",
    },
    "power bi": {
        "canonical_name": "Power BI",
        "demand_score": 0.68,
        "trend": "GROWING",
        "growth_rate_pct": 19.0,
        "sample_job_openings_k": 62,
        "confidence_score": 0.89,
        "top_industries": ["Business Intelligence", "Corporate Reporting", "Financial Analytics"],
        "market_context": "Microsoft-integrated dashboarding tool with huge corporate adoption for executive KPI monitoring and DAX modeling.",
    },
    "mysql": {
        "canonical_name": "MySQL",
        "demand_score": 0.66,
        "trend": "STABLE",
        "growth_rate_pct": 4.2,
        "sample_job_openings_k": 85,
        "confidence_score": 0.91,
        "top_industries": ["Web Development", "LAMP Stack", "E-commerce", "SaaS Databases"],
        "market_context": "Longstanding open-source database powering WordPress, web hosting, and high-throughput transactional backends.",
    },
    "statistics": {
        "canonical_name": "Statistics",
        "demand_score": 0.65,
        "trend": "STABLE",
        "growth_rate_pct": 9.0,
        "sample_job_openings_k": 68,
        "confidence_score": 0.92,
        "top_industries": ["Data Science", "A/B Testing", "Quantitative Finance", "Research"],
        "market_context": "Fundamental mathematical underpinning for hypothesis testing, confidence intervals, regression, and data validity.",
    },
    "ccna": {
        "canonical_name": "CCNA",
        "demand_score": 0.58,
        "trend": "STABLE",
        "growth_rate_pct": 3.5,
        "sample_job_openings_k": 35,
        "confidence_score": 0.86,
        "top_industries": ["Network Engineering", "Cisco Administration", "ISP Operations"],
        "market_context": "Standard vendor certification for entry and mid-level Cisco network installation and troubleshooting.",
    },
    "routing and switching": {
        "canonical_name": "Routing and Switching",
        "demand_score": 0.55,
        "trend": "STABLE",
        "growth_rate_pct": 2.8,
        "sample_job_openings_k": 32,
        "confidence_score": 0.85,
        "top_industries": ["Enterprise LAN/WAN", "Campus Networks", "Data Center Hardware"],
        "market_context": "Core hardware networking discipline transitioning gradually toward software-defined networking (SDN).",
    },
    "html": {
        "canonical_name": "HTML",
        "demand_score": 0.52,
        "trend": "STABLE",
        "growth_rate_pct": 1.5,
        "sample_job_openings_k": 95,
        "confidence_score": 0.93,
        "top_industries": ["Web Development", "Email Marketing", "Content Management"],
        "market_context": "Foundational markup language for all web content, assumed as a basic universal literacy.",
    },
    "css": {
        "canonical_name": "CSS",
        "demand_score": 0.50,
        "trend": "STABLE",
        "growth_rate_pct": 2.0,
        "sample_job_openings_k": 92,
        "confidence_score": 0.92,
        "top_industries": ["Frontend Design", "UI/UX Implementation", "Responsive Web"],
        "market_context": "Visual styling standard for web layouts, flexbox/grid, animations, and responsive cross-device presentation.",
    },
    "excel": {
        "canonical_name": "Excel",
        "demand_score": 0.45,
        "trend": "DECLINING",
        "growth_rate_pct": -3.2,
        "sample_job_openings_k": 110,
        "confidence_score": 0.90,
        "top_industries": ["Business Operations", "Finance / Accounting", "Data Entry"],
        "market_context": "Ubiquitous spreadsheet tool, gradually giving way to automated Python/SQL and BI pipelines for engineering analytics.",
    },
}


class IndustryDemandService:
    """
    Evaluates real-time market trends and computes dynamic skill demand weighting.
    """

    @staticmethod
    def normalize_demand_score(score: float) -> str:
        """
        Maps a continuous demand score [0.0 - 1.0] to a standardized tier:
        - 0.80 - 1.00: VERY_HIGH
        - 0.60 - 0.79: HIGH
        - 0.40 - 0.59: MODERATE
        - 0.20 - 0.39: LOW
        - 0.00 - 0.19: VERY_LOW
        """
        s = max(0.0, min(1.0, float(score)))
        if s >= 0.80:
            return "VERY_HIGH"
        elif s >= 0.60:
            return "HIGH"
        elif s >= 0.40:
            return "MODERATE"
        elif s >= 0.20:
            return "LOW"
        else:
            return "VERY_LOW"

    @staticmethod
    def calculate_market_demand_factor(demand_score: float) -> float:
        """
        Computes the market demand multiplier:
        Factor = 0.80 + 0.40 * demand_score
        Range: [0.80, 1.20]
        - demand_score 0.0 -> factor 0.80 (-20%)
        - demand_score 0.5 -> factor 1.00 (0% change)
        - demand_score 1.0 -> factor 1.20 (+20%)
        """
        s = max(0.0, min(1.0, float(demand_score)))
        factor = 0.80 + (0.40 * s)
        return round(factor, 3)

    @staticmethod
    def calculate_dynamic_priority(
        career_importance: int,
        demand_score: float
    ) -> Tuple[float, float, float]:
        """
        Calculates:
        1. Market Demand Factor [0.80 - 1.20]
        2. Dynamic Priority = Career Importance * Factor
        3. Priority Change % = (Factor - 1.0) * 100

        Preserves static career_importance intact.
        """
        importance = max(1, min(5, int(career_importance)))
        factor = IndustryDemandService.calculate_market_demand_factor(demand_score)
        dynamic_priority = round(importance * factor, 2)
        priority_change_pct = round((factor - 1.0) * 100.0, 1)
        return dynamic_priority, factor, priority_change_pct

    @classmethod
    def get_skill_market_data(cls, skill_name: str) -> Dict[str, Any]:
        """
        Resolves skill to market catalog with alias resolution and case-insensitivity.
        Falls back to neutral benchmark defaults if not cataloged.
        """
        norm_name = normalize_skill_name(strip_parenthetical_qualifiers(skill_name))

        # Direct match in catalog
        if norm_name in SKILL_MARKET_DEMAND_CATALOG:
            data = SKILL_MARKET_DEMAND_CATALOG[norm_name].copy()
            data["demand_level"] = cls.normalize_demand_score(data["demand_score"])
            data["is_catalog_match"] = True
            return data

        # Check DB aliases or CanonicalSkill
        canonical_name = norm_name
        try:
            alias = SkillAlias.query.filter(
                SkillAlias.alias.ilike(norm_name)
            ).first()
            if alias and alias.canonical_skill:
                canonical_name = normalize_skill_name(alias.canonical_skill.name)
            else:
                c_skill = CanonicalSkill.query.filter(
                    CanonicalSkill.name.ilike(norm_name)
                ).first()
                if c_skill:
                    canonical_name = normalize_skill_name(c_skill.name)
        except Exception:
            pass

        if canonical_name in SKILL_MARKET_DEMAND_CATALOG:
            data = SKILL_MARKET_DEMAND_CATALOG[canonical_name].copy()
            data["demand_level"] = cls.normalize_demand_score(data["demand_score"])
            data["is_catalog_match"] = True
            return data

        # Deterministic Neutral Fallback for uncataloged skills
        return {
            "canonical_name": skill_name.strip(),
            "demand_score": 0.50,
            "demand_level": "MODERATE",
            "trend": "STABLE",
            "growth_rate_pct": 0.0,
            "sample_job_openings_k": 25,
            "confidence_score": 0.50,
            "top_industries": ["General Technology"],
            "market_context": "Baseline technical skill with steady industry utilization.",
            "is_catalog_match": False,
        }

    @classmethod
    def evaluate_career_industry_demand(
        cls,
        career_id: int,
        user_id: Optional[int] = None,
        trend_filter: Optional[str] = None,
        demand_level_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Performs full market demand evaluation and dynamic skill weighting for a career.
        Maintains four separate concepts:
        - Market Evidence
        - Static Career Requirements
        - Dynamic Demand Weights
        - Student Proficiency

        Enriches with:
        - Phase 11.1 Skill ROI
        - Phase 11.2 Portfolio Project recommendations
        - Phase 11.3 Academic Curriculum alignment
        """
        career = Career.query.get(career_id)
        if not career:
            return {"error": "CAREER_NOT_FOUND", "message": f"Career with id {career_id} not found"}

        # Fetch required skills
        career_skills = CareerSkill.query.filter_by(career_id=career_id).all()
        if not career_skills:
            return {"error": "NO_CAREER_SKILLS", "message": f"No required skills found for career {career_id}"}

        # Student skills inspection if user_id provided
        student_proficiencies: Dict[str, int] = {}
        is_personalized = False
        if user_id:
            is_personalized = True
            try:
                user_skills = Skill.query.filter_by(user_id=user_id).all()
                for sp in user_skills:
                    s_name = getattr(sp, "skill_name", None)
                    if s_name:
                        norm_s = normalize_skill_name(s_name)
                        student_proficiencies[norm_s] = max(
                            student_proficiencies.get(norm_s, 0),
                            int(getattr(sp, "proficiency", 0))
                        )
            except Exception:
                pass

        # Phase 11.1 Skill ROI lookup if personalized
        roi_lookup: Dict[str, Dict[str, Any]] = {}
        if is_personalized:
            try:
                roi_result = SkillRoiService.rank_career_skill_rois(
                    career_id=career_id,
                    user_id=user_id,
                    hours_per_week=10
                )
                if "ranked_skills" in roi_result:
                    for r_item in roi_result["ranked_skills"]:
                        r_name = normalize_skill_name(r_item.get("skill_name", ""))
                        roi_lookup[r_name] = r_item
            except Exception:
                pass

        # Phase 11.3 Academic coverage lookup
        academic_coverage_lookup: Dict[str, Dict[str, Any]] = {}
        try:
            academic_bench = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=career_id,
                user_id=user_id
            )
            if "skills_analysis" in academic_bench:
                for a_item in academic_bench["skills_analysis"]:
                    a_name = normalize_skill_name(a_item.get("skill_name", ""))
                    academic_coverage_lookup[a_name] = a_item
        except Exception:
            pass

        evaluated_skills: List[Dict[str, Any]] = []
        total_demand_score = 0.0

        for cs in career_skills:
            skill_name = cs.skill.name if hasattr(cs, "skill") and hasattr(cs.skill, "name") else cs.canonical_skill.name if hasattr(cs, "canonical_skill") and cs.canonical_skill else str(cs.canonical_skill_id)
            career_importance = int(getattr(cs, "importance", 3))
            required_proficiency = int(getattr(cs, "required_proficiency", 3))

            market_data = cls.get_skill_market_data(skill_name)
            demand_score = market_data["demand_score"]
            total_demand_score += demand_score

            dynamic_priority, factor, priority_change_pct = cls.calculate_dynamic_priority(
                career_importance=career_importance,
                demand_score=demand_score
            )

            norm_name = normalize_skill_name(skill_name)
            student_prof = student_proficiencies.get(norm_name, 0)
            gap = max(0, required_proficiency - student_prof)
            is_gap = gap > 0
            dynamic_gap_priority = round(gap * factor, 2)

            skill_entry: Dict[str, Any] = {
                "skill_name": skill_name,
                "canonical_name": market_data["canonical_name"],
                "career_importance": career_importance,
                "required_proficiency": required_proficiency,
                "demand_score": demand_score,
                "demand_level": market_data["demand_level"],
                "trend": market_data["trend"],
                "growth_rate_pct": market_data["growth_rate_pct"],
                "sample_job_openings_k": market_data["sample_job_openings_k"],
                "market_demand_factor": factor,
                "dynamic_priority": dynamic_priority,
                "priority_change_pct": priority_change_pct,
                "confidence_score": market_data["confidence_score"],
                "top_industries": market_data["top_industries"],
                "market_context": market_data["market_context"],
                "is_catalog_match": market_data["is_catalog_match"],
                # Student proficiency separation
                "student_proficiency": student_prof if is_personalized else None,
                "gap": gap if is_personalized else None,
                "is_gap": is_gap if is_personalized else None,
                "dynamic_gap_priority": dynamic_gap_priority if is_personalized else None,
            }

            # Enrich with Phase 11.1 Skill ROI if available
            if norm_name in roi_lookup:
                roi_info = roi_lookup[norm_name]
                skill_entry["roi_score"] = roi_info.get("roi_score")
                skill_entry["marginal_gain"] = roi_info.get("marginal_gain")
                skill_entry["study_weeks"] = roi_info.get("study_weeks")
                skill_entry["roi_ranking"] = roi_info.get("rank")
            else:
                skill_entry["roi_score"] = None
                skill_entry["marginal_gain"] = None
                skill_entry["study_weeks"] = None
                skill_entry["roi_ranking"] = None

            # Enrich with Phase 11.3 Academic Coverage
            if norm_name in academic_coverage_lookup:
                ac_info = academic_coverage_lookup[norm_name]
                skill_entry["academic_covered"] = ac_info.get("academic_covered", False)
                skill_entry["academic_evidence"] = ac_info.get("evidence_course")
            else:
                skill_entry["academic_covered"] = False
                skill_entry["academic_evidence"] = None

            evaluated_skills.append(skill_entry)

        # Filters
        filtered_skills = evaluated_skills
        if trend_filter:
            tf_upper = trend_filter.strip().upper()
            filtered_skills = [s for s in filtered_skills if s["trend"].upper() == tf_upper]

        if demand_level_filter:
            df_upper = demand_level_filter.strip().upper()
            filtered_skills = [s for s in filtered_skills if s["demand_level"].upper() == df_upper]

        # Sorting: if personalized, sort by dynamic_gap_priority desc, then dynamic_priority desc
        if is_personalized:
            filtered_skills.sort(
                key=lambda s: (s["dynamic_gap_priority"] or 0, s["dynamic_priority"]),
                reverse=True
            )
        else:
            filtered_skills.sort(
                key=lambda s: (s["dynamic_priority"], s["demand_score"]),
                reverse=True
            )

        if limit and limit > 0:
            filtered_skills = filtered_skills[:limit]

        # Career market temperature
        avg_demand = round(total_demand_score / len(career_skills), 3) if career_skills else 0.50
        if avg_demand >= 0.85:
            temperature = "VERY_HOT"
        elif avg_demand >= 0.75:
            temperature = "HOT"
        elif avg_demand >= 0.60:
            temperature = "STRONG"
        elif avg_demand >= 0.40:
            temperature = "MODERATE"
        else:
            temperature = "COOLING"

        # Trending and high demand highlights
        highest_demand = sorted(evaluated_skills, key=lambda s: s["demand_score"], reverse=True)[:3]
        fastest_growing = sorted(
            [s for s in evaluated_skills if s["trend"] == "GROWING"],
            key=lambda s: s["growth_rate_pct"],
            reverse=True
        )[:3]

        # Phase 11.3 Academic gap vs market highlight:
        # Trending skills with high demand that are NOT covered in standard academic curriculum
        academic_industry_disconnect = [
            s["skill_name"] for s in evaluated_skills
            if s["demand_level"] in ["VERY_HIGH", "HIGH"] and not s["academic_covered"]
        ]

        # Phase 11.2 Recommended Portfolio Project for top dynamic skills
        recommended_portfolio_project = None
        try:
            port_recs = PortfolioProjectService.recommend_projects_for_career(
                career_id=career_id,
                user_id=user_id,
                limit=1
            )
            if "recommended_projects" in port_recs and port_recs["recommended_projects"]:
                top_p = port_recs["recommended_projects"][0]
                recommended_portfolio_project = {
                    "project_id": top_p.get("project_id"),
                    "title": top_p.get("title"),
                    "difficulty": top_p.get("difficulty"),
                    "estimated_hours": top_p.get("estimated_hours"),
                    "skills_covered": top_p.get("skills_covered"),
                    "recommendation_reason": top_p.get("recommendation_reason"),
                }
        except Exception:
            pass

        return {
            "career_id": career.id,
            "career_title": career.title,
            "provenance": INDUSTRY_DEMAND_PROVENANCE,
            "is_personalized": is_personalized,
            "overall_market_temperature": temperature,
            "avg_market_demand_score": avg_demand,
            "highest_demand_skills": [s["skill_name"] for s in highest_demand],
            "fastest_growing_skills": [
                {"skill_name": s["skill_name"], "growth_rate_pct": s["growth_rate_pct"]}
                for s in fastest_growing
            ],
            "academic_industry_disconnect": academic_industry_disconnect,
            "recommended_portfolio_project": recommended_portfolio_project,
            "total_skills_evaluated": len(evaluated_skills),
            "filtered_skills_count": len(filtered_skills),
            "skills": filtered_skills,
        }
