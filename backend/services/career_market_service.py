"""
Career Market Outlook Service for AI Career Navigator.

Provides labor market intelligence, industry demand indicators,
salary bands, top hiring sectors, and growth trends for all canonical career tracks.
"""

from typing import Any, Dict, List, Optional
from models.career import Career


# Standardized Labor Market Intelligence Dataset for all 10 Canonical Careers
CAREER_MARKET_INTELLIGENCE: Dict[int, Dict[str, Any]] = {
    1: {
        "career_id": 1,
        "career_title": "Software Developer",
        "domain": "Software Engineering",
        "demand_score": 92,
        "demand_level": "Very High",
        "five_year_growth_rate": "+22%",
        "salary_bands": {
            "entry_level": "$78,000 / yr",
            "median": "$115,000 / yr",
            "senior": "$165,000 / yr"
        },
        "top_hiring_sectors": [
            "Enterprise Software & SaaS",
            "Financial Services & FinTech",
            "Healthcare & HealthTech",
            "E-Commerce & Digital Retail"
        ],
        "key_trends": [
            "Increased focus on API-first and microservices architectures",
            "Integration of AI code-assist tooling in daily development cycles",
            "Strong demand for backend resilience and cloud deployment automation"
        ]
    },
    2: {
        "career_id": 2,
        "career_title": "Data Scientist",
        "domain": "Data & AI",
        "demand_score": 89,
        "demand_level": "Very High",
        "five_year_growth_rate": "+31%",
        "salary_bands": {
            "entry_level": "$85,000 / yr",
            "median": "$126,000 / yr",
            "senior": "$175,000 / yr"
        },
        "top_hiring_sectors": [
            "Technology & Social Media",
            "Banking & Risk Management",
            "Pharmaceuticals & Biotech",
            "Supply Chain & Logistics"
        ],
        "key_trends": [
            "Shift from experimentation to production ML pipelines (MLOps)",
            "Rising reliance on causal inference and explainable AI models",
            "Emphasis on deep SQL proficiency paired with statistical modeling"
        ]
    },
    3: {
        "career_id": 3,
        "career_title": "Cybersecurity Analyst",
        "domain": "Security & Infrastructure",
        "demand_score": 95,
        "demand_level": "Extremely High",
        "five_year_growth_rate": "+33%",
        "salary_bands": {
            "entry_level": "$80,000 / yr",
            "median": "$118,000 / yr",
            "senior": "$170,000 / yr"
        },
        "top_hiring_sectors": [
            "Aerospace & Defense",
            "Banking & Financial Systems",
            "Government & Public Sector",
            "Cloud Hosting & Telecom"
        ],
        "key_trends": [
            "Zero Trust architecture adoption across hybrid multi-cloud environments",
            "Automated Security Orchestration, Automation, and Response (SOAR)",
            "Heightened regulatory scrutiny on data privacy and incident response"
        ]
    },
    4: {
        "career_id": 4,
        "career_title": "AI / ML Engineer",
        "domain": "Data & AI",
        "demand_score": 96,
        "demand_level": "Extremely High",
        "five_year_growth_rate": "+38%",
        "salary_bands": {
            "entry_level": "$92,000 / yr",
            "median": "$138,000 / yr",
            "senior": "$195,000 / yr"
        },
        "top_hiring_sectors": [
            "Artificial Intelligence Startups",
            "Autonomous Vehicles & Robotics",
            "Cloud Infrastructure Providers",
            "Creative & Digital Media"
        ],
        "key_trends": [
            "Widespread fine-tuning and deployment of LLMs and generative agents",
            "High demand for model optimization (quantization, TensorRT, vLLM)",
            "Convergence of data engineering pipelines with scalable model training"
        ]
    },
    5: {
        "career_id": 5,
        "career_title": "DevOps Engineer",
        "domain": "Cloud & Infrastructure",
        "demand_score": 91,
        "demand_level": "Very High",
        "five_year_growth_rate": "+24%",
        "salary_bands": {
            "entry_level": "$82,000 / yr",
            "median": "$122,000 / yr",
            "senior": "$172,000 / yr"
        },
        "top_hiring_sectors": [
            "Cloud SaaS Providers",
            "FinTech & Online Trading",
            "Digital Media & Streaming",
            "Consulting & IT Services"
        ],
        "key_trends": [
            "GitOps as the dominant deployment standard for Kubernetes",
            "Infrastructure-as-Code policy validation and shift-left security (DevSecOps)",
            "Observability platforms (Prometheus, OpenTelemetry) replacing simple monitoring"
        ]
    },
    6: {
        "career_id": 6,
        "career_title": "Cloud Engineer",
        "domain": "Cloud & Infrastructure",
        "demand_score": 94,
        "demand_level": "Extremely High",
        "five_year_growth_rate": "+28%",
        "salary_bands": {
            "entry_level": "$84,000 / yr",
            "median": "$125,000 / yr",
            "senior": "$178,000 / yr"
        },
        "top_hiring_sectors": [
            "Multi-national Enterprises",
            "Cloud Managed Service Providers",
            "Financial Technologies",
            "Telecommunications"
        ],
        "key_trends": [
            "Multi-cloud architectures balancing AWS, Azure, and Google Cloud",
            "FinOps and cloud cost governance becoming vital core competencies",
            "Serverless architecture expansion for event-driven backend services"
        ]
    },
    7: {
        "career_id": 7,
        "career_title": "Full Stack Developer",
        "domain": "Software Engineering",
        "demand_score": 90,
        "demand_level": "Very High",
        "five_year_growth_rate": "+20%",
        "salary_bands": {
            "entry_level": "$76,000 / yr",
            "median": "$112,000 / yr",
            "senior": "$160,000 / yr"
        },
        "top_hiring_sectors": [
            "Early-stage to Series B Startups",
            "Digital Agencies & Studios",
            "E-Commerce Brands",
            "Enterprise Portals"
        ],
        "key_trends": [
            "Full-stack React frameworks (Next.js/Remix) standardizing unified SSR codebases",
            "TypeScript adoption across both client and server microservices",
            "Headless CMS and composable commerce integrations"
        ]
    },
    8: {
        "career_id": 8,
        "career_title": "Product Manager (Tech)",
        "domain": "Product & Management",
        "demand_score": 85,
        "demand_level": "High",
        "five_year_growth_rate": "+16%",
        "salary_bands": {
            "entry_level": "$82,000 / yr",
            "median": "$128,000 / yr",
            "senior": "$182,000 / yr"
        },
        "top_hiring_sectors": [
            "B2B SaaS Enterprises",
            "Consumer Internet & Mobile Apps",
            "FinTech Platforms",
            "Health & Wellness Tech"
        ],
        "key_trends": [
            "Product-led growth (PLG) data analytics and behavioral cohort metrics",
            "AI-integrated feature roadmapping and rapid MVP prototyping",
            "Deeper technical alignment required with engineering architectures"
        ]
    },
    9: {
        "career_id": 9,
        "career_title": "Data Engineer",
        "domain": "Data & AI",
        "demand_score": 93,
        "demand_level": "Extremely High",
        "five_year_growth_rate": "+27%",
        "salary_bands": {
            "entry_level": "$86,000 / yr",
            "median": "$124,000 / yr",
            "senior": "$176,000 / yr"
        },
        "top_hiring_sectors": [
            "Streaming & Big Data Services",
            "Retail Banking & Insurance",
            "Healthcare Analytics",
            "Global Supply Chain"
        ],
        "key_trends": [
            "Modern Data Stack consolidation (dbt, Snowflake, Databricks, Apache Iceberg)",
            "Real-time stream processing with Kafka and Flink becoming standard",
            "Data contracts and data observability ensuring pipeline quality"
        ]
    },
    10: {
        "career_id": 10,
        "career_title": "Mobile App Developer",
        "domain": "Software Engineering",
        "demand_score": 86,
        "demand_level": "High",
        "five_year_growth_rate": "+18%",
        "salary_bands": {
            "entry_level": "$75,000 / yr",
            "median": "$110,000 / yr",
            "senior": "$158,000 / yr"
        },
        "top_hiring_sectors": [
            "Direct-to-Consumer Apps",
            "FinTech & Mobile Banking",
            "Health & Fitness Technologies",
            "Gaming & Interactive Media"
        ],
        "key_trends": [
            "Cross-platform parity with Flutter and React Native dominating new builds",
            "On-device ML models for low-latency privacy-preserving features",
            "Deep focus on mobile accessibility and fluid micro-interactions"
        ]
    }
}


class CareerMarketService:
    """Service class for retrieving and comparing career labor market outlooks."""

    @classmethod
    def get_market_outlook_by_career_id(cls, career_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves market intelligence for a specific career ID."""
        career = Career.query.get(career_id)
        if not career:
            return None

        # Return predefined market dataset if available
        if career_id in CAREER_MARKET_INTELLIGENCE:
            record = CAREER_MARKET_INTELLIGENCE[career_id].copy()
            record["career_title"] = career.title
            record["domain"] = career.domain
            return record

        # Fallback profile for custom/dynamic careers
        return {
            "career_id": career.id,
            "career_title": career.title,
            "domain": career.domain,
            "demand_score": 80,
            "demand_level": "High",
            "five_year_growth_rate": "+15%",
            "salary_bands": {
                "entry_level": "$70,000 / yr",
                "median": "$105,000 / yr",
                "senior": "$150,000 / yr"
            },
            "top_hiring_sectors": [
                "Information Technology",
                "Financial Services",
                "Professional Consulting"
            ],
            "key_trends": [
                "Digital transformation accelerating demand across industries",
                "Increasing adoption of cloud-native collaboration tooling"
            ]
        }

    @classmethod
    def get_all_market_outlooks(cls) -> List[Dict[str, Any]]:
        """Retrieves labor market intelligence for all careers."""
        careers = Career.query.order_by(Career.id).all()
        outlooks = []
        for career in careers:
            outlook = cls.get_market_outlook_by_career_id(career.id)
            if outlook:
                outlooks.append(outlook)
        return outlooks

    @classmethod
    def compare_market_outlooks(cls, career_ids: List[int]) -> List[Dict[str, Any]]:
        """Retrieves side-by-side market outlook records for multiple career IDs."""
        results = []
        for cid in career_ids:
            outlook = cls.get_market_outlook_by_career_id(cid)
            if outlook:
                results.append(outlook)
        return results
