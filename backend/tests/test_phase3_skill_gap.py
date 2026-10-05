"""
Phase 3 Verification & Skill-Gap Test Suite for AI Career Navigator.

Validates:
- Case 1: Student has all required skills (MATCHED / EXCEEDS)
- Case 2: Student has none of the required skills (MISSING)
- Case 3: Student has skills below required proficiency (WEAK)
- Case 4: Student has a mixture of matched, weak, and missing skills
- Deterministic prioritization formula and explainable justifications
- Learning roadmap generation and industry certification mapping
- API Endpoints: /api/careers, /api/careers/<id>/skill-gap, /api/careers/<id>/roadmap
- Data Integrity: No duplicate canonical skills, foreign key validity, provenance preservation
"""

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
from models.career_skill import CareerSkill
from models.data_source import DataSource
from models.skill import Skill
from models.skill_alias import SkillAlias
from models.user import User
from services.roadmap_service import RoadmapService, generate_learning_roadmap
from services.skill_gap_service import SkillGapService, SkillGapStatus, assess_career_skill_gap


class TestSkillGapEngine(unittest.TestCase):
    """Unit tests for the deterministic SkillGapService."""

    def setUp(self):
        # Create a mock target career with 4 required skills
        self.mock_career = SimpleNamespace(
            id=101,
            title="Cloud Solutions Engineer",
            domain="Cloud & DevOps",
            description="Designs and maintains scalable cloud infrastructure.",
            skills=[
                SimpleNamespace(
                    id=1,
                    career_id=101,
                    canonical_skill_id=10,
                    skill_name="Python",
                    required_level=4,
                    importance=5
                ),
                SimpleNamespace(
                    id=2,
                    career_id=101,
                    canonical_skill_id=11,
                    skill_name="AWS",
                    required_level=4,
                    importance=5
                ),
                SimpleNamespace(
                    id=3,
                    career_id=101,
                    canonical_skill_id=12,
                    skill_name="Docker",
                    required_level=3,
                    importance=4
                ),
                SimpleNamespace(
                    id=4,
                    career_id=101,
                    canonical_skill_id=13,
                    skill_name="Linux",
                    required_level=3,
                    importance=3
                )
            ]
        )

    def test_case_1_all_required_skills_matched_or_exceeds(self):
        """Case 1: Student possesses all required skills at or above proficiency."""
        student_skills = [
            # Python: raw 8 -> normalized 4.0 == required 4 -> MATCHED
            SimpleNamespace(id=1, canonical_skill_id=10, skill_name="Python", proficiency=8),
            # AWS: raw 10 -> normalized 5.0 > required 4 -> EXCEEDS
            SimpleNamespace(id=2, canonical_skill_id=11, skill_name="AWS", proficiency=10),
            # Docker: raw 6 -> normalized 3.0 == required 3 -> MATCHED
            SimpleNamespace(id=3, canonical_skill_id=12, skill_name="Docker", proficiency=6),
            # Linux: raw 8 -> normalized 4.0 > required 3 -> EXCEEDS
            SimpleNamespace(id=4, canonical_skill_id=13, skill_name="Linux", proficiency=8),
        ]

        result = SkillGapService.evaluate_career_gap(self.mock_career, student_skills)

        summary = result["summary"]
        self.assertEqual(summary["total_required_skills"], 4)
        self.assertEqual(summary["matched_skills"], 4)
        self.assertEqual(summary["weak_skills"], 0)
        self.assertEqual(summary["missing_skills"], 0)
        self.assertEqual(summary["readiness_percentage"], 100.0)

        # Ensure all statuses are MATCHED or EXCEEDS, priority score is 0, and gap value is 0
        for gap in result["prioritized_skill_gaps"]:
            self.assertIn(gap["status"], [SkillGapStatus.MATCHED, SkillGapStatus.EXCEEDS])
            self.assertEqual(gap["gap_value"], 0.0)
            self.assertEqual(gap["priority_score"], 0.0)
            self.assertEqual(gap["priority_level"], "NONE")
            self.assertTrue(len(gap["explanation"]) > 0)

    def test_case_2_none_of_required_skills_present(self):
        """Case 2: Student has zero skills recorded."""
        student_skills = []

        result = SkillGapService.evaluate_career_gap(self.mock_career, student_skills)

        summary = result["summary"]
        self.assertEqual(summary["total_required_skills"], 4)
        self.assertEqual(summary["matched_skills"], 0)
        self.assertEqual(summary["weak_skills"], 0)
        self.assertEqual(summary["missing_skills"], 4)
        self.assertEqual(summary["readiness_percentage"], 0.0)

        gaps = result["prioritized_skill_gaps"]
        self.assertEqual(len(gaps), 4)

        for gap in gaps:
            self.assertEqual(gap["status"], SkillGapStatus.MISSING)
            self.assertEqual(gap["current_proficiency"], 0.0)
            self.assertEqual(gap["gap_value"], float(gap["required_level"]))
            # Formula: importance * gap_value * 1.25
            expected_score = round(gap["importance"] * float(gap["required_level"]) * 1.25, 2)
            self.assertEqual(gap["priority_score"], expected_score)
            self.assertIn("missing", gap["explanation"].lower())

        # Check deterministic descending ordering: Python (5*4*1.25=25) and AWS (25) at top
        self.assertEqual(gaps[0]["priority_score"], 25.0)
        self.assertEqual(gaps[1]["priority_score"], 25.0)
        self.assertEqual(gaps[2]["priority_score"], 15.0)  # Docker (4*3*1.25=15)
        self.assertEqual(gaps[3]["priority_score"], 11.25) # Linux (3*3*1.25=11.25)

    def test_case_3_all_skills_weak(self):
        """Case 3: Student has required skills but below the required proficiency."""
        student_skills = [
            # Python: raw 4 -> normalized 2.0 < required 4 (gap = 2.0)
            SimpleNamespace(id=1, canonical_skill_id=10, skill_name="Python", proficiency=4),
            # AWS: raw 2 -> normalized 1.0 < required 4 (gap = 3.0)
            SimpleNamespace(id=2, canonical_skill_id=11, skill_name="AWS", proficiency=2),
            # Docker: raw 2 -> normalized 1.0 < required 3 (gap = 2.0)
            SimpleNamespace(id=3, canonical_skill_id=12, skill_name="Docker", proficiency=2),
            # Linux: raw 4 -> normalized 2.0 < required 3 (gap = 1.0)
            SimpleNamespace(id=4, canonical_skill_id=13, skill_name="Linux", proficiency=4),
        ]

        result = SkillGapService.evaluate_career_gap(self.mock_career, student_skills)

        summary = result["summary"]
        self.assertEqual(summary["total_required_skills"], 4)
        self.assertEqual(summary["matched_skills"], 0)
        self.assertEqual(summary["weak_skills"], 4)
        self.assertEqual(summary["missing_skills"], 0)

        # Total required points: 4+4+3+3 = 14. Achieved points: 2+1+1+2 = 6. (6/14)*100 = 42.9%
        self.assertEqual(summary["readiness_percentage"], 42.9)

        gaps = result["prioritized_skill_gaps"]
        # AWS: importance 5 * gap 3.0 * 1.0 = 15.0 -> HIGH
        # Python: importance 5 * gap 2.0 * 1.0 = 10.0 -> MEDIUM
        # Docker: importance 4 * gap 2.0 * 1.0 = 8.0 -> MEDIUM
        # Linux: importance 3 * gap 1.0 * 1.0 = 3.0 -> LOW
        self.assertEqual(gaps[0]["skill_name"], "AWS")
        self.assertEqual(gaps[0]["gap_value"], 3.0)
        self.assertEqual(gaps[0]["priority_score"], 15.0)
        self.assertEqual(gaps[0]["priority_level"], "HIGH")

        self.assertEqual(gaps[1]["skill_name"], "Python")
        self.assertEqual(gaps[1]["gap_value"], 2.0)
        self.assertEqual(gaps[1]["priority_score"], 10.0)
        self.assertEqual(gaps[1]["priority_level"], "MEDIUM")

        self.assertEqual(gaps[2]["skill_name"], "Docker")
        self.assertEqual(gaps[2]["gap_value"], 2.0)
        self.assertEqual(gaps[2]["priority_score"], 8.0)
        self.assertEqual(gaps[2]["priority_level"], "MEDIUM")

        self.assertEqual(gaps[3]["skill_name"], "Linux")
        self.assertEqual(gaps[3]["gap_value"], 1.0)
        self.assertEqual(gaps[3]["priority_score"], 3.0)
        self.assertEqual(gaps[3]["priority_level"], "LOW")

    def test_case_4_mixture_of_matched_weak_missing(self):
        """Case 4: Student has a mixture of matched, weak, and missing skills."""
        student_skills = [
            # Python: raw 8 -> normalized 4.0 == required 4 -> MATCHED
            SimpleNamespace(id=1, canonical_skill_id=10, skill_name="Python", proficiency=8),
            # Docker: raw 2 -> normalized 1.0 < required 3 -> WEAK (gap 2.0)
            SimpleNamespace(id=2, canonical_skill_id=12, skill_name="Docker", proficiency=2),
            # AWS and Linux are MISSING
        ]

        result = SkillGapService.evaluate_career_gap(self.mock_career, student_skills)

        summary = result["summary"]
        self.assertEqual(summary["total_required_skills"], 4)
        self.assertEqual(summary["matched_skills"], 1)
        self.assertEqual(summary["weak_skills"], 1)
        self.assertEqual(summary["missing_skills"], 2)

        # Achieved: Python 4.0 + Docker 1.0 = 5.0 out of 14 -> 35.7%
        self.assertEqual(summary["readiness_percentage"], 35.7)

        gaps = result["prioritized_skill_gaps"]
        # Priorities:
        # AWS: MISSING, gap 4.0, imp 5 -> 5 * 4.0 * 1.25 = 25.0 (HIGH)
        # Linux: MISSING, gap 3.0, imp 3 -> 3 * 3.0 * 1.25 = 11.25 (MEDIUM)
        # Docker: WEAK, gap 2.0, imp 4 -> 4 * 2.0 * 1.0 = 8.0 (MEDIUM)
        # Python: MATCHED, gap 0.0 -> score 0.0 (NONE)
        self.assertEqual(gaps[0]["skill_name"], "AWS")
        self.assertEqual(gaps[0]["status"], SkillGapStatus.MISSING)
        self.assertEqual(gaps[0]["priority_score"], 25.0)

        self.assertEqual(gaps[1]["skill_name"], "Linux")
        self.assertEqual(gaps[1]["status"], SkillGapStatus.MISSING)
        self.assertEqual(gaps[1]["priority_score"], 11.25)

        self.assertEqual(gaps[2]["skill_name"], "Docker")
        self.assertEqual(gaps[2]["status"], SkillGapStatus.WEAK)
        self.assertEqual(gaps[2]["priority_score"], 8.0)

        self.assertEqual(gaps[3]["skill_name"], "Python")
        self.assertEqual(gaps[3]["status"], SkillGapStatus.MATCHED)
        self.assertEqual(gaps[3]["priority_score"], 0.0)


class TestRoadmapService(unittest.TestCase):
    """Unit tests for the RoadmapService and certification recommendations."""

    def test_roadmap_filtering_and_step_generation(self):
        """Roadmap should include only actionable gaps (MISSING and WEAK) and sequence them."""
        skill_gaps = [
            {
                "skill_name": "AWS",
                "status": "MISSING",
                "required_level": 4,
                "current_proficiency": 0.0,
                "importance": 5,
                "priority_score": 25.0,
            },
            {
                "skill_name": "Docker",
                "status": "WEAK",
                "required_level": 3,
                "current_proficiency": 1.0,
                "importance": 4,
                "priority_score": 8.0,
            },
            {
                "skill_name": "Python",
                "status": "MATCHED",
                "required_level": 4,
                "current_proficiency": 4.0,
                "importance": 5,
                "priority_score": 0.0,
            }
        ]

        roadmap = generate_learning_roadmap("Cloud Architect", skill_gaps)

        # Python should be omitted since it is MATCHED
        self.assertEqual(roadmap["total_roadmap_steps"], 2)
        steps = roadmap["sequential_steps"]
        self.assertEqual(len(steps), 2)

        self.assertEqual(steps[0]["step_number"], 1)
        self.assertEqual(steps[0]["skill_name"], "AWS")
        self.assertEqual(steps[0]["gap_status"], "MISSING")
        self.assertTrue(len(steps[0]["industry_certifications"]) > 0)
        # AWS should match AWS certifications
        cert_names = [c["certification_name"] for c in steps[0]["industry_certifications"]]
        self.assertTrue(any("AWS" in c for c in cert_names))

        self.assertEqual(steps[1]["step_number"], 2)
        self.assertEqual(steps[1]["skill_name"], "Docker")
        self.assertEqual(steps[1]["gap_status"], "WEAK")
        docker_certs = [c["certification_name"] for c in steps[1]["industry_certifications"]]
        self.assertTrue(any("Docker" in c for c in docker_certs))

        # Check explainability string
        self.assertIn("Cloud Architect", steps[0]["reason"])
        self.assertIn("AWS", steps[0]["reason"])

    def test_certification_mapping_coverage(self):
        """Verify industry certifications exist for key technology areas."""
        test_queries = [
            ("AWS", "aws"),
            ("CCNA", "networking"),
            ("Linux", "linux"),
            ("Docker", "docker"),
            ("Kubernetes", "kubernetes"),
            ("Python", "python")
        ]
        for name, norm in test_queries:
            certs = RoadmapService.get_certifications_for_skill(name, norm)
            self.assertTrue(len(certs) > 0, f"Expected certifications for {name}")


class TestAPIAndDataIntegrity(unittest.TestCase):
    """Integration tests on live Flask app and PostgreSQL database."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_api_list_careers(self):
        """GET /api/careers should return 200 with list of careers."""
        response = self.client.get("/api/careers")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["count"], 0)
        self.assertIsInstance(data["careers"], list)

    def test_api_get_career_detail(self):
        """GET /api/careers/1 should return career details and required skills."""
        response = self.client.get("/api/careers/1")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        career = data["career"]
        self.assertEqual(career["id"], 1)
        self.assertTrue(len(career["required_skills"]) > 0)

    def test_api_get_career_not_found(self):
        """GET /api/careers/99999 should return 404."""
        response = self.client.get("/api/careers/99999")
        self.assertEqual(response.status_code, 404)

    def test_api_skill_gap_endpoint(self):
        """GET /api/careers/1/skill-gap should return gap analysis payload."""
        # Query with user_id=1
        response = self.client.get("/api/careers/1/skill-gap?user_id=1")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["career_id"], 1)
        self.assertIn("readiness_percentage", data)
        self.assertIn("matched", data)
        self.assertIn("weak", data)
        self.assertIn("missing", data)
        self.assertIn("skill_gaps", data)

    def test_api_roadmap_endpoint(self):
        """GET /api/careers/1/roadmap should return learning roadmap."""
        response = self.client.get("/api/careers/1/roadmap?user_id=1")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["career_id"], 1)
        self.assertIn("readiness_percentage", data)
        self.assertIn("roadmap", data)
        roadmap = data["roadmap"]
        self.assertIn("sequential_steps", roadmap)
        self.assertIn("roadmap_phases", roadmap)

    def test_api_skills_search_and_autocomplete(self):
        """GET /api/skills?q=python should return matching skills."""
        response = self.client.get("/api/skills?q=python")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertTrue(any("python" in s["skill_name"].lower() for s in data))

    def test_data_integrity_no_duplicate_canonical_skills(self):
        """Step 13: Verify zero duplicate canonical skills in database."""
        with self.app.app_context():
            from sqlalchemy import func
            duplicates = (
                db.session.query(CanonicalSkill.normalized_name, func.count(CanonicalSkill.id))
                .group_by(CanonicalSkill.normalized_name)
                .having(func.count(CanonicalSkill.id) > 1)
                .all()
            )
            self.assertEqual(len(duplicates), 0, f"Found duplicate canonical skills: {duplicates}")

    def test_data_integrity_no_orphaned_canonical_skill_ids(self):
        """Step 13: Verify no invalid canonical_skill_id foreign key references."""
        with self.app.app_context():
            valid_ids = {c.id for c in CanonicalSkill.query.all()}
            orphaned_career_skills = [
                cs for cs in CareerSkill.query.all()
                if cs.canonical_skill_id is not None and cs.canonical_skill_id not in valid_ids
            ]
            self.assertEqual(len(orphaned_career_skills), 0, "Found invalid canonical_skill_ids in career_skills")

            orphaned_student_skills = [
                s for s in Skill.query.all()
                if s.canonical_skill_id is not None and s.canonical_skill_id not in valid_ids
            ]
            self.assertEqual(len(orphaned_student_skills), 0, "Found invalid canonical_skill_ids in skills")

    def test_data_integrity_data_sources_provenance(self):
        """Step 13: Verify source provenance records exist."""
        with self.app.app_context():
            sources = DataSource.query.all()
            source_names = {s.source_name for s in sources}
            self.assertIn("O*NET", source_names)
            self.assertIn("ESCO", source_names)
            self.assertGreaterEqual(len(sources), 4)

    def test_data_integrity_raw_and_candidate_datasets_exist(self):
        """Step 13: Verify raw and processed candidate datasets are intact."""
        repo_root = os.path.abspath(os.path.join(BASE_DIR, ".."))
        critical_paths = [
            os.path.join(repo_root, "data/processed/skill_candidates.csv"),
            os.path.join(repo_root, "data/processed/skill_mapping_review.csv"),
            os.path.join(repo_root, "data/processed/esco/skills.csv"),
            os.path.join(repo_root, "data/processed/esco/occupations.csv"),
            os.path.join(repo_root, "data/processed/esco/occupation_skill_relations.csv"),
            os.path.join(repo_root, "data/processed/onet/onet_skill_candidates.csv")
        ]
        for p in critical_paths:
            self.assertTrue(os.path.exists(p), f"Missing critical dataset: {p}")
            self.assertGreater(os.path.getsize(p), 0, f"Empty critical dataset: {p}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
