"""
Seed the main branch learning catalog with certification and practical-project
resources required by the existing Phase 7 tests.

This is additive and idempotent:
- existing resources are preserved;
- resources are keyed by title;
- only missing catalog entries are inserted.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app
from extensions import db
from models.canonical_skill import CanonicalSkill
from models.learning_resource import LearningResource


CERTIFICATIONS = [
    {
        "skill": "aws",
        "title": "AWS Certified Cloud Practitioner",
        "provider": "Amazon Web Services",
        "url": "https://aws.amazon.com/certification/certified-cloud-practitioner/",
        "difficulty": "Beginner",
        "duration": "30 hours",
        "description": "Foundational AWS cloud, security, architecture, and pricing knowledge.",
    },
    {
        "skill": "aws",
        "title": "AWS Certified Solutions Architect – Associate",
        "provider": "Amazon Web Services",
        "url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
        "difficulty": "Intermediate",
        "duration": "60 hours",
        "description": "Designing secure, resilient and cost-effective AWS architectures.",
    },
    {
        "skill": "python",
        "title": "Certified Associate in Python Programming (PCAP)",
        "provider": "Python Institute",
        "url": "https://pythoninstitute.org/pcap",
        "difficulty": "Intermediate",
        "duration": "45 hours",
        "description": "Python programming fundamentals, object-oriented concepts and modules.",
    },
    {
        "skill": "linux",
        "title": "Linux Professional Institute Certification (LPIC-1)",
        "provider": "Linux Professional Institute",
        "url": "https://www.lpi.org/our-certifications/lpic-1-overview/",
        "difficulty": "Intermediate",
        "duration": "50 hours",
        "description": "Command-line maintenance, installation and configuration skills.",
    },
    {
        "skill": "linux",
        "title": "Red Hat Certified System Administrator (RHCSA)",
        "provider": "Red Hat",
        "url": "https://www.redhat.com/en/services/certification/rhcsa",
        "difficulty": "Intermediate",
        "duration": "55 hours",
        "description": "Core enterprise Linux administration capabilities.",
    },
    {
        "skill": "kubernetes",
        "title": "Certified Kubernetes Administrator (CKA)",
        "provider": "Cloud Native Computing Foundation",
        "url": "https://www.cncf.io/certification/cka/",
        "difficulty": "Advanced",
        "duration": "60 hours",
        "description": "Hands-on Kubernetes administration and cluster operations.",
    },
    {
        "skill": "docker",
        "title": "Docker Certified Associate",
        "provider": "Mirantis",
        "url": "https://training.mirantis.com/certification/dca-certification-exam/",
        "difficulty": "Intermediate",
        "duration": "40 hours",
        "description": "Container images, networking, security and orchestration fundamentals.",
    },
    {
        "skill": "cybersecurity",
        "title": "CompTIA Security+",
        "provider": "CompTIA",
        "url": "https://www.comptia.org/certifications/security",
        "difficulty": "Intermediate",
        "duration": "50 hours",
        "description": "Baseline cybersecurity, risk, network security and incident-response knowledge.",
    },
    {
        "skill": "ccna",
        "title": "Cisco Certified Network Associate (CCNA)",
        "provider": "Cisco",
        "url": "https://www.cisco.com/site/us/en/learn/training-certifications/certifications/enterprise/ccna/index.html",
        "difficulty": "Intermediate",
        "duration": "60 hours",
        "description": "Networking fundamentals, IP connectivity, security and automation.",
    },
    {
        "skill": "git",
        "title": "GitHub Foundations Certification",
        "provider": "GitHub",
        "url": "https://resources.github.com/learn/certifications/",
        "difficulty": "Beginner",
        "duration": "25 hours",
        "description": "GitHub workflows, repositories, collaboration and development practices.",
    },
]

PROJECTS = [
    {
        "skill": "python",
        "title": "Python REST API Health Monitor",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Beginner",
        "duration": "8 hours",
        "description": "Build a Python utility that checks multiple REST endpoints and reports latency and failures.",
    },
    {
        "skill": "python",
        "title": "Resume Skill Evidence Extractor",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Intermediate",
        "duration": "14 hours",
        "description": "Build a Python pipeline that extracts and normalizes technical skills from resume text.",
    },
    {
        "skill": "sql",
        "title": "Sales Analytics SQL Case Study",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Beginner",
        "duration": "8 hours",
        "description": "Analyze customers, orders and revenue using joins, grouping, filtering and aggregates.",
    },
    {
        "skill": "git",
        "title": "Collaborative Git Workflow Project",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Beginner",
        "duration": "6 hours",
        "description": "Practice feature branches, pull requests, conflict resolution and release tagging.",
    },
    {
        "skill": "docker",
        "title": "Dockerize a Flask API",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Intermediate",
        "duration": "10 hours",
        "description": "Containerize a Flask API with a production-style Dockerfile and health endpoint.",
    },
    {
        "skill": "kubernetes",
        "title": "Kubernetes Deployment Lab",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Advanced",
        "duration": "14 hours",
        "description": "Deploy a small API using a Deployment, Service, ConfigMap and rolling update.",
    },
    {
        "skill": "linux",
        "title": "Linux Server Operations Lab",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Beginner",
        "duration": "8 hours",
        "description": "Configure users, permissions, services, logs and scheduled jobs on a Linux environment.",
    },
    {
        "skill": "aws",
        "title": "AWS Three-Tier Architecture Prototype",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Advanced",
        "duration": "18 hours",
        "description": "Design a secure three-tier AWS architecture and document networking and scaling decisions.",
    },
    {
        "skill": "javascript",
        "title": "Live Job Search Dashboard",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Intermediate",
        "duration": "12 hours",
        "description": "Build a JavaScript UI that consumes a jobs API and supports search and filtering.",
    },
    {
        "skill": "machine learning",
        "title": "Skill Gap Classification Prototype",
        "provider": "AI Career Navigator Practical Task",
        "url": "https://github.com/",
        "difficulty": "Advanced",
        "duration": "20 hours",
        "description": "Build an interpretable ML prototype that classifies evidence states from structured features.",
    },
]


def normalize(value):
    return " ".join((value or "").strip().lower().split())


def seed_resources():
    app = create_app()
    with app.app_context():
        existing_titles = {
            normalize(r.title)
            for r in LearningResource.query.with_entities(LearningResource.title).all()
        }

        created = {"Certification": 0, "Project": 0}
        skipped_missing_skill = []
        skipped_existing = 0

        for resource_type, catalog in (
            ("Certification", CERTIFICATIONS),
            ("Project", PROJECTS),
        ):
            for item in catalog:
                title_key = normalize(item["title"])
                if title_key in existing_titles:
                    skipped_existing += 1
                    continue

                skill = CanonicalSkill.query.filter_by(
                    normalized_name=normalize(item["skill"])
                ).first()

                if not skill:
                    skipped_missing_skill.append(item["skill"])
                    continue

                db.session.add(
                    LearningResource(
                        canonical_skill_id=skill.id,
                        title=item["title"],
                        resource_type=resource_type,
                        provider=item["provider"],
                        url=item["url"],
                        difficulty_level=item["difficulty"],
                        estimated_duration=item["duration"],
                        description=item["description"],
                        certification_available=(resource_type == "Certification"),
                        status="Active",
                    )
                )
                existing_titles.add(title_key)
                created[resource_type] += 1

        db.session.commit()

        print("Learning catalog seed complete.")
        print(f"Certifications added: {created['Certification']}")
        print(f"Projects added: {created['Project']}")
        print(f"Existing entries skipped: {skipped_existing}")

        if skipped_missing_skill:
            print(
                "Skills missing from canonical catalog: "
                + ", ".join(sorted(set(skipped_missing_skill)))
            )


if __name__ == "__main__":
    seed_resources()
