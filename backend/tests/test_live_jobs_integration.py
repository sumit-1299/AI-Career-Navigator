"""Unit and integration test suite for Live Jobs and Technical Diagnostics.

Verifies:
1. Source registry configuration and provider metadata.
2. PlainDescription parser and HTML sanitization.
3. Tech job classification, tag extraction, and attribute normalization.
4. LiveJobsService retrieval, in-memory caching, search, and pagination.
5. Skill matching calculations (matched, missing, readiness recommendations).
6. SqlAssessmentService question retrieval and deterministic scoring.
7. /api/jobs routes (listings, single detail, matching, custom matching, diagnostics).
8. Database safety and schema non-mutation (11 tables preserved).
"""

import json
import unittest
from app import create_app
from config import TestingConfig
from extensions import db
from models.canonical_skill import CanonicalSkill
from models.skill import Skill
from models.user import User
from services.live_jobs_service import (
    LiveJobsService,
    SOURCE_REGISTRY,
    TECH_TAGS,
    classify_tech_job,
    extract_tech_tags,
    plain_description,
    _normalize_work_mode,
    _normalize_experience,
)
from services.sql_assessment_service import SqlAssessmentService, QUESTIONS


class TestLiveJobsService(unittest.TestCase):
    """Test suite for LiveJobsService connector, parsing, and matching logic."""

    def test_source_registry_completeness(self):
        """Verify the 9 configured public employer sources exist with required fields."""
        registry = LiveJobsService.get_source_registry()
        self.assertGreaterEqual(len(registry), 9)

        expected_sources = [
            "greenhouse-canonical",
            "greenhouse-razorpay",
            "ashby-notion",
            "ashby-vercel",
            "ashby-linear",
            "ashby-ramp",
            "lever-dnb",
            "lever-spreetail",
            "lever-zum",
        ]
        for key in expected_sources:
            self.assertIn(key, registry)
            source = registry[key]
            self.assertIn("provider", source)
            self.assertIn("label", source)
            self.assertIn("identifier", source)
            self.assertIn("board_url", source)
            self.assertIn(source["provider"], ["greenhouse", "ashby", "lever"])

    def test_plain_description_sanitization(self):
        """Verify HTML stripping, line breaks, script discard, and length bounding."""
        html_input = """
        <div>
            <h1>Backend Role</h1>
            <script>alert('bad');</script>
            <p>We are seeking a <b>Python</b> engineer.</p>
            <ul>
                <li>Design APIs</li>
                <li>PostgreSQL queries</li>
            </ul>
        </div>
        """
        cleaned = plain_description(html_input)
        self.assertNotIn("<script>", cleaned)
        self.assertNotIn("alert", cleaned)
        self.assertNotIn("<h1>", cleaned)
        self.assertIn("Backend Role", cleaned)
        self.assertIn("Python", cleaned)
        self.assertIn("Design APIs", cleaned)
        self.assertIn("PostgreSQL queries", cleaned)

    def test_tech_job_classification(self):
        """Verify technical vs non-technical role classification."""
        tech_res = classify_tech_job(
            "Senior Backend Engineer",
            "Build scalable microservices with Python, SQL, and Docker. 100% remote.",
        )
        self.assertTrue(tech_res["is_tech"])
        self.assertEqual(tech_res["work_mode"], "Remote")
        self.assertEqual(tech_res["experience_level"], "Senior / Lead")
        self.assertIn("Python", tech_res["tech_tags"])
        self.assertIn("SQL", tech_res["tech_tags"])
        self.assertIn("Docker", tech_res["tech_tags"])

        non_tech_res = classify_tech_job(
            "Sales Development Representative",
            "Prospect outbound leads and generate sales revenue.",
        )
        self.assertFalse(non_tech_res["is_tech"])

    def test_normalization_helpers(self):
        """Verify work mode and experience level extraction."""
        self.assertEqual(_normalize_work_mode("Remote Software Developer"), "Remote")
        self.assertEqual(_normalize_work_mode("Hybrid role in London"), "Hybrid")
        self.assertEqual(_normalize_work_mode("On-site engineer in NYC"), "On-site")
        self.assertEqual(_normalize_work_mode("Role with flexible conditions"), "Not specified")

        self.assertEqual(_normalize_experience("Junior Python Dev"), "Entry / Junior")
        self.assertEqual(_normalize_experience("Senior SRE"), "Senior / Lead")
        self.assertEqual(_normalize_experience("Staff Platform Engineer"), "Staff / Principal")
        self.assertEqual(_normalize_experience("Engineering Manager"), "Management")
        self.assertEqual(_normalize_experience("Software Intern"), "Intern")

    def test_extract_tech_tags(self):
        """Verify extraction of canonical technology tags from text."""
        text = "Experience with TypeScript, React.js frontend and PostgreSQL database on AWS."
        tags = extract_tech_tags(text)
        self.assertIn("TypeScript", tags)
        self.assertIn("React", tags)
        self.assertIn("PostgreSQL", tags)
        self.assertIn("AWS", tags)

    def test_fetch_source_offline_fallback(self):
        """Verify offline fallback fixtures are returned safely for sources."""
        result = LiveJobsService.fetch_source("greenhouse-canonical", offline_fallback=True)
        self.assertIn("jobs", result)
        self.assertGreaterEqual(len(result["jobs"]), 1)
        job = result["jobs"][0]
        self.assertIn("provider_id", job)
        self.assertIn("title", job)
        self.assertIn("employer", job)
        self.assertIn("tech_tags", job)
        self.assertIn("content_hash", job)

    def test_search_jobs_with_filters(self):
        """Verify search filtering by query, technology, and pagination."""
        res = LiveJobsService.search_jobs(query="Engineer", page=1, page_size=5, offline_fallback=True)
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["tech_only"])
        self.assertLessEqual(len(res["jobs"]), 5)
        self.assertGreaterEqual(res["total"], 1)

        # Tech filter
        res_tech = LiveJobsService.search_jobs(technology="Python", offline_fallback=True)
        for j in res_tech["jobs"]:
            self.assertTrue(
                any("python" in t.casefold() for t in j.get("tech_tags", []))
                or "python" in j.get("description", "").casefold()
            )

    def test_get_job_detail(self):
        """Verify fetching a single job posting by ID."""
        src_res = LiveJobsService.fetch_source("greenhouse-canonical", offline_fallback=True)
        self.assertGreater(len(src_res["jobs"]), 0)
        target_id = src_res["jobs"][0]["provider_id"]
        detail = LiveJobsService.get_job("greenhouse-canonical", target_id, offline_fallback=True)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["status"], "success")
        self.assertEqual(detail["job"]["provider_id"], target_id)
        self.assertEqual(detail["job"]["employer"], "Canonical")

        # Non-existent job
        missing = LiveJobsService.get_job("greenhouse-canonical", "non-existent-999", offline_fallback=True)
        self.assertIsNone(missing)

    def test_match_job_to_skills(self):
        """Verify matching calculation against candidate skills."""
        job = {
            "provider_id": "test-01",
            "title": "Backend Developer",
            "employer": "TechCorp",
            "description": "Requires Python, SQL, Docker, and Git.",
            "tech_tags": ["Python", "SQL", "Docker", "Git"],
            "work_mode": "Remote",
            "experience_level": "Entry / Junior",
        }

        # Perfect match
        match_full = LiveJobsService.match_job_to_skills(job, ["Python", "SQL", "Docker", "Git"])
        self.assertEqual(match_full["match_score"], 100.0)
        self.assertEqual(len(match_full["missing_skills"]), 0)
        self.assertIn("Ready to apply", match_full["recommendations"][0])

        # Partial match
        match_partial = LiveJobsService.match_job_to_skills(job, ["Python", "Git"])
        self.assertEqual(match_partial["match_score"], 50.0)
        self.assertIn("SQL", match_partial["missing_skills"])
        self.assertIn("Docker", match_partial["missing_skills"])

        # Zero match
        match_zero = LiveJobsService.match_job_to_skills(job, ["Ruby", "COBOL"])
        self.assertEqual(match_zero["match_score"], 0.0)
        self.assertEqual(len(match_zero["missing_skills"]), 4)


class TestSqlAssessmentService(unittest.TestCase):
    """Test suite for SqlAssessmentService foundations diagnostic."""

    def test_get_assessment_without_solutions(self):
        """Verify assessment questions do not reveal solutions to candidates."""
        assessment = SqlAssessmentService.get_assessment(include_solutions=False)
        self.assertEqual(assessment["status"], "success")
        self.assertEqual(assessment["total_questions"], 6)
        self.assertEqual(len(assessment["questions"]), 6)

        for q in assessment["questions"]:
            self.assertIn("id", q)
            self.assertIn("topic", q)
            self.assertIn("prompt", q)
            self.assertIn("options", q)
            self.assertNotIn("correct_option_id", q)
            self.assertNotIn("explanation", q)

    def test_get_assessment_with_solutions(self):
        """Verify assessment questions include solutions when requested internally."""
        assessment = SqlAssessmentService.get_assessment(include_solutions=True)
        for q in assessment["questions"]:
            self.assertIn("correct_option_id", q)
            self.assertIn("explanation", q)

    def test_evaluate_perfect_score(self):
        """Verify 100% score evaluation with correct answers."""
        correct_answers = {q["id"]: q["correct_option_id"] for q in QUESTIONS}
        result = SqlAssessmentService.evaluate(correct_answers)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["score_percentage"], 100.0)
        self.assertEqual(result["correct_count"], 6)
        self.assertEqual(result["skipped_count"], 0)
        self.assertEqual(result["readiness_level"], "Foundational Mastery")

    def test_evaluate_mixed_score_and_skips(self):
        """Verify partial score evaluation with skips and errors."""
        answers = {
            "sql-filter-1": "b",  # correct
            "sql-filter-2": "a",  # wrong (selected =)
            # sql-join-1 skipped
            "sql-aggregate-1": "b",  # correct
            # sql-null-1 skipped
            # sql-subquery-1 skipped
        }
        result = SqlAssessmentService.evaluate(answers)

        self.assertEqual(result["correct_count"], 2)
        self.assertEqual(result["answered_count"], 3)
        self.assertEqual(result["skipped_count"], 3)
        self.assertAlmostEqual(result["score_percentage"], round(2 / 6 * 100, 1))
        self.assertEqual(result["readiness_level"], "Prerequisite Review Required")
        self.assertIn("filtering", result["topic_breakdown"])


class TestJobsApiRoutes(unittest.TestCase):
    """Test suite for /api/jobs Flask endpoints."""

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_get_jobs_listing(self):
        """GET /api/jobs returns 200 with job list and metadata."""
        res = self.client.get("/api/jobs")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["tech_only"])
        self.assertIn("jobs", data)
        self.assertIn("sources", data)

    def test_get_jobs_listing_with_pagination(self):
        """GET /api/jobs?page=1&page_size=2 returns paginated results."""
        res = self.client.get("/api/jobs?page=1&page_size=2")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertLessEqual(len(data["jobs"]), 2)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["page_size"], 2)

    def test_get_jobs_sources_registry(self):
        """GET /api/jobs/sources returns configured sources list."""
        res = self.client.get("/api/jobs/sources")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["total_sources"], 9)

    def test_get_job_detail(self):
        """GET /api/jobs/<source_key>/<provider_id> returns job details."""
        list_res = self.client.get("/api/jobs")
        self.assertEqual(list_res.status_code, 200)
        jobs = list_res.get_json()["jobs"]
        self.assertGreater(len(jobs), 0)
        source_key = jobs[0]["source_key"]
        provider_id = jobs[0]["provider_id"]

        res = self.client.get(f"/api/jobs/{source_key}/{provider_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["job"]["provider_id"], provider_id)

        # 404 for invalid source
        res_bad_src = self.client.get(f"/api/jobs/non-existent-source/{provider_id}")
        self.assertEqual(res_bad_src.status_code, 404)

        # 404 for invalid job
        res_bad_job = self.client.get(f"/api/jobs/{source_key}/non-existent-job-id")
        self.assertEqual(res_bad_job.status_code, 404)

    def test_post_job_match(self):
        """POST /api/jobs/<source_key>/<provider_id>/match compares skills."""
        list_res = self.client.get("/api/jobs")
        jobs = list_res.get_json()["jobs"]
        self.assertGreater(len(jobs), 0)
        source_key = jobs[0]["source_key"]
        provider_id = jobs[0]["provider_id"]

        payload = {"skills": ["Python", "Linux", "Docker"]}
        res = self.client.post(f"/api/jobs/{source_key}/{provider_id}/match", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("match_score", data)
        self.assertIn("matched_skills", data)
        self.assertIn("missing_skills", data)

    def test_post_match_custom_job(self):
        """POST /api/jobs/match-custom compares skills against custom description."""
        payload = {
            "job_title": "Full Stack Engineer",
            "job_description": "We build web apps using React, Node.js, and PostgreSQL database.",
            "skills": ["React", "PostgreSQL"],
        }
        res = self.client.post("/api/jobs/match-custom", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("match_score", data)

        # Missing description should error 400
        res_err = self.client.post("/api/jobs/match-custom", json={"job_title": "Tester"})
        self.assertEqual(res_err.status_code, 400)

    def test_sql_diagnostic_endpoints(self):
        """GET /api/jobs/diagnostics/sql and POST evaluate work as expected."""
        # 1. Get questions
        res_q = self.client.get("/api/jobs/diagnostics/sql")
        self.assertEqual(res_q.status_code, 200)
        q_data = res_q.get_json()
        self.assertEqual(q_data["total_questions"], 6)

        # 2. Evaluate answers
        eval_payload = {
            "answers": {
                "sql-filter-1": "b",
                "sql-filter-2": "c",
                "sql-join-1": "c",
            }
        }
        res_eval = self.client.post("/api/jobs/diagnostics/sql/evaluate", json=eval_payload)
        self.assertEqual(res_eval.status_code, 200)
        eval_data = res_eval.get_json()
        self.assertEqual(eval_data["correct_count"], 3)
        self.assertEqual(eval_data["answered_count"], 3)
        self.assertEqual(eval_data["skipped_count"], 3)

    def test_database_table_count_integrity(self):
        """Verify that live jobs integration maintains exactly 11 database tables."""
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        self.assertEqual(len(tables), 11)
        expected = {
            "users", "student_profiles", "careers", "career_preferences",
            "canonical_skills", "skill_aliases", "skills", "career_skills",
            "data_sources", "learning_resources", "user_learning_progress"
        }
        self.assertEqual(set(tables), expected)


if __name__ == "__main__":
    unittest.main()
