"""Matching semantics, candidate ownership and immutable comparison snapshots."""

from copy import deepcopy
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
from models.job_comparison import JobComparison
from services.job_matching import EXTRACTION_VERSION, build_comparison, fragments
from services.semantic_encoder import SemanticUnavailable, get_encoder, model_status
from services.skill_catalog import SKILLS, canonical_key, keyword_keys
from services.sql_assessment import QUESTIONS


def empty_snapshot():
    return {"skills": [], "evidence": [], "sql_assessment": None}


class MatchingPolicyTests(unittest.TestCase):
    def test_aliases_preserve_distinct_technologies(self):
        self.assertEqual(canonical_key("  PYTHON   programming "), "python")
        self.assertEqual(canonical_key("RESTful APIs"), "rest_api")
        self.assertEqual(canonical_key("Postgres"), "postgresql")
        self.assertEqual(keyword_keys("JavaScript and NoSQL with MySQL"), ["javascript"])
        self.assertEqual(keyword_keys("Use Python\tprogramming and RESTful APIs."), ["python", "rest_api"])
        self.assertIsNone(canonical_key("API"))

    def test_framework_claim_does_not_become_language_proficiency(self):
        snapshot = empty_snapshot()
        snapshot["skills"] = [{"id": 1, "skill_name": "Django", "proficiency": 9}]
        result = build_comparison("Python programming is required.", snapshot, "keyword")
        row = result["skills"][0]
        self.assertEqual(row["candidate_claims"], [])
        self.assertEqual(row["related_claims"][0]["skill_label"], "Django")
        self.assertEqual(result["summary"]["explicit_mentions_with_claims"], 0)

    def test_missing_evidence_is_unknown_not_a_deficit(self):
        result = build_comparison("Python and SQL are required.", empty_snapshot(), "keyword")
        self.assertEqual(len(result["skills"]), 2)
        self.assertTrue(all("does not establish a skill deficit" in row["guidance"] for row in result["skills"]))
        self.assertNotIn("score", result)

    def test_negation_is_preserved_for_manual_review(self):
        result = build_comparison("SQL is not required. JavaScript is required. No experience with Java needed. Docker isn't required.", empty_snapshot(), "keyword")
        self.assertEqual([row["skill_key"] for row in result["skills"]], ["javascript"])
        self.assertEqual(len(result["manual_review"]), 3)

    def test_sql_guidance_distinguishes_correct_incorrect_and_unassessed(self):
        for answered, incorrect, unanswered, phrase in (
                (6, 0, 0, "answered correctly"), (5, 0, 1, "some questions remain unassessed"),
                (5, 2, 1, "practise the topics answered incorrectly"), (0, 0, 6, "entirely skipped")):
            snapshot = empty_snapshot()
            snapshot["sql_assessment"] = {"result": {"answered_count": answered, "incorrect_count": incorrect, "unanswered_count": unanswered}}
            result = build_comparison("SQL is required for this role.", snapshot, "keyword")
            self.assertIn(phrase, result["skills"][0]["guidance"])

    def test_preferred_heading_does_not_become_required(self):
        result = build_comparison("Requirements:\nPython\nPreferred skills:\nDocker\nResponsibilities:\nUse Git.", empty_snapshot(), "keyword")
        priorities = {row["skill_key"]: row["job_sources"][0]["importance"] for row in result["skills"]}
        self.assertEqual(priorities, {"python": "required", "docker": "optional", "git": "mentioned"})

    def test_unknown_text_and_candidate_tags_are_visible(self):
        snapshot = empty_snapshot()
        snapshot["skills"] = [{"id": 1, "skill_name": "Rust", "proficiency": 5}]
        result = build_comparison("Experience with Rust is required.", snapshot, "keyword")
        self.assertEqual(result["skills"], [])
        self.assertEqual(result["unmapped_candidate_tags"], ["Rust"])
        self.assertEqual(result["unassigned_fragments"], ["Experience with Rust is required."])

    def test_keyword_mode_does_not_load_semantic_model(self):
        with patch("services.job_matching.get_encoder", side_effect=AssertionError("Model must not run")):
            result = build_comparison("SQL is required for this role.", empty_snapshot(), "keyword")
        self.assertIsNone(result["model"])
        self.assertEqual(result["summary"]["semantic_suggestions"], 0)

    def test_fragment_limit_rejects_instead_of_silently_dropping_tail(self):
        with self.assertRaises(ValueError):
            fragments("\n".join(["Python"] * 61))
        result = fragments(" ".join(["word"] * 100) + " SQL")
        self.assertIn("SQL", result[-1]["text"])


class JobComparisonApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.headers = self.register("match-one@example.test")
        self.other = self.register("match-two@example.test")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register(self, email):
        account = {"name": "Matching Demo", "email": email, "password": "test-only-credential"}
        self.assertEqual(self.client.post("/api/register", json=account).status_code, 201)
        token = self.client.post("/api/login", json=account).get_json()["access_token"]
        return {"Authorization": "Bearer " + token}

    def payload(self, **changes):
        return {"submission_id": str(uuid4()), "title": "Python backend developer", "description": "Python, SQL and REST APIs are required. Docker is preferred.", "source_url": "", "mode": "keyword", **changes}

    def create(self, body=None):
        response = self.client.post("/api/job-matches", headers=self.headers, json=body or self.payload())
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["comparison"]

    def evidence(self):
        body = {"submission_id": str(uuid4()), "kind": "project", "title": "Python service", "description": "A demonstration web service.", "contribution": "I built and tested the API routes.", "source_url": "https://github.com/example/demo", "skills": ["Python", "REST APIs"]}
        return self.client.post("/api/evidence", headers=self.headers, json=body).get_json()["evidence"]

    def assessment(self, choices):
        started = self.client.post("/api/assessments/sql/attempts", headers=self.headers, json={}).get_json()["attempt"]
        body = {"answers": [{"question_id": q["id"], "option_id": option} for q, option in zip(QUESTIONS, choices)]}
        return self.client.post(f"/api/assessments/attempts/{started['id']}/submit", headers=self.headers, json=body).get_json()["attempt"]

    def test_authentication_and_owner_isolation(self):
        for method, path in [("GET", "/api/job-matches"), ("POST", "/api/job-matches"), ("GET", "/api/job-matches/metadata"), ("GET", f"/api/job-matches/{uuid4()}")]:
            self.assertEqual(self.client.open(path, method=method, json={}).status_code, 401)
        item = self.create()
        self.assertEqual(self.client.get("/api/job-matches", headers=self.other).get_json()["comparisons"], [])
        self.assertEqual(self.client.get(f"/api/job-matches/{item['id']}", headers=self.other).status_code, 404)

    def test_validation_and_client_score_or_profile_rejected(self):
        for body in ([], True, {}, {"score": 100}, {**self.payload(), "user_id": 2}, {**self.payload(), "candidate_snapshot": {}},
                     self.payload(mode=[]), self.payload(mode="trained"), self.payload(title=[]), self.payload(description="short"),
                     self.payload(description="x" * 8001), self.payload(source_url="javascript:alert(1)"), self.payload(submission_id="invalid")):
            self.assertEqual(self.client.post("/api/job-matches", headers=self.headers, json=body).status_code, 400, body)
        self.assertEqual(self.client.post("/api/job-matches", headers=self.headers, data="{", content_type="application/json").status_code, 400)

    def test_saved_snapshot_contains_only_owner_active_evidence(self):
        own = self.evidence()
        self.client.post("/api/skills", headers=self.headers, json={"skill_name": "SQL", "proficiency": 7})
        self.client.post("/api/skills", headers=self.other, json={"skill_name": "Java", "proficiency": 10})
        saved = self.create()
        self.assertEqual([item["id"] for item in saved["candidate_snapshot"]["evidence"]], [own["id"]])
        self.assertEqual([item["skill_name"] for item in saved["candidate_snapshot"]["skills"]], ["SQL"])
        rows = {row["skill_key"]: row for row in saved["result"]["skills"]}
        self.assertEqual(rows["python"]["candidate_claims"][0]["verification_status"], "unverified")
        self.client.patch(f"/api/evidence/{own['id']}/archive", headers=self.headers, json={"version": 1, "archived": True})
        self.assertEqual(self.create()["candidate_snapshot"]["evidence"], [])

    def test_snapshot_is_immutable_after_evidence_change_and_new_assessment(self):
        evidence = self.evidence()
        self.assessment(("b", "c", "a", "b", "b", None))
        saved = self.create()
        self.client.patch(f"/api/evidence/{evidence['id']}/archive", headers=self.headers, json={"version": 1, "archived": True})
        self.assessment((None,) * 6)
        path = f"/api/job-matches/{saved['id']}"
        self.assertEqual(self.client.get(path, headers=self.headers).get_json()["comparison"], saved)
        self.assertEqual(self.client.put(path, headers=self.headers, json={"score": 100}).status_code, 405)

    def test_latest_assessment_is_used_even_if_all_skipped(self):
        self.assessment(("b", "c", "d", "a", "b", "c"))
        latest = self.assessment((None,) * 6)
        saved = self.create()
        sql = next(row for row in saved["result"]["skills"] if row["skill_key"] == "sql")
        self.assertEqual(sql["assessment"]["attempt_id"], latest["id"])
        self.assertIsNone(sql["assessment"]["result"]["accuracy_on_answered_percent"])
        self.assertIn("entirely skipped", sql["guidance"])

    def test_creation_retry_returns_original_snapshot_without_rerunning(self):
        body = self.payload()
        saved = self.create(body)
        self.client.post("/api/skills", headers=self.headers, json={"skill_name": "Python", "proficiency": 8})
        with patch("routes.job_matches.build_comparison", side_effect=AssertionError("No rerun")):
            response = self.client.post("/api/job-matches", headers=self.headers, json=body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["comparison"], saved)
        self.assertEqual(self.client.post("/api/job-matches", headers=self.headers, json={**body, "title": "Changed"}).status_code, 409)
        with self.app.app_context():
            self.assertEqual(db.session.query(JobComparison).count(), 1)

    def test_missing_model_is_explicit_and_does_not_silently_fallback(self):
        with patch("services.job_matching.get_encoder", side_effect=SemanticUnavailable("Model unavailable")):
            response = self.client.post("/api/job-matches", headers=self.headers, json=self.payload(mode="semantic"))
        self.assertEqual(response.status_code, 503)
        self.assertIn("unavailable", response.get_json()["message"])
        with self.app.app_context():
            self.assertEqual(db.session.query(JobComparison).count(), 0)

    def test_list_summaries_and_no_store(self):
        item = self.create()
        response = self.client.get("/api/job-matches", headers=self.headers)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        summary = response.get_json()["comparisons"][0]
        self.assertEqual(summary["id"], item["id"])
        self.assertNotIn("candidate_snapshot", summary)
        metadata = self.client.get("/api/job-matches/metadata", headers=self.headers).get_json()
        self.assertEqual(len(metadata["skills"]), 10)

    def test_context_review_reasons_and_extraction_version_are_saved(self):
        saved = self.create(self.payload(description="Our company develops Python products. Responsibilities:\nUse HTTP/REST and Git."))
        result = saved['result']
        self.assertEqual({row['skill_key'] for row in result['skills']}, {'rest_api', 'git'})
        self.assertEqual(result['extraction_version'], EXTRACTION_VERSION)
        self.assertEqual(result['manual_review'][0]['reason_code'], 'company_context')
        self.assertEqual(self.client.get(f"/api/job-matches/{saved['id']}", headers=self.headers).get_json()['comparison'], saved)

    def test_comparison_does_not_change_assessment_or_roadmap(self):
        attempt = self.assessment(("b", "c", "a", "b", "b", None))
        path = f"/api/roadmaps/attempts/{attempt['id']}"
        roadmap = self.client.post(path, headers=self.headers, json={}).get_json()["roadmap"]
        self.create()
        self.assertEqual(self.client.get(f"/api/assessments/attempts/{attempt['id']}", headers=self.headers).get_json()["attempt"], attempt)
        self.assertEqual(self.client.get(path, headers=self.headers).get_json()["roadmap"], roadmap)


@unittest.skipUnless(model_status()["available"], "Optional semantic dependencies/model not installed; run setup_semantic_model.py")
class RealSemanticModelTests(unittest.TestCase):
    def test_real_embeddings_are_normalized_and_padding_invariant(self):
        encoder = get_encoder()
        texts = ["SQL queries", "Create HTTP endpoints with JSON requests and responses."]
        vectors = encoder.encode(texts)
        for vector in vectors:
            self.assertEqual(len(vector), 384)
            self.assertAlmostEqual(sum(value * value for value in vector), 1, places=5)
        alone = encoder.encode(texts[:1])[0]
        self.assertLess(max(abs(a - b) for a, b in zip(alone, vectors[0])), 1e-5)

    def test_real_model_adds_reviewable_suggestions_without_inventing_claims(self):
        text = "Write relational queries to combine tables and summarize records. Build web endpoints that accept JSON requests and return responses over HTTP."
        snapshot = empty_snapshot()
        lexical = build_comparison(text, snapshot, "keyword")
        semantic = build_comparison(text, snapshot, "semantic")
        self.assertEqual(lexical["skills"], [])
        self.assertEqual({row["skill_key"] for row in semantic["skills"]}, {"sql", "rest_api"})
        self.assertTrue(all(row["mapping"] == "semantic_suggestion" and row["candidate_claims"] == [] for row in semantic["skills"]))
        self.assertEqual(semantic["suggestion_policy"]["validation_status"], "heuristic_not_calibrated")


if __name__ == "__main__":
    unittest.main()
