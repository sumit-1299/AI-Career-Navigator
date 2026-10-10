"""
Regression tests for Learning Pathways contract, duplicate boost prevention,
undefined route fallbacks, and global API 405 error handling.
"""

import unittest
from datetime import datetime
from flask_jwt_extended import create_access_token

from app import create_app
from extensions import db
from models.user import User
from models.canonical_skill import CanonicalSkill
from models.learning_resource import LearningResource
from models.user_learning_progress import UserLearningProgress
from models.skill import Skill
from services.learning_progress_service import LearningProgressService


class TestLearningPathwaysContractRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            # Setup or get test user
            user = User.query.filter_by(email="linux_regression_learner@test.com").first()
            if not user:
                user = User(
                    name="Linux Regression Learner",
                    email="linux_regression_learner@test.com",
                    password_hash="pbkdf2:sha256:dummyhash"
                )
                db.session.add(user)
                db.session.commit()
            cls.test_user_id = user.id

            # Ensure Linux canonical skill exists
            linux_skill = CanonicalSkill.query.filter_by(canonical_name="Linux").first()
            if not linux_skill:
                linux_skill = CanonicalSkill(
                    canonical_name="Linux",
                    skill_type="technical"
                )
                db.session.add(linux_skill)
                db.session.commit()
            cls.linux_skill_id = linux_skill.id

            # Ensure Introduction to Linux (LFS101x) exists
            linux_course = LearningResource.query.filter_by(title="Introduction to Linux (LFS101x)").first()
            if not linux_course:
                linux_course = LearningResource(
                    canonical_skill_id=linux_skill.id,
                    title="Introduction to Linux (LFS101x)",
                    resource_type="Course",
                    provider="edX / Linux Foundation",
                    url="https://www.edx.org/learn/linux/the-linux-foundation-introduction-to-linux",
                    difficulty_level="Beginner",
                    estimated_duration="14 hours",
                    description="Develop a good working knowledge of Linux using both the graphical interface and command line.",
                    certification_available=True,
                    status="Active"
                )
                db.session.add(linux_course)
                db.session.commit()
            cls.linux_course_id = linux_course.id

            with cls.app.test_request_context():
                cls.token = create_access_token(identity=str(cls.test_user_id))

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        # Clear any prior progress records for this test user
        UserLearningProgress.query.filter_by(user_id=self.test_user_id).delete()
        # Clear any student skill for Linux
        Skill.query.filter_by(user_id=self.test_user_id, canonical_skill_id=self.linux_skill_id).delete()
        db.session.commit()

    def tearDown(self):
        UserLearningProgress.query.filter_by(user_id=self.test_user_id).delete()
        Skill.query.filter_by(user_id=self.test_user_id, canonical_skill_id=self.linux_skill_id).delete()
        db.session.commit()
        self.ctx.pop()

    def test_curated_catalog_loading_and_canonical_skill_name(self):
        """Test GET /api/learning-resources returns status 200 with canonical_skill_name."""
        res = self.client.get("/api/learning-resources")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "application/json")
        data = res.get_json()
        self.assertIn("resources", data)
        self.assertGreaterEqual(len(data["resources"]), 1)
        found = any(
            r["title"] == "Introduction to Linux (LFS101x)" and r["canonical_skill_name"] == "Linux"
            for r in data["resources"]
        )
        self.assertTrue(found, "Introduction to Linux (LFS101x) with canonical_skill_name Linux must exist in catalog")

    def test_dual_contract_keys_in_progress_model(self):
        """Test UserLearningProgress.to_dict() provides both resource_id and learning_resource_id."""
        progress = UserLearningProgress(
            user_id=self.test_user_id,
            learning_resource_id=self.linux_course_id,
            canonical_skill_id=self.linux_skill_id,
            status="In Progress",
            progress_percentage=45.0,
            notes="Completed module 3"
        )
        db.session.add(progress)
        db.session.commit()

        data = progress.to_dict()
        self.assertEqual(data["resource_id"], self.linux_course_id)
        self.assertEqual(data["learning_resource_id"], self.linux_course_id)
        self.assertEqual(data["resource"]["id"], self.linux_course_id)
        self.assertEqual(data["progress_percentage"], 45.0)

    def test_update_learning_progress_via_put(self):
        """Test PUT /api/learning-resources/<id>/progress updates progress percentage and notes."""
        start_res = self.client.post(
            f"/api/learning-resources/{self.linux_course_id}/start",
            headers=self.headers
        )
        self.assertEqual(start_res.status_code, 200)

        # Update progress via PUT
        update_res = self.client.put(
            f"/api/learning-resources/{self.linux_course_id}/progress",
            headers=self.headers,
            json={"progress_percentage": 65.5, "notes": "Halfway through labs"}
        )
        self.assertEqual(update_res.status_code, 200)
        up_data = update_res.get_json()
        self.assertEqual(up_data["status"], "success")
        self.assertEqual(up_data["progress"]["progress_percentage"], 65.5)
        self.assertEqual(up_data["progress"]["notes"], "Halfway through labs")

        # Verify persistence via GET /api/learning-resources/progress
        get_res = self.client.get("/api/learning-resources/progress", headers=self.headers)
        self.assertEqual(get_res.status_code, 200)
        prog_list = get_res.get_json()["progress"]
        enrolled = [p for p in prog_list if p["learning_resource_id"] == self.linux_course_id]
        self.assertEqual(len(enrolled), 1)
        self.assertEqual(enrolled[0]["progress_percentage"], 65.5)
        self.assertEqual(enrolled[0]["resource_id"], self.linux_course_id)

    def test_complete_and_boost_lifecycle(self):
        """Test POST /api/learning-resources/<id>/complete sets status to Completed and boosts skill proficiency."""
        comp_res = self.client.post(
            f"/api/learning-resources/{self.linux_course_id}/complete",
            headers=self.headers
        )
        self.assertEqual(comp_res.status_code, 200)
        comp_data = comp_res.get_json()
        self.assertEqual(comp_data["status"], "success")
        self.assertEqual(comp_data["progress"]["status"], "Completed")
        self.assertEqual(comp_data["progress"]["progress_percentage"], 100.0)
        self.assertIsNotNone(comp_data.get("skill_boost"))
        self.assertFalse(comp_data["skill_boost"]["duplicate_boost_prevented"])

        # Check student skill in DB
        user_skill = Skill.query.filter_by(
            user_id=self.test_user_id,
            canonical_skill_id=self.linux_skill_id
        ).first()
        self.assertIsNotNone(user_skill)
        self.assertGreaterEqual(user_skill.proficiency, 1)

    def test_duplicate_boost_prevention(self):
        """Calling complete a second time must NOT repeatedly increment skill proficiency."""
        first_comp = self.client.post(
            f"/api/learning-resources/{self.linux_course_id}/complete",
            headers=self.headers
        )
        self.assertEqual(first_comp.status_code, 200)
        initial_skill = Skill.query.filter_by(
            user_id=self.test_user_id,
            canonical_skill_id=self.linux_skill_id
        ).first()
        prof_after_first = initial_skill.proficiency

        second_comp = self.client.post(
            f"/api/learning-resources/{self.linux_course_id}/complete",
            headers=self.headers
        )
        self.assertEqual(second_comp.status_code, 200)
        sec_data = second_comp.get_json()
        self.assertTrue(sec_data["skill_boost"]["duplicate_boost_prevented"])
        self.assertEqual(sec_data["skill_boost"]["action"], "already_boosted")

        skill_after_second = Skill.query.filter_by(
            user_id=self.test_user_id,
            canonical_skill_id=self.linux_skill_id
        ).first()
        self.assertEqual(skill_after_second.proficiency, prof_after_first)

    def test_undefined_resource_id_fallback_routes(self):
        """Explicitly calling undefined routes returns 400 Bad Request JSON, not 405 HTML."""
        routes = [
            ("POST", "/api/learning-resources/undefined/start"),
            ("PUT", "/api/learning-resources/undefined/progress"),
            ("POST", "/api/learning-resources/undefined/complete"),
        ]
        for method, route in routes:
            if method == "POST":
                res = self.client.post(route, headers=self.headers, json={})
            elif method == "PUT":
                res = self.client.put(route, headers=self.headers, json={"progress_percentage": 50})
            self.assertEqual(res.status_code, 400, f"Expected 400 for {method} {route}, got {res.status_code}")
            self.assertEqual(res.content_type, "application/json")
            data = res.get_json()
            self.assertEqual(data["status"], "error")
            self.assertIn("undefined", data["message"].lower())

    def test_global_405_json_error_handler(self):
        """Disallowed HTTP methods on /api/* routes must return JSON with status error, never Werkzeug HTML."""
        res = self.client.get(f"/api/learning-resources/{self.linux_course_id}/complete")
        self.assertEqual(res.status_code, 405)
        self.assertEqual(res.content_type, "application/json")
        data = res.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("405", data["message"])

    def test_linux_course_full_lifecycle(self):
        """End-to-end lifecycle verification for Introduction to Linux (LFS101x)."""
        res_start = self.client.post(
            f"/api/learning-resources/{self.linux_course_id}/start",
            headers=self.headers
        )
        self.assertEqual(res_start.status_code, 200)
        start_dict = res_start.get_json()["progress"]
        self.assertEqual(start_dict["status"], "In Progress")

        res_up = self.client.put(
            f"/api/learning-resources/{self.linux_course_id}/progress",
            headers=self.headers,
            json={"progress_percentage": 50.0, "notes": "Mid-course check"}
        )
        self.assertEqual(res_up.status_code, 200)
        self.assertEqual(res_up.get_json()["progress"]["progress_percentage"], 50.0)

        res_comp = self.client.post(
            f"/api/learning-resources/{self.linux_course_id}/complete",
            headers=self.headers
        )
        self.assertEqual(res_comp.status_code, 200)
        comp_dict = res_comp.get_json()["progress"]
        self.assertEqual(comp_dict["status"], "Completed")
        self.assertEqual(comp_dict["progress_percentage"], 100.0)


if __name__ == "__main__":
    unittest.main()
