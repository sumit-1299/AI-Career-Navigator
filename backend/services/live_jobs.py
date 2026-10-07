"""Read-only live job connectors for public employer job-board feeds.

Supported public sources:
- Greenhouse Job Board API
- Ashby Public Job Postings API
- Lever public XML postings feed

The connector layer never writes live vacancies to the database. Saved job
comparisons remain immutable snapshots handled by the route layer.
"""

from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
import re
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

from services.candidate_evidence import source_url


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
    # Ashby public job boards.
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
    # Lever public feeds.
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

# Compatibility aliases for earlier Greenhouse-only code/tests.
BOARDS = {
    "canonical": "Canonical",
    "razorpaysoftwareprivatelimited": "Razorpay",
}

MAX_BYTES = 15 * 1024 * 1024
MAX_DESCRIPTION = 60000
MAX_JOBS = 5000
REQUEST_TIMEOUT = 10
MAX_REQUEST_SECONDS = 14


class FeedUnavailable(Exception):
    """Raised when a live employer feed cannot be trusted."""


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


def _safe_source_url(value, fallback):
    candidate = value if isinstance(value, str) and value.strip() else fallback
    try:
        return source_url(candidate)
    except ValueError as exc:
        raise FeedUnavailable("The provider returned an invalid public job URL.") from exc


def plain_description(content):
    """Convert trusted provider HTML/plain text to normalized text."""
    if not isinstance(content, str) or len(content) > 250000:
        raise FeedUnavailable("Unexpected job description format.")

    parser = PlainDescription()
    try:
        parser.feed(unescape(unescape(content)))
        parser.close()
    except Exception as exc:
        raise FeedUnavailable("The employer returned an unreadable job description.") from exc

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in "".join(parser.parts).splitlines()
    ]
    text = "\n".join(line for line in lines if line)

    if not text:
        raise FeedUnavailable("A job description was empty.")
    if len(text) > MAX_DESCRIPTION:
        raise FeedUnavailable("A job description was too large.")
    return text


def _fetch_bytes(url, *, accept, user_agent):
    request = Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": user_agent,
        },
    )

    try:
        start = time.monotonic()
        with build_opener(NoRedirect()).open(request, timeout=REQUEST_TIMEOUT) as response:
            if response.status != 200:
                raise FeedUnavailable("Unexpected employer provider response.")

            chunks = []
            size = 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES or time.monotonic() - start > MAX_REQUEST_SECONDS:
                    raise FeedUnavailable("The provider response exceeded the download limit.")
                chunks.append(chunk)
            return b"".join(chunks)
    except FeedUnavailable:
        raise
    except Exception as exc:
        raise FeedUnavailable("The employer provider could not be reached.") from exc


def _fetch_json(url):
    payload = _fetch_bytes(
        url,
        accept="application/json",
        user_agent="AI-Career-Navigator-Research/1.0",
    )
    try:
        return json.loads(payload)
    except Exception as exc:
        raise FeedUnavailable("The employer provider returned invalid JSON.") from exc


def _fetch_text(url):
    payload = _fetch_bytes(
        url,
        accept="application/xml,text/xml;q=0.9,text/plain;q=0.8,*/*;q=0.5",
        user_agent="AI-Career-Navigator-Research/1.0",
    )
    try:
        return payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise FeedUnavailable("The employer feed was not valid UTF-8.") from exc


def _validate_identifier(identifier):
    if not isinstance(identifier, str) or not identifier.strip() or len(identifier) > 300:
        raise FeedUnavailable("Provider posting identifier is invalid.")
    return identifier.strip()


def _content_hash(job):
    return sha256(
        json.dumps(job, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _normalize_location(primary, secondary=None):
    values = []
    for value in [primary, *(secondary or [])]:
        if isinstance(value, str) and value.strip():
            cleaned = " ".join(value.split())
            if cleaned and cleaned not in values:
                values.append(cleaned)
    return " · ".join(values)[:2000]


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


TECH_TAGS = {
    "Python": [r"\bpython\b"],
    "Java": [r"\bjava\b(?!script)"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript": [r"\btypescript\b", r"\bts\b"],
    "SQL": [r"\bsql\b"],
    "PostgreSQL": [r"\bpostgres(?:ql)?\b"],
    "MySQL": [r"\bmysql\b"],
    "REST APIs": [r"\brest(?:ful)?\s+(?:api|apis)\b", r"\bhttp(?:s)?\s+api\b"],
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
    "Data": [r"\bdata engineer\b", r"\bdata scientist\b", r"\bdata analyst\b", r"\banalytics engineer\b"],
    "DevOps": [r"\bdevops\b", r"\bdevsecops\b", r"\bsre\b", r"\bsite reliability\b"],
    "Cloud": [r"\bcloud engineer\b", r"\bcloud architect\b"],
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


def extract_tech_tags(text):
    text = text or ""
    found = []
    for label, patterns in TECH_TAGS.items():
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            found.append(label)
    return found


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

    # Strict tech-only policy: explicit non-tech title always wins.
    is_tech = False if explicit_nontech else (explicit_tech or technical_department or len(tags) >= 2)

    workplace = _normalize_work_mode(title, description)
    experience = _normalize_experience(title, description)

    return {
        "is_tech": is_tech,
        "work_mode": workplace,
        "experience_level": experience,
        "tech_tags": tags,
    }


def _finalize_job(record):
    required = {
        "provider_id", "title", "location", "description", "source_url",
        "provider_updated_at", "department", "team", "work_mode", "experience_level",
    }
    if not required.issubset(record):
        raise FeedUnavailable("Provider returned an incomplete job record.")

    if not isinstance(record["title"], str) or not record["title"].strip() or len(record["title"]) > 500:
        raise FeedUnavailable("Invalid job title.")
    if not isinstance(record["location"], str) or len(record["location"]) > 2000:
        raise FeedUnavailable("Invalid job location.")

    record["provider_id"] = _validate_identifier(record["provider_id"])
    record["title"] = record["title"].strip()
    record["location"] = record["location"].strip()
    record["description"] = plain_description(record["description"])
    record["source_url"] = _safe_source_url(record["source_url"], record["source_url"])
    record["department"] = str(record.get("department") or "").strip()[:300]
    record["team"] = str(record.get("team") or "").strip()[:300]

    classification = classify_tech_job(
        record["title"], record["description"], record["department"], record["team"]
    )
    record.update(classification)

    # Keep remote mode hints supplied by the provider when available.
    provider_mode = record.get("provider_work_mode")
    if provider_mode:
        record["work_mode"] = provider_mode

    record["content_hash"] = _content_hash(
        {
            key: record[key]
            for key in [
                "provider_id", "title", "location", "description", "department",
                "team", "work_mode", "experience_level", "source_url",
            ]
        }
    )
    return record


def _fetch_greenhouse(identifier):
    url = f"https://boards-api.greenhouse.io/v1/boards/{identifier}/jobs?content=true"
    payload = _fetch_json(url)

    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise FeedUnavailable("Unexpected Greenhouse provider response.")

    jobs = payload["jobs"]
    meta = payload.get("meta")
    if not isinstance(meta, dict) or type(meta.get("total")) is not int or meta["total"] != len(jobs):
        raise FeedUnavailable("The Greenhouse provider response was incomplete.")
    if len(jobs) > MAX_JOBS:
        raise FeedUnavailable("The Greenhouse provider returned too many postings.")

    normalized = []
    seen = set()
    for job in jobs:
        if not isinstance(job, dict) or type(job.get("id")) is not int or job["id"] <= 0:
            raise FeedUnavailable("Greenhouse returned an invalid posting identifier.")
        if job["id"] in seen:
            raise FeedUnavailable("Greenhouse returned duplicate posting identifiers.")
        seen.add(job["id"])

        location_data = job.get("location") if isinstance(job.get("location"), dict) else {}
        normalized.append(
            _finalize_job(
                {
                    "provider_id": str(job["id"]),
                    "title": job.get("title"),
                    "location": location_data.get("name", ""),
                    "description": job.get("content", ""),
                    "source_url": job.get("absolute_url"),
                    "provider_updated_at": job.get("updated_at"),
                    "department": " ".join(
                        item.get("name", "")
                        for item in (job.get("departments") or [])
                        if isinstance(item, dict)
                    ),
                    "team": " ".join(
                        item.get("name", "")
                        for item in (job.get("offices") or [])
                        if isinstance(item, dict)
                    ),
                    "work_mode": _normalize_work_mode(
                        job.get("title"), location_data.get("name", ""), job.get("content", "")
                    ),
                    "experience_level": _normalize_experience(job.get("title"), job.get("content", "")),
                }
            )
        )

    return normalized


def _ashby_posting_id(job):
    for key in ("jobId", "id", "jobPostingId"):
        value = job.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    job_url = job.get("jobUrl") or job.get("applyUrl")
    if isinstance(job_url, str):
        path = urlsplit(job_url).path.rstrip("/")
        if path:
            candidate = path.split("/")[-1]
            if candidate:
                return candidate
    raise FeedUnavailable("Ashby returned a posting without a stable public identifier.")


def _fetch_ashby(identifier):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{identifier}?includeCompensation=false"
    payload = _fetch_json(url)
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise FeedUnavailable("Unexpected Ashby provider response.")

    normalized = []
    seen = set()
    for job in payload["jobs"]:
        if not isinstance(job, dict):
            raise FeedUnavailable("Ashby returned an invalid job record.")
        if job.get("isListed") is False:
            continue

        provider_id = _ashby_posting_id(job)
        if provider_id in seen:
            raise FeedUnavailable("Ashby returned duplicate posting identifiers.")
        seen.add(provider_id)

        secondary = [
            item.get("location", "")
            for item in (job.get("secondaryLocations") or [])
            if isinstance(item, dict)
        ]

        postal = ((job.get("address") or {}).get("postalAddress") or {})
        address_parts = [postal.get("addressLocality"), postal.get("addressRegion"), postal.get("addressCountry")]
        primary_location = job.get("location") or ", ".join(part for part in address_parts if part)
        workplace = job.get("workplaceType") or _normalize_work_mode(job.get("location"), job.get("descriptionPlain", ""))

        normalized.append(
            _finalize_job(
                {
                    "provider_id": provider_id,
                    "title": job.get("title"),
                    "location": _normalize_location(primary_location, secondary),
                    "description": job.get("descriptionHtml") or job.get("descriptionPlain") or "",
                    "source_url": job.get("jobUrl") or job.get("applyUrl"),
                    "provider_updated_at": job.get("publishedAt"),
                    "department": job.get("department", ""),
                    "team": job.get("team", ""),
                    "work_mode": _normalize_work_mode(
                        workplace, "remote" if job.get("isRemote") else ""
                    ),
                    "provider_work_mode": workplace.title() if isinstance(workplace, str) else None,
                    "experience_level": _normalize_experience(job.get("title"), job.get("descriptionPlain", "")),
                }
            )
        )

    return normalized


def _xml_text(element, tag):
    child = element.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text


def _fetch_lever(identifier):
    # Lever documents a public XML feed for job boards. This avoids requiring
    # private API credentials while keeping the integration read-only.
    url = f"https://api.lever.co/v0/postings/{identifier}?mode=xml"
    raw = _fetch_text(url)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise FeedUnavailable("The Lever provider returned invalid XML.") from exc

    normalized = []
    seen = set()
    for job in root.findall(".//job"):
        provider_id = _xml_text(job, "id").strip()
        if not provider_id or provider_id in seen:
            raise FeedUnavailable("Lever returned an invalid or duplicate posting identifier.")
        seen.add(provider_id)

        title = _xml_text(job, "position")
        description = _xml_text(job, "description")
        location = _xml_text(job, "location")
        category = _xml_text(job, "category")
        commitment = _xml_text(job, "commitment")
        apply_url = _xml_text(job, "apply_url")
        post_date = _xml_text(job, "post_date")

        updated = None
        if post_date.isdigit():
            try:
                updated = datetime.fromtimestamp(int(post_date) / 1000, tz=timezone.utc).isoformat()
            except (ValueError, OverflowError, OSError):
                updated = None

        source = apply_url or f"https://jobs.lever.co/{identifier}/{provider_id}"
        normalized.append(
            _finalize_job(
                {
                    "provider_id": provider_id,
                    "title": title,
                    "location": location,
                    "description": description,
                    "source_url": source,
                    "provider_updated_at": updated,
                    "department": category,
                    "team": category,
                    "work_mode": _normalize_work_mode(location, description),
                    "experience_level": _normalize_experience(title, description),
                }
            )
        )

    if len(normalized) > MAX_JOBS:
        raise FeedUnavailable("The Lever provider returned too many postings.")
    return normalized


def fetch_source(source_key):
    """Fetch one configured source and return only normalized public jobs."""
    source = SOURCE_REGISTRY.get(source_key)
    if not source:
        raise ValueError("Unknown live job source.")

    provider = source["provider"]
    identifier = source["identifier"]

    if provider == "greenhouse":
        jobs = _fetch_greenhouse(identifier)
    elif provider == "ashby":
        jobs = _fetch_ashby(identifier)
    elif provider == "lever":
        jobs = _fetch_lever(identifier)
    else:
        raise FeedUnavailable("Unsupported live job provider.")

    return {
        "source_key": source_key,
        "provider": provider,
        "employer": source["label"],
        "source_url": source["board_url"],
        "jobs": jobs,
    }


def source_summary(source_key):
    source = SOURCE_REGISTRY[source_key]
    return {
        "source_key": source_key,
        "provider": source["provider"],
        "employer": source["label"],
        "source_url": source["board_url"],
    }


def normalize_feed(payload):
    """Backward-compatible Greenhouse normalization helper used by tests."""
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise FeedUnavailable("Unexpected employer provider response.")

    jobs = payload["jobs"]
    meta = payload.get("meta")
    if (
        not isinstance(meta, dict)
        or type(meta.get("total")) is not int
        or meta["total"] != len(jobs)
        or len(jobs) > MAX_JOBS
    ):
        raise FeedUnavailable("The provider response was incomplete.")

    normalized = []
    prospects = 0
    seen = set()
    for job in jobs:
        if not isinstance(job, dict) or type(job.get("id")) is not int or job["id"] <= 0:
            raise FeedUnavailable("Invalid Greenhouse posting identifier.")
        if job["id"] in seen:
            raise FeedUnavailable("Duplicate Greenhouse posting identifier.")
        seen.add(job["id"])
        if "internal_job_id" not in job:
            raise FeedUnavailable("Missing Greenhouse job identifier.")
        if job["internal_job_id"] is None:
            prospects += 1
            continue

        location_data = job.get("location") if isinstance(job.get("location"), dict) else {}
        normalized.append(
            {
                "provider_id": str(job["id"]),
                "title": str(job.get("title") or "").strip(),
                "location": str(location_data.get("name") or "").strip(),
                "description": plain_description(job.get("content") or ""),
                "source_url": _safe_source_url(job.get("absolute_url"), job.get("absolute_url")),
                "provider_updated_at": job.get("updated_at"),
            }
        )

    for job in normalized:
        job["content_hash"] = _content_hash(job)
    return normalized, prospects


# Backwards-compatible helper used by the older Greenhouse route/tests.
def fetch_board(board):
    if board not in BOARDS:
        raise ValueError("Unknown employer board.")
    source_key = next(
        key for key, source in SOURCE_REGISTRY.items()
        if source["provider"] == "greenhouse" and source["identifier"] == board
    )
    raw = _fetch_json(
        f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    )
    return raw
