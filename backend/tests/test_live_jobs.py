"""Tests for live multi-provider tech-job retrieval."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "assessment-tests-only-not-a-deployment-secret-2026"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from extensions import db
from services.live_jobs import normalize_feed, plain_description, classify_tech_job


def posting(number=1, **changes):
    return {
        "id": number,
        "internal_job_id": number + 100,
        "title": "Python backend developer",
        "location": {"name": "Bengaluru, India"},
        "absolute_url": f"https://job-boards.greenhouse.io/canonical/jobs/{number}",
        "content": "<h2>Requirements</h2><p>Python, SQL and REST APIs are required.</p>",
        "updated_at": "2026-09-20T12:00:00Z",
        **changes,
    }


def feed(*jobs):
    return {"jobs": list(jobs), "meta": {"total": len(jobs)}}


class ProviderTests(unittest.TestCase):
    def test_plain_text_conversion(self):
        text = plain_description("<h2>Requirements</h2><p>Python &amp; SQL</p>")
        self.assertEqual(text, "Requirements\nPython & SQL")

    def test_greenhouse_normalization_rejects_incomplete_payload(self):
        with self.assertRaises(Exception):
            normalize_feed({"jobs": []})

    def test_tech_classifier_excludes_non_tech_roles(self):
        self.assertTrue(classify_tech_job("Python Backend Engineer", "Build APIs")["is_tech"])
        self.assertFalse(classify_tech_job("Account Executive", "Sell software")["is_tech"])
        self.assertTrue(classify_tech_job("Senior Data Analyst", "Analyze SQL datasets")["is_tech"])


class LiveJobsApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        account = {
            "name": "Live Demo",
            "email": f"jobs-{uuid4()}@example.test",
            "password": "test-only-credential",
        }
        self.assertEqual(self.client.post("/api/register", json=account).status_code, 201)
        token = self.client.post("/api/login", json=account).get_json()["access_token"]
        self.headers = {"Authorization": "Bearer " + token}

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_requires_authentication(self):
        self.assertEqual(self.client.get("/api/jobs").status_code, 401)

    def test_multi_source_fetch_does_not_touch_current_app_in_worker(self):
        fake_job = {
            "provider_id": "1",
            "title": "Python Backend Engineer",
            "location": "Bengaluru",
            "source_url": "https://example.com/jobs/1",
            "provider_updated_at": None,
            "description": "Python SQL REST APIs",
            "content_hash": "abc",
            "department": "Engineering",
            "team": "Platform",
            "work_mode": "Remote",
            "experience_level": "Entry / Junior",
            "tech_tags": ["Python", "SQL", "REST APIs"],
            "is_tech": True,
        }

        def fake_fetch(source_key):
            return {
                "source_key": source_key,
                "provider": "greenhouse",
                "employer": "Demo",
                "source_url": "https://example.com/careers",
                "jobs": [fake_job],
            }

        registry = {
            "greenhouse-demo": {
                "provider": "greenhouse",
                "label": "Demo",
                "identifier": "demo",
                "board_url": "https://example.com/careers",
            }
        }

        with patch("routes.jobs.fetch_source", side_effect=fake_fetch), patch(
            "routes.jobs.SOURCE_REGISTRY", registry
        ), patch("routes.jobs.source_summary", return_value={
            "source_key": "greenhouse-demo",
            "provider": "greenhouse",
            "employer": "Demo",
            "source_url": "https://example.com/careers",
        }):
            response = self.client.get("/api/jobs", headers=self.headers)

        self.assertEqual(response.status_code, 200, response.get_json())
        data = response.get_json()
        self.assertEqual(data["source"], "live_multi_provider")
        self.assertTrue(data["tech_only"])
        self.assertEqual(data["total"], 1)

    def test_legacy_greenhouse_filter_still_works(self):
        source = {
            "source_key": "greenhouse-canonical",
            "provider": "greenhouse",
            "employer": "Canonical",
            "source_url": "https://job-boards.greenhouse.io/canonical",
            "jobs": [
                {
                    "provider_id": "1",
                    "title": "Python Backend Engineer",
                    "location": "Bengaluru",
                    "source_url": "https://example.com/jobs/1",
                    "provider_updated_at": None,
                    "description": "Python",
                    "content_hash": "abc",
                    "department": "Engineering",
                    "team": "Platform",
                    "work_mode": "Remote",
                    "experience_level": "Entry / Junior",
                    "tech_tags": ["Python"],
                    "is_tech": True,
                }
            ],
        }
        with patch("routes.jobs.fetch_source", return_value=source):
            response = self.client.get(
                "/api/jobs?board=canonical&q=Python",
                headers=self.headers,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["total"], 1)


if __name__ == "__main__":
    unittest.main()
