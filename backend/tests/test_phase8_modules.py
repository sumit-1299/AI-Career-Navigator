"""
Unit and Integration Tests for Phase 8 Module 8.2 in AI Career Navigator.

Covers:
- Resume-to-Career ATS Matching & Alignment Scoring service logic
- POST /api/skills/extract-resume/score API endpoint
- Backward compatibility of POST /api/skills/extract-resume
"""

import unittest
from werkzeug.security import generate_password_hash
from app import create_app
from extensions import db
from models.user import User
from models.career import Career
from services.resume_extraction_service import ResumeExtractionService


class TestPhase8Module82ATSScoring(unittest.TestCase):
    """Test suite for Resume-to-Career ATS Matching & Alignment Scoring."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        # Find or create a test user
        cls.user = User.query.filter_by(email="phase8_test@example.com").first()
        if not cls.user:
            cls.user = User(
                name="Phase8 Test User",
                email="phase8_test@example.com",
                password_hash=generate_password_hash("password123")
            )
            db.session.add(cls.user)
            db.session.commit()

        # Login to obtain JWT
        resp = cls.client.post("/api/login", json={
            "email": "phase8_test@example.com",
            "password": "password123"
        })
        data = resp.get_json()
        cls.token = data.get("access_token")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_service_score_matching_career(self):
        """Test 1 (Service): Resume matching Software Developer (Python, Git, SQL)."""
        resume_text = (
            "Senior Backend Engineer\n"
            "Technical Skills: Python, Git version control, SQL database design, PostgreSQL.\n"
            "Experience: Built microservices and automated testing pipelines."
        )
        result = ResumeExtractionService.score_resume_against_career(
            resume_text=resume_text,
            career_id=1  # Software Developer (requires: Python, Java, Data Structures, Git, SQL)
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["career_id"], 1)
        self.assertGreater(result["ats_score"], 40)
        self.assertIn("Python", result["matched_keywords"])
        self.assertIn("Git", result["matched_keywords"])
        self.assertIn("SQL", result["matched_keywords"])
        self.assertIn(result["alignment_level"], ["Strong", "Excellent", "Moderate"])

    def test_service_score_mismatched_career(self):
        """Test 2 (Service): Resume with unrelated skills scored against Cloud Engineer."""
        # Cloud Engineer requires: Linux, Networking, AWS, Python, Docker
        resume_text = (
            "UI / UX Graphic Designer\n"
            "Skills: Figma, Adobe Photoshop, User Research, Wireframing, Typography."
        )
        result = ResumeExtractionService.score_resume_against_career(
            resume_text=resume_text,
            career_id=6  # Cloud Engineer
        )
        self.assertIsNotNone(result)
        self.assertLess(result["ats_score"], 40)
        self.assertEqual(result["alignment_level"], "Weak")
        self.assertIn("AWS", result["missing_keywords"])
        self.assertIn("Docker", result["missing_keywords"])
        self.assertIn("Linux", result["missing_keywords"])

    def test_service_missing_resume_raises_value_error(self):
        """Test 3 (Service): Empty or whitespace resume raises ValueError."""
        with self.assertRaises(ValueError):
            ResumeExtractionService.score_resume_against_career(
                resume_text="",
                career_id=1
            )
        with self.assertRaises(ValueError):
            ResumeExtractionService.score_resume_against_career(
                resume_text="   \n  ",
                career_id=1
            )

    def test_service_invalid_career_returns_none(self):
        """Test 4 (Service): Non-existent career ID returns None."""
        result = ResumeExtractionService.score_resume_against_career(
            resume_text="Python and SQL developer",
            career_id=999999
        )
        self.assertIsNone(result)

    def test_api_score_matching_career_with_jwt(self):
        """API Test: POST /api/skills/extract-resume/score?career_id=1 returns valid ATS score."""
        payload = {
            "resume_text": "Experienced engineer skilled in Python, Java, Git, and SQL."
        }
        resp = self.client.post(
            "/api/skills/extract-resume/score?career_id=1",
            json=payload,
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("ats_score", data)
        self.assertIn("matched_keywords", data)
        self.assertIn("missing_keywords", data)
        self.assertIn("alignment_level", data)
        self.assertGreaterEqual(data["ats_score"], 60)
        self.assertIn("Python", data["matched_keywords"])
        self.assertIn("Git", data["matched_keywords"])

    def test_api_score_invalid_career_returns_404(self):
        """API Test: Scoring against non-existent career returns 404."""
        resp = self.client.post(
            "/api/skills/extract-resume/score?career_id=999999",
            json={"resume_text": "Python and SQL"},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 404)

    def test_api_score_missing_resume_returns_400(self):
        """API Test: Missing resume_text returns 400."""
        resp = self.client.post(
            "/api/skills/extract-resume/score?career_id=1",
            json={},
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 400)

    def test_api_score_unauthenticated_returns_401(self):
        """API Test: Unauthenticated request returns 401."""
        resp = self.client.post(
            "/api/skills/extract-resume/score?career_id=1",
            json={"resume_text": "Python developer"}
        )
        self.assertEqual(resp.status_code, 401)

    def test_api_backward_compatibility_extract_resume(self):
        """Backward Compatibility: POST /api/skills/extract-resume still functions as expected."""
        resp = self.client.post(
            "/api/skills/extract-resume",
            json={"resume_text": "Software engineer with Python and Docker experience"}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("detected_skills", data)
        self.assertGreaterEqual(data["detected_skills_count"], 1)


if __name__ == "__main__":
    unittest.main()
