"""A bounded, read-only Greenhouse connector for explicitly selected employer boards."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
import re
from threading import Lock
import time
from urllib.request import HTTPRedirectHandler, Request, build_opener

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from extensions import db
from models.assessment_attempt import iso_utc, utc_now
from models.live_job import JobBoardSync, LiveJob
from services.candidate_evidence import source_url

# Server-controlled tokens only; no arbitrary URLs are accepted from a browser.
BOARDS = {"canonical": "Canonical", "razorpaysoftwareprivatelimited": "Razorpay"}
REFRESH_SECONDS = 300
STALE_SECONDS = 86400
MAX_BYTES = 15 * 1024 * 1024
MAX_DESCRIPTION = 60000
BOARD_LOCKS = {board: Lock() for board in BOARDS}


class FeedUnavailable(Exception):
    pass


class RefreshBusy(Exception):
    pass


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def is_stale(value):
    return value is None or (utc_now() - aware(value)).total_seconds() >= STALE_SECONDS


def sync_status(board, row):
    next_refresh = aware(row.last_attempt_at) + timedelta(seconds=REFRESH_SECONDS) if row and row.last_attempt_at else None
    return {"board": board, "employer": BOARDS[board],
            "source_url": f"https://job-boards.greenhouse.io/{board}",
            "last_attempt_at": iso_utc(row.last_attempt_at) if row else None,
            "last_success_at": iso_utc(row.last_success_at) if row else None,
            "last_error": row.last_error if row else None,
            "listed_count": row.listed_count if row else 0,
            "prospect_count": row.prospect_count if row else 0,
            "stale": is_stale(row.last_success_at if row else None),
            "next_refresh_at": iso_utc(next_refresh),
            "can_refresh": next_refresh is None or utc_now() >= next_refresh}


class PlainDescription(HTMLParser):
    """Extract text and paragraph boundaries; never render upstream markup."""
    breaks = {"p", "div", "li", "ul", "ol", "br", "h1", "h2", "h3", "h4", "section", "tr"}
    blocked = {"script", "style", "iframe", "object", "template"}

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


def plain_description(content):
    if not isinstance(content, str) or len(content) > 250000:
        raise FeedUnavailable("Unexpected job description format.")
    # The API can return entity-encoded HTML. Decode before extracting plain text.
    parser = PlainDescription()
    parser.feed(unescape(unescape(content)))
    parser.close()
    lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(parser.parts).splitlines()]
    text = "\n".join(line for line in lines if line)
    if not text or len(text) > MAX_DESCRIPTION:
        raise FeedUnavailable("A job description was empty or too large.")
    return text


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FeedUnavailable("The provider redirected the board request.")


def fetch_board(board):
    if board not in BOARDS:
        raise ValueError("Unknown employer board.")
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "AI-Career-Navigator-Research/1.0"})
    try:
        start = time.monotonic()
        with build_opener(NoRedirect()).open(request, timeout=8) as response:
            if response.status != 200:
                raise FeedUnavailable("Unexpected provider response.")
            chunks, size = [], 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES or time.monotonic() - start > 12:
                    raise FeedUnavailable("Provider response exceeded the download limit.")
                chunks.append(chunk)
        return json.loads(b"".join(chunks))
    except Exception as exc:
        raise FeedUnavailable("The employer board could not be refreshed. Previously saved listings are retained.") from exc


def normalize_feed(payload):
    """Validate the complete response before changing any listing status."""
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise FeedUnavailable("Unexpected provider response.")
    jobs = payload["jobs"]
    meta = payload.get("meta")
    if (not isinstance(meta, dict) or type(meta.get("total")) is not int
            or meta["total"] != len(jobs) or len(jobs) > 5000):
        raise FeedUnavailable("The provider response was incomplete.")
    normalized, seen, prospects = [], set(), 0
    try:
        for job in jobs:
            if not isinstance(job, dict) or type(job.get("id")) is not int or job["id"] <= 0 or job["id"] in seen:
                raise ValueError("Invalid or duplicate posting identifier.")
            seen.add(job["id"])
            if "internal_job_id" not in job:
                raise ValueError("Missing job identifier.")
            if job["internal_job_id"] is None:
                prospects += 1
                continue
            title = job.get("title")
            location = job.get("location", {}).get("name", "")
            if not isinstance(title, str) or not title.strip() or len(title) > 500:
                raise ValueError("Invalid title.")
            if not isinstance(location, str) or len(location) > 1000:
                raise ValueError("Invalid location.")
            updated = job.get("updated_at")
            if updated is not None:
                if not isinstance(updated, str) or len(updated) > 60:
                    raise ValueError("Invalid update date.")
                if datetime.fromisoformat(updated.replace("Z", "+00:00")).tzinfo is None:
                    raise ValueError("Missing update timezone.")
            item = {"provider_id": str(job["id"]), "title": title.strip(), "location": location.strip(),
                    "description": plain_description(job.get("content")),
                    "source_url": source_url(job.get("absolute_url")), "provider_updated_at": updated}
            item["content_hash"] = sha256(json.dumps(item, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            normalized.append(item)
    except (ValueError, TypeError, AttributeError) as exc:
        raise FeedUnavailable("The provider returned a malformed listing; the previous cache is retained.") from exc
    return normalized, prospects


def refresh_board(board):
    """Atomic per-board updates. A failed fetch never removes cached vacancies."""
    lock = BOARD_LOCKS[board]
    if not lock.acquire(blocking=False):
        raise RefreshBusy("This board is already refreshing. Try again shortly.")
    try:
        # The PK handles first-use races; the row lock serializes workers on PostgreSQL.
        if db.session.get(JobBoardSync, board) is None:
            try:
                db.session.add(JobBoardSync(board=board))
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
        sync = db.session.execute(select(JobBoardSync).where(JobBoardSync.board == board).with_for_update()
                                  .execution_options(populate_existing=True)).scalar_one()
        if not sync_status(board, sync)["can_refresh"]:
            db.session.rollback()
            return {"outcome": "cooldown", "board": sync_status(board, sync)}
        sync.last_attempt_at = utc_now()
        try:
            jobs, prospects = normalize_feed(fetch_board(board))
        except FeedUnavailable as exc:
            sync.last_error = str(exc)
            db.session.commit()
            return {"outcome": "failed", "board": sync_status(board, sync)}
        now = utc_now()
        cached = {item.provider_id: item for item in db.session.execute(
            select(LiveJob).where(LiveJob.board == board)).scalars()}
        present = set()
        for item in jobs:
            present.add(item["provider_id"])
            record = cached.get(item["provider_id"])
            if record is None:
                record = LiveJob(board=board, **item, version=1, first_seen_at=now)
                db.session.add(record)
            elif record.content_hash != item["content_hash"] or not record.listed:
                record.version += 1
                for key, value in item.items():
                    setattr(record, key, value)
            record.listed = True
            record.last_seen_at = now
            record.last_checked_at = now
        for provider_id, record in cached.items():
            if provider_id not in present:
                if record.listed:
                    record.version += 1
                record.listed = False
                record.last_checked_at = now
        sync.last_success_at = now
        sync.last_error = None
        sync.listed_count = len(jobs)
        sync.prospect_count = prospects
        db.session.commit()
        return {"outcome": "refreshed", "board": sync_status(board, sync)}
    finally:
        lock.release()
