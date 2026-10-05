"""
Phase 4 Verification Test Suite for AI Career Navigator.

Tests:
1. Curated Learning Resource Catalog & Service
2. Multi-Career Recommendation Engine
3. Career Transition Pathway Analysis
4. Resume Skill Extraction & Canonical Mapping Pipeline
5. Phase 4 API Endpoints (/api/careers/recommendations, /api/careers/transition,
   /api/learning-resources, /api/skills/extract-resume)
6. Error handling, empty inputs, and database integrity
"""

import io
import os
import sys
import unittest
from types import SimpleNamespace

# Ensure backend root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from extensions import db
from models.canonical_skill import CanonicalSkill
from models.career import Career
from models.learning_resource import LearningResource
from models.skill import Skill
from models.user import User
from services.career_recommendation_service import CareerRecommendationService
from services.career_transition_service import CareerTransitionService
from services.learning_resource_service import LearningResourceService
from services.resume_extraction_service import ResumeExtractionService


class TestLearningResourceCatalog(unittest.TestCase):
    """Tests for the Learning Resource catalog, models, and service queries."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()

    def test_curated_resources_seeded(self):
        """Curated benchmark learning resources should be present and valid."""
        with self.app.app_context():
            count = LearningResource.query.count()
            self.assertGreaterEqual(count, 10, "Expected at least 10 curated learning resources")

            # Check required fields on all resources
            resources = LearningResource.query.all()
            for r in resources:
                self.assertIsNotNone(r.canonical_skill_id)
                self.assertIsNotNone(r.title)
                self.assertIsNotNone(r.resource_type)
                self.assertIsNotNone(r.provider)
                self.assertTrue(r.url.startswith("http"))
                self.assertIn(r.difficulty_level, ["Beginner", "Intermediate", "Advanced"])
                self.assertEqual(r.status, "Active")
                self.assertIsNotNone(r.canonical_skill)

    def test_query_by_canonical_skill(self):
        """Retrieve resources for a specific canonical skill (e.g. Python)."""
        with self.app.app_context():
            python_skill = CanonicalSkill.query.filter_by(normalized_name="python").first()
            self.assertIsNotNone(python_skill)

            resources = LearningResourceService.get_resources_for_canonical_skill(python_skill.id)
            self.assertGreaterEqual(len(resources), 1)
            for r in resources:
                self.assertEqual(r["canonical_skill_id"], python_skill.id)

    def test_search_and_filter_resources(self):
        """Search learning resources by query text, difficulty, and type."""
        with self.app.app_context():
            # Search by keyword "AWS"
            aws_results = LearningResourceService.search_resources(query_text="AWS")
            self.assertGreaterEqual(len(aws_results), 1)
            self.assertTrue(any("AWS" in r["title"] or "AWS" in r["provider"] for r in aws_results))

            # Filter by difficulty "Beginner"
            beginner_results = LearningResourceService.search_resources(difficulty_level="Beginner")
            self.assertGreaterEqual(len(beginner_results), 1)
            for r in beginner_results:
                self.assertEqual(r["difficulty_level"].lower(), "beginner")


class TestMultiCareerRecommendationEngine(unittest.TestCase):
    """Tests for the Multi-Career Recommendation Service."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()

    def test_recommendation_ranking_for_cloud_profile(self):
        """A student with cloud competencies should receive Cloud Engineer as top recommendation."""
        with self.app.app_context():
            # Mock student skills matching Cloud Engineer: Docker (9/10), Python (8/10), AWS (8/10)
            mock_skills = [
                SimpleNamespace(id=1, canonical_skill_id=9, skill_name="Docker", proficiency=9),
                SimpleNamespace(id=2, canonical_skill_id=1, skill_name="Python", proficiency=8),
                SimpleNamespace(id=3, canonical_skill_id=16, skill_name="AWS", proficiency=8),
            ]

            recs = CareerRecommendationService.recommend_careers(mock_skills)
            self.assertGreaterEqual(len(recs), 5)

            # Top career should be Cloud Engineer or DevOps Engineer
            top_rec = recs[0]
            self.assertIn(top_rec["career_title"], ["Cloud Engineer", "DevOps Engineer", "Software Developer"])
            self.assertGreater(top_rec["recommendation_score"], 40.0)
            self.assertGreater(top_rec["readiness_percentage"], 40.0)
            self.assertTrue(len(top_rec["matched_skills"]) >= 2)
            self.assertIn("strong foundation", top_rec["explanation"])

    def test_recommendation_with_empty_skills(self):
        """A student with 0 skills should receive 0% readiness across all careers."""
        with self.app.app_context():
            recs = CareerRecommendationService.recommend_careers([])
            self.assertGreaterEqual(len(recs), 5)
            for r in recs:
                self.assertEqual(r["readiness_percentage"], 0.0)
                self.assertEqual(r["recommendation_score"], 0.0)
                self.assertEqual(r["skill_acquisition_distance"], 100.0)
                self.assertEqual(len(r["matched_skills"]), 0)
                self.assertIn("no recorded prerequisites", r["explanation"])

    def test_recommendation_deterministic_sorting(self):
        """Recommendations must be sorted descending by score and readiness."""
        with self.app.app_context():
            mock_skills = [
                SimpleNamespace(id=1, canonical_skill_id=1, skill_name="Python", proficiency=8),
                SimpleNamespace(id=2, canonical_skill_id=3, skill_name="SQL", proficiency=8),
            ]
            recs = CareerRecommendationService.recommend_careers(mock_skills)
            for i in range(len(recs) - 1):
                self.assertGreaterEqual(
                    recs[i]["recommendation_score"],
                    recs[i + 1]["recommendation_score"]
                )


class TestCareerTransitionPathways(unittest.TestCase):
    """Tests for career-to-career transition pathway analysis."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()

    def test_software_developer_to_cloud_engineer_transition(self):
        """Analyze Software Developer -> Cloud Engineer transition."""
        with self.app.app_context():
            dev = Career.query.filter_by(title="Software Developer").first()
            cloud = Career.query.filter_by(title="Cloud Engineer").first()
            self.assertIsNotNone(dev)
            self.assertIsNotNone(cloud)

            res = CareerTransitionService.analyze_transition(dev.id, cloud.id)
            self.assertIsNotNone(res)

            summary = res["transition_summary"]
            self.assertGreater(summary["overlap_percentage"], 0.0)
            self.assertIn("transition_difficulty", summary)
            self.assertIn("explanation", summary)

            # Check overlapping skills (Python is shared)
            overlap_names = [o["skill_name"] for o in res["overlapping_skills"]]
            self.assertIn("Python", overlap_names)

            # Check additional skills required (AWS, Docker, Linux, Networking)
            add_names = [a["skill_name"] for a in res["additional_skills_required"]]
            self.assertTrue(any(s in add_names for s in ["AWS", "Docker", "Linux", "Networking"]))

            # Check surplus skills in source (Java, Data Structures, Git, SQL)
            surplus_names = [s["skill_name"] for s in res["surplus_source_skills"]]
            self.assertTrue(any(s in surplus_names for s in ["Java", "Data Structures", "SQL"]))

    def test_nonexistent_career_transition(self):
        """Invalid career IDs should return None."""
        with self.app.app_context():
            res = CareerTransitionService.analyze_transition(9999, 1)
            self.assertIsNone(res)


class TestResumeSkillExtraction(unittest.TestCase):
    """Tests for the resume skill extraction and canonical mapping pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()

    def test_resume_extraction_pipeline(self):
        """Detect skills from structured technical resume text."""
        resume = """
        Alice Smith - Cloud & DevOps Specialist

        TECHNICAL SKILLS
        Programming: Python, Java, SQL
        Cloud Infrastructure: AWS, Docker, Kubernetes, Linux
        Tools & Version Control: Git, CI/CD

        EXPERIENCE
        DevOps Intern - TechCorp
        - Managed Kubernetes clusters and provisioned AWS resources.
        - Wrote Python automation scripts and configured Docker containers.

        EDUCATION
        B.S. in Information Technology
        """
        with self.app.app_context():
            result = ResumeExtractionService.extract_skills_from_text(resume)
            self.assertEqual(result["status"], "success")
            self.assertIn("skills", result["sections_detected"])
            self.assertIn("experience", result["sections_detected"])
            self.assertGreaterEqual(result["detected_skills_count"], 6)

            detected_names = [s["canonical_name"] for s in result["detected_skills"]]
            self.assertIn("Python", detected_names)
            self.assertIn("AWS", detected_names)
            self.assertIn("Docker", detected_names)
            self.assertIn("Kubernetes", detected_names)
            self.assertIn("Git", detected_names)

            for s in result["detected_skills"]:
                self.assertIsNotNone(s["canonical_skill_id"])
                self.assertGreaterEqual(s["confidence_score"], 0.70)
                self.assertIn(s["confidence_tier"], ["HIGH", "MEDIUM", "LOW"])
                self.assertGreaterEqual(s["suggested_proficiency"], 5)

    def test_empty_resume_handling(self):
        """Empty or whitespace-only resume should return zero detected skills safely."""
        with self.app.app_context():
            result = ResumeExtractionService.extract_skills_from_text("   \n\t  ")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["detected_skills_count"], 0)
            self.assertEqual(len(result["detected_skills"]), 0)


class TestPhase4APIEndpoints(unittest.TestCase):
    """Integration tests for all newly introduced Phase 4 REST API endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_api_career_recommendations(self):
        """GET /api/careers/recommendations should return ranked careers."""
        response = self.client.get("/api/careers/recommendations?user_id=1")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 5)
        self.assertIsInstance(data["recommendations"], list)

        first_rec = data["recommendations"][0]
        self.assertIn("recommendation_score", first_rec)
        self.assertIn("readiness_percentage", first_rec)
        self.assertIn("matched_skills", first_rec)
        self.assertIn("missing_skills", first_rec)
        self.assertIn("explanation", first_rec)

    def test_api_career_transition_get(self):
        """GET /api/careers/1/transition/6 should return transition analysis."""
        response = self.client.get("/api/careers/1/transition/6")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        trans = data["transition"]
        self.assertEqual(trans["source_career"]["id"], 1)
        self.assertEqual(trans["target_career"]["id"], 6)
        self.assertIn("transition_summary", trans)
        self.assertIn("overlapping_skills", trans)
        self.assertIn("additional_skills_required", trans)

    def test_api_career_transition_post(self):
        """POST /api/careers/transition should accept JSON body and return analysis."""
        payload = {"from_career_id": 1, "to_career_id": 6}
        response = self.client.post("/api/careers/transition", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("transition", data)

    def test_api_career_transition_invalid_input(self):
        """POST /api/careers/transition should return 400 when missing career IDs."""
        response = self.client.post("/api/careers/transition", json={"from_career_id": 1})
        self.assertEqual(response.status_code, 400)

        # 404 on unknown career ID
        response404 = self.client.get("/api/careers/99999/transition/1")
        self.assertEqual(response404.status_code, 404)

    def test_api_learning_resources_list(self):
        """GET /api/learning-resources should return curated catalog."""
        response = self.client.get("/api/learning-resources")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 5)
        self.assertIsInstance(data["resources"], list)

    def test_api_learning_resources_filtered(self):
        """GET /api/learning-resources?difficulty=Beginner should filter by difficulty."""
        response = self.client.get("/api/learning-resources?difficulty=Beginner")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        for r in data["resources"]:
            self.assertEqual(r["difficulty_level"].lower(), "beginner")

    def test_api_canonical_skill_resources(self):
        """GET /api/skills/canonical/1/resources should return Python resources."""
        response = self.client.get("/api/skills/canonical/1/resources")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["canonical_skill_id"], 1)
        self.assertGreaterEqual(data["count"], 1)

    def test_api_extract_resume_json(self):
        """POST /api/skills/extract-resume should extract skills from JSON text."""
        payload = {
            "resume_text": "Experienced Python and AWS developer with strong SQL and Docker skills."
        }
        response = self.client.post("/api/skills/extract-resume", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["detected_skills_count"], 3)
        detected_names = [s["canonical_name"] for s in data["detected_skills"]]
        self.assertIn("Python", detected_names)
        self.assertIn("AWS", detected_names)
        self.assertIn("Docker", detected_names)

    def test_api_extract_resume_empty_input(self):
        """POST /api/skills/extract-resume should return 400 on empty text."""
        response = self.client.post("/api/skills/extract-resume", json={"resume_text": ""})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
