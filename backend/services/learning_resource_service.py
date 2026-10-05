"""
Curated Learning Resource Service for AI Career Navigator.

Provides query, search, filtering, and seeding utilities for connecting
canonical skills to high-quality learning resources (Courses, Tutorials,
Documentation, Projects, Books, Practice Platforms, Certifications).
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import or_

from extensions import db
from models.canonical_skill import CanonicalSkill
from models.learning_resource import LearningResource
from utils.normalization import normalize_skill_name


CURATED_SAMPLE_CATALOG = [
    {
        "skill_normalized": "python",
        "title": "Python for Everybody Specialization",
        "resource_type": "Course",
        "provider": "Coursera / University of Michigan",
        "url": "https://www.coursera.org/specializations/python",
        "difficulty_level": "Beginner",
        "estimated_duration": "40 hours",
        "description": "Learn to program and analyze data with Python, from basic syntax to databases and web scrapers.",
        "certification_available": True,
        "status": "Active"
    },
    {
        "skill_normalized": "python",
        "title": "Official Python 3 Documentation & Tutorial",
        "resource_type": "Documentation",
        "provider": "Python Software Foundation",
        "url": "https://docs.python.org/3/tutorial/",
        "difficulty_level": "Beginner",
        "estimated_duration": "15 hours",
        "description": "Authoritative language tutorial and reference covering data types, control flow, functions, and standard libraries.",
        "certification_available": False,
        "status": "Active"
    },
    {
        "skill_normalized": "aws",
        "title": "AWS Cloud Practitioner Essentials",
        "resource_type": "Course",
        "provider": "AWS Skill Builder",
        "url": "https://explore.skillbuilder.aws/learn/course/external/view/elearning/134/aws-cloud-practitioner-essentials",
        "difficulty_level": "Beginner",
        "estimated_duration": "6 hours",
        "description": "Foundational understanding of the AWS Cloud, security, architecture, pricing, and support.",
        "certification_available": True,
        "status": "Active"
    },
    {
        "skill_normalized": "aws",
        "title": "AWS Certified Solutions Architect Associate Hands-on Labs",
        "resource_type": "Project",
        "provider": "AWS Workshops",
        "url": "https://workshops.aws/",
        "difficulty_level": "Intermediate",
        "estimated_duration": "25 hours",
        "description": "Architectural patterns, VPC networking, auto-scaling, and multi-tier resilient application deployments.",
        "certification_available": True,
        "status": "Active"
    },
    {
        "skill_normalized": "docker",
        "title": "Docker Getting Started Tutorial & Play with Docker",
        "resource_type": "Practice Platform",
        "provider": "Docker Inc.",
        "url": "https://docs.docker.com/get-started/",
        "difficulty_level": "Beginner",
        "estimated_duration": "8 hours",
        "description": "Interactive browser-based sandbox and tutorial for containerizing applications, building Dockerfiles, and compose stacks.",
        "certification_available": False,
        "status": "Active"
    },
    {
        "skill_normalized": "docker",
        "title": "Docker & Kubernetes: The Complete Practical Guide",
        "resource_type": "Course",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/",
        "difficulty_level": "Intermediate",
        "estimated_duration": "22 hours",
        "description": "Build, test, and deploy Docker applications with Kubernetes production setups.",
        "certification_available": True,
        "status": "Active"
    },
    {
        "skill_normalized": "sql",
        "title": "SQL Tutorial & Interactive Practice",
        "resource_type": "Practice Platform",
        "provider": "Mode Analytics / SQLBolt",
        "url": "https://mode.com/sql-tutorial/",
        "difficulty_level": "Beginner",
        "estimated_duration": "12 hours",
        "description": "Comprehensive SQL tutorial covering SELECT, aggregations, JOINs, subqueries, and window functions.",
        "certification_available": False,
        "status": "Active"
    },
    {
        "skill_normalized": "git",
        "title": "Pro Git Book & Interactive Git Branching",
        "resource_type": "Book",
        "provider": "Git SCM",
        "url": "https://git-scm.com/book/en/v2",
        "difficulty_level": "Beginner",
        "estimated_duration": "10 hours",
        "description": "The definitive open-source guide to Git internals, branching workflows, merging strategies, and remote collaboration.",
        "certification_available": False,
        "status": "Active"
    },
    {
        "skill_normalized": "linux",
        "title": "Introduction to Linux (LFS101x)",
        "resource_type": "Course",
        "provider": "The Linux Foundation / edX",
        "url": "https://www.edx.org/course/introduction-to-linux",
        "difficulty_level": "Beginner",
        "estimated_duration": "30 hours",
        "description": "Fundamental concepts, command-line operations, shell scripts, and system administration.",
        "certification_available": True,
        "status": "Active"
    },
    {
        "skill_normalized": "data structures",
        "title": "Data Structures and Algorithms Specialization",
        "resource_type": "Course",
        "provider": "Coursera / UC San Diego",
        "url": "https://www.coursera.org/specializations/data-structures-algorithms",
        "difficulty_level": "Intermediate",
        "estimated_duration": "45 hours",
        "description": "Algorithmic thinking, trees, hash tables, graphs, dynamic programming, and algorithm optimization.",
        "certification_available": True,
        "status": "Active"
    },
    {
        "skill_normalized": "kubernetes",
        "title": "Kubernetes Official Tutorials & Interactive Tasks",
        "resource_type": "Tutorial",
        "provider": "Cloud Native Computing Foundation",
        "url": "https://kubernetes.io/docs/tutorials/",
        "difficulty_level": "Intermediate",
        "estimated_duration": "15 hours",
        "description": "Deploying containerized apps, exploring Pods, services, scaling, and rolling updates.",
        "certification_available": False,
        "status": "Active"
    }
]


class LearningResourceService:
    """Service for managing and querying curated learning resources."""

    @staticmethod
    def get_resources_for_canonical_skill(
        canonical_skill_id: int,
        difficulty_level: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: str = "Active"
    ) -> List[Dict[str, Any]]:
        """Retrieve active learning resources for a canonical skill."""
        query = LearningResource.query.filter_by(
            canonical_skill_id=canonical_skill_id,
            status=status
        )

        if difficulty_level:
            query = query.filter(LearningResource.difficulty_level.ilike(difficulty_level))
        if resource_type:
            query = query.filter(LearningResource.resource_type.ilike(resource_type))

        resources = query.order_by(
            LearningResource.difficulty_level,
            LearningResource.title
        ).all()

        return [r.to_dict() for r in resources]

    @staticmethod
    def get_resources_for_skills(
        canonical_skill_ids: List[int],
        difficulty_level: Optional[str] = None,
        status: str = "Active"
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Retrieve learning resources mapped by canonical_skill_id."""
        if not canonical_skill_ids:
            return {}

        query = LearningResource.query.filter(
            LearningResource.canonical_skill_id.in_(canonical_skill_ids),
            LearningResource.status == status
        )

        if difficulty_level:
            query = query.filter(LearningResource.difficulty_level.ilike(difficulty_level))

        resources = query.all()
        mapping: Dict[int, List[Dict[str, Any]]] = {sid: [] for sid in canonical_skill_ids}
        for r in resources:
            mapping[r.canonical_skill_id].append(r.to_dict())

        return mapping

    @staticmethod
    def search_resources(
        query_text: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search learning resources across title, provider, and description."""
        query = LearningResource.query.filter(LearningResource.status == "Active")

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.filter(
                or_(
                    LearningResource.title.ilike(search_pattern),
                    LearningResource.provider.ilike(search_pattern),
                    LearningResource.description.ilike(search_pattern)
                )
            )

        if difficulty_level:
            query = query.filter(LearningResource.difficulty_level.ilike(difficulty_level))
        if resource_type:
            query = query.filter(LearningResource.resource_type.ilike(resource_type))

        results = query.limit(limit).all()
        return [r.to_dict() for r in results]

    @staticmethod
    def create_resource(
        canonical_skill_id: int,
        title: str,
        resource_type: str,
        provider: str,
        url: str,
        difficulty_level: str = "Beginner",
        estimated_duration: Optional[str] = None,
        description: Optional[str] = None,
        certification_available: bool = False,
        status: str = "Active"
    ) -> LearningResource:
        """Create and persist a new curated learning resource."""
        res = LearningResource(
            canonical_skill_id=canonical_skill_id,
            title=title,
            resource_type=resource_type,
            provider=provider,
            url=url,
            difficulty_level=difficulty_level,
            estimated_duration=estimated_duration,
            description=description,
            certification_available=certification_available,
            status=status
        )
        db.session.add(res)
        db.session.commit()
        return res

    @classmethod
    def seed_curated_sample_resources(cls) -> int:
        """
        Seeds verified baseline resources for benchmark canonical skills.
        Safe and idempotent: checks if already seeded.
        """
        existing_count = LearningResource.query.count()
        if existing_count > 0:
            return existing_count

        created = 0
        for item in CURATED_SAMPLE_CATALOG:
            skill = CanonicalSkill.query.filter_by(normalized_name=item["skill_normalized"]).first()
            if skill:
                cls.create_resource(
                    canonical_skill_id=skill.id,
                    title=item["title"],
                    resource_type=item["resource_type"],
                    provider=item["provider"],
                    url=item["url"],
                    difficulty_level=item["difficulty_level"],
                    estimated_duration=item["estimated_duration"],
                    description=item["description"],
                    certification_available=item["certification_available"],
                    status=item["status"]
                )
                created += 1

        return created
