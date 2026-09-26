"""Assessment API checks using an isolated in-memory database.

Run in a separate process: python -m unittest discover -s backend/tests -v
The overrides below prevent this test process from opening the developer database.
"""

from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import sys
import unittest
from uuid import uuid4


os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "assessment-tests-only-not-a-deployment-secret-2026"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from extensions import db
from models.assessment_attempt import AssessmentAttempt
from models.skill import Skill
from services.sql_assessment import QUESTIONS


class AssessmentApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.headers = self.register("one@example.test")
        self.other_headers = self.register("two@example.test")
        response = self.client.post("/api/skills", headers=self.headers, json={
            "skill_name": "SQL", "proficiency": 7,
        })
        self.assertEqual(response.status_code, 201)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register(self, email):
        account = {"name": "Assessment Test", "email": email, "password": "test-only-credential"}
        self.assertEqual(self.client.post("/api/register", json=account).status_code, 201)
        response = self.client.post("/api/login", json=account)
        self.assertEqual(response.status_code, 200)
        return {"Authorization": "Bearer " + response.get_json()["access_token"]}

    def start(self, headers=None):
        response = self.client.post("/api/assessments/sql/attempts", headers=headers or self.headers, json={})
        self.assertEqual(response.status_code, 201)
        return response.get_json()["attempt"]

    def submit(self, attempt, answers, headers=None):
        return self.client.post(
            f"/api/assessments/attempts/{attempt['id']}/submit",
            headers=headers or self.headers, json={"answers": answers},
        )

    @staticmethod
    def answers(choices=("b", "c", "d", "a", "b", "c")):
        ids = ["sql-filter-1", "sql-filter-2", "sql-join-1", "sql-join-2", "sql-aggregate-1", "sql-aggregate-2"]
        return [{"question_id": question_id, "option_id": choice} for question_id, choice in zip(ids, choices)]

    def test_all_routes_require_login(self):
        attempt_id = uuid4()
        for method, path in [
            ("GET", "/api/assessments/sql"), ("GET", "/api/assessments/sql/attempts"),
            ("POST", "/api/assessments/sql/attempts"),
            ("GET", f"/api/assessments/attempts/{attempt_id}"),
            ("POST", f"/api/assessments/attempts/{attempt_id}/submit"),
        ]:
            with self.subTest(path=path, method=method):
                self.assertEqual(self.client.open(path, method=method, json={}).status_code, 401)

    def test_start_hides_answer_key_and_snapshots_claim(self):
        attempt = self.start()
        self.assertEqual(attempt["status"], "in_progress")
        self.assertIsNone(attempt["result"])
        self.assertEqual(attempt["self_reported_claims"][0]["proficiency"], 7)
        for question in attempt["questions"]:
            self.assertEqual(set(question), {"id", "topic", "prompt", "options"})
        response = self.client.get(f"/api/assessments/attempts/{attempt['id']}", headers=self.headers)
        self.assertEqual(response.get_json()["attempt"], attempt)

    def test_cannot_access_or_submit_another_candidates_attempt(self):
        attempt = self.start()
        path = f"/api/assessments/attempts/{attempt['id']}"
        self.assertEqual(self.client.get(path, headers=self.other_headers).status_code, 404)
        self.assertEqual(self.submit(attempt, self.answers(), self.other_headers).status_code, 404)
        history = self.client.get("/api/assessments/sql/attempts", headers=self.other_headers).get_json()
        self.assertEqual(history["attempts"], [])

    def test_mixed_result_is_persisted_without_overwriting_claim(self):
        attempt = self.start()
        response = self.submit(attempt, self.answers(("b", "c", "a", "b", "b", None)))
        self.assertEqual(response.status_code, 200)
        result = response.get_json()["attempt"]["result"]
        self.assertEqual(result["correct_count"], 3)
        self.assertEqual(result["incorrect_count"], 2)
        self.assertEqual(result["unanswered_count"], 1)
        self.assertEqual(result["accuracy_on_answered_percent"], 60.0)
        self.assertEqual(result["coverage_percent"], 83.33)
        topics = {topic["topic"]: topic for topic in result["topics"]}
        self.assertTrue(topics["joins"]["practice_suggested"])
        self.assertEqual(topics["aggregation"]["evidence_status"], "incomplete")
        stored = self.client.get(f"/api/assessments/attempts/{attempt['id']}", headers=self.headers).get_json()
        self.assertEqual(stored["attempt"]["result"], result)
        skills = self.client.get("/api/skills", headers=self.headers).get_json()["skills"]
        self.assertEqual(skills[0]["proficiency"], 7)

    def test_skips_remain_unassessed(self):
        result = self.submit(self.start(), self.answers((None,) * 6)).get_json()["attempt"]["result"]
        self.assertIsNone(result["accuracy_on_answered_percent"])
        self.assertEqual(result["coverage_percent"], 0)
        for topic in result["topics"]:
            self.assertEqual(topic["evidence_status"], "not_assessed")
            self.assertFalse(topic["practice_suggested"])
            self.assertTrue(topic["additional_evidence_needed"])

    def test_invalid_answers_do_not_complete_the_attempt(self):
        attempt = self.start()
        duplicate = self.answers()
        duplicate[-1] = deepcopy(duplicate[0])
        unknown = self.answers()
        unknown[0]["question_id"] = "unassigned"
        bad_option = self.answers()
        bad_option[0]["option_id"] = True
        for answers in [None, {}, [], self.answers()[:-1], duplicate, unknown, bad_option, [1] * 6]:
            with self.subTest(answers=answers):
                self.assertEqual(self.submit(attempt, answers).status_code, 400)
        stored = self.client.get(f"/api/assessments/attempts/{attempt['id']}", headers=self.headers).get_json()
        self.assertEqual(stored["attempt"]["status"], "in_progress")

    def test_client_cannot_supply_a_score_or_candidate_id(self):
        for payload in [[], None, {"user_id": 2}, {"score": 100}]:
            response = self.client.post("/api/assessments/sql/attempts", headers=self.headers,
                                        data=json.dumps(payload), content_type="application/json")
            self.assertEqual(response.status_code, 400)
        attempt = self.start()
        for payload in [{"answers": self.answers(), "score": 100}, [], None]:
            response = self.client.post(f"/api/assessments/attempts/{attempt['id']}/submit", headers=self.headers,
                                        data=json.dumps(payload), content_type="application/json")
            self.assertEqual(response.status_code, 400)
        malformed = self.client.post(f"/api/assessments/attempts/{attempt['id']}/submit", headers=self.headers,
                                     data="{broken", content_type="application/json")
        self.assertEqual(malformed.status_code, 400)

    def test_submitted_attempt_cannot_be_overwritten(self):
        attempt = self.start()
        first = self.submit(attempt, self.answers())
        self.assertEqual(first.get_json()["attempt"]["result"]["correct_count"], 6)
        self.assertEqual(self.submit(attempt, self.answers((None,) * 6)).status_code, 409)
        stored = self.client.get(f"/api/assessments/attempts/{attempt['id']}", headers=self.headers).get_json()
        self.assertEqual(stored["attempt"]["result"]["correct_count"], 6)

    def test_snapshot_survives_later_claim_or_bank_changes(self):
        attempt = self.start()
        original_key = QUESTIONS[0]["correct_option_id"]
        try:
            QUESTIONS[0]["correct_option_id"] = "a"
            with self.app.app_context():
                claim = db.session.execute(db.select(Skill)).scalars().first()
                claim.proficiency = 2
                db.session.commit()
            stored = self.submit(attempt, self.answers()).get_json()["attempt"]
            self.assertEqual(stored["result"]["correct_count"], 6)
            self.assertEqual(stored["self_reported_claims"][0]["proficiency"], 7)
        finally:
            QUESTIONS[0]["correct_option_id"] = original_key

    def test_second_attempt_has_separate_history(self):
        first, second = self.start(), self.start()
        self.assertNotEqual(first["id"], second["id"])
        self.submit(first, self.answers())
        history = self.client.get("/api/assessments/sql/attempts", headers=self.headers).get_json()["attempts"]
        self.assertEqual({attempt["id"] for attempt in history}, {first["id"], second["id"]})
        with self.app.app_context():
            self.assertEqual(db.session.scalar(db.select(db.func.count()).select_from(AssessmentAttempt)), 2)


class SqlExampleTests(unittest.TestCase):
    def test_concrete_join_and_aggregate_examples(self):
        with sqlite3.connect(":memory:") as connection:
            connection.executescript("""
                CREATE TABLE customers (id INTEGER PRIMARY KEY);
                CREATE TABLE orders (customer_id INTEGER);
                INSERT INTO customers VALUES (1), (2);
                INSERT INTO orders VALUES (1), (1);
                CREATE TABLE payments (amount INTEGER);
                INSERT INTO payments VALUES (10), (NULL), (20);
            """)
            self.assertEqual(len(connection.execute("SELECT c.id FROM customers c INNER JOIN orders o ON o.customer_id = c.id").fetchall()), 2)
            self.assertEqual(len(connection.execute("SELECT c.id FROM customers c LEFT JOIN orders o ON o.customer_id = c.id").fetchall()), 3)
            self.assertEqual(connection.execute("SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id HAVING COUNT(*) >= 2").fetchall(), [(1, 2)])
            self.assertEqual(connection.execute("SELECT COUNT(amount) FROM payments").fetchone(), (2,))


if __name__ == "__main__":
    unittest.main()
