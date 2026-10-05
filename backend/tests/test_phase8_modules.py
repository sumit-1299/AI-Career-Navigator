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
from services.roadmap_service import RoadmapService, generate_learning_roadmap
from services.readiness_summary_service import ReadinessSummaryService


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


class TestPhase8Module83StudyPlan(unittest.TestCase):
    """Test suite for Phase 8 Module 8.3 Structured Weekly Study Plan & Completion Timeline Calculator."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        cls.user = User.query.filter_by(email="phase8_test@example.com").first()
        if not cls.user:
            cls.user = User(
                name="Phase8 Test User",
                email="phase8_test@example.com",
                password_hash=generate_password_hash("password123")
            )
            db.session.add(cls.user)
            db.session.commit()

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

    def test_study_plan_5_hours_per_week(self):
        """Test study plan calculation at 5 hours/week intensity."""
        sample_steps = [
            {"step_number": 1, "skill_name": "Python", "estimated_hours": 25},
            {"step_number": 2, "skill_name": "SQL", "estimated_hours": 15},
        ]
        plan = RoadmapService.calculate_study_plan(sample_steps, hours_per_week=5)
        self.assertEqual(plan["hours_per_week"], 5)
        self.assertEqual(plan["estimated_total_hours"], 40)
        self.assertEqual(plan["estimated_weeks"], 8)
        self.assertEqual(len(plan["weekly_milestones"]), 8)
        total_target = sum(m["target_hours"] for m in plan["weekly_milestones"])
        self.assertEqual(total_target, 40)

    def test_study_plan_10_hours_per_week(self):
        """Test study plan calculation at 10 hours/week intensity."""
        sample_steps = [
            {"step_number": 1, "skill_name": "Python", "estimated_hours": 25},
            {"step_number": 2, "skill_name": "SQL", "estimated_hours": 15},
        ]
        plan = RoadmapService.calculate_study_plan(sample_steps, hours_per_week=10)
        self.assertEqual(plan["hours_per_week"], 10)
        self.assertEqual(plan["estimated_total_hours"], 40)
        self.assertEqual(plan["estimated_weeks"], 4)
        self.assertEqual(len(plan["weekly_milestones"]), 4)

    def test_study_plan_20_hours_per_week(self):
        """Test study plan calculation at 20 hours/week intensity."""
        sample_steps = [
            {"step_number": 1, "skill_name": "Python", "estimated_hours": 25},
            {"step_number": 2, "skill_name": "SQL", "estimated_hours": 15},
        ]
        plan = RoadmapService.calculate_study_plan(sample_steps, hours_per_week=20)
        self.assertEqual(plan["hours_per_week"], 20)
        self.assertEqual(plan["estimated_total_hours"], 40)
        self.assertEqual(plan["estimated_weeks"], 2)
        self.assertEqual(len(plan["weekly_milestones"]), 2)

    def test_study_plan_math_ceil_rounding(self):
        """Test that completion weeks rounds up via math.ceil (e.g. 25 hrs @ 10 hrs/wk -> 3 weeks)."""
        sample_steps = [
            {"step_number": 1, "skill_name": "Python", "estimated_hours": 25},
        ]
        plan = RoadmapService.calculate_study_plan(sample_steps, hours_per_week=10)
        self.assertEqual(plan["estimated_weeks"], 3)
        self.assertEqual(len(plan["weekly_milestones"]), 3)
        self.assertEqual(plan["weekly_milestones"][0]["target_hours"], 10)
        self.assertEqual(plan["weekly_milestones"][1]["target_hours"], 10)
        self.assertEqual(plan["weekly_milestones"][2]["target_hours"], 5)

    def test_study_plan_completion_date_format(self):
        """Test that estimated_completion_date is a valid ISO date YYYY-MM-DD in the future."""
        sample_steps = [
            {"step_number": 1, "skill_name": "Docker", "estimated_hours": 20},
        ]
        plan = RoadmapService.calculate_study_plan(sample_steps, hours_per_week=10)
        date_str = plan["estimated_completion_date"]
        self.assertRegex(date_str, r"^\d{4}-\d{2}-\d{2}$")

    def test_study_plan_zero_hours_or_empty_steps(self):
        """Test edge case when student has 0 gaps (empty steps / 0 hours)."""
        plan = RoadmapService.calculate_study_plan([], hours_per_week=10)
        self.assertEqual(plan["estimated_total_hours"], 0)
        self.assertEqual(plan["estimated_weeks"], 0)
        self.assertEqual(plan["weekly_milestones"], [])
        self.assertRegex(plan["estimated_completion_date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_study_plan_invalid_non_positive_hours_raises_error(self):
        """Test that non-positive hours_per_week raises ValueError."""
        with self.assertRaises(ValueError):
            RoadmapService.calculate_study_plan([], hours_per_week=0)
        with self.assertRaises(ValueError):
            RoadmapService.calculate_study_plan([], hours_per_week=-5)

    def test_api_roadmap_with_valid_hours_per_week(self):
        """API Test: GET /api/careers/1/roadmap?hours_per_week=10 returns study plan metrics."""
        resp = self.client.get("/api/careers/1/roadmap?hours_per_week=10", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["hours_per_week"], 10)
        self.assertIn("estimated_total_hours", data)
        self.assertIn("estimated_weeks", data)
        self.assertIn("estimated_completion_date", data)
        self.assertIn("weekly_milestones", data)
        self.assertGreater(data["estimated_total_hours"], 0)
        self.assertGreater(data["estimated_weeks"], 0)
        self.assertIsInstance(data["weekly_milestones"], list)

    def test_api_roadmap_backward_compatibility_omitted_param(self):
        """Backward Compatibility: GET /api/careers/1/roadmap without hours_per_week succeeds."""
        resp = self.client.get("/api/careers/1/roadmap", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["career_id"], 1)
        self.assertIn("roadmap", data)
        self.assertNotIn("hours_per_week", data)

    def test_api_roadmap_invalid_zero_hours_returns_400(self):
        """Validation: hours_per_week=0 returns 400 Bad Request."""
        resp = self.client.get("/api/careers/1/roadmap?hours_per_week=0", headers=self.headers)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data["status"], "error")

    def test_api_roadmap_invalid_negative_hours_returns_400(self):
        """Validation: negative hours_per_week returns 400 Bad Request."""
        resp = self.client.get("/api/careers/1/roadmap?hours_per_week=-10", headers=self.headers)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data["status"], "error")

    def test_api_roadmap_invalid_non_numeric_hours_returns_400(self):
        """Validation: non-numeric hours_per_week returns 400 Bad Request."""
        resp = self.client.get("/api/careers/1/roadmap?hours_per_week=fast", headers=self.headers)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data["status"], "error")

    def test_api_roadmap_unsupported_intensity_returns_400(self):
        """Validation: unsupported intensities (e.g. 7 or 15) return 400 Bad Request."""
        for unsupported in [7, 15, 30]:
            resp = self.client.get(f"/api/careers/1/roadmap?hours_per_week={unsupported}", headers=self.headers)
            self.assertEqual(resp.status_code, 400)
            data = resp.get_json()
            self.assertEqual(data["status"], "error")


class TestPhase8Module84ReadinessReport(unittest.TestCase):
    """Test suite for Phase 8 Module 8.4 Placement-Ready Career Readiness Summary & Report View."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        cls.user = User.query.filter_by(email="phase8_test@example.com").first()
        if not cls.user:
            cls.user = User(
                name="Phase8 Test User",
                email="phase8_test@example.com",
                password_hash=generate_password_hash("password123")
            )
            db.session.add(cls.user)
            db.session.commit()

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

    def test_service_generate_summary_structure(self):
        """Service Test: verify all required sections in readiness summary report."""
        summary = ReadinessSummaryService.generate_readiness_summary(
            career_id=1,
            user_id=self.user.id,
            hours_per_week=10
        )
        self.assertIsNotNone(summary)
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["career_id"], 1)
        self.assertEqual(summary["career_title"], "Software Developer")
        self.assertEqual(summary["career_category"], "Software Development")

        # 1. Overall readiness
        self.assertIn("overall_readiness", summary)
        self.assertIn("percentage", summary["overall_readiness"])
        self.assertIn("category", summary["overall_readiness"])

        # 2. Competencies & gaps
        self.assertIn("verified_skills", summary)
        self.assertIn("remaining_skill_gaps", summary)
        self.assertIn("missing", summary["remaining_skill_gaps"])
        self.assertIn("weak", summary["remaining_skill_gaps"])

        # 3. ATS alignment
        self.assertIn("ats_alignment", summary)
        self.assertIn("alignment_level", summary["ats_alignment"])

        # 4. Study timeline
        self.assertIn("study_timeline", summary)
        self.assertEqual(summary["study_timeline"]["hours_per_week"], 10)
        self.assertGreater(summary["study_timeline"]["estimated_total_hours"], 0)
        self.assertGreater(summary["study_timeline"]["estimated_weeks"], 0)

        # 5. Portfolio recommendations
        self.assertIn("portfolio_recommendations", summary)
        self.assertIsInstance(summary["portfolio_recommendations"], list)
        self.assertGreater(len(summary["portfolio_recommendations"]), 0)

        # 6. Market outlook
        self.assertIn("market_outlook", summary)
        self.assertIn("demand_level", summary["market_outlook"])
        self.assertIn("salary_bands", summary["market_outlook"])

        # 7. Placement summary
        self.assertIn("placement_summary", summary)
        self.assertIn("tier", summary["placement_summary"])
        self.assertIn("verdict", summary["placement_summary"])
        self.assertIn("action_plan", summary["placement_summary"])

    def test_service_study_intensity_variations(self):
        """Service Test: verify 5 vs 20 hrs/week intensity alters timeline weeks."""
        summary_5 = ReadinessSummaryService.generate_readiness_summary(career_id=1, hours_per_week=5)
        summary_20 = ReadinessSummaryService.generate_readiness_summary(career_id=1, hours_per_week=20)
        self.assertEqual(summary_5["study_timeline"]["hours_per_week"], 5)
        self.assertEqual(summary_20["study_timeline"]["hours_per_week"], 20)
        self.assertGreater(summary_5["study_timeline"]["estimated_weeks"], summary_20["study_timeline"]["estimated_weeks"])

    def test_service_with_resume_text_ats_scoring(self):
        """Service Test: providing resume_text calculates live ATS score."""
        resume = "Software developer proficient in Python, SQL, and Git version control."
        summary = ReadinessSummaryService.generate_readiness_summary(
            career_id=1,
            hours_per_week=10,
            resume_text=resume
        )
        self.assertTrue(summary["ats_alignment"]["is_scored"])
        self.assertGreater(summary["ats_alignment"]["ats_score"], 0)
        self.assertIn("Python", summary["ats_alignment"]["matched_keywords"])

    def test_service_invalid_hours_raises_error(self):
        """Service Test: invalid study intensity raises ValueError."""
        with self.assertRaises(ValueError):
            ReadinessSummaryService.generate_readiness_summary(career_id=1, hours_per_week=7)

    def test_service_invalid_career_returns_none(self):
        """Service Test: non-existent career returns None."""
        summary = ReadinessSummaryService.generate_readiness_summary(career_id=999999)
        self.assertIsNone(summary)

    def test_api_readiness_summary_get_200(self):
        """API Test: GET /api/careers/1/readiness-summary returns HTTP 200 with all required sections."""
        resp = self.client.get("/api/careers/1/readiness-summary", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["career_id"], 1)
        self.assertIn("overall_readiness", data)
        self.assertIn("placement_summary", data)
        self.assertIn("study_timeline", data)
        self.assertIn("market_outlook", data)
        self.assertIn("portfolio_recommendations", data)

    def test_api_readiness_summary_intensity_param(self):
        """API Test: GET /api/careers/1/readiness-summary?hours_per_week=20 returns 20 hrs timeline."""
        resp = self.client.get("/api/careers/1/readiness-summary?hours_per_week=20", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["study_timeline"]["hours_per_week"], 20)

    def test_api_readiness_summary_invalid_intensity_400(self):
        """API Test: invalid hours_per_week returns HTTP 400 Bad Request."""
        resp = self.client.get("/api/careers/1/readiness-summary?hours_per_week=15", headers=self.headers)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertEqual(data["status"], "error")

    def test_api_readiness_summary_post_with_resume(self):
        """API Test: POST /api/careers/1/readiness-summary with resume_text calculates ATS score."""
        payload = {
            "hours_per_week": 10,
            "resume_text": "Experienced Python engineer with SQL and Git knowledge"
        }
        resp = self.client.post("/api/careers/1/readiness-summary", json=payload, headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["ats_alignment"]["is_scored"])
        self.assertIn("Python", data["ats_alignment"]["matched_keywords"])

    def test_api_readiness_summary_invalid_career_404(self):
        """API Test: non-existent career returns HTTP 404 Not Found."""
        resp = self.client.get("/api/careers/999999/readiness-summary", headers=self.headers)
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertEqual(data["status"], "error")

    def test_api_protected_endpoints_backward_compatibility(self):
        """Backward Compatibility: existing career endpoints remain intact."""
        # 1. Skill gap endpoint
        resp_gap = self.client.get("/api/careers/1/skill-gap", headers=self.headers)
        self.assertEqual(resp_gap.status_code, 200)

        # 2. Roadmap endpoint
        resp_road = self.client.get("/api/careers/1/roadmap", headers=self.headers)
        self.assertEqual(resp_road.status_code, 200)

        # 3. Analytics endpoint
        resp_ana = self.client.get("/api/careers/1/analytics", headers=self.headers)
        self.assertEqual(resp_ana.status_code, 200)


if __name__ == "__main__":
    unittest.main()


