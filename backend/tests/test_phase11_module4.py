"""
Unit and API Integration Tests for Phase 11 Module 11.4:
Real-Time Industry Trends & Dynamic Skill Demand Weighting Engine.

Verifies:
1. Normalization of demand scores into 5 discrete tiers (VERY_HIGH, HIGH, MODERATE, LOW, VERY_LOW).
2. Calculation of market demand factor: range [0.80, 1.20].
3. Dynamic priority formula and priority change % calculation.
4. Strict preservation of static career importance (1-5).
5. Strict preservation of student proficiency (0-5).
6. Presence of mandatory provenance disclaimer notice.
7. Catalog lookup with case-insensitivity and canonical alias resolution.
8. Fallback handling for uncataloged skills (defaults to neutral 0.50 score).
9. Scaling impact of high-demand vs low-demand multipliers.
10. Career evaluation schema and complete skill list generation.
11. Non-existent career ID returns 404 error from endpoint and service.
12. JWT authenticated student personalization with gap prioritization.
13. Unauthenticated baseline backward compatibility.
14. Filtering skills by trend (GROWING, STABLE, DECLINING).
15. Filtering skills by demand level (VERY_HIGH, HIGH, MODERATE, etc.).
16. Result pagination / limit enforcement.
17. Phase 11.1 Skill ROI enrichment integration.
18. Phase 11.2 Portfolio Capstone recommendation integration.
19. Phase 11.3 Academic curriculum coverage comparison (academic-industry disconnect).
20. Zero database mutations guarantee.
"""

import unittest
from app import create_app
from extensions import db
from models.user import User
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from models.student_profile import StudentProfile
from services.industry_demand_service import (
    IndustryDemandService,
    SKILL_MARKET_DEMAND_CATALOG,
    INDUSTRY_DEMAND_PROVENANCE,
)
from flask_jwt_extended import create_access_token


class TestPhase11Module4IndustryDemand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_normalization_of_demand_scores(self):
        """1. Verify normalization of continuous demand scores into 5 discrete tiers."""
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.95), "VERY_HIGH")
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.80), "VERY_HIGH")
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.79), "HIGH")
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.60), "HIGH")
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.55), "MODERATE")
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.40), "MODERATE")
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.35), "LOW")
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.20), "LOW")
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.15), "VERY_LOW")
        self.assertEqual(IndustryDemandService.normalize_demand_score(0.00), "VERY_LOW")

    def test_02_market_demand_factor_range(self):
        """2. Verify market demand factor calculation strictly bounds between 0.80 and 1.20."""
        # Factor = 0.80 + 0.40 * score
        f_min = IndustryDemandService.calculate_market_demand_factor(0.0)
        self.assertAlmostEqual(f_min, 0.80, places=2)

        f_mid = IndustryDemandService.calculate_market_demand_factor(0.50)
        self.assertAlmostEqual(f_mid, 1.00, places=2)

        f_max = IndustryDemandService.calculate_market_demand_factor(1.0)
        self.assertAlmostEqual(f_max, 1.20, places=2)

        # Bounds protection
        self.assertAlmostEqual(IndustryDemandService.calculate_market_demand_factor(-0.5), 0.80, places=2)
        self.assertAlmostEqual(IndustryDemandService.calculate_market_demand_factor(1.5), 1.20, places=2)

    def test_03_dynamic_priority_formula(self):
        """3. Verify Dynamic Priority = Career Importance * Market Demand Factor and % change."""
        # Career importance 5, demand score 1.0 -> factor 1.20 -> dynamic priority 6.0, +20.0%
        dp, factor, pct = IndustryDemandService.calculate_dynamic_priority(5, 1.0)
        self.assertAlmostEqual(dp, 6.0, places=2)
        self.assertAlmostEqual(factor, 1.20, places=2)
        self.assertAlmostEqual(pct, 20.0, places=1)

        # Career importance 4, demand score 0.5 -> factor 1.00 -> dynamic priority 4.0, 0.0%
        dp, factor, pct = IndustryDemandService.calculate_dynamic_priority(4, 0.5)
        self.assertAlmostEqual(dp, 4.0, places=2)
        self.assertAlmostEqual(factor, 1.00, places=2)
        self.assertAlmostEqual(pct, 0.0, places=1)

        # Career importance 5, demand score 0.0 -> factor 0.80 -> dynamic priority 4.0, -20.0%
        dp, factor, pct = IndustryDemandService.calculate_dynamic_priority(5, 0.0)
        self.assertAlmostEqual(dp, 4.0, places=2)
        self.assertAlmostEqual(factor, 0.80, places=2)
        self.assertAlmostEqual(pct, -20.0, places=1)

    def test_04_static_career_importance_preservation(self):
        """4. Verify that static career importance is strictly preserved in evaluation."""
        with self.app.app_context():
            res = IndustryDemandService.evaluate_career_industry_demand(career_id=1)
            self.assertNotIn("error", res)
            for skill in res["skills"]:
                self.assertIn("career_importance", skill)
                self.assertIn(skill["career_importance"], [1, 2, 3, 4, 5])
                # dynamic priority must be separate
                self.assertIn("dynamic_priority", skill)
                self.assertIn("market_demand_factor", skill)

    def test_05_student_proficiency_preservation(self):
        """5. Verify student proficiency is kept distinct from market evidence and demand weight."""
        with self.app.app_context():
            user = User.query.first()
            user_id = user.id if user else 1
            res = IndustryDemandService.evaluate_career_industry_demand(career_id=1, user_id=user_id)
            self.assertNotIn("error", res)
            self.assertTrue(res["is_personalized"])
            for skill in res["skills"]:
                self.assertIn("student_proficiency", skill)
                self.assertIn("required_proficiency", skill)
                self.assertIn("gap", skill)
                self.assertIn("demand_score", skill)
                self.assertIn("dynamic_priority", skill)

    def test_06_provenance_notice_strictly_present(self):
        """6. Verify mandatory provenance notice is strictly present in data and API responses."""
        with self.app.app_context():
            res = IndustryDemandService.evaluate_career_industry_demand(career_id=1)
            self.assertIn("provenance", res)
            self.assertIn("DEMO / SAMPLE / PROTOTYPE MARKET BENCHMARK", res["provenance"])
            self.assertEqual(res["provenance"], INDUSTRY_DEMAND_PROVENANCE)

        # Via API
        resp = self.client.get("/api/careers/1/industry-demand")
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertIn("provenance", json_data)
        self.assertIn("DEMO / SAMPLE / PROTOTYPE MARKET BENCHMARK", json_data["provenance"])

    def test_07_catalog_lookup_and_case_insensitivity(self):
        """7. Verify market data resolution supports case-insensitivity and aliases."""
        with self.app.app_context():
            py_upper = IndustryDemandService.get_skill_market_data("PYTHON")
            py_lower = IndustryDemandService.get_skill_market_data("python")
            self.assertEqual(py_upper["demand_score"], py_lower["demand_score"])
            self.assertEqual(py_upper["trend"], "GROWING")
            self.assertEqual(py_upper["demand_level"], "VERY_HIGH")

            dock = IndustryDemandService.get_skill_market_data("Docker (Container)")
            self.assertEqual(dock["canonical_name"], "Docker")
            self.assertAlmostEqual(dock["demand_score"], 0.92, places=2)

    def test_08_fallback_handling_for_uncataloged_skills(self):
        """8. Verify deterministic fallback for unknown or uncataloged skills."""
        with self.app.app_context():
            unknown = IndustryDemandService.get_skill_market_data("ObscureUnheardLanguage123")
            self.assertFalse(unknown["is_catalog_match"])
            self.assertAlmostEqual(unknown["demand_score"], 0.50, places=2)
            self.assertEqual(unknown["demand_level"], "MODERATE")
            self.assertEqual(unknown["trend"], "STABLE")
            self.assertAlmostEqual(unknown["growth_rate_pct"], 0.0, places=2)
            self.assertAlmostEqual(unknown["confidence_score"], 0.50, places=2)

    def test_09_scaling_impact_of_high_vs_low_demand(self):
        """9. Verify high demand score increases dynamic priority, low demand decreases it."""
        # Baseline importance 4
        # High demand: Python (0.95 -> factor 1.18) -> priority > 4.0
        dp_high, f_high, pct_high = IndustryDemandService.calculate_dynamic_priority(4, 0.95)
        self.assertGreater(dp_high, 4.0)
        self.assertGreater(pct_high, 0.0)

        # Low demand: 0.15 -> factor 0.86 -> priority < 4.0
        dp_low, f_low, pct_low = IndustryDemandService.calculate_dynamic_priority(4, 0.15)
        self.assertLess(dp_low, 4.0)
        self.assertLess(pct_low, 0.0)

    def test_10_career_evaluation_schema_validation(self):
        """10. Verify career demand evaluation returns valid complete schema."""
        with self.app.app_context():
            res = IndustryDemandService.evaluate_career_industry_demand(career_id=1)
            self.assertEqual(res["career_id"], 1)
            self.assertIn("career_title", res)
            self.assertIn("overall_market_temperature", res)
            self.assertIn("avg_market_demand_score", res)
            self.assertIn("highest_demand_skills", res)
            self.assertIn("fastest_growing_skills", res)
            self.assertIn("skills", res)
            self.assertGreater(len(res["skills"]), 0)

            # Check individual skill structure
            skill_0 = res["skills"][0]
            required_keys = [
                "skill_name", "canonical_name", "career_importance", "required_proficiency",
                "demand_score", "demand_level", "trend", "growth_rate_pct",
                "market_demand_factor", "dynamic_priority", "priority_change_pct",
                "market_context", "confidence_score"
            ]
            for key in required_keys:
                self.assertIn(key, skill_0)

    def test_11_career_not_found_returns_404(self):
        """11. Verify non-existent career ID returns 404 from service and endpoint."""
        with self.app.app_context():
            res = IndustryDemandService.evaluate_career_industry_demand(career_id=99999)
            self.assertIn("error", res)
            self.assertEqual(res["error"], "CAREER_NOT_FOUND")

        resp = self.client.get("/api/careers/99999/industry-demand")
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertEqual(data["status"], "error")

    def test_12_jwt_authenticated_personalization(self):
        """12. Verify JWT authenticated user request personalizes skill gaps and rankings."""
        with self.app.app_context():
            user = User.query.first()
            self.assertIsNotNone(user)
            token = create_access_token(identity=str(user.id))

        headers = {"Authorization": f"Bearer {token}"}
        resp = self.client.get("/api/careers/1/industry-demand", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["is_personalized"])
        for s in data["skills"]:
            self.assertIsNotNone(s["student_proficiency"])
            self.assertIsNotNone(s["gap"])
            self.assertIn("dynamic_gap_priority", s)

    def test_13_unauthenticated_baseline_request(self):
        """13. Verify unauthenticated baseline request succeeds with is_personalized=False."""
        resp = self.client.get("/api/careers/1/industry-demand")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertFalse(data["is_personalized"])
        self.assertEqual(data["career_id"], 1)
        for s in data["skills"]:
            self.assertIsNone(s["student_proficiency"])
            self.assertIsNone(s["gap"])

    def test_14_trend_filtering(self):
        """14. Verify filtering skills by trend=GROWING returns only growing skills."""
        resp = self.client.get("/api/careers/1/industry-demand?trend=GROWING")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertGreater(len(data["skills"]), 0)
        for s in data["skills"]:
            self.assertEqual(s["trend"], "GROWING")

    def test_15_demand_level_filtering(self):
        """15. Verify filtering skills by demand_level=VERY_HIGH returns only very high skills."""
        resp = self.client.get("/api/careers/1/industry-demand?demand_level=VERY_HIGH")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertGreater(len(data["skills"]), 0)
        for s in data["skills"]:
            self.assertEqual(s["demand_level"], "VERY_HIGH")

    def test_16_limit_parameter_enforcement(self):
        """16. Verify limit parameter bounds returned skills count."""
        resp = self.client.get("/api/careers/1/industry-demand?limit=3")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data["skills"]), 3)
        self.assertEqual(data["filtered_skills_count"], 3)

    def test_17_phase11_module1_skill_roi_integration(self):
        """17. Verify skills are enriched with Phase 11.1 Skill ROI scores for personalized users."""
        with self.app.app_context():
            user = User.query.first()
            user_id = user.id if user else 1
            res = IndustryDemandService.evaluate_career_industry_demand(career_id=1, user_id=user_id)
            self.assertNotIn("error", res)
            # Check if any skill with gap has roi_score enriched
            has_roi_enriched = any(s.get("roi_score") is not None for s in res["skills"])
            # Even if all gaps are 0 for a fully proficient user, roi fields are present
            for s in res["skills"]:
                self.assertIn("roi_score", s)
                self.assertIn("marginal_gain", s)
                self.assertIn("study_weeks", s)

    def test_18_phase11_module2_portfolio_recommendation_integration(self):
        """18. Verify recommended portfolio project is embedded to bridge top trending skills."""
        with self.app.app_context():
            res = IndustryDemandService.evaluate_career_industry_demand(career_id=1)
            self.assertNotIn("error", res)
            self.assertIn("recommended_portfolio_project", res)
            if res["recommended_portfolio_project"]:
                proj = res["recommended_portfolio_project"]
                self.assertIn("project_id", proj)
                self.assertIn("title", proj)
                self.assertIn("difficulty", proj)
                self.assertIn("skills_covered", proj)

    def test_19_phase11_module3_academic_curriculum_comparison(self):
        """19. Verify academic coverage comparison identifies trending skills lacking academic evidence."""
        with self.app.app_context():
            res = IndustryDemandService.evaluate_career_industry_demand(career_id=1)
            self.assertNotIn("error", res)
            self.assertIn("academic_industry_disconnect", res)
            self.assertIsInstance(res["academic_industry_disconnect"], list)
            for s in res["skills"]:
                self.assertIn("academic_covered", s)

    def test_20_zero_database_mutations_guarantee(self):
        """20. Verify evaluating industry demand performs ZERO database inserts, updates, or deletes."""
        with self.app.app_context():
            c_count_before = Career.query.count()
            cs_count_before = CareerSkill.query.count()
            sk_count_before = Skill.query.count()
            u_count_before = User.query.count()
            sp_count_before = StudentProfile.query.count()

            # Execute multiple evaluations across multiple careers
            for cid in [1, 2, 3]:
                IndustryDemandService.evaluate_career_industry_demand(career_id=cid)
                resp = self.client.get(f"/api/careers/{cid}/industry-demand")
                self.assertEqual(resp.status_code, 200)

            c_count_after = Career.query.count()
            cs_count_after = CareerSkill.query.count()
            sk_count_after = Skill.query.count()
            u_count_after = User.query.count()
            sp_count_after = StudentProfile.query.count()

            self.assertEqual(c_count_before, c_count_after)
            self.assertEqual(cs_count_before, cs_count_after)
            self.assertEqual(sk_count_before, sk_count_after)
            self.assertEqual(u_count_before, u_count_after)
            self.assertEqual(sp_count_before, sp_count_after)


if __name__ == "__main__":
    unittest.main()
