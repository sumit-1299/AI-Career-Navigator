"""
Unit and Integration Tests for Phase 9 Module 9.1 in AI Career Navigator.

Covers:
- Multi-factor recommendation scoring formula (50% Skill, 20% Preference, 15% Market, 15% Academic)
- Factor breakdown and explainability justification generation
- Resume ATS blending within Skill Fit
- Preference Fit, Market Demand, and Academic Fit calculation engines
- Authenticated JWT-based personalized recommendations
- Unauthenticated / public skill-only fallback behavior
- Authoritative JWT identity resolution (overriding query user_id)
- Query parameter validation (limit, user_id)
- Backward compatibility of GET /api/careers/recommendations
"""

import unittest
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models.career import Career
from models.career_preference import CareerPreference
from models.skill import Skill
from models.student_profile import StudentProfile
from models.user import User
from services.career_recommendation_service import CareerRecommendationService


class TestPhase9Module91ScoringModel(unittest.TestCase):
    """Unit tests for the Module 9.1 multi-factor scoring model and components."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_formula_weighting_calculation(self):
        """Verify exact weights: 50% Skill, 20% Preference, 15% Market, 15% Academic."""
        skill_fit = 80.0
        preference_fit = 70.0
        market_demand = 90.0
        academic_fit = 60.0

        final_score, breakdown = CareerRecommendationService.calculate_multi_factor_score(
            skill_fit=skill_fit,
            preference_fit=preference_fit,
            market_demand=market_demand,
            academic_fit=academic_fit
        )

        # Expected: (0.50 * 80) + (0.20 * 70) + (0.15 * 90) + (0.15 * 60)
        # = 40.0 + 14.0 + 13.5 + 9.0 = 76.5
        self.assertEqual(final_score, 76.5)

        self.assertEqual(breakdown["skill_fit"]["weight"], 0.50)
        self.assertEqual(breakdown["skill_fit"]["score"], 80.0)
        self.assertEqual(breakdown["skill_fit"]["weighted_contribution"], 40.0)

        self.assertEqual(breakdown["preference_fit"]["weight"], 0.20)
        self.assertEqual(breakdown["preference_fit"]["score"], 70.0)
        self.assertEqual(breakdown["preference_fit"]["weighted_contribution"], 14.0)

        self.assertEqual(breakdown["market_demand"]["weight"], 0.15)
        self.assertEqual(breakdown["market_demand"]["score"], 90.0)
        self.assertEqual(breakdown["market_demand"]["weighted_contribution"], 13.5)

        self.assertEqual(breakdown["academic_fit"]["weight"], 0.15)
        self.assertEqual(breakdown["academic_fit"]["score"], 60.0)
        self.assertEqual(breakdown["academic_fit"]["weighted_contribution"], 9.0)

    def test_skill_fit_ats_blending(self):
        """Verify Skill Fit blends base skill score with optional ATS resume score."""
        base_score = CareerRecommendationService.calculate_skill_fit(
            readiness_pct=80.0,
            matched_count=4,
            weak_count=1,
            total_required=5,
            distance=20.0,
            ats_score=None
        )
        self.assertGreater(base_score, 0.0)

        # With ATS match (e.g. 90.0), skill fit blends 85% base + 15% ATS
        blended_score = CareerRecommendationService.calculate_skill_fit(
            readiness_pct=80.0,
            matched_count=4,
            weak_count=1,
            total_required=5,
            distance=20.0,
            ats_score=90.0
        )
        expected_blend = round((0.85 * base_score) + (0.15 * 90.0), 1)
        self.assertEqual(blended_score, expected_blend)

    def test_preference_fit_scoring(self):
        """Verify Preference Fit calculates role and domain alignments."""
        career = Career.query.get(1)  # Software Developer, Software Engineering
        self.assertIsNotNone(career)

        # 1. Exact role and domain match -> 100.0
        pref_exact = CareerPreference(
            target_role=career.title,
            preferred_domain=career.domain,
            experience_level="Entry-Level"
        )
        score_exact = CareerRecommendationService.calculate_preference_fit(career, pref_exact)
        self.assertEqual(score_exact, 100.0)

        # 2. None preference -> default neutral 50.0
        score_none = CareerRecommendationService.calculate_preference_fit(career, None)
        self.assertEqual(score_none, 50.0)

        # 3. Unrelated preference -> lower score
        pref_unrelated = CareerPreference(
            target_role="Botanist",
            preferred_domain="Agriculture",
            experience_level="Mid-Level"
        )
        score_unrelated = CareerRecommendationService.calculate_preference_fit(career, pref_unrelated)
        self.assertLess(score_unrelated, 40.0)

    def test_market_demand_scoring(self):
        """Verify Market Demand retrieves demand score from intelligence service."""
        # Career 1: Software Developer has demand score 92 in standardized intelligence
        demand_score = CareerRecommendationService.calculate_market_demand(1)
        self.assertEqual(demand_score, 92.0)

        # Non-existent career defaults gracefully to 70.0
        fallback_score = CareerRecommendationService.calculate_market_demand(9999)
        self.assertEqual(fallback_score, 70.0)

    def test_academic_fit_scoring(self):
        """Verify Academic Fit handles specialization, CGPA standing, and degree level."""
        career = Career.query.get(1)  # Software Developer

        # Strong computer science profile
        profile_strong = StudentProfile(
            education="Master of Science in Computer Science",
            specialization="Software Engineering",
            cgpa=9.2
        )
        score_strong = CareerRecommendationService.calculate_academic_fit(career, profile_strong)
        self.assertGreaterEqual(score_strong, 90.0)

        # Neutral fallback when profile is None
        score_none = CareerRecommendationService.calculate_academic_fit(career, None)
        self.assertEqual(score_none, 50.0)

    def test_multi_factor_justification_format(self):
        """Verify multi-factor justification text is transparent and structured."""
        justification = CareerRecommendationService.generate_multi_factor_justification(
            career_title="Data Scientist",
            final_score=84.5,
            skill_fit=82.0,
            preference_fit=90.0,
            market_demand=89.0,
            academic_fit=80.0
        )
        self.assertIn("84.5/100", justification)
        self.assertIn("50%", justification)
        self.assertIn("20%", justification)
        self.assertIn("15%", justification)
        self.assertIn("Strongest alignment", justification)


class TestPhase9Module91Integration(unittest.TestCase):
    """Integration tests for Module 9.1 API endpoints and authorization contracts."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        # Create or fetch test user
        cls.user = User.query.filter_by(email="phase9_test_student@example.com").first()
        if not cls.user:
            cls.user = User(
                name="Phase9 Test Student",
                email="phase9_test_student@example.com",
                password_hash=generate_password_hash("password123")
            )
            db.session.add(cls.user)
            db.session.commit()

        # Add profile for test user
        cls.profile = StudentProfile.query.filter_by(user_id=cls.user.id).first()
        if not cls.profile:
            cls.profile = StudentProfile(
                user_id=cls.user.id,
                education="B.Tech Computer Science",
                specialization="Software Engineering",
                cgpa=8.8
            )
            db.session.add(cls.profile)
            db.session.commit()

        # Add career preference for test user
        cls.pref = CareerPreference.query.filter_by(user_id=cls.user.id).first()
        if not cls.pref:
            cls.pref = CareerPreference(
                user_id=cls.user.id,
                target_role="Software Developer",
                preferred_domain="Software Engineering",
                experience_level="Entry-Level"
            )
            db.session.add(cls.pref)
            db.session.commit()

        # Add some skills for user
        existing_skills = Skill.query.filter_by(user_id=cls.user.id).all()
        if not existing_skills:
            db.session.add(Skill(user_id=cls.user.id, skill_name="Python", proficiency=8))
            db.session.add(Skill(user_id=cls.user.id, skill_name="Git", proficiency=7))
            db.session.commit()

        # Authenticate and obtain JWT
        resp = cls.client.post("/api/login", json={
            "email": "phase9_test_student@example.com",
            "password": "password123"
        })
        data = resp.get_json()
        cls.token = data.get("access_token")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_api_unauthenticated_recommendations(self):
        """Unauthenticated GET /api/careers/recommendations falls back to skill-only scoring."""
        resp = self.client.get("/api/careers/recommendations")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertFalse(data["is_personalized"])
        self.assertGreaterEqual(len(data["recommendations"]), 1)

        first_rec = data["recommendations"][0]
        self.assertIn("recommendation_score", first_rec)
        self.assertIn("final_score", first_rec)
        self.assertFalse(first_rec["is_personalized"])
        self.assertIsNone(first_rec["multi_factor_justification"])

    def test_api_authenticated_recommendations(self):
        """Authenticated GET /api/careers/recommendations returns multi-factor personalized scores."""
        resp = self.client.get("/api/careers/recommendations", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["is_personalized"])
        self.assertEqual(data["user_id"], self.user.id)
        self.assertGreaterEqual(len(data["recommendations"]), 1)

        first_rec = data["recommendations"][0]
        self.assertTrue(first_rec["is_personalized"])
        self.assertIn("final_score", first_rec)
        self.assertIn("factor_breakdown", first_rec)
        self.assertIsNotNone(first_rec["multi_factor_justification"])

        # Check factor breakdown
        breakdown = first_rec["factor_breakdown"]
        self.assertIn("skill_fit", breakdown)
        self.assertIn("preference_fit", breakdown)
        self.assertIn("market_demand", breakdown)
        self.assertIn("academic_fit", breakdown)

        self.assertEqual(breakdown["skill_fit"]["weight"], 0.50)
        self.assertEqual(breakdown["preference_fit"]["weight"], 0.20)
        self.assertEqual(breakdown["market_demand"]["weight"], 0.15)
        self.assertEqual(breakdown["academic_fit"]["weight"], 0.15)

    def test_api_authoritative_jwt_identity_overrides_query_param(self):
        """Authenticated request with ?user_id=999 must strictly prioritize JWT identity."""
        resp = self.client.get("/api/careers/recommendations?user_id=999", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        # Identity must match the JWT user, NOT 999
        self.assertEqual(data["user_id"], self.user.id)
        self.assertTrue(data["is_personalized"])

    def test_api_query_param_validation_limit(self):
        """Malformed or non-positive limit query parameters must return HTTP 400."""
        # 0 limit
        resp1 = self.client.get("/api/careers/recommendations?limit=0")
        self.assertEqual(resp1.status_code, 400)
        self.assertIn("limit must be a positive integer", resp1.get_json()["message"])

        # Negative limit
        resp2 = self.client.get("/api/careers/recommendations?limit=-5")
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("limit must be a positive integer", resp2.get_json()["message"])

        # Non-integer limit
        resp3 = self.client.get("/api/careers/recommendations?limit=abc")
        self.assertEqual(resp3.status_code, 400)
        self.assertIn("limit must be a positive integer", resp3.get_json()["message"])

        # Valid limit
        resp4 = self.client.get("/api/careers/recommendations?limit=3")
        self.assertEqual(resp4.status_code, 200)
        self.assertEqual(len(resp4.get_json()["recommendations"]), 3)

    def test_api_query_param_validation_user_id(self):
        """Malformed or non-positive user_id query parameters must return HTTP 400."""
        # Non-integer user_id
        resp1 = self.client.get("/api/careers/recommendations?user_id=invalid")
        self.assertEqual(resp1.status_code, 400)
        self.assertIn("user_id must be a valid integer", resp1.get_json()["message"])

        # Non-positive user_id
        resp2 = self.client.get("/api/careers/recommendations?user_id=-2")
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("user_id must be a valid integer", resp2.get_json()["message"])

    def test_api_backward_compatibility_fields(self):
        """Verify all existing Phase 1-8 fields remain intact on every recommendation item."""
        resp = self.client.get("/api/careers/recommendations", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()

        for rec in data["recommendations"]:
            self.assertIn("career_id", rec)
            self.assertIn("career_title", rec)
            self.assertIn("domain", rec)
            self.assertIn("description", rec)
            self.assertIn("recommendation_score", rec)
            self.assertIn("readiness_percentage", rec)
            self.assertIn("skill_acquisition_distance", rec)
            self.assertIn("total_required_skills", rec)
            self.assertIn("matched_skills", rec)
            self.assertIn("weak_skills", rec)
            self.assertIn("missing_skills", rec)
            self.assertIn("high_priority_missing_skills", rec)
            self.assertIn("explanation", rec)


if __name__ == "__main__":
    unittest.main()
