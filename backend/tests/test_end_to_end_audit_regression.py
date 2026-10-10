"""
End-to-End Audit & Regression Tests for AI Career Navigator.
Specifically verifies:
1. Interview Simulator: No 405 Method Not Allowed on undefined/bare career paths or evaluate endpoints.
2. Interview Simulator: Verification of Beginner tier with 3 questions, answer submission, and rubric evaluation.
3. Resume ATS Parser: Public extraction, authenticated ATS scoring, and unauthenticated 401 guard.
4. Auth & Token Propagation: 7-day JWT expiration configuration and route aliases.
5. Learning Progress Contract: Schema consistency with both progress and progress_items.
"""

from datetime import timedelta
import json
import unittest
from flask_jwt_extended import create_access_token

from app import create_app
from extensions import db
from models.career import Career
from models.user import User


class EndToEndAuditRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            # Ensure at least one test user exists
            test_user = User.query.filter_by(email="audit_regression_user@example.com").first()
            if not test_user:
                test_user = User(
                    name="Audit Tester",
                    email="audit_regression_user@example.com",
                    password_hash="pbkdf2:sha256:dummyhash"
                )
                db.session.add(test_user)
                db.session.commit()
            cls.test_user_id = test_user.id
            cls.test_token = create_access_token(identity=str(cls.test_user_id))

    # --- 1. INTERVIEW SIMULATOR REGRESSIONS ---

    def test_interview_simulation_undefined_and_bare_alias(self):
        """Verify no 405 Method Not Allowed when career_id is undefined or omitted."""
        # 1. Bare alias
        res_bare = self.client.get("/api/careers/interview-simulation?difficulty=BEGINNER&question_count=3")
        self.assertEqual(res_bare.status_code, 200, f"Expected 200, got {res_bare.status_code}: {res_bare.data}")
        data_bare = res_bare.get_json()
        self.assertEqual(data_bare["status"], "success")
        self.assertIn("questions", data_bare)

        # 2. Undefined alias
        res_undef = self.client.get("/api/careers/undefined/interview-simulation?difficulty=BEGINNER&question_count=3")
        self.assertEqual(res_undef.status_code, 200, f"Expected 200, got {res_undef.status_code}: {res_undef.data}")
        data_undef = res_undef.get_json()
        self.assertEqual(data_undef["status"], "success")

        # 3. Bare evaluate alias
        eval_bare = self.client.post("/api/careers/interview-simulation/evaluate", json={
            "answers": [{"question_id": data_bare["questions"][0]["question_id"], "answer": "Sample answer."}],
            "difficulty": "BEGINNER"
        })
        self.assertEqual(eval_bare.status_code, 200, f"Expected 200, got {eval_bare.status_code}: {eval_bare.data}")

        # 4. Undefined evaluate alias
        eval_undef = self.client.post("/api/careers/undefined/interview-simulation/evaluate", json={
            "answers": [{"question_id": data_bare["questions"][0]["question_id"], "answer": "Sample answer."}],
            "difficulty": "BEGINNER"
        })
        self.assertEqual(eval_undef.status_code, 200, f"Expected 200, got {eval_undef.status_code}: {eval_undef.data}")

    def test_interview_simulation_beginner_three_questions_workflow(self):
        """Verify full interview lifecycle: 3 Beginner questions, answer submission, and rubric evaluation."""
        # 1. Start session with Beginner difficulty and 3 questions for Career 1
        res = self.client.get("/api/careers/1/interview-simulation?difficulty=BEGINNER&question_count=3")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        questions = data.get("questions", [])
        self.assertEqual(len(questions), 3, f"Expected exactly 3 questions, got {len(questions)}")

        # Verify question structure
        answers_payload = []
        for q in questions:
            self.assertIn("question_id", q)
            self.assertIn("question_text", q)
            self.assertIn("difficulty", q)
            self.assertEqual(q["difficulty"], "BEGINNER")
            answers_payload.append({
                "question_id": q["question_id"],
                "answer": "We utilize standard object-oriented programming principles, modular functions, and robust unit testing."
            })

        # 2. Submit answers for evaluation
        eval_res = self.client.post("/api/careers/1/interview-simulation/evaluate", json={
            "answers": answers_payload,
            "difficulty": "BEGINNER"
        })
        self.assertEqual(eval_res.status_code, 200)
        eval_data = eval_res.get_json()
        self.assertEqual(eval_data["status"], "success")
        self.assertIn("overall_readiness", eval_data)
        self.assertIn("question_results", eval_data)
        self.assertEqual(len(eval_data["question_results"]), 3)

    # --- 2. RESUME ATS PARSER REGRESSIONS ---

    def test_resume_extraction_public(self):
        """Verify resume extraction is public and returns parsed canonical skills."""
        res = self.client.post("/api/skills/extract-resume", json={
            "resume_text": "Experienced Python Software Engineer skilled in Flask, Docker, PostgreSQL, and Git."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("auto_matched_skills", data)
        self.assertGreater(data.get("auto_matched_count", 0), 0)

    def test_resume_ats_unauthenticated_returns_401(self):
        """Verify ATS scoring endpoint requires authentication and returns 401 for guests."""
        res = self.client.post("/api/skills/extract-resume/score?career_id=1", json={
            "resume_text": "Experienced Python Software Engineer skilled in Flask, Docker, PostgreSQL, and Git."
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertIn("msg", data)

    def test_resume_ats_authenticated_returns_200(self):
        """Verify ATS scoring endpoint succeeds with 200 when authenticated."""
        res = self.client.post(
            "/api/skills/extract-resume/score?career_id=1",
            headers={"Authorization": f"Bearer {self.test_token}"},
            json={"resume_text": "Experienced Python Software Engineer skilled in Flask, Docker, PostgreSQL, and Git."}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("ats_score", data)
        self.assertIn("alignment_level", data)
        self.assertIn("matched_keywords", data)
        self.assertIn("missing_keywords", data)

    # --- 3. CONFIGURATION & SCHEMA CONTRACT REGRESSIONS ---

    def test_jwt_access_token_expires_configured_to_seven_days(self):
        """Verify JWT_ACCESS_TOKEN_EXPIRES is set to 7 days to prevent session expiration."""
        expiry = self.app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
        self.assertEqual(expiry, timedelta(days=7))

    def test_learning_resources_progress_contract_dual_keys(self):
        """Verify learning resources progress returns both 'progress' and 'progress_items'."""
        res = self.client.get(
            "/api/learning-resources/progress",
            headers={"Authorization": f"Bearer {self.test_token}"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("progress", data)
        self.assertIn("progress_items", data)


if __name__ == "__main__":
    unittest.main()
