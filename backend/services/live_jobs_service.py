"""Read-only live job connectors for public employer job-board feeds.

Supported public sources:
- Greenhouse Job Board API (e.g. Canonical, Razorpay)
- Ashby Public Job Postings API (e.g. Notion, Vercel, Linear, Ramp)
- Lever public XML postings feed (e.g. Dun & Bradstreet, Spreetail, Zūm)

The connector layer operates completely read-only and never mutates the database.
Includes robust in-memory caching and offline/sandbox fallback fixtures.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
import logging
import re
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

SOURCE_REGISTRY = {
    # Greenhouse
    "greenhouse-canonical": {
        "provider": "greenhouse",
        "label": "Canonical",
        "identifier": "canonical",
        "board_url": "https://job-boards.greenhouse.io/canonical",
    },
    "greenhouse-razorpay": {
        "provider": "greenhouse",
        "label": "Razorpay",
        "identifier": "razorpaysoftwareprivatelimited",
        "board_url": "https://job-boards.greenhouse.io/razorpaysoftwareprivatelimited",
    },
    # Ashby public job boards
    "ashby-notion": {
        "provider": "ashby",
        "label": "Notion",
        "identifier": "notion",
        "board_url": "https://jobs.ashbyhq.com/notion",
    },
    "ashby-vercel": {
        "provider": "ashby",
        "label": "Vercel",
        "identifier": "vercel",
        "board_url": "https://jobs.ashbyhq.com/vercel",
    },
    "ashby-linear": {
        "provider": "ashby",
        "label": "Linear",
        "identifier": "linear",
        "board_url": "https://jobs.ashbyhq.com/linear",
    },
    "ashby-ramp": {
        "provider": "ashby",
        "label": "Ramp",
        "identifier": "ramp",
        "board_url": "https://jobs.ashbyhq.com/ramp",
    },
    # Lever public feeds
    "lever-dnb": {
        "provider": "lever",
        "label": "Dun & Bradstreet",
        "identifier": "dnb",
        "board_url": "https://jobs.lever.co/dnb",
    },
    "lever-spreetail": {
        "provider": "lever",
        "label": "Spreetail",
        "identifier": "spreetail",
        "board_url": "https://jobs.lever.co/spreetail",
    },
    "lever-zum": {
        "provider": "lever",
        "label": "Zūm",
        "identifier": "zum",
        "board_url": "https://jobs.lever.co/zum",
    },
}

MAX_BYTES = 15 * 1024 * 1024
MAX_DESCRIPTION = 60000
MAX_JOBS = 5000
REQUEST_TIMEOUT = 8
MAX_REQUEST_SECONDS = 12
CACHE_TTL_SECONDS = 300

TECH_TAGS = {
    "Python": [r"\bpython\b"],
    "Java": [r"\bjava\b(?!script)"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript": [r"\btypescript\b", r"\bts\b"],
    "SQL": [r"\bsql\b"],
    "PostgreSQL": [r"\bpostgres(?:ql)?\b"],
    "MySQL": [r"\bmysql\b"],
    "REST APIs": [r"\brest(?:ful)?\s+(?:api|apis)\b", r"\bhttp(?:s)?\s+api\b", r"\brest\b"],
    "Django": [r"\bdjango\b"],
    "Flask": [r"\bflask\b"],
    "React": [r"\breact(?:\.js)?\b"],
    "Angular": [r"\bangular\b"],
    "Vue": [r"\bvue(?:\.js)?\b"],
    "Node.js": [r"\bnode(?:\.js)?\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "AWS": [r"\baws\b", r"amazon web services"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"google cloud"],
    "Terraform": [r"\bterraform\b"],
    "Linux": [r"\blinux\b"],
    "Git": [r"\bgit\b", r"github", r"gitlab"],
    "GraphQL": [r"\bgraphql\b"],
    "Kafka": [r"\bkafka\b"],
    "Spark": [r"\bspark\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml engineer\b", r"\bmlops\b"],
    "Artificial Intelligence": [r"\bartificial intelligence\b", r"\bai engineer\b", r"\bgenerative ai\b"],
    "Data Analysis": [r"\bdata engineer\b", r"\bdata scientist\b", r"\bdata analyst\b", r"\banalytics\b"],
    "DevOps": [r"\bdevops\b", r"\bdevsecops\b", r"\bsre\b", r"\bsite reliability\b"],
    "Cloud Computing": [r"\bcloud engineer\b", r"\bcloud architect\b"],
    "Cybersecurity": [r"\bcybersecurity\b", r"\bsecurity engineer\b", r"\bapplication security\b"],
}

TECH_TITLE_PATTERNS = [
    r"software", r"developer", r"engineer", r"engineering", r"backend", r"back-end",
    r"frontend", r"front-end", r"full[- ]stack", r"web developer", r"mobile",
    r"android", r"ios", r"devops", r"reliability", r"platform", r"infrastructure",
    r"cloud", r"database", r"data scientist", r"data engineer", r"data analyst",
    r"analytics engineer", r"machine learning", r"ai ", r"artificial intelligence",
    r"cyber", r"security engineer", r"qa", r"quality assurance", r"automation",
    r"test engineer", r"network engineer", r"systems engineer", r"solution architect",
    r"technical architect", r"technical program", r"developer advocate", r"technical writer",
    r"product engineer",
]

NON_TECH_TITLE_PATTERNS = [
    r"\bsales\b", r"\baccount executive\b", r"\bbusiness development\b", r"\bmarketing\b",
    r"\bfinance\b", r"\baccounting\b", r"\blegal\b", r"\bcompliance\b", r"\bpayroll\b",
    r"\bpeople operations\b", r"\bhuman resources\b", r"\bhr\b", r"\brecruit(?:er|ing)\b",
    r"\bcustomer success\b", r"\bcustomer support\b", r"\bcommunications\b", r"\bpublic relations\b",
    r"\bpr manager\b", r"\bcontent marketing\b", r"\boperations\b(?!.*engineer)",
]


class FeedUnavailable(Exception):
    """Raised when a live employer feed cannot be reached or trusted."""


class PlainDescription(HTMLParser):
    """Convert provider HTML into safe plain text."""

    breaks = {
        "p", "div", "li", "ul", "ol", "br", "h1", "h2", "h3", "h4",
        "section", "tr", "table", "blockquote",
    }
    blocked = {"script", "style", "iframe", "object", "template", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = []

    def handle_starttag(self, tag, attrs):
        if tag in self.blocked:
            self.hidden.append(tag)
        if not self.hidden and tag in self.breaks:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
        elif tag in self.breaks:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


class NoRedirect(HTTPRedirectHandler):
    """Reject unexpected provider redirects from API/feed requests."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FeedUnavailable("The employer provider redirected the live request.")


def plain_description(content):
    """Convert provider HTML or plain text into normalized plain text."""
    if not isinstance(content, str):
        return ""
    if len(content) > 250000:
        content = content[:250000]

    parser = PlainDescription()
    try:
        parser.feed(unescape(unescape(content)))
        parser.close()
    except Exception:
        # Fallback regex strip if HTMLParser fails
        cleaned = re.sub(r"<[^>]+>", " ", content)
        return re.sub(r"\s+", " ", cleaned).strip()

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in "".join(parser.parts).splitlines()
    ]
    text = "\n".join(line for line in lines if line)
    return text[:MAX_DESCRIPTION]


def _safe_source_url(candidate, fallback=""):
    val = candidate if isinstance(candidate, str) and candidate.strip() else fallback
    val = val.strip()
    if not val.startswith("https://") and not val.startswith("http://"):
        return fallback or "https://example.com"
    return val[:2048]


def _normalize_location(primary, secondary=None):
    values = []
    for value in [primary, *(secondary or [])]:
        if isinstance(value, str) and value.strip():
            cleaned = " ".join(value.split())
            if cleaned and cleaned not in values:
                values.append(cleaned)
    return " · ".join(values)[:2000] if values else "Remote / Flexible"


def _normalize_work_mode(*values):
    text = " ".join(value for value in values if isinstance(value, str)).casefold()
    if "remote" in text:
        return "Remote"
    if "hybrid" in text:
        return "Hybrid"
    if "on-site" in text or "onsite" in text or "on site" in text:
        return "On-site"
    return "Not specified"


def _normalize_experience(*values):
    text = " ".join(value for value in values if isinstance(value, str)).casefold()
    if re.search(r"\b(intern|internship)\b", text):
        return "Intern"
    if re.search(r"\b(entry[- ]level|junior|graduate|new grad|associate)\b", text):
        return "Entry / Junior"
    if re.search(r"\b(principal|staff)\b", text):
        return "Staff / Principal"
    if re.search(r"\b(senior|sr\.?|lead)\b", text):
        return "Senior / Lead"
    if re.search(r"\b(manager|director|head)\b", text):
        return "Management"
    return "Not specified"


def extract_tech_tags(text):
    text = text or ""
    found = []
    for label, patterns in TECH_TAGS.items():
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            found.append(label)
    return sorted(found)


def classify_tech_job(title, description, department="", team=""):
    title_text = title or ""
    combined = " ".join(value or "" for value in [title, department, team, description])
    title_lower = title_text.casefold()
    tags = extract_tech_tags(combined)

    explicit_nontech = any(
        re.search(pattern, title_lower, flags=re.IGNORECASE)
        for pattern in NON_TECH_TITLE_PATTERNS
    )

    explicit_tech = any(
        re.search(pattern, title_lower, flags=re.IGNORECASE)
        for pattern in TECH_TITLE_PATTERNS
    )

    department_lower = " ".join([department or "", team or ""]).casefold()
    technical_department = any(
        term in department_lower
        for term in [
            "engineering", "software", "technology", "technical", "data",
            "machine learning", "artificial intelligence", "security", "infrastructure",
            "platform", "developer", "quality assurance", "qa",
        ]
    )

    is_tech = False if explicit_nontech else (explicit_tech or technical_department or len(tags) >= 2)
    workplace = _normalize_work_mode(title, description)
    experience = _normalize_experience(title, description)

    return {
        "is_tech": is_tech,
        "work_mode": workplace,
        "experience_level": experience,
        "tech_tags": tags,
    }


def _content_hash(job):
    content = f"{job.get('title')}:{job.get('employer')}:{job.get('provider_id')}:{job.get('description', '')[:500]}"
    return sha256(content.encode("utf-8")).hexdigest()


# In-memory source cache
_cache = {
    "sources": {},  # key -> {"data": [...], "timestamp": float}
}


# Curated offline fallback fixtures for testing or when live network is unavailable
OFFLINE_FIXTURES = {
    "greenhouse-canonical": [
        {
            "provider_id": "gh-can-01",
            "source_key": "greenhouse-canonical",
            "employer": "Canonical",
            "provider": "greenhouse",
            "title": "Software Engineer - Ubuntu Core",
            "location": "Remote - Worldwide",
            "work_mode": "Remote",
            "experience_level": "Entry / Junior",
            "description": "Develop and maintain Ubuntu Core Linux distribution packages. Requirements: Strong Python and C/C++ programming skills, Linux systems architecture, Git version control, and Docker containerization.",
            "tech_tags": ["Python", "Linux", "Git", "Docker"],
            "source_url": "https://job-boards.greenhouse.io/canonical",
            "provider_updated_at": "2026-10-01T10:00:00Z",
            "is_tech": True,
        },
        {
            "provider_id": "gh-can-02",
            "source_key": "greenhouse-canonical",
            "employer": "Canonical",
            "provider": "greenhouse",
            "title": "Cloud Solutions Architect - OpenStack",
            "location": "London, UK / Remote",
            "work_mode": "Hybrid",
            "experience_level": "Senior / Lead",
            "description": "Architect enterprise OpenStack and Kubernetes deployments. Requirements: Deep knowledge of Kubernetes, Docker, Python, Terraform, Linux, and Cloud Computing infrastructure.",
            "tech_tags": ["Kubernetes", "Docker", "Python", "Terraform", "Linux", "Cloud Computing"],
            "source_url": "https://job-boards.greenhouse.io/canonical",
            "provider_updated_at": "2026-10-02T12:00:00Z",
            "is_tech": True,
        },
    ],
    "ashby-notion": [
        {
            "provider_id": "ash-not-01",
            "source_key": "ashby-notion",
            "employer": "Notion",
            "provider": "ashby",
            "title": "Full Stack Engineer - Platform",
            "location": "San Francisco, CA / Remote",
            "work_mode": "Hybrid",
            "experience_level": "Senior / Lead",
            "description": "Build high-scale collaborative document editing infrastructure. Requirements: TypeScript, React, Node.js, PostgreSQL, SQL query optimization, and REST APIs.",
            "tech_tags": ["TypeScript", "React", "Node.js", "PostgreSQL", "SQL", "REST APIs"],
            "source_url": "https://jobs.ashbyhq.com/notion",
            "provider_updated_at": "2026-10-03T14:00:00Z",
            "is_tech": True,
        },
        {
            "provider_id": "ash-not-02",
            "source_key": "ashby-notion",
            "employer": "Notion",
            "provider": "ashby",
            "title": "Data Infrastructure Engineer",
            "location": "New York, NY / Remote",
            "work_mode": "Remote",
            "experience_level": "Entry / Junior",
            "description": "Maintain data lake pipelines and analytics query engines. Requirements: Python, SQL, PostgreSQL, Spark, Kafka, and AWS cloud services.",
            "tech_tags": ["Python", "SQL", "PostgreSQL", "Spark", "Kafka", "AWS"],
            "source_url": "https://jobs.ashbyhq.com/notion",
            "provider_updated_at": "2026-10-04T09:00:00Z",
            "is_tech": True,
        },
    ],
    "ashby-vercel": [
        {
            "provider_id": "ash-ver-01",
            "source_key": "ashby-vercel",
            "employer": "Vercel",
            "provider": "ashby",
            "title": "Frontend Infrastructure Engineer",
            "location": "Remote - Global",
            "work_mode": "Remote",
            "experience_level": "Entry / Junior",
            "description": "Enhance Next.js rendering pipeline and edge runtime. Requirements: Modern JavaScript, TypeScript, React, REST APIs, and Git version control.",
            "tech_tags": ["JavaScript", "TypeScript", "React", "REST APIs", "Git"],
            "source_url": "https://jobs.ashbyhq.com/vercel",
            "provider_updated_at": "2026-10-05T11:00:00Z",
            "is_tech": True,
        },
    ],
    "lever-dnb": [
        {
            "provider_id": "lev-dnb-01",
            "source_key": "lever-dnb",
            "employer": "Dun & Bradstreet",
            "provider": "lever",
            "title": "Machine Learning Engineer",
            "location": "Austin, TX / Hybrid",
            "work_mode": "Hybrid",
            "experience_level": "Senior / Lead",
            "description": "Develop financial risk scoring and predictive analytics models. Requirements: Python, Machine Learning, Pandas, NumPy, SQL, Docker, and AWS.",
            "tech_tags": ["Python", "Machine Learning", "Pandas", "NumPy", "SQL", "Docker", "AWS"],
            "source_url": "https://jobs.lever.co/dnb",
            "provider_updated_at": "2026-10-06T15:00:00Z",
            "is_tech": True,
        },
    ],
}


class LiveJobsService:
    """Service providing search, retrieval, and skill matching for live tech employer vacancies."""

    @staticmethod
    def get_source_registry():
        """Return the dictionary of configured public employer job sources."""
        return SOURCE_REGISTRY

    @classmethod
    def fetch_source(cls, source_key, force_refresh=False, offline_fallback=True):
        """Fetch and normalize jobs for a single source key with TTL caching and offline fallback."""
        if source_key not in SOURCE_REGISTRY:
            raise ValueError(f"Unknown live job source: {source_key}")

        now = time.time()
        cached = _cache["sources"].get(source_key)
        if not force_refresh and cached and (now - cached["timestamp"] < CACHE_TTL_SECONDS):
            return cached["data"]

        source_info = SOURCE_REGISTRY[source_key]
        provider = source_info["provider"]
        identifier = source_info["identifier"]
        jobs = []
        is_live = False
        error_msg = None

        try:
            if provider == "greenhouse":
                jobs = cls._fetch_greenhouse(source_key, identifier, source_info)
            elif provider == "ashby":
                jobs = cls._fetch_ashby(source_key, identifier, source_info)
            elif provider == "lever":
                jobs = cls._fetch_lever(source_key, identifier, source_info)
            is_live = True
        except Exception as exc:
            logger.warning("Live fetch failed for %s: %s", source_key, exc)
            error_msg = str(exc)
            if offline_fallback and source_key in OFFLINE_FIXTURES:
                jobs = [dict(j) for j in OFFLINE_FIXTURES[source_key]]
                for j in jobs:
                    j["content_hash"] = _content_hash(j)
                    j["retrieved_at"] = datetime.now(timezone.utc).isoformat()
                is_live = False
            else:
                jobs = []

        result = {
            "source_key": source_key,
            "provider": provider,
            "employer": source_info["label"],
            "source_url": source_info["board_url"],
            "available": is_live or bool(jobs),
            "is_live_network": is_live,
            "last_error": error_msg if not is_live else None,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "listed_count": len(jobs),
            "jobs": jobs,
        }

        _cache["sources"][source_key] = {"data": result, "timestamp": now}
        return result

    @classmethod
    def fetch_all_sources(cls, source_keys=None, force_refresh=False, offline_fallback=True):
        """Concurrently fetch all (or selected) sources."""
        keys = source_keys or list(SOURCE_REGISTRY.keys())
        results = {}

        with ThreadPoolExecutor(max_workers=min(6, len(keys))) as executor:
            future_to_key = {
                executor.submit(cls.fetch_source, key, force_refresh, offline_fallback): key
                for key in keys
            }
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as exc:
                    results[key] = {
                        "source_key": key,
                        "available": False,
                        "jobs": [],
                        "listed_count": 0,
                        "last_error": str(exc),
                    }
        return results

    @classmethod
    def search_jobs(
        cls,
        query="",
        location="",
        work_mode="",
        experience="",
        technology="",
        provider="",
        source_key="",
        page=1,
        page_size=10,
        offline_fallback=True,
    ):
        """Search and filter live vacancies across all configured sources."""
        requested_keys = [source_key] if source_key and source_key in SOURCE_REGISTRY else None
        source_results = cls.fetch_all_sources(requested_keys, offline_fallback=offline_fallback)

        all_jobs = []
        sources_summary = []

        for key, res in source_results.items():
            sources_summary.append({
                "source_key": key,
                "employer": res.get("employer", key),
                "provider": res.get("provider", "unknown"),
                "available": res.get("available", False),
                "is_live_network": res.get("is_live_network", False),
                "listed_count": res.get("listed_count", 0),
                "last_error": res.get("last_error"),
                "retrieved_at": res.get("retrieved_at"),
            })
            for j in res.get("jobs", []):
                all_jobs.append(j)

        # Filters
        filtered = cls._filter_job_list(
            all_jobs,
            query=query,
            location=location,
            work_mode=work_mode,
            experience=experience,
            technology=technology,
            provider=provider,
        )

        total = len(filtered)
        page = max(1, int(page))
        page_size = max(1, min(50, int(page_size)))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_jobs = filtered[start_idx:end_idx]

        return {
            "status": "success",
            "source": "live_multi_provider",
            "tech_only": True,
            "public_browsing": True,
            "jobs": paged_jobs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "sources": sorted(sources_summary, key=lambda s: s["employer"]),
        }

    @classmethod
    def get_job(cls, source_key, provider_id, offline_fallback=True):
        """Retrieve single job details by source key and provider ID."""
        source_res = cls.fetch_source(source_key, offline_fallback=offline_fallback)
        for j in source_res.get("jobs", []):
            if str(j.get("provider_id")) == str(provider_id):
                return {
                    "status": "success",
                    "job": j,
                    "source_info": {
                        "source_key": source_key,
                        "employer": source_res.get("employer"),
                        "provider": source_res.get("provider"),
                        "available": source_res.get("available"),
                        "retrieved_at": source_res.get("retrieved_at"),
                    },
                }
        return None

    @classmethod
    def match_job_to_skills(cls, job, user_skills):
        """Match a live vacancy against a candidate's skill set."""
        job_tags = job.get("tech_tags", [])
        job_desc = job.get("description", "")
        job_title = job.get("title", "")

        # Normalize candidate skills
        candidate_skill_names = {
            s.strip().casefold()
            for s in user_skills
            if isinstance(s, str) and s.strip()
        }

        # Determine target job skills from tags and description keywords
        target_skills = list(job_tags)
        for tag, patterns in TECH_TAGS.items():
            if tag not in target_skills:
                if any(re.search(p, job_title + " " + job_desc, re.I) for p in patterns):
                    target_skills.append(tag)

        target_skills = sorted(list(set(target_skills)))

        matched = []
        missing = []

        for skill in target_skills:
            skill_lower = skill.casefold()
            is_match = any(
                skill_lower == c or skill_lower in c or c in skill_lower
                for c in candidate_skill_names
            )
            if is_match:
                matched.append(skill)
            else:
                missing.append(skill)

        total_req = len(target_skills)
        match_score = round((len(matched) / max(total_req, 1)) * 100, 1) if total_req > 0 else 100.0

        recommendations = []
        if match_score >= 80:
            recommendations.append("High alignment with vacancy core technical stack. Ready to apply!")
        elif match_score >= 50:
            recommendations.append(f"Moderate alignment. Consider reinforcing: {', '.join(missing[:3])}.")
        else:
            recommendations.append(f"Key skill gaps detected: {', '.join(missing[:4])}. Study roadmap suggested before applying.")

        return {
            "status": "success",
            "job_id": job.get("provider_id"),
            "job_title": job_title,
            "employer": job.get("employer"),
            "match_score": match_score,
            "total_target_skills": total_req,
            "matched_skills": matched,
            "missing_skills": missing,
            "work_mode": job.get("work_mode"),
            "experience_level": job.get("experience_level"),
            "recommendations": recommendations,
        }

    # Internal Provider Connectors
    @classmethod
    def _fetch_greenhouse(cls, source_key, identifier, source_info):
        url = f"https://boards-api.greenhouse.io/v1/boards/{identifier}/jobs?content=true"
        payload = cls._http_get_json(url)
        raw_jobs = payload.get("jobs", []) if isinstance(payload, dict) else []

        normalized = []
        for job in raw_jobs:
            if not isinstance(job, dict) or not job.get("id"):
                continue
            if job.get("internal_job_id") is None:
                continue

            title = str(job.get("title") or "").strip()
            content = plain_description(job.get("content") or "")
            location_dict = job.get("location") if isinstance(job.get("location"), dict) else {}
            loc_name = str(location_dict.get("name") or "").strip()

            classification = classify_tech_job(title, content)
            if not classification["is_tech"]:
                continue

            rec = {
                "provider_id": str(job["id"]),
                "source_key": source_key,
                "employer": source_info["label"],
                "provider": "greenhouse",
                "title": title,
                "location": _normalize_location(loc_name),
                "work_mode": classification["work_mode"],
                "experience_level": classification["experience_level"],
                "description": content,
                "tech_tags": classification["tech_tags"],
                "source_url": _safe_source_url(job.get("absolute_url"), source_info["board_url"]),
                "provider_updated_at": job.get("updated_at"),
                "is_tech": True,
            }
            rec["content_hash"] = _content_hash(rec)
            rec["retrieved_at"] = datetime.now(timezone.utc).isoformat()
            normalized.append(rec)

        return normalized

    @classmethod
    def _fetch_ashby(cls, source_key, identifier, source_info):
        url = f"https://api.ashbyhq.com/posting-api/job-board/{identifier}?includeCompensation=false"
        payload = cls._http_get_json(url)
        raw_jobs = payload.get("jobs", []) if isinstance(payload, dict) else []

        normalized = []
        for job in raw_jobs:
            if not isinstance(job, dict) or job.get("isListed") is False:
                continue

            provider_id = str(job.get("jobId") or job.get("id") or job.get("jobPostingId") or "")
            if not provider_id:
                continue

            title = str(job.get("title") or "").strip()
            desc_raw = job.get("descriptionHtml") or job.get("descriptionPlain") or ""
            content = plain_description(desc_raw)
            loc_name = str(job.get("location") or "")

            classification = classify_tech_job(title, content)
            if not classification["is_tech"]:
                continue

            rec = {
                "provider_id": provider_id,
                "source_key": source_key,
                "employer": source_info["label"],
                "provider": "ashby",
                "title": title,
                "location": _normalize_location(loc_name),
                "work_mode": classification["work_mode"],
                "experience_level": classification["experience_level"],
                "description": content,
                "tech_tags": classification["tech_tags"],
                "source_url": _safe_source_url(job.get("jobUrl") or job.get("applyUrl"), source_info["board_url"]),
                "provider_updated_at": job.get("publishedAt"),
                "is_tech": True,
            }
            rec["content_hash"] = _content_hash(rec)
            rec["retrieved_at"] = datetime.now(timezone.utc).isoformat()
            normalized.append(rec)

        return normalized

    @classmethod
    def _fetch_lever(cls, source_key, identifier, source_info):
        url = f"https://api.lever.co/v0/postings/{identifier}?mode=xml"
        raw_text = cls._http_get_text(url)
        root = ET.fromstring(raw_text)

        normalized = []
        for posting in root.findall(".//posting"):
            title_node = posting.find("text")
            title = title_node.text.strip() if title_node is not None and title_node.text else ""
            desc_node = posting.find("description")
            desc_raw = desc_node.text.strip() if desc_node is not None and desc_node.text else ""
            content = plain_description(desc_raw)

            id_node = posting.find("id")
            provider_id = id_node.text.strip() if id_node is not None and id_node.text else ""
            if not provider_id:
                continue

            categories = posting.find("categories") or {}
            loc = categories.find("location").text if categories.find("location") is not None else ""

            classification = classify_tech_job(title, content)
            if not classification["is_tech"]:
                continue

            url_node = posting.find("hostedUrl")
            post_url = url_node.text.strip() if url_node is not None and url_node.text else source_info["board_url"]

            rec = {
                "provider_id": provider_id,
                "source_key": source_key,
                "employer": source_info["label"],
                "provider": "lever",
                "title": title,
                "location": _normalize_location(loc),
                "work_mode": classification["work_mode"],
                "experience_level": classification["experience_level"],
                "description": content,
                "tech_tags": classification["tech_tags"],
                "source_url": _safe_source_url(post_url, source_info["board_url"]),
                "provider_updated_at": None,
                "is_tech": True,
            }
            rec["content_hash"] = _content_hash(rec)
            rec["retrieved_at"] = datetime.now(timezone.utc).isoformat()
            normalized.append(rec)

        return normalized

    @classmethod
    def _http_get_json(cls, url):
        req = Request(url, headers={"User-Agent": "AI-Career-Navigator/1.0", "Accept": "application/json"})
        with build_opener(NoRedirect()).open(req, timeout=REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                raise FeedUnavailable(f"Provider returned status {resp.status}")
            data = resp.read(MAX_BYTES)
            return json.loads(data.decode("utf-8"))

    @classmethod
    def _http_get_text(cls, url):
        req = Request(url, headers={"User-Agent": "AI-Career-Navigator/1.0", "Accept": "application/xml, text/xml"})
        with build_opener(NoRedirect()).open(req, timeout=REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                raise FeedUnavailable(f"Provider returned status {resp.status}")
            data = resp.read(MAX_BYTES)
            return data.decode("utf-8")

    @classmethod
    def _filter_job_list(cls, jobs, query="", location="", work_mode="", experience="", technology="", provider=""):
        q = query.casefold().strip()
        loc = location.casefold().strip()
        wm = work_mode.casefold().strip()
        exp = experience.casefold().strip()
        tech = technology.casefold().strip()
        prov = provider.casefold().strip()

        filtered = []
        for j in jobs:
            if q and not (
                q in j.get("title", "").casefold()
                or q in j.get("employer", "").casefold()
                or q in j.get("description", "").casefold()
            ):
                continue
            if loc and loc not in j.get("location", "").casefold():
                continue
            if wm and wm != "all" and wm not in j.get("work_mode", "").casefold():
                continue
            if exp and exp != "all" and exp not in j.get("experience_level", "").casefold():
                continue
            if tech and not any(tech in tag.casefold() for tag in j.get("tech_tags", [])):
                continue
            if prov and prov not in j.get("provider", "").casefold() and prov not in j.get("source_key", "").casefold():
                continue
            filtered.append(j)

        return filtered
