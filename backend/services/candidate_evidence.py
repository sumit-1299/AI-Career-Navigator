"""Validate submissions without fetching URLs or certifying their claims."""

from datetime import date, datetime, timezone
import ipaddress
import re
from urllib.parse import urlsplit
from uuid import UUID


COMMON_FIELDS = {"kind", "title", "description", "source_url", "skills"}
KIND_FIELDS = {"project": {"contribution"}, "certification": {"issuer", "issued_on"}}


def text_field(value, label, maximum):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise ValueError(f"{label} must contain 1 to {maximum} characters.")
    value = value.strip()
    if any(ord(character) < 32 and character not in "\n\r\t" for character in value):
        raise ValueError(f"{label} contains unsupported control characters.")
    return value


def source_url(value):
    value = text_field(value, "Source link", 2048)
    if any(character.isspace() or ord(character) < 32 for character in value) or "\\" in value:
        raise ValueError("Source link cannot contain spaces, control characters or backslashes.")
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").encode("idna").decode("ascii").lower()
        port = parsed.port
    except (ValueError, UnicodeError):
        raise ValueError("Enter a valid HTTPS source link.") from None
    if parsed.scheme != "https" or not host or parsed.username is not None or parsed.password is not None or port not in (None, 443):
        raise ValueError("Use an HTTPS link without a username, password or custom port.")
    # A syntactic restriction, not a DNS/public-access or ownership verification.
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("Use a public website domain, not an IP address.")
    labels = host.split(".")
    if (len(host) > 253 or len(labels) < 2 or
            not re.fullmatch(r"[a-z]{2,63}|xn--[a-z0-9-]{2,59}", labels[-1]) or
            any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels) or
            labels[-1] in {"localhost", "local", "internal", "invalid", "test", "example", "onion"}):
        raise ValueError("Use a public website domain for the source link.")
    return value


def submission_id(value):
    try:
        parsed = UUID(value) if isinstance(value, str) else None
    except ValueError:
        parsed = None
    if parsed is None or parsed.version != 4 or str(parsed) != value:
        raise ValueError("submission_id must be a canonical UUID v4.")
    return value


def validate_details(body, extra_field):
    if not isinstance(body, dict):
        raise ValueError("Send a JSON object containing the evidence fields.")
    kind = body.get("kind")
    if not isinstance(kind, str) or kind not in KIND_FIELDS:
        raise ValueError("Evidence kind must be project or certification.")
    expected = COMMON_FIELDS | KIND_FIELDS[kind] | {extra_field}
    if set(body) != expected:
        raise ValueError("Send only the required fields for this evidence type.")
    skills = body["skills"]
    if not isinstance(skills, list) or not 1 <= len(skills) <= 10:
        raise ValueError("Add 1 to 10 skill names.")
    normalized = []
    seen = set()
    for value in skills:
        skill = " ".join(text_field(value, "Skill name", 40).split())
        if skill.casefold() not in seen:
            normalized.append(skill)
            seen.add(skill.casefold())
    result = {
        "kind": kind,
        "title": text_field(body["title"], "Title", 160),
        "description": text_field(body["description"], "Description", 2000),
        "source_url": source_url(body["source_url"]),
        "skills": normalized,
    }
    if kind == "project":
        result["contribution"] = text_field(body["contribution"], "Your contribution", 2000)
    else:
        result["issuer"] = text_field(body["issuer"], "Issuer", 160)
        value = body["issued_on"]
        try:
            issued = date.fromisoformat(value) if isinstance(value, str) else None
        except ValueError:
            issued = None
        if issued is None or issued.isoformat() != value or issued > datetime.now(timezone.utc).date():
            raise ValueError("Issue date must be a real date in YYYY-MM-DD format, today or earlier.")
        result["issued_on"] = value
    return result


def valid_version(value):
    return type(value) is int and 1 <= value <= 2147483646
