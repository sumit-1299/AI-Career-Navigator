"""Tests for live Greenhouse retrieval and immutable comparisons."""

import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite://"
os.environ[
    "JWT_SECRET_KEY"
] = "assessment-tests-only-not-a-deployment-secret-2026"

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from app import create_app
from extensions import db
from services.live_jobs import (
    FeedUnavailable,
    fetch_board,
    normalize_feed,
    plain_description,
)


def posting(number=1, **changes):
    return {
        "id": number,
        "internal_job_id": number + 100,
        "title": "Python backend developer",
        "location": {
            "name": "Bengaluru, India"
        },
        "absolute_url": (
            "https://job-boards.greenhouse.io/"
            f"canonical/jobs/{number}"
        ),
        "content": (
            "&lt;h2&gt;Requirements&lt;/h2&gt;"
            "&lt;p&gt;Python, SQL and REST APIs are required.&lt;/p&gt;"
        ),
        "updated_at": "2026-09-20T12:00:00Z",
        **changes,
    }


def feed(*jobs):
    return {
        "jobs": list(jobs),
        "meta": {
            "total": len(jobs)
        },
    }


class ProviderTests(unittest.TestCase):
    def test_plain_text_conversion(self):
        text = plain_description(
            "&lt;h2&gt;Requirements&lt;/h2&gt;"
            "&lt;p&gt;Python &amp;amp; SQL&lt;/p&gt;"
            "<script>ignored()</script>"
            "<style>ignored()</style>"
            "<ul><li>Git</li></ul>"
        )

        self.assertEqual(
            text,
            "Requirements\nPython & SQL\nGit",
        )

    def test_malformed_feed_is_rejected(self):
        cases = [
            {},
            {"jobs": [], "meta": {"total": 1}},
            feed(
                posting(
                    title="",
                )
            ),
            feed(
                posting(
                    content="",
                )
            ),
            feed(
                posting(
                    updated_at="yesterday",
                )
            ),
        ]

        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(FeedUnavailable):
                    normalize_feed(data)

    def test_valid_multiple_postings_are_accepted(self):
        jobs, prospects = normalize_feed(
            feed(
                posting(1),
                posting(2),
            )
        )

        self.assertEqual(
            len(jobs),
            2,
        )

        self.assertEqual(
            prospects,
            0,
        )

    def test_general_interest_posts_are_excluded(self):
        jobs, prospects = normalize_feed(
            feed(
                posting(),
                posting(
                    2,
                    internal_job_id=None,
                ),
            )
        )

        self.assertEqual(
            len(jobs),
            1,
        )

        self.assertEqual(
            prospects,
            1,
        )

    def test_missing_location_is_allowed(self):
        jobs, prospects = normalize_feed(
            feed(
                posting(
                    location=None,
                )
            )
        )

        self.assertEqual(
            len(jobs),
            1,
        )

        self.assertEqual(
            jobs[0]["location"],
            "",
        )

        self.assertEqual(
            prospects,
            0,
        )

    def test_fetch_uses_only_configured_board(self):
        with patch(
            "services.live_jobs.build_opener"
        ) as opener:
            with self.assertRaises(ValueError):
                fetch_board(
                    "https://attacker.example"
                )

            opener.assert_not_called()

            response = (
                opener.return_value
                .open.return_value
                .__enter__
                .return_value
            )

            response.status = 200
            response.read.side_effect = [
                json.dumps(
                    feed(posting())
                ).encode(),
                b"",
            ]

            result = fetch_board(
                "canonical"
            )

            self.assertEqual(
                result["meta"]["total"],
                1,
            )

            args, kwargs = (
                opener.return_value
                .open.call_args
            )

            self.assertEqual(
                args[0].full_url,
                "https://boards-api.greenhouse.io/"
                "v1/boards/canonical/jobs?content=true",
            )

            self.assertEqual(
                kwargs["timeout"],
                8,
            )

    def test_provider_errors_are_sanitized(self):
        with patch(
            "services.live_jobs.build_opener",
            side_effect=RuntimeError(
                "private proxy information"
            ),
        ):
            with self.assertRaises(
                FeedUnavailable
            ) as caught:
                fetch_board("canonical")

        self.assertNotIn(
            "private proxy",
            str(caught.exception),
        )


class LiveJobsApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.headers = self.register(
            "jobs-one@example.test"
        )

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register(self, email):
        account = {
            "name": "Jobs Demo",
            "email": email,
            "password": "jobs-test-only-password",
        }

        response = self.client.post(
            "/api/register",
            json=account,
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        token = self.client.post(
            "/api/login",
            json=account,
        ).get_json()["access_token"]

        return {
            "Authorization": f"Bearer {token}"
        }

    def test_requires_authentication(self):
        response = self.client.get(
            "/api/jobs"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_listing_reads_live_provider(self):
        with patch(
            "routes.jobs.fetch_board",
            return_value=feed(posting()),
        ) as fetch:
            response = self.client.get(
                "/api/jobs",
                headers=self.headers,
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["source"],
            "greenhouse_live",
        )

        self.assertEqual(
            data["total"],
            2,
        )

        fetch.assert_called()

        self.assertEqual(
            response.headers["Cache-Control"],
            "no-store",
        )

    def test_filters_are_applied_to_live_results(self):
        jobs = [
            posting(
                1,
                title="Python Backend Engineer",
                location={
                    "name": "Bengaluru"
                },
            ),
            posting(
                2,
                title="SQL Data Engineer",
                location={
                    "name": "Pune"
                },
                content=(
                    "<p>SQL and Python required.</p>"
                ),
            ),
        ]

        with patch(
            "routes.jobs.fetch_board",
            return_value=feed(*jobs),
        ) as fetch:
            response = self.client.get(
                "/api/jobs"
                "?q=Python"
                "&location=Bengaluru"
                "&board=canonical",
                headers=self.headers,
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["total"],
            1,
        )

        self.assertEqual(
            data["jobs"][0]["title"],
            "Python Backend Engineer",
        )

        fetch.assert_called_once_with(
            "canonical"
        )

    def test_selected_job_is_fetched_live(self):
        with patch(
            "routes.jobs.fetch_board",
            return_value=feed(posting()),
        ) as fetch:
            response = self.client.get(
                "/api/jobs/canonical/1",
                headers=self.headers,
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.get_json()

        self.assertEqual(
            data["source"],
            "greenhouse_live",
        )

        self.assertEqual(
            data["job"]["provider_id"],
            "1",
        )

        self.assertTrue(
            data["job"]["description"]
        )

        fetch.assert_called_once_with(
            "canonical"
        )

    def test_missing_live_job_returns_404(self):
        with patch(
            "routes.jobs.fetch_board",
            return_value=feed(),
        ) as fetch:
            response = self.client.get(
                "/api/jobs/canonical/999999",
                headers=self.headers,
            )

        self.assertEqual(
            response.status_code,
            404,
        )

        fetch.assert_called_once_with(
            "canonical"
        )

    def test_live_comparison_saves_snapshot(self):
        with patch(
            "routes.jobs.fetch_board",
            return_value=feed(posting()),
        ) as fetch:
            body = {
                "submission_id": str(
                    uuid4()
                ),
                "mode": "keyword",
            }

            response = self.client.post(
                "/api/jobs/canonical/1/compare",
                headers=self.headers,
                json=body,
            )

        self.assertIn(
            response.status_code,
            (200, 201),
        )

        comparison = (
            response.get_json()["comparison"]
        )

        self.assertEqual(
            comparison["job"]["source_type"],
            "greenhouse",
        )

        self.assertEqual(
            comparison["job"]["provider_id"],
            "1",
        )

        self.assertEqual(
            comparison["job"]["description"],
            "Requirements\n"
            "Python, SQL and REST APIs are required.",
        )

        self.assertTrue(
            comparison["job"]["content_hash"]
        )

        fetch.assert_called_once_with(
            "canonical"
        )


if __name__ == "__main__":
    unittest.main()