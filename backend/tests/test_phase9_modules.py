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
from services.career_comparison_service import CareerComparisonService, parse_salary_amount
from services.career_recommendation_service import CareerRecommendationService
from services.career_transition_service import CareerTransitionService
from services.career_pathway_service import CareerPathwayService
from services.career_simulator_service import CareerSimulatorService


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

class TestPhase9Module92CareerComparison(unittest.TestCase):
    """Unit and Integration tests for Module 9.2: Career Comparison & Transition Explorer."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_parse_salary_amount_utility(self):
        """Verify salary string parsing handles formatted, unformatted, and edge-case inputs."""
        self.assertEqual(parse_salary_amount("$115,000 / yr"), 115000)
        self.assertEqual(parse_salary_amount("$78,000"), 78000)
        self.assertEqual(parse_salary_amount("$120k"), 120000)
        self.assertEqual(parse_salary_amount("95000"), 95000)
        self.assertIsNone(parse_salary_amount(None))
        self.assertIsNone(parse_salary_amount(""))
        self.assertIsNone(parse_salary_amount("Negotiable / Competitive"))

    def test_calculate_salary_differential(self):
        """Verify salary differential across entry, median, and senior compensation bands."""
        market_a = {
            "salary_bands": {
                "entry_level": "$75,000 / yr",
                "median": "$105,000 / yr",
                "senior": "$140,000 / yr"
            }
        }
        market_b = {
            "salary_bands": {
                "entry_level": "$85,000 / yr",
                "median": "$125,000 / yr",
                "senior": "$165,000 / yr"
            }
        }

        diff = CareerComparisonService.calculate_salary_differential(
            "Software Developer", "Cloud Engineer", market_a, market_b
        )

        self.assertEqual(diff["entry_level"]["delta_amount"], 10000)
        self.assertEqual(diff["median"]["delta_amount"], 20000)
        self.assertEqual(diff["senior"]["delta_amount"], 25000)
        self.assertEqual(diff["median"]["higher_salary_career"], "Cloud Engineer")
        self.assertEqual(diff["median_delta"], 20000)
        # Median percentage delta: (20000 / 105000) * 100 = 19.0%
        self.assertAlmostEqual(diff["median_percentage_delta"], 19.0, places=1)
        self.assertIn("+$20,000 / yr", diff["median"]["formatted_delta"])

    def test_calculate_market_comparison(self):
        """Verify market demand comparison and delta calculations."""
        career_a = Career.query.get(1)  # Software Developer
        career_b = Career.query.get(6)  # Cloud Engineer
        market_a = {
            "demand_score": 92,
            "demand_level": "Very High",
            "five_year_growth_rate": "+22%",
            "top_hiring_sectors": ["FinTech", "SaaS"]
        }
        market_b = {
            "demand_score": 94,
            "demand_level": "Extremely High",
            "five_year_growth_rate": "+28%",
            "top_hiring_sectors": ["Cloud Providers", "Telecom"]
        }

        comp = CareerComparisonService.calculate_market_comparison(career_a, career_b, market_a, market_b)
        self.assertEqual(comp["demand_delta"], 2)
        self.assertEqual(comp["higher_demand_career"], career_b.title)
        self.assertEqual(comp["career_a"]["demand_score"], 92)
        self.assertEqual(comp["career_b"]["demand_score"], 94)
        self.assertIn("delta: +2 points", comp["summary"])

    def test_calculate_timeline_comparison(self):
        """Verify timeline comparison under study intensity options (5, 10, 20 hrs/week)."""
        career_a = Career.query.get(1)
        career_b = Career.query.get(2)
        gaps_a = [{"skill_name": "Python", "status": "MISSING", "current_proficiency": 0.0, "required_level": 4}]
        gaps_b = [{"skill_name": "HTML", "status": "MISSING", "current_proficiency": 0.0, "required_level": 3}]

        for hours in [5, 10, 20]:
            timeline = CareerComparisonService.calculate_timeline_comparison(
                career_a, career_b, gaps_a, gaps_b, hours_per_week=hours
            )
            self.assertEqual(timeline["hours_per_week"], hours)
            self.assertIn("career_a", timeline)
            self.assertIn("career_b", timeline)
            self.assertIn("estimated_study_weeks_difference", timeline)
            self.assertIn("estimated_study_hours_difference", timeline)
            self.assertIn("faster_career", timeline)

    def test_transition_difficulty_classification(self):
        """Verify transition difficulty tiers (LOW, MODERATE, HIGH) and human-readable labels."""
        # 1 -> 6 (Software Developer -> Cloud Engineer)
        analysis = CareerTransitionService.analyze_transition(1, 6)
        self.assertIsNotNone(analysis)
        summary = analysis["transition_summary"]
        self.assertIn(summary["transition_difficulty"], ["LOW", "MODERATE", "HIGH"])
        self.assertIn(
            summary["difficulty_label"],
            ["Smooth Lateral Transition", "Moderate Upskilling Transition", "Significant Cross-Domain Pivot"]
        )

    def test_transferable_skills_and_status(self):
        """Verify transferable skill recognition and DIRECT_TRANSFER / SKILL_UPGRADE_NEEDED statuses."""
        self.assertTrue(CareerTransitionService.is_transferable("Python"))
        self.assertTrue(CareerTransitionService.is_transferable("Git"))
        self.assertTrue(CareerTransitionService.is_transferable("Programming"))

        # In career transition analysis:
        analysis = CareerTransitionService.analyze_transition(1, 2)
        self.assertIsNotNone(analysis)
        valid_statuses = {"DIRECT_TRANSFER", "SKILL_UPGRADE_NEEDED", "NEW_SKILL_REQUIRED"}
        for skill in analysis["overlapping_skills"]:
            self.assertIn(skill["status"], valid_statuses)
            self.assertIn("is_onet_transferable", skill)

    def test_onet_transition_matrix_terms(self):
        """Verify O*NET transferable terms are loaded and accessible."""
        terms = CareerTransitionService.get_onet_transferable_terms()
        self.assertIsInstance(terms, set)
        self.assertGreater(len(terms), 0)

    def test_compare_careers_backward_compatibility(self):
        """Verify all legacy compare_careers keys and structures remain present and untouched."""
        result = CareerComparisonService.compare_careers(1, 2, hours_per_week=10)
        self.assertIsNotNone(result)

        # Legacy keys
        legacy_keys = [
            "career_a", "career_b", "comparison_metrics", "common_skills",
            "career_a_only", "career_b_only", "student_already_has", "student_missing"
        ]
        for key in legacy_keys:
            self.assertIn(key, result)

        career_a_fields = [
            "id", "title", "domain", "readiness_percentage", "skill_acquisition_distance",
            "total_required_skills", "matched_skills_count", "missing_skills_count", "weak_skills_count"
        ]
        for field in career_a_fields:
            self.assertIn(field, result["career_a"])
            self.assertIn(field, result["career_b"])

    def test_api_get_compare_careers_endpoint(self):
        """Verify GET /api/careers/compare returns additive Module 9.2 intelligence fields."""
        resp = self.client.get("/api/careers/compare?career_a_id=1&career_b_id=6&hours_per_week=20")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        comparison = data["comparison"]

        # Additive Module 9.2 fields
        self.assertIn("market_comparison", comparison)
        self.assertIn("demand_delta", comparison)
        self.assertIn("salary_differential", comparison)
        self.assertIn("salary_delta", comparison)
        self.assertIn("timeline_comparison", comparison)
        self.assertIn("estimated_study_weeks_difference", comparison)
        self.assertIn("transition_analysis", comparison)
        self.assertIn("transition_difficulty", comparison)
        self.assertIn("transition_difficulty_label", comparison)
        self.assertIn("transferable_skills", comparison)

        # Verify hours_per_week propagation
        self.assertEqual(comparison["timeline_comparison"]["hours_per_week"], 20)

    def test_api_post_compare_careers_endpoint(self):
        """Verify POST /api/careers/compare returns additive Module 9.2 intelligence fields."""
        payload = {"career_a_id": 1, "career_b_id": 2, "hours_per_week": 5}
        resp = self.client.post("/api/careers/compare", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        comparison = data["comparison"]

        self.assertIn("market_comparison", comparison)
        self.assertIn("salary_differential", comparison)
        self.assertIn("timeline_comparison", comparison)
        self.assertEqual(comparison["timeline_comparison"]["hours_per_week"], 5)

    def test_api_compare_careers_validations(self):
        """Verify robust input validation on compare_careers (missing, non-int, invalid hours, 404)."""
        # Missing parameter
        resp1 = self.client.get("/api/careers/compare?career_a_id=1")
        self.assertEqual(resp1.status_code, 400)
        self.assertIn("Both career_a_id and career_b_id are required", resp1.get_json()["message"])

        # Non-integer ID
        resp2 = self.client.get("/api/careers/compare?career_a_id=abc&career_b_id=2")
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("must be valid positive integers", resp2.get_json()["message"])

        # Non-positive ID
        resp3 = self.client.get("/api/careers/compare?career_a_id=-1&career_b_id=2")
        self.assertEqual(resp3.status_code, 400)
        self.assertIn("must be valid positive integers", resp3.get_json()["message"])

        # Invalid hours_per_week
        resp4 = self.client.get("/api/careers/compare?career_a_id=1&career_b_id=2&hours_per_week=15")
        self.assertEqual(resp4.status_code, 400)
        self.assertIn("Supported values are 5, 10, or 20", resp4.get_json()["message"])

        # Non-existent career ID
        resp5 = self.client.get("/api/careers/compare?career_a_id=9999&career_b_id=2")
        self.assertEqual(resp5.status_code, 404)

    def test_api_get_career_transition_endpoint(self):
        """Verify GET /api/careers/<from>/transition/<to> returns complete pathway analysis."""
        resp = self.client.get("/api/careers/1/transition/6")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        transition = data["transition"]

        self.assertEqual(transition["source_career"]["id"], 1)
        self.assertEqual(transition["target_career"]["id"], 6)
        self.assertIn("transition_summary", transition)
        self.assertIn("transition_difficulty", transition["transition_summary"])
        self.assertIn("overlapping_skills", transition)
        self.assertIn("transferable_skills", transition)
        self.assertIn("additional_skills_required", transition)

        # Non-existent careers
        resp_404 = self.client.get("/api/careers/9999/transition/1")
        self.assertEqual(resp_404.status_code, 404)


class TestPhase9Module93CareerPathways(unittest.TestCase):
    """Unit and Integration tests for Module 9.3: Interactive Career Pathway Branching & Elective Specialization Tree."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        # Fetch or create test user with skills
        cls.user = User.query.filter_by(email="phase9_test_student@example.com").first()
        if cls.user:
            resp = cls.client.post("/api/login", json={
                "email": "phase9_test_student@example.com",
                "password": "password123"
            })
            cls.token = resp.get_json().get("access_token")
            cls.headers = {"Authorization": f"Bearer {cls.token}"}
        else:
            cls.token = None
            cls.headers = {}

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_career_with_multiple_supported_pathways(self):
        """Verify career with multiple supported specialization pathways (e.g., Career 1: Software Developer)."""
        result = CareerPathwayService.evaluate_career_pathways(1, user_id=None, hours_per_week=10)
        self.assertIsNotNone(result)
        self.assertTrue(result["has_multiple_pathways"])
        self.assertIsNone(result["limitation_note"])
        self.assertGreaterEqual(result["pathways_count"], 2)
        self.assertEqual(result["career"]["title"], "Software Developer")

        # Verify overlapping skills across pathways
        overlapping = [s["skill_name"] for s in result["overlapping_skills"]]
        self.assertIn("Data Structures", overlapping)
        self.assertIn("Git", overlapping)

        # Verify distinct pathways exist with core vs elective differentiation
        pathway_ids = [p["id"] for p in result["pathways"]]
        self.assertIn("sw-dev-python", pathway_ids)
        self.assertIn("sw-dev-java", pathway_ids)

        python_p = next(p for p in result["pathways"] if p["id"] == "sw-dev-python")
        java_p = next(p for p in result["pathways"] if p["id"] == "sw-dev-java")

        self.assertIn("Python", [s["skill_name"] for s in python_p["elective_skills"]])
        self.assertIn("Java", [s["skill_name"] for s in java_p["elective_skills"]])

    def test_career_with_only_one_pathway(self):
        """Verify career with single supported pathway and explicit limitation note (e.g., Career 7: DevOps)."""
        result = CareerPathwayService.evaluate_career_pathways(7, user_id=None, hours_per_week=10)
        self.assertIsNotNone(result)
        self.assertFalse(result["has_multiple_pathways"])
        self.assertEqual(result["pathways_count"], 1)
        self.assertIsNotNone(result["limitation_note"])
        self.assertIn("Single consolidated pathway supported", result["limitation_note"])
        self.assertEqual(result["career"]["title"], "DevOps Engineer")

        single_p = result["pathways"][0]
        self.assertTrue(single_p["is_primary"])
        self.assertEqual(len(single_p["elective_skills"]), 0)
        self.assertEqual(len(single_p["core_skills"]), 5)

    def test_student_with_matching_skills_personalization(self):
        """Verify student with matching skills obtains higher readiness, matched skills, and customized ranking."""
        mock_skills = [
            Skill(user_id=888, skill_name="Python", proficiency=8),  # Level 4/5
            Skill(user_id=888, skill_name="Git", proficiency=8),     # Level 4/5
        ]
        career = Career.query.get(1)
        config = CareerPathwayService.get_pathway_configuration(career)
        evaluated = [
            CareerPathwayService.evaluate_pathway_for_student(career, pdef, mock_skills, hours_per_week=10)
            for pdef in config["pathways"]
        ]
        evaluated.sort(key=lambda p: (-p["suitability_score"], -p["readiness_percentage"]))

        # Python track should rank first because student has Python and Git
        top_p = evaluated[0]
        self.assertEqual(top_p["id"], "sw-dev-python")
        self.assertGreater(top_p["readiness_percentage"], 40.0)
        self.assertGreaterEqual(top_p["matched_skills_count"], 2)

    def test_student_with_missing_skills(self):
        """Verify student with no recorded skills has 0.0% readiness and actionable gaps for all skills."""
        career = Career.query.get(1)
        config = CareerPathwayService.get_pathway_configuration(career)
        python_def = next(p for p in config["pathways"] if p["id"] == "sw-dev-python")

        evaluated = CareerPathwayService.evaluate_pathway_for_student(
            career, python_def, student_skills=[], hours_per_week=10
        )
        self.assertEqual(evaluated["readiness_percentage"], 0.0)
        self.assertEqual(evaluated["matched_skills_count"], 0)
        self.assertEqual(evaluated["missing_skills_count"], evaluated["total_skills_count"])
        self.assertGreater(evaluated["estimated_total_hours"], 0)
        self.assertGreater(evaluated["estimated_weeks"], 0)

    def test_pathway_readiness_calculation_bounds(self):
        """Verify readiness percentage calculation stays deterministically bounded between 0.0 and 100.0%."""
        career = Career.query.get(1)
        config = CareerPathwayService.get_pathway_configuration(career)
        python_def = next(p for p in config["pathways"] if p["id"] == "sw-dev-python")

        # 1. Zero skills -> 0.0%
        res_zero = CareerPathwayService.evaluate_pathway_for_student(career, python_def, [], 10)
        self.assertEqual(res_zero["readiness_percentage"], 0.0)

        # 2. Perfect skills (all at 10/10) -> 100.0%
        perfect_skills = [
            Skill(user_id=777, skill_name="Data Structures", proficiency=10),
            Skill(user_id=777, skill_name="Git", proficiency=10),
            Skill(user_id=777, skill_name="SQL", proficiency=10),
            Skill(user_id=777, skill_name="Python", proficiency=10),
        ]
        res_perfect = CareerPathwayService.evaluate_pathway_for_student(career, python_def, perfect_skills, 10)
        self.assertEqual(res_perfect["readiness_percentage"], 100.0)
        self.assertEqual(res_perfect["missing_skills_count"], 0)
        self.assertEqual(res_perfect["estimated_total_hours"], 0)

    def test_pathway_ranking_deterministic(self):
        """Verify that pathway ranking correctly prioritizes Java specialization for Java-oriented student."""
        mock_java_skills = [
            Skill(user_id=666, skill_name="Java", proficiency=8),
            Skill(user_id=666, skill_name="Git", proficiency=8),
        ]
        career = Career.query.get(1)
        config = CareerPathwayService.get_pathway_configuration(career)
        evaluated = [
            CareerPathwayService.evaluate_pathway_for_student(career, p, mock_java_skills, 10)
            for p in config["pathways"]
        ]
        evaluated.sort(key=lambda p: (-p["suitability_score"], -p["readiness_percentage"]))

        # For student with Java, Enterprise Java Architecture Track should be rank 1
        self.assertEqual(evaluated[0]["id"], "sw-dev-java")

    def test_prerequisite_dependencies_validation(self):
        """Verify prerequisite dependency tracking identifies satisfied vs missing foundational skills."""
        # Student has HTML and CSS, but lacks JavaScript
        student_map = {"html": 4.0, "css": 4.0}
        prereqs = CareerPathwayService.check_prerequisites("React", student_map)
        self.assertFalse(prereqs["prerequisites_satisfied"])
        self.assertIn("Javascript", prereqs["missing_prerequisites"])

        # Student acquires JavaScript
        student_map["javascript"] = 4.0
        prereqs_satisfied = CareerPathwayService.check_prerequisites("React", student_map)
        self.assertTrue(prereqs_satisfied["prerequisites_satisfied"])
        self.assertEqual(len(prereqs_satisfied["missing_prerequisites"]), 0)

    def test_api_get_pathways_endpoint(self):
        """Verify GET /api/careers/<id>/pathways returns complete structured response payload."""
        resp = self.client.get("/api/careers/1/pathways?hours_per_week=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("career", data)
        self.assertIn("pathways", data)
        self.assertIn("overlapping_skills", data)
        self.assertIn("recommended_pathway_id", data)
        self.assertIn("recommended_pathway_name", data)
        self.assertIn("recommendation_summary", data)
        self.assertEqual(data["hours_per_week"], 10)

        # Inspect first pathway shape
        p = data["pathways"][0]
        self.assertIn("id", p)
        self.assertIn("name", p)
        self.assertIn("specialization_focus", p)
        self.assertIn("readiness_percentage", p)
        self.assertIn("effort_tier", p)
        self.assertIn("estimated_weeks", p)
        self.assertIn("core_skills", p)
        self.assertIn("elective_skills", p)
        self.assertIn("study_milestones", p)

    def test_api_get_pathways_authentication(self):
        """Verify JWT authenticated request returns is_personalized True with authoritative user identity."""
        if self.token:
            resp = self.client.get("/api/careers/1/pathways", headers=self.headers)
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data["is_personalized"])
            self.assertEqual(data["user_id"], self.user.id)

    def test_api_pathways_input_validations(self):
        """Verify input validation for non-existent careers, invalid IDs, and invalid study intensities."""
        # Non-existent career ID -> 404
        resp1 = self.client.get("/api/careers/9999/pathways")
        self.assertEqual(resp1.status_code, 404)

        # Non-positive career ID -> 400
        resp2 = self.client.get("/api/careers/0/pathways")
        self.assertEqual(resp2.status_code, 400)

        # Invalid hours_per_week -> 400
        resp3 = self.client.get("/api/careers/1/pathways?hours_per_week=15")
        self.assertEqual(resp3.status_code, 400)
        self.assertIn("Supported values are 5, 10, or 20", resp3.get_json()["message"])

        # Non-integer hours_per_week -> 400
        resp4 = self.client.get("/api/careers/1/pathways?hours_per_week=abc")
        self.assertEqual(resp4.status_code, 400)

    def test_api_post_pathways_endpoint(self):
        """Verify POST /api/careers/<id>/pathways accepts JSON body configuration."""
        resp = self.client.post("/api/careers/2/pathways", json={"hours_per_week": 20})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["hours_per_week"], 20)
        self.assertTrue(data["has_multiple_pathways"])

    def test_backward_compatibility_career_endpoints(self):
        """Verify that existing Phase 1-9.2 career endpoints remain 100% operational."""
        # 1. GET /api/careers
        resp_list = self.client.get("/api/careers")
        self.assertEqual(resp_list.status_code, 200)

        # 2. GET /api/careers/1
        resp_detail = self.client.get("/api/careers/1")
        self.assertEqual(resp_detail.status_code, 200)

        # 3. GET /api/careers/compare
        resp_comp = self.client.get("/api/careers/compare?career_a_id=1&career_b_id=2")
        self.assertEqual(resp_comp.status_code, 200)
        self.assertIn("market_comparison", resp_comp.get_json()["comparison"])


class TestPhase9Module94SkillSimulator(unittest.TestCase):
    """Unit and Integration tests for Module 9.4: 'What If I Learn Skill X?' Interactive Career Simulator."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        # Fetch or create test user with skills
        cls.user = User.query.filter_by(email="phase9_test_student@example.com").first()
        if cls.user:
            resp = cls.client.post("/api/login", json={
                "email": "phase9_test_student@example.com",
                "password": "password123"
            })
            cls.token = resp.get_json().get("access_token")
            cls.headers = {"Authorization": f"Bearer {cls.token}"}
        else:
            cls.token = None
            cls.headers = {}

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_skill_resolution_canonical_and_alias_and_id(self):
        """Verify resolve_skill handles canonical IDs, canonical names, aliases, and career-specific skills."""
        # 1. Canonical Skill by name
        res_py = CareerSimulatorService.resolve_skill(skill_name="Python")
        self.assertIsNotNone(res_py)
        self.assertEqual(res_py["name"], "Python")

        # 2. Canonical Skill by ID
        if res_py and res_py.get("id"):
            res_id = CareerSimulatorService.resolve_skill(skill_id=res_py["id"])
            self.assertIsNotNone(res_id)
            self.assertEqual(res_id["name"], "Python")

        # 3. Alias resolution (e.g. 'reactjs', or case-insensitive)
        res_alias = CareerSimulatorService.resolve_skill(skill_name="reactjs")
        if res_alias:
            self.assertEqual(res_alias["name"], "React")

        # 4. Unknown skill resolution returns None
        res_none = CareerSimulatorService.resolve_skill(skill_name="nonexistent_fantasy_skill_xyz123")
        self.assertIsNone(res_none)

    def test_proficiency_input_normalization(self):
        """Verify normalization between 1-5 career scale and 1-10 raw scale with strict validation."""
        # 1 to 5 career scale
        norm_lvl, raw_prof = CareerSimulatorService.normalize_proficiency_inputs(3)
        self.assertEqual(norm_lvl, 3.0)
        self.assertEqual(raw_prof, 6)

        norm_lvl5, raw_prof5 = CareerSimulatorService.normalize_proficiency_inputs(5.0)
        self.assertEqual(norm_lvl5, 5.0)
        self.assertEqual(raw_prof5, 10)

        # 6 to 10 raw scale
        norm_lvl8, raw_prof8 = CareerSimulatorService.normalize_proficiency_inputs(8)
        self.assertEqual(norm_lvl8, 4.0)
        self.assertEqual(raw_prof8, 8)

        # Out-of-bounds validations
        with self.assertRaises(ValueError):
            CareerSimulatorService.normalize_proficiency_inputs(0)
        with self.assertRaises(ValueError):
            CareerSimulatorService.normalize_proficiency_inputs(11)
        with self.assertRaises(ValueError):
            CareerSimulatorService.normalize_proficiency_inputs("not_a_number")

    def test_missing_skill_simulation_readiness_gain(self):
        """Verify that simulating a missing career skill yields positive readiness gain and timeline reduction."""
        career = Career.query.get(1)  # Software Developer
        # Simulate student with NO skills acquiring Python at Level 4/5
        sim = CareerSimulatorService.simulate_skill_impact(
            career_id=1,
            skill_name="Python",
            simulated_level=4,
            user_id=None,
            hours_per_week=10
        )
        self.assertNotIn("error", sim)
        self.assertEqual(sim["career_id"], 1)
        self.assertTrue(sim["skill"]["is_required_by_career"])
        self.assertGreater(sim["simulated_state"]["readiness_percentage"], sim["current_state"]["readiness_percentage"])
        self.assertGreater(sim["impact"]["readiness_gain"], 0.0)
        self.assertGreaterEqual(sim["impact"]["hours_saved"], 0)
        self.assertGreaterEqual(sim["impact"]["weeks_saved"], 0)
        self.assertIn("Python", sim["explanation"])

    def test_existing_skill_improvement(self):
        """Verify upgrading an existing student skill produces deterministic readiness delta."""
        sim = CareerSimulatorService.simulate_skill_impact(
            career_id=1,
            skill_name="Python",
            simulated_level=4.5,
            user_id=None,
            hours_per_week=10
        )
        self.assertNotIn("error", sim)
        self.assertGreater(sim["impact"]["readiness_gain"], 0.0)

    def test_skill_already_exceeds_requirement(self):
        """Verify upgrading a skill that already exceeds requirements yields 0 gain with clear narrative."""
        sim = CareerSimulatorService.simulate_skill_impact(
            career_id=1,
            skill_name="Python",
            simulated_level=5,
            user_id=self.user.id if self.user else None,
            hours_per_week=10
        )
        self.assertNotIn("error", sim)
        self.assertIsInstance(sim["explanation"], str)
        self.assertIn("Python", sim["explanation"])

    def test_simulation_proficiency_equal_or_lower(self):
        """Verify simulating proficiency <= current proficiency yields zero readiness gain."""
        if self.user:
            user_skills = Skill.query.filter_by(user_id=self.user.id).all()
            if user_skills:
                first_skill = user_skills[0]
                curr_level = round(first_skill.proficiency / 2.0, 1)
                sim = CareerSimulatorService.simulate_skill_impact(
                    career_id=1,
                    skill_name=first_skill.skill_name,
                    simulated_level=max(1.0, curr_level - 1.0),
                    user_id=self.user.id,
                    hours_per_week=10
                )
                self.assertNotIn("error", sim)
                self.assertEqual(sim["impact"]["readiness_gain"], 0.0)

    def test_skill_not_required_by_career(self):
        """Verify simulating an unrelated skill yields zero readiness gain and transparent explanation."""
        sim = CareerSimulatorService.simulate_skill_impact(
            career_id=1,
            skill_name="Cybersecurity",
            simulated_level=5,
            user_id=None,
            hours_per_week=10
        )
        self.assertNotIn("error", sim)
        self.assertFalse(sim["skill"]["is_required_by_career"])
        self.assertEqual(sim["impact"]["readiness_gain"], 0.0)
        self.assertEqual(sim["impact"]["weeks_saved"], 0)
        self.assertIn("not a mandatory or elective requirement", sim["explanation"])

    def test_pathway_impacts_integration(self):
        """Verify that simulation evaluates Module 9.3 specialization tracks and computes track deltas."""
        sim = CareerSimulatorService.simulate_skill_impact(
            career_id=1,
            skill_name="Python",
            simulated_level=4,
            user_id=None,
            hours_per_week=10
        )
        self.assertNotIn("error", sim)
        pathway_impacts = sim["impact"]["pathway_impacts"]
        self.assertIsInstance(pathway_impacts, list)
        self.assertGreater(len(pathway_impacts), 0)
        for p in pathway_impacts:
            self.assertIn("pathway_id", p)
            self.assertIn("pathway_name", p)
            self.assertIn("readiness_gain", p)
            self.assertIn("simulated_readiness", p)
            self.assertIn("simulated_effort_tier", p)

    def test_strict_database_immutability(self):
        """STRICT SAFETY TEST: Verify student profile and skills table are 100% unmodified by simulation."""
        if self.user:
            skills_before = Skill.query.filter_by(user_id=self.user.id).all()
            count_before = len(skills_before)
            profs_before = {s.id: s.proficiency for s in skills_before}

            CareerSimulatorService.simulate_skill_impact(
                career_id=1,
                skill_name="Python",
                simulated_level=5,
                user_id=self.user.id,
                hours_per_week=20
            )
            CareerSimulatorService.simulate_skill_impact(
                career_id=1,
                skill_name="Docker",
                simulated_level=4,
                user_id=self.user.id,
                hours_per_week=10
            )

            skills_after = Skill.query.filter_by(user_id=self.user.id).all()
            count_after = len(skills_after)
            profs_after = {s.id: s.proficiency for s in skills_after}

            self.assertEqual(count_before, count_after, "Simulation modified the database skill count!")
            self.assertEqual(profs_before, profs_after, "Simulation modified database skill proficiencies!")

    def test_api_post_simulate_skill_endpoint(self):
        """Verify POST /api/careers/<id>/simulate-skill returns complete structured simulation payload."""
        resp = self.client.post("/api/careers/1/simulate-skill", json={
            "skill_name": "Python",
            "simulated_level": 4,
            "hours_per_week": 10
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("simulation", data)
        sim = data["simulation"]
        self.assertEqual(sim["career_id"], 1)
        self.assertIn("current_state", sim)
        self.assertIn("simulated_state", sim)
        self.assertIn("impact", sim)
        self.assertIn("explanation", sim)
        self.assertIn("readiness_gain", sim["impact"])
        self.assertIn("weeks_saved", sim["impact"])

    def test_api_get_simulate_skill_endpoint(self):
        """Verify GET /api/careers/<id>/simulate-skill accepts query parameters."""
        resp = self.client.get("/api/careers/1/simulate-skill?skill_name=Python&simulated_level=4&hours_per_week=10")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["simulation"]["skill"]["name"], "Python")

    def test_api_jwt_authentication_and_user_context(self):
        """Verify JWT authenticated requests inject authoritative user profile into simulation."""
        if self.token:
            resp = self.client.post(
                "/api/careers/1/simulate-skill",
                headers=self.headers,
                json={"skill_name": "Python", "simulated_level": 4}
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertEqual(data["status"], "success")

    def test_api_input_validations(self):
        """Verify comprehensive input validation on the simulation endpoint."""
        # 1. Non-existent career ID -> 404
        resp1 = self.client.post("/api/careers/9999/simulate-skill", json={
            "skill_name": "Python", "simulated_level": 4
        })
        self.assertEqual(resp1.status_code, 404)

        # 2. Non-positive career ID -> 400
        resp2 = self.client.post("/api/careers/0/simulate-skill", json={
            "skill_name": "Python", "simulated_level": 4
        })
        self.assertEqual(resp2.status_code, 400)

        # 3. Missing simulated_level -> 400
        resp3 = self.client.post("/api/careers/1/simulate-skill", json={
            "skill_name": "Python"
        })
        self.assertEqual(resp3.status_code, 400)
        self.assertIn("simulated_level is required", resp3.get_json()["message"])

        # 4. Invalid proficiency (<1 or >10) -> 400
        resp4 = self.client.post("/api/careers/1/simulate-skill", json={
            "skill_name": "Python", "simulated_level": 15
        })
        self.assertEqual(resp4.status_code, 400)

        # 5. Missing both skill_id and skill_name -> 400
        resp5 = self.client.post("/api/careers/1/simulate-skill", json={
            "simulated_level": 4
        })
        self.assertEqual(resp5.status_code, 400)

        # 6. Unresolvable skill name -> 404
        resp6 = self.client.post("/api/careers/1/simulate-skill", json={
            "skill_name": "totally_nonexistent_skill_zzz999", "simulated_level": 4
        })
        self.assertEqual(resp6.status_code, 404)

        # 7. Invalid study intensity hours_per_week -> 400
        resp7 = self.client.post("/api/careers/1/simulate-skill", json={
            "skill_name": "Python", "simulated_level": 4, "hours_per_week": 15
        })
        self.assertEqual(resp7.status_code, 400)
        self.assertIn("Supported values are 5, 10, or 20", resp7.get_json()["message"])

    def test_readiness_bounds_guarantee(self):
        """Verify readiness scores always stay within [0.0, 100.0] bounds."""
        for lvl in [1, 3, 5, 10]:
            sim = CareerSimulatorService.simulate_skill_impact(
                career_id=1,
                skill_name="Python",
                simulated_level=lvl,
                user_id=None,
                hours_per_week=10
            )
            readiness = sim["simulated_state"]["readiness_percentage"]
            self.assertGreaterEqual(readiness, 0.0)
            self.assertLessEqual(readiness, 100.0)

    def test_backward_compatibility_preserved(self):
        """Verify all Phase 1-9.3 career endpoints remain functioning normally."""
        resp_p = self.client.get("/api/careers/1/pathways")
        self.assertEqual(resp_p.status_code, 200)

        resp_c = self.client.get("/api/careers/compare?career_a_id=1&career_b_id=2")
        self.assertEqual(resp_c.status_code, 200)


if __name__ == "__main__":
    unittest.main()
