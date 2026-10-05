"""
Unit and Integration Tests for Phase 7 Modules in AI Career Navigator.

Covers:
- Curated Learning Catalog Expansion (Industry Certifications & Projects)
- Career Labor Market Outlook Service
- Career Market Intelligence API Endpoints
"""

import unittest
from app import create_app
from extensions import db
from models.learning_resource import LearningResource
from services.career_market_service import CareerMarketService, CAREER_MARKET_INTELLIGENCE
from services.roadmap_service import generate_learning_roadmap


class TestPhase7LearningCatalogExpansion(unittest.TestCase):
    """Test suite verifying curated certifications and project learning resources."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_catalog_certifications_count(self):
        """Verify database has at least 10 official industry certifications."""
        count = LearningResource.query.filter_by(resource_type="Certification").count()
        self.assertGreaterEqual(count, 10, f"Expected at least 10 certifications, found {count}")

    def test_catalog_projects_count(self):
        """Verify database has at least 10 real-world practical projects."""
        count = LearningResource.query.filter_by(resource_type="Project").count()
        self.assertGreaterEqual(count, 10, f"Expected at least 10 projects, found {count}")

    def test_roadmap_project_and_cert_integration(self):
        """Verify roadmap generation produces certifications and structured steps."""
        dummy_gaps = [
            {
                "skill_name": "AWS",
                "status": "MISSING",
                "importance": 5,
                "required_level": 4,
                "current_proficiency": 0,
                "priority_score": 20.0
            },
            {
                "skill_name": "Docker",
                "status": "WEAK",
                "importance": 4,
                "required_level": 3,
                "current_proficiency": 1,
                "priority_score": 8.0
            }
        ]
        roadmap = generate_learning_roadmap("Cloud Engineer", dummy_gaps)
        self.assertIn("sequential_steps", roadmap)
        self.assertGreaterEqual(len(roadmap["sequential_steps"]), 2)
        step1 = roadmap["sequential_steps"][0]
        self.assertIn("industry_certifications", step1)
        self.assertGreater(len(step1["industry_certifications"]), 0)


class TestPhase7MarketOutlookService(unittest.TestCase):
    """Test suite verifying Career Market Outlook service logic."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_market_intelligence_catalog_completeness(self):
        """Verify all 10 canonical careers have market intelligence records."""
        self.assertEqual(len(CAREER_MARKET_INTELLIGENCE), 10)
        for cid, record in CAREER_MARKET_INTELLIGENCE.items():
            self.assertEqual(record["career_id"], cid)
            self.assertIn("demand_score", record)
            self.assertIn("demand_level", record)
            self.assertIn("five_year_growth_rate", record)
            self.assertIn("salary_bands", record)
            self.assertIn("entry_level", record["salary_bands"])
            self.assertIn("median", record["salary_bands"])
            self.assertIn("senior", record["salary_bands"])
            self.assertGreater(len(record["top_hiring_sectors"]), 0)
            self.assertGreater(len(record["key_trends"]), 0)

    def test_service_lookup_by_id(self):
        """Verify lookup by valid and invalid career IDs."""
        outlook = CareerMarketService.get_market_outlook_by_career_id(1)
        self.assertIsNotNone(outlook)
        self.assertEqual(outlook["career_title"], "Software Developer")
        self.assertGreater(outlook["demand_score"], 80)

        invalid_outlook = CareerMarketService.get_market_outlook_by_career_id(999999)
        self.assertIsNone(invalid_outlook)

    def test_service_comparison_logic(self):
        """Verify comparison returns valid items for given career IDs."""
        comparison = CareerMarketService.compare_market_outlooks([1, 6])
        self.assertEqual(len(comparison), 2)
        titles = [c["career_title"] for c in comparison]
        self.assertIn("Software Developer", titles)
        self.assertIn("Cloud Engineer", titles)


class TestPhase7APIEndpoints(unittest.TestCase):
    """Test suite verifying Phase 7 API endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_api_career_market_outlook_all(self):
        """GET /api/careers/market-outlook should return all career outlooks."""
        resp = self.client.get("/api/careers/market-outlook")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 10)
        self.assertEqual(len(data["market_outlooks"]), data["count"])

    def test_api_career_market_outlook_single(self):
        """GET /api/careers/1/market-outlook should return Software Developer outlook."""
        resp = self.client.get("/api/careers/1/market-outlook")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["market_outlook"]["career_id"], 1)
        self.assertEqual(data["market_outlook"]["career_title"], "Software Developer")
        self.assertIn("salary_bands", data["market_outlook"])

    def test_api_career_market_outlook_404(self):
        """GET /api/careers/999999/market-outlook should return 404."""
        resp = self.client.get("/api/careers/999999/market-outlook")
        self.assertEqual(resp.status_code, 404)

    def test_api_career_market_outlook_compare(self):
        """POST /api/careers/market-outlook/compare should return comparison list."""
        resp = self.client.post(
            "/api/careers/market-outlook/compare",
            json={"career_ids": [1, 2]}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 2)

    def test_api_career_market_outlook_compare_invalid(self):
        """POST /api/careers/market-outlook/compare should return 400 on empty input."""
        resp = self.client.post(
            "/api/careers/market-outlook/compare",
            json={}
        )
        self.assertEqual(resp.status_code, 400)

    def test_api_cors_preflight(self):
        """OPTIONS preflight should return 200 with CORS headers."""
        resp = self.client.options("/api/careers/market-outlook")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

    def test_api_learning_resources_certifications_filter(self):
        """GET /api/learning-resources?type=Certification should return certifications."""
        resp = self.client.get("/api/learning-resources?type=Certification")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 10)
        for r in data["resources"]:
            self.assertEqual(r["resource_type"], "Certification")

    def test_api_learning_resources_projects_filter(self):
        """GET /api/learning-resources?type=Project should return projects."""
        resp = self.client.get("/api/learning-resources?type=Project")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 10)
        for r in data["resources"]:
            self.assertEqual(r["resource_type"], "Project")


if __name__ == "__main__":
    unittest.main()
