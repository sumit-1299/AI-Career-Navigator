"""Cross-skill ownership, snapshot compatibility and evidence-to-roadmap checks."""

import os
from pathlib import Path
import sys
import unittest
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "assessment-tests-only-not-a-deployment-secret-2026"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from extensions import db
from services.assessment_catalog import BANKS, new_snapshot
from services.sql_assessment import new_snapshot as sql_snapshot


CORRECT = {"sql": ("b", "c", "d", "a", "b", "c"),
           "python": ("b", "a", "d", "c", "b", "d"),
           "rest_api": ("a", "c", "b", "d", "a", "c")}


class MultiSkillFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.owner = self.register("multi-one@example.test")
        self.other = self.register("multi-two@example.test")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register(self, email):
        account = {"name": "Multi-skill check", "email": email, "password": "local-test-only-password"}
        self.assertEqual(self.client.post("/api/register", json=account).status_code, 201)
        response = self.client.post("/api/login", json=account)
        return {"Authorization": "Bearer " + response.get_json()["access_token"]}

    def start(self, key, headers=None):
        response = self.client.post(f"/api/assessments/{key}/attempts", headers=headers or self.owner, json={})
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["attempt"]

    def submit(self, attempt, choices):
        body = {"answers": [{"question_id": item["id"], "option_id": choice}
                            for item, choice in zip(attempt["questions"], choices)]}
        response = self.client.post(f"/api/assessments/attempts/{attempt['id']}/submit", headers=self.owner, json=body)
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()["attempt"]

    def compare(self):
        response = self.client.post("/api/job-matches", headers=self.owner, json={
            "submission_id": str(uuid4()), "title": "Backend prototype test role",
            "description": "Requirements:\nPython, SQL and REST APIs.\nPreferred skills:\nDocker.",
            "source_url": "", "mode": "keyword",
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["comparison"]

    def roadmap(self, attempt):
        response = self.client.post(f"/api/roadmaps/attempts/{attempt['id']}", headers=self.owner, json={})
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["roadmap"]

    def test_sql_snapshot_stays_identical_and_new_snapshots_are_isolated(self):
        self.assertEqual(new_snapshot("sql"), sql_snapshot())
        first = new_snapshot("python")
        first["questions"][0]["correct_option_id"] = "changed"
        self.assertEqual(new_snapshot("python")["questions"][0]["correct_option_id"], "b")

    def test_catalog_and_new_routes_require_auth_and_hide_keys(self):
        for path in ("/api/assessments/catalog", "/api/assessments/attempts",
                     "/api/assessments/python", "/api/assessments/rest_api/attempts"):
            self.assertEqual(self.client.get(path).status_code, 401)
        catalog = self.client.get("/api/assessments/catalog", headers=self.owner).get_json()["assessments"]
        self.assertEqual([item["skill_key"] for item in catalog], ["sql", "python", "rest_api"])
        for key in ("python", "rest_api"):
            attempt = self.start(key)
            self.assertEqual(len(attempt["questions"]), 6)
            self.assertTrue(all(set(q) == {"id", "topic", "prompt", "options"} for q in attempt["questions"]))
        self.assertNotIn("correct_option_id", str(catalog))

    def test_unknown_skills_and_cross_bank_answers_are_rejected(self):
        for method, path in (("GET", "/api/assessments/rust"), ("POST", "/api/assessments/rust/attempts"),
                             ("GET", "/api/assessments/rust/attempts")):
            self.assertEqual(self.client.open(path, method=method, json={}, headers=self.owner).status_code, 404)
        attempt = self.start("python")
        answers = [{"question_id": q["id"], "option_id": None} for q in BANKS["rest_api"]["questions"]]
        path = f"/api/assessments/attempts/{attempt['id']}"
        self.assertEqual(self.client.post(path + "/submit", json={"answers": answers}, headers=self.owner).status_code, 400)
        self.assertEqual(self.client.get(path, headers=self.owner).get_json()["attempt"]["status"], "in_progress")

    def test_claim_aliases_are_scoped_to_selected_skill(self):
        for name in ("SQL", "Python programming", "RESTful APIs", "Django"):
            self.assertEqual(self.client.post("/api/skills", headers=self.owner,
                             json={"skill_name": name, "proficiency": 7}).status_code, 201)
        for key, expected in (("sql", "SQL"), ("python", "Python programming"), ("rest_api", "RESTful APIs")):
            attempt = self.start(key)
            self.assertEqual([claim["skill_name"] for claim in attempt["self_reported_claims"]], [expected])

    def test_history_and_attempts_are_owner_scoped_across_skills(self):
        for key in BANKS:
            attempt = self.start(key)
            path = f"/api/assessments/attempts/{attempt['id']}"
            self.assertEqual(self.client.get(path, headers=self.other).status_code, 404)
            self.assertEqual(self.client.post(path + "/submit", headers=self.other, json={"answers": []}).status_code, 404)
            history = self.client.get(f"/api/assessments/{key}/attempts", headers=self.owner).get_json()["attempts"]
            self.assertEqual([item["skill_key"] for item in history], [key])
        own = self.client.get("/api/assessments/attempts", headers=self.owner).get_json()["attempts"]
        self.assertEqual({item["skill_key"] for item in own}, set(BANKS))
        self.assertEqual(self.client.get("/api/assessments/attempts", headers=self.other).get_json()["attempts"], [])

    def test_mixed_new_results_create_correct_resource_catalog_and_preserve_skips(self):
        for key in ("python", "rest_api"):
            with self.subTest(key=key):
                # First topic: two correct; second: two wrong; third: two skipped.
                choices = ("b", "a", "a", "b", None, None) if key == "python" else ("a", "c", "a", "a", None, None)
                attempt = self.submit(self.start(key), choices)
                roadmap = self.roadmap(attempt)
                steps = roadmap["snapshot"]["steps"]
                self.assertEqual(attempt["result"]["correct_count"], 2)
                self.assertEqual([step["kind"] for step in steps], ["practice", "collect_evidence"])
                self.assertEqual(steps[1]["source_counts"]["unanswered_count"], 2)
                self.assertTrue(roadmap["snapshot"]["catalog_version"].startswith("python-" if key == "python" else "rest-http-"))
                self.assertTrue(all(step["task"]["starter_code"] and step["resources"] for step in steps))
                url = f"/api/roadmaps/attempts/{attempt['id']}"
                self.assertEqual(self.client.post(url, json={}, headers=self.owner).get_json()["roadmap"], roadmap)
                for method in ("GET", "POST"):
                    self.assertEqual(self.client.open(url, method=method, json={}, headers=self.other).status_code, 404)
                progress = f"/api/roadmaps/{roadmap['id']}/progress"
                body = {"step_id": steps[0]["id"], "completed": True}
                self.assertEqual(self.client.patch(progress, json=body, headers=self.other).status_code, 404)
                self.assertEqual(self.client.patch(progress, json=body, headers=self.owner).get_json()["roadmap"]["completed_count"], 1)
                saved = self.client.get(f"/api/assessments/attempts/{attempt['id']}", headers=self.owner).get_json()["attempt"]
                self.assertEqual(saved, attempt)

    def test_latest_per_skill_uses_skipped_attempt_not_previous_best(self):
        for key in BANKS:
            self.submit(self.start(key), CORRECT[key])
        initial = self.compare()
        self.assertEqual(initial["result"]["summary"]["skills_with_assessment_records"], 3)
        skipped = self.submit(self.start("python"), (None,) * 6)
        # An unfinished newer attempt must not hide the latest submitted result.
        self.start("python")
        other = self.start("rest_api", self.other)
        current = self.compare()
        rows = {row["skill_key"]: row for row in current["result"]["skills"]}
        self.assertEqual(rows["python"]["assessment"]["attempt_id"], skipped["id"])
        self.assertIn("entirely skipped", rows["python"]["guidance"])
        self.assertNotEqual(rows["rest_api"]["assessment"]["attempt_id"], other["id"])
        self.assertIn("answered correctly", rows["rest_api"]["guidance"])
        self.assertIsNone(rows["docker"]["assessment"])
        unchanged = self.client.get(f"/api/job-matches/{initial['id']}", headers=self.owner).get_json()["comparison"]
        self.assertEqual(unchanged, initial)
        self.assertEqual(current["candidate_snapshot"]["sql_assessment"], current["candidate_snapshot"]["assessments"]["sql"])

    def test_correct_new_attempts_have_no_remedial_steps_and_skips_need_evidence(self):
        for key in ("python", "rest_api"):
            complete = self.submit(self.start(key), CORRECT[key])
            self.assertEqual(complete["result"]["accuracy_on_answered_percent"], 100)
            self.assertEqual(self.roadmap(complete)["snapshot"]["steps"], [])
            skipped = self.submit(self.start(key), (None,) * 6)
            self.assertIsNone(skipped["result"]["accuracy_on_answered_percent"])
            steps = self.roadmap(skipped)["snapshot"]["steps"]
            self.assertEqual(len(steps), 3)
            self.assertTrue(all(step["kind"] == "collect_evidence" for step in steps))


if __name__ == "__main__":
    unittest.main()
