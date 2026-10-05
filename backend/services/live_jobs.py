"""Bounded, read-only Greenhouse connector for selected employer boards."""

from datetime import datetime
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
import re
import time
from urllib.request import HTTPRedirectHandler, Request, build_opener

from services.candidate_evidence import source_url


BOARDS = {
    "canonical": "Canonical",
    "razorpaysoftwareprivatelimited": "Razorpay",
}

MAX_BYTES = 15 * 1024 * 1024
MAX_DESCRIPTION = 60000


class FeedUnavailable(Exception):
    """Raised when a live employer feed cannot be trusted."""


class PlainDescription(HTMLParser):
    """Convert provider HTML into safe plain text."""

    breaks = {
        "p",
        "div",
        "li",
        "ul",
        "ol",
        "br",
        "h1",
        "h2",
        "h3",
        "h4",
        "section",
        "tr",
    }

    blocked = {
        "script",
        "style",
        "iframe",
        "object",
        "template",
    }

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
    """Reject unexpected provider redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FeedUnavailable(
            "The employer board redirected the live request."
        )


def plain_description(content):
    if not isinstance(content, str) or len(content) > 250000:
        raise FeedUnavailable(
            "Unexpected job description format."
        )

    parser = PlainDescription()

    try:
        parser.feed(
            unescape(
                unescape(content)
            )
        )
        parser.close()
    except Exception as exc:
        raise FeedUnavailable(
            "The employer returned an unreadable job description."
        ) from exc

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in "".join(parser.parts).splitlines()
    ]

    text = "\n".join(
        line for line in lines if line
    )

    if not text or len(text) > MAX_DESCRIPTION:
        raise FeedUnavailable(
            "A job description was empty or too large."
        )

    return text


def fetch_board(board):
    """
    Fetch one employer board directly from Greenhouse.

    No database reads or writes occur here.
    """

    if board not in BOARDS:
        raise ValueError("Unknown employer board.")

    url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        f"{board}/jobs?content=true"
    )

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AI-Career-Navigator-Research/1.0",
        },
    )

    try:
        start = time.monotonic()

        with build_opener(NoRedirect()).open(
            request,
            timeout=8,
        ) as response:
            if response.status != 200:
                raise FeedUnavailable(
                    "Unexpected employer provider response."
                )

            chunks = []
            size = 0

            while True:
                chunk = response.read(65536)

                if not chunk:
                    break

                size += len(chunk)

                if (
                    size > MAX_BYTES
                    or time.monotonic() - start > 12
                ):
                    raise FeedUnavailable(
                        "The provider response exceeded the download limit."
                    )

                chunks.append(chunk)

        return json.loads(
            b"".join(chunks)
        )

    except FeedUnavailable:
        raise

    except Exception as exc:
        raise FeedUnavailable(
            "The employer board could not be reached."
        ) from exc


def normalize_feed(payload):
    """
    Validate and normalize a complete Greenhouse response.

    No listing is persisted here.
    """

    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("jobs"), list)
    ):
        raise FeedUnavailable(
            "Unexpected employer provider response."
        )

    jobs = payload["jobs"]
    meta = payload.get("meta")

    if (
        not isinstance(meta, dict)
        or type(meta.get("total")) is not int
        or meta["total"] != len(jobs)
        or len(jobs) > 5000
    ):
        raise FeedUnavailable(
            "The provider response was incomplete."
        )

    normalized = []
    seen = set()
    prospects = 0

    try:
        for job in jobs:
            if (
                not isinstance(job, dict)
                or type(job.get("id")) is not int
                or job["id"] <= 0
                or job["id"] in seen
            ):
                raise ValueError(
                    "Invalid or duplicate posting identifier."
                )

            seen.add(job["id"])

            if "internal_job_id" not in job:
                raise ValueError(
                    "Missing job identifier."
                )

            if job["internal_job_id"] is None:
                prospects += 1
                continue

            title = job.get("title")

            location_data = job.get(
                "location",
                {},
            )

            location = (
                location_data.get("name", "")
                if isinstance(location_data, dict)
                else ""
            )

            if (
                not isinstance(title, str)
                or not title.strip()
                or len(title) > 500
            ):
                raise ValueError(
                    "Invalid title."
                )

            if (
                not isinstance(location, str)
                or len(location) > 1000
            ):
                raise ValueError(
                    "Invalid location."
                )

            updated = job.get("updated_at")

            if updated is not None:
                if (
                    not isinstance(updated, str)
                    or len(updated) > 60
                ):
                    raise ValueError(
                        "Invalid update date."
                    )

                parsed = datetime.fromisoformat(
                    updated.replace("Z", "+00:00")
                )

                if parsed.tzinfo is None:
                    raise ValueError(
                        "Missing update timezone."
                    )

            absolute_url = job.get(
                "absolute_url"
            )

            normalized_job = {
                "provider_id": str(job["id"]),
                "title": title.strip(),
                "location": location.strip(),
                "description": plain_description(
                    job.get("content")
                ),
                "source_url": source_url(
                    absolute_url
                ),
                "provider_updated_at": updated,
            }

            normalized_job["content_hash"] = sha256(
                json.dumps(
                    normalized_job,
                    sort_keys=True,
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest()

            normalized.append(
                normalized_job
            )

    except (
        ValueError,
        TypeError,
        AttributeError,
    ) as exc:
        raise FeedUnavailable(
            "The provider returned a malformed listing."
        ) from exc

    return normalized, prospects