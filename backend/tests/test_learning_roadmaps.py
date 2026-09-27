"""Roadmap semantics and ownership, using an isolated SQLite test database."""

from copy import deepcopy
import os
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch
from urllib.parse import urlparse
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "assessment-tests-only-not-a-deployment-secret-2026"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from extensions import db
from models.learning_roadmap import LearningRoadmap
from services.learning_roadmap import CATALOG, CATALOG_VERSION, POLICY_VERSION, build_roadmap
from services.sql_assessment import QUESTIONS, grade_answers


class LearningRoadmapTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.headers = self.register("one@example.test")
        self.other = self.register("two@example.test")
        self.client.post("/api/skills", headers=self.headers, json={"skill_name": "SQL", "proficiency": 7})

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register(self, email):
        account = {"name": "Roadmap Demo", "email": email, "password": "test-only-credential"}
        self.assertEqual(self.client.post("/api/register", json=account).status_code, 201)
        response = self.client.post("/api/login", json=account)
        return {"Authorization": "Bearer " + response.get_json()["access_token"]}

    def attempt(self, choices=("b", "c", "a", "b", "b", None)):
        attempt = self.client.post("/api/assessments/sql/attempts", headers=self.headers, json={}).get_json()["attempt"]
        if choices is not None:
            answers = [{"question_id": question["id"], "option_id": option} for question, option in zip(QUESTIONS, choices)]
            response = self.client.post(f"/api/assessments/attempts/{attempt['id']}/submit", headers=self.headers, json={"answers": answers})
            self.assertEqual(response.status_code, 200)
            attempt = response.get_json()["attempt"]
        return attempt

    def create(self, attempt):
        response = self.client.post(f"/api/roadmaps/attempts/{attempt['id']}", headers=self.headers, json={})
        self.assertEqual(response.status_code, 201)
        return response.get_json()["roadmap"]

    def progress(self, roadmap, step, completed):
        return self.client.patch(f"/api/roadmaps/{roadmap['id']}/progress", headers=self.headers, json={"step_id": step, "completed": completed})

    def test_routes_require_authentication(self):
        for method, path in [("GET", f"/api/roadmaps/attempts/{uuid4()}"), ("POST", f"/api/roadmaps/attempts/{uuid4()}"), ("PATCH", f"/api/roadmaps/{uuid4()}/progress")]:
            self.assertEqual(self.client.open(path, method=method, json={}).status_code, 401)

    def test_other_candidate_cannot_read_create_or_update(self):
        attempt = self.attempt()
        roadmap = self.create(attempt)
        for method in ("GET", "POST"):
            self.assertEqual(self.client.open(f"/api/roadmaps/attempts/{attempt['id']}", method=method, headers=self.other, json={}).status_code, 404)
        self.assertEqual(self.client.patch(f"/api/roadmaps/{roadmap['id']}/progress", headers=self.other, json={"step_id": "joins", "completed": True}).status_code, 404)

    def test_get_is_read_only_and_unfinished_attempt_cannot_create(self):
        attempt = self.attempt(choices=None)
        path = f"/api/roadmaps/attempts/{attempt['id']}"
        self.assertIsNone(self.client.get(path, headers=self.headers).get_json()["roadmap"])
        self.assertEqual(self.client.post(path, headers=self.headers, json={}).status_code, 409)
        with self.app.app_context():
            self.assertEqual(db.session.query(LearningRoadmap).count(), 0)

    def test_mixed_result_distinguishes_practice_from_missing_evidence(self):
        roadmap = self.create(self.attempt())
        steps = roadmap["snapshot"]["steps"]
        self.assertEqual([step["id"] for step in steps], ["joins", "aggregation"])
        self.assertEqual([step["kind"] for step in steps], ["practice", "collect_evidence"])
        self.assertEqual(steps[0]["source_counts"]["incorrect_count"], 2)
        self.assertIn("not enough evidence", steps[1]["reason"])
        self.assertEqual(roadmap["snapshot"]["catalog_version"], CATALOG_VERSION)
        self.assertEqual(roadmap["snapshot"]["policy_version"], POLICY_VERSION)
        self.assertEqual(roadmap["snapshot"]["source_assessment_version"], "sql-foundations-v1")

    def test_twenty_percent_example_creates_three_practice_steps(self):
        roadmap = self.create(self.attempt(("b", "a", "a", "b", "a", None)))
        steps = roadmap["snapshot"]["steps"]
        self.assertEqual([step["id"] for step in steps], ["filtering", "joins", "aggregation"])
        self.assertTrue(all(step["kind"] == "practice" for step in steps))
        self.assertIn("remain unassessed", steps[-1]["reason"])

    def test_all_skipped_requests_evidence_without_inventing_deficits(self):
        roadmap = self.create(self.attempt((None,) * 6))
        self.assertEqual(roadmap["step_count"], 3)
        self.assertTrue(all(step["kind"] == "collect_evidence" for step in roadmap["snapshot"]["steps"]))
        self.assertTrue(all("optional support" in step["resource_guidance"] for step in roadmap["snapshot"]["steps"]))

    def test_all_correct_does_not_prescribe_remedial_steps(self):
        roadmap = self.create(self.attempt(("b", "c", "d", "a", "b", "c")))
        self.assertEqual(roadmap["snapshot"]["steps"], [])
        self.assertEqual(roadmap["completed_count"], 0)
        self.assertEqual(self.progress(roadmap, "joins", True).status_code, 400)

    def test_creation_is_idempotent_and_saved_catalogue_is_immutable(self):
        attempt = self.attempt()
        roadmap = self.create(attempt)
        path = f"/api/roadmaps/attempts/{attempt['id']}"
        with patch.dict(CATALOG["joins"], {"title": "Edited future catalogue"}):
            response = self.client.post(path, headers=self.headers, json={})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["roadmap"], roadmap)
            self.assertEqual(self.client.get(path, headers=self.headers).get_json()["roadmap"], roadmap)
        with self.app.app_context():
            self.assertEqual(db.session.query(LearningRoadmap).count(), 1)

    def test_progress_is_reversible_persisted_and_separate_from_scores(self):
        attempt = self.attempt()
        roadmap = self.create(attempt)
        saved = self.progress(roadmap, "joins", True).get_json()["roadmap"]
        self.assertEqual(saved["completed_count"], 1)
        self.assertTrue(saved["self_reported_progress"]["joins"]["completed"])
        self.assertEqual(self.progress(roadmap, "joins", True).get_json()["roadmap"], saved)
        self.assertEqual(self.progress(roadmap, "aggregation", True).get_json()["roadmap"]["completed_count"], 2)
        final = self.progress(roadmap, "joins", False).get_json()["roadmap"]
        self.assertEqual(final["completed_count"], 1)
        self.assertTrue(final["self_reported_progress"]["aggregation"]["completed"])
        self.assertEqual(final["snapshot"], roadmap["snapshot"])
        self.assertEqual(self.client.get(f"/api/roadmaps/attempts/{attempt['id']}", headers=self.headers).get_json()["roadmap"], final)
        self.assertEqual(self.client.get(f"/api/assessments/attempts/{attempt['id']}", headers=self.headers).get_json()["attempt"], attempt)
        self.assertEqual(self.client.get("/api/skills", headers=self.headers).get_json()["skills"][0]["proficiency"], 7)

    def test_invalid_payloads_and_client_scores_are_rejected(self):
        attempt = self.attempt()
        path = f"/api/roadmaps/attempts/{attempt['id']}"
        for body in ([], True, {"user_id": 1}, {"score": 100}):
            self.assertEqual(self.client.post(path, headers=self.headers, json=body).status_code, 400)
        roadmap = self.create(attempt)
        for body in ({}, [], {"step_id": "joins", "completed": 1}, {"step_id": "joins", "completed": "true"}, {"step_id": [], "completed": True}, {"step_id": "unknown", "completed": True}, {"step_id": "joins", "completed": True, "score": 100}, {"step_id": "joins", "completed": True, "user_id": 2}):
            response = self.client.patch(f"/api/roadmaps/{roadmap['id']}/progress", headers=self.headers, json=body)
            self.assertEqual(response.status_code, 400, body)
        self.assertEqual(self.client.get(path, headers=self.headers).get_json()["roadmap"]["self_reported_progress"], {})

    def test_new_attempt_gets_its_own_roadmap_and_progress(self):
        first = self.create(self.attempt())
        self.progress(first, "joins", True)
        second = self.create(self.attempt())
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(second["self_reported_progress"], {})


class RoadmapContentTests(unittest.TestCase):
    def test_original_practice_tasks_match_their_self_checks(self):
        with sqlite3.connect(":memory:") as connection:
            def run(topic, query):
                starter = CATALOG[topic]["task"]["starter_sql"].split("-- Add your SELECT below.")[0]
                return connection.execute(starter + query).fetchall()
            self.assertEqual(run("filtering", "SELECT item_id FROM items WHERE price >= 400 AND discount IS NULL ORDER BY item_id"), [(101,), (104,)])
            self.assertEqual(run("joins", "SELECT c.customer_id, o.order_id FROM customers c INNER JOIN orders o ON c.customer_id = o.customer_id ORDER BY c.customer_id, o.order_id"), [(11, 501), (11, 502), (13, 503)])
            self.assertEqual(run("joins", "SELECT c.customer_id, o.order_id FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id ORDER BY c.customer_id, o.order_id"), [(11, 501), (11, 502), (12, None), (13, 503)])
            self.assertEqual(run("aggregation", "SELECT customer_id, COUNT(*), COUNT(amount), SUM(amount) FROM payments GROUP BY customer_id HAVING COUNT(*) >= 2 ORDER BY customer_id"), [(11, 3, 2, 350), (12, 2, 2, 200)])

    def test_resources_have_checked_https_links_and_original_tasks(self):
        for topic in CATALOG.values():
            self.assertTrue(topic["task"]["instructions"])
            self.assertTrue(any(item["kind"] == "course_lesson" for item in topic["resources"]))
            for item in topic["resources"]:
                url = urlparse(item["url"])
                self.assertEqual(url.scheme, "https")
                self.assertIn(url.hostname, ("cs50.harvard.edu", "www.postgresql.org"))
                self.assertEqual(item["checked_on"], "2026-09-26")

    def test_unmapped_topic_is_explicit_instead_of_silently_treated_as_covered(self):
        answers = [{"question_id": item["id"], "option_id": item["correct_option_id"]} for item in QUESTIONS]
        result = grade_answers(QUESTIONS, answers)
        unknown = deepcopy(result["topics"][0])
        unknown["topic"] = "window_functions"
        result["topics"].append(unknown)
        roadmap = build_roadmap(result, "future-bank", "future-scoring")
        self.assertEqual(roadmap["unmapped_topics"], ["window_functions"])


if __name__ == "__main__":
    unittest.main()
