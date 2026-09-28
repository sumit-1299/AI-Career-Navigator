"""Small, explicit vocabulary for the first backend-job comparison experiment."""

import re

CATALOG_VERSION = "backend-skills-2026-09-27-v1"
ESCO_BASE = "http://data.europa.eu/esco/skill/"

# These aliases are curated for this prototype, not all aliases in the source data.
# Local concepts have no invented ESCO ID. Descriptions below are original anchors.
SKILLS = [
    {"key": "python", "label": "Python", "aliases": ["Python", "Python programming", "Python 3"],
     "anchor": "Python programming language. Write Python functions, scripts, modules and backend applications.",
     "esco_uri": ESCO_BASE + "ccd0a1d9-afda-43d9-b901-96344886e14d"},
    {"key": "sql", "label": "SQL", "aliases": ["SQL", "Structured Query Language"],
     "anchor": "SQL relational database queries. Retrieve and filter table rows, join tables and aggregate grouped records.",
     "esco_uri": ESCO_BASE + "598de5b0-5b58-4ea7-8058-a4bc4d18c742"},
    {"key": "rest_api", "label": "REST APIs", "aliases": ["REST API", "REST APIs", "RESTful API", "RESTful APIs", "RESTful services", "Representational State Transfer"],
     "anchor": "REST API development. Design HTTP endpoints for web services with JSON requests and responses, resources, GET, POST, PUT and DELETE.",
     "esco_uri": None},
    {"key": "django", "label": "Django", "aliases": ["Django"],
     "anchor": "Django web framework. Develop backend applications with Django models, views, templates and the Django ORM.", "esco_uri": None},
    {"key": "flask", "label": "Flask", "aliases": ["Flask"],
     "anchor": "Flask Python web framework. Implement Flask routes, blueprints and web application request handling.", "esco_uri": None},
    {"key": "postgresql", "label": "PostgreSQL", "aliases": ["PostgreSQL", "Postgres"],
     "anchor": "PostgreSQL database system. Create and administer PostgreSQL databases, indexes, tables and transactions.",
     "esco_uri": ESCO_BASE + "a8d07b5a-c1a1-42c6-9d53-db9c7a2ca996"},
    {"key": "git", "label": "Git", "aliases": ["Git", "Git version control"],
     "anchor": "Git version control. Track source code changes with commits, branches, merges and pull requests.", "esco_uri": None},
    {"key": "docker", "label": "Docker", "aliases": ["Docker", "Docker containers"],
     "anchor": "Docker containers. Build Docker images using Dockerfiles and run isolated application containers.", "esco_uri": None},
    {"key": "javascript", "label": "JavaScript", "aliases": ["JavaScript", "ECMAScript"],
     "anchor": "JavaScript programming language. Implement browser interactions and JavaScript server applications.",
     "esco_uri": ESCO_BASE + "3cd569a2-4f88-4c1e-9995-8dce8c5e51a7"},
    {"key": "java", "label": "Java", "aliases": ["Java", "Java programming"],
     "anchor": "Java programming language. Develop Java classes and applications using the Java virtual machine.",
     "esco_uri": ESCO_BASE + "19a8293b-8e95-4de3-983f-77484079c389"},
]

BY_KEY = {skill["key"]: skill for skill in SKILLS}
RELATIONS = [
    {"source": "django", "target": "python", "relation": "framework_for"},
    {"source": "flask", "target": "python", "relation": "framework_for"},
    {"source": "postgresql", "target": "sql", "relation": "database_supports_language"},
]


def normalize_name(value):
    return " ".join(value.casefold().split())


ALIASES = {normalize_name(alias): skill["key"] for skill in SKILLS for alias in [skill["label"], *skill["aliases"]]}
PATTERNS = {
    skill["key"]: re.compile(r"(?<!\w)(?:" + "|".join(re.escape(alias).replace(r"\ ", r"\s+") for alias in sorted(skill["aliases"], key=len, reverse=True)) + r")(?!\w)", re.I)
    for skill in SKILLS
}


def canonical_key(name):
    return ALIASES.get(normalize_name(name)) if isinstance(name, str) else None


def keyword_keys(text):
    return [key for key, pattern in PATTERNS.items() if pattern.search(text)]
