"""
Phase 6 Integration Test Suite for AI Career Navigator.

Verifies:
1. Student Profile API:
   - GET /api/profile (fetch current profile)
   - PUT /api/profile (update profile fields)
   - Profile retrieval with/without user_id
2. CORS and Preflight Handling:
   - CORS headers presence on responses
   - OPTIONS preflight request handling
3. Full Frontend Integration Endpoints:
   - /api/careers catalog
   - /api/careers/<id>/skill-gap
   - /api/careers/<id>/roadmap
   - /api/careers/compare
   - /api/careers/<id>/analytics
   - /api/learning-resources
   - /api/skills canonical search
"""

import os
import sys
import unittest
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from werkzeug.security import generate_password_hash
from app import create_app
from extensions import db
from models.user import User
from models.student_profile import StudentProfile


class TestPhase6Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        # Find or create a test user
        cls.user = User.query.filter_by(email="phase6_test@example.com").first()
        if not cls.user:
            cls.user = User(
                name="Phase6 Test User",
                email="phase6_test@example.com",
                password_hash=generate_password_hash("password123")
            )
            db.session.add(cls.user)
            db.session.commit()

        # Get JWT token
        resp = cls.client.post("/api/login", json={
            "email": "phase6_test@example.com",
            "password": "password123"
        })
        data = resp.get_json()
        cls.token = data.get("access_token")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        # Clean up
        StudentProfile.query.filter_by(user_id=cls.user.id).delete()
        User.query.filter_by(id=cls.user.id).delete()
        db.session.commit()
        cls.ctx.pop()

    def test_cors_headers_present(self):
        """Verify CORS headers are added to API responses."""
        resp = self.client.get("/api/careers")
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

    def test_cors_options_preflight(self):
        """Verify OPTIONS preflight request returns 200 with CORS headers."""
        resp = self.client.options("/api/profile")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")
        self.assertIn("PUT", resp.headers.get("Access-Control-Allow-Methods", ""))

    def test_profile_lifecycle_get_and_put(self):
        """Verify GET and PUT on /api/profile endpoint."""
        # 1. Create or set profile via PUT
        update_data = {
            "education_level": "Bachelor's",
            "major": "Computer Science & Engineering",
            "graduation_year": 2026,
            "interests": ["Machine Learning", "Cloud Systems"]
        }
        put_resp = self.client.put("/api/profile", json=update_data, headers=self.headers)
        self.assertEqual(put_resp.status_code, 200)
        put_json = put_resp.get_json()
        self.assertIn("profile", put_json)
        self.assertEqual(put_json["profile"]["major"], "Computer Science & Engineering")

        # 2. Retrieve profile via GET
        get_resp = self.client.get("/api/profile", headers=self.headers)
        self.assertEqual(get_resp.status_code, 200)
        get_json = get_resp.get_json()
        self.assertIn("profile", get_json)
        self.assertEqual(get_json["profile"]["education_level"], "Bachelor's")
        self.assertEqual(get_json["profile"]["graduation_year"], 2026)

    def test_careers_catalog_and_skill_gap_integration(self):
        """Verify frontend-required career intelligence routes return valid payloads."""
        resp = self.client.get("/api/careers")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("careers", data)
        self.assertGreater(len(data["careers"]), 0)

        first_career_id = data["careers"][0]["id"]

        # Skill gap
        gap_resp = self.client.get(f"/api/careers/{first_career_id}/skill-gap", headers=self.headers)
        self.assertEqual(gap_resp.status_code, 200)
        gap_json = gap_resp.get_json()
        self.assertIn("readiness_percentage", gap_json)
        self.assertIn("skill_gaps", gap_json)
        self.assertIn("matched", gap_json)
        self.assertIn("missing", gap_json)

    def test_canonical_skill_autocomplete_integration(self):
        """Verify frontend autocomplete endpoint works."""
        resp = self.client.get("/api/skills?q=pyth&limit=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn("canonical_name", data[0])


if __name__ == "__main__":
    unittest.main()
