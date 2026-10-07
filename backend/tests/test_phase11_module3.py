"""
Unit and API Integration Tests for Phase 11 Module 11.3:
Academic Recommendation Benchmarking Engine.

Verifies:
1. Academic skill coverage detection from curriculum baselines.
2. Career skill coverage comparison.
3. Academic-to-career alignment score calculation (importance-weighted).
4. Weighted skill importance impact on alignment score.
5. Missing academic skill detection (industry-specific gaps).
6. Strict distinction between academic coverage and student proficiency.
7. Canonical skill matching and case-insensitive normalization.
8. Alias resolution via SkillAlias.
9. Deterministic results across multiple runs.
10. Custom curriculum and empty evidence handling.
11. Non-existent career ID returns 404.
12. JWT authentication and student personalization.
13. API endpoint GET /api/careers/<id>/academic-benchmark schema validation.
14. Phase 11.1 Skill ROI integration (ROI scores and quickest win enrichment).
15. Phase 11.2 Portfolio Project integration (capstone project bridge).
16. Zero database mutations guarantee.
17. Degree program differences (B.Tech CS vs B.Sc Data Science vs BCA/MCA).
18. Backward compatibility with unauthenticated baseline requests.
"""

import unittest
from app import create_app
from extensions import db
from models.user import User
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from models.student_profile import StudentProfile
from services.academic_benchmark_service import (
    AcademicBenchmarkService,
    SAMPLE_ACADEMIC_CURRICULA,
    PROVENANCE_NOTICE
)
from flask_jwt_extended import create_access_token


class TestPhase11Module3AcademicBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_academic_skill_coverage_detection(self):
        """1. Verify academic skills are extracted from curriculum baselines with correct coverage strength."""
        with self.app.app_context():
            curriculum = SAMPLE_ACADEMIC_CURRICULA["btech_cs"]
            academic_map = AcademicBenchmarkService.extract_academic_skills(curriculum)

            self.assertIn("python", academic_map)
            self.assertIn("java", academic_map)
            self.assertIn("data structures", academic_map)
            self.assertIn("sql", academic_map)
            self.assertIn("linux", academic_map)
            self.assertIn("networking", academic_map)
            self.assertIn("git", academic_map)

            # Strength check
            self.assertEqual(academic_map["python"]["coverage_strength"], 1.0)
            self.assertIn("CS101", academic_map["python"]["courses"][0])

    def test_02_career_skill_coverage_comparison(self):
        """2. Verify career skills are compared against academic coverage for Cloud Engineer."""
        with self.app.app_context():
            # Cloud Engineer (Career 6): Linux, Networking, AWS, Python, Docker
            res = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=6,
                program_id="btech_cs"
            )
            self.assertNotIn("error", res)
            self.assertEqual(res["career_id"], 6)

            # In standard B.Tech CS: Linux, Networking, Python are evidenced; AWS, Docker are industry gaps
            self.assertIn("Linux", res["academic_foundations"])
            self.assertIn("Networking", res["academic_foundations"])
            self.assertIn("Python", res["academic_foundations"])
            self.assertIn("AWS", res["industry_gaps"])
            self.assertIn("Docker", res["industry_gaps"])

    def test_03_academic_alignment_score_calculation(self):
        """3. Verify deterministic importance-weighted Academic Alignment Score."""
        with self.app.app_context():
            # Software Developer (Career 1): Python (5), Java (5), Data Structures (5), Git (4), SQL (3)
            # Total importance = 22. All 5 are covered in B.Tech CS -> Score = 100.0%
            res = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=1,
                program_id="btech_cs"
            )
            self.assertEqual(res["academic_alignment_score"], 100.0)
            self.assertEqual(res["academic_gap_count"], 0)

            # Cloud Engineer (Career 6): Linux (5), Networking (5), AWS (5), Python (3), Docker (4)
            # Total importance = 22. Covered: Linux(5) + Networking(5) + Python(3) = 13.
            # Score = (13 / 22) * 100 = 59.1%
            res_cloud = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=6,
                program_id="btech_cs"
            )
            self.assertEqual(res_cloud["academic_alignment_score"], 59.1)

    def test_04_weighted_skill_importance_impact(self):
        """4. Verify higher-importance skills have greater impact on alignment score."""
        with self.app.app_context():
            breakdown_high = [
                {"importance": 5, "coverage_strength": 1.0},
                {"importance": 1, "coverage_strength": 0.0}
            ]
            breakdown_low = [
                {"importance": 5, "coverage_strength": 0.0},
                {"importance": 1, "coverage_strength": 1.0}
            ]
            score_high = AcademicBenchmarkService.calculate_academic_alignment_score(breakdown_high)
            score_low = AcademicBenchmarkService.calculate_academic_alignment_score(breakdown_low)

            self.assertEqual(score_high, 83.3)
            self.assertEqual(score_low, 16.7)
            self.assertGreater(score_high, score_low)

    def test_05_missing_academic_skill_detection(self):
        """5. Verify unevidenced skills are cleanly categorized as industry gaps."""
        with self.app.app_context():
            # DevOps Engineer (Career 7): Linux (5), Docker (5), Kubernetes (5), Git (4), CI/CD (5)
            res = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=7,
                program_id="btech_cs"
            )
            # Standard B.Tech CS does not cover Docker, Kubernetes, CI/CD
            self.assertIn("Docker", res["industry_gaps"])
            self.assertIn("Kubernetes", res["industry_gaps"])
            self.assertIn("CI/CD", res["industry_gaps"])
            self.assertGreaterEqual(res["academic_gap_count"], 3)

    def test_06_strict_academic_vs_student_proficiency_distinction(self):
        """6. Verify academic coverage does NOT assume student proficiency (the 4 distinct states)."""
        with self.app.app_context():
            user = User(
                name="Academic vs Practical Student",
                email="academic_distinction@example.com",
                password_hash="testhash"
            )
            db.session.add(user)
            db.session.commit()

            try:
                # Student has weak Python (proficiency 4 / 10 -> 2.0 / 5, required 4)
                # and satisfies Java (proficiency 10 / 10 -> 5.0 / 5, required 4)
                s_py = Skill(user_id=user.id, skill_name="Python", proficiency=4)
                s_java = Skill(user_id=user.id, skill_name="Java", proficiency=10)
                db.session.add_all([s_py, s_java])
                db.session.commit()

                res = AcademicBenchmarkService.benchmark_career_curriculum(
                    career_id=1,  # Software Developer
                    user_id=user.id,
                    program_id="btech_cs"
                )

                items = {i["skill_name"]: i for i in res["curriculum_breakdown"]}

                # Java is academically covered AND student satisfied
                self.assertEqual(items["Java"]["academic_coverage"], "COVERED")
                self.assertEqual(items["Java"]["student_status"], "MATCHED")
                self.assertEqual(items["Java"]["benchmark_status"], "ACADEMICALLY_ANCHORED_AND_SATISFIED")

                # Python is academically covered BUT student proficiency is below target
                self.assertEqual(items["Python"]["academic_coverage"], "COVERED")
                self.assertEqual(items["Python"]["student_status"], "WEAK")
                self.assertEqual(items["Python"]["benchmark_status"], "ACADEMICATION_NEEDS_REINFORCEMENT".replace("ATION", "_FOUNDATION"))

            finally:
                Skill.query.filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.commit()

    def test_07_canonical_skill_matching_and_normalization(self):
        """7. Verify skill resolution handles whitespace, casing, and normalization."""
        with self.app.app_context():
            academic_map = {
                "python": {"coverage_strength": 1.0, "courses": ["Intro Programming"]},
                "data structures": {"coverage_strength": 1.0, "courses": ["Algorithms"]}
            }
            # Test variations
            is_match, strength, courses = AcademicBenchmarkService.resolve_academic_match("  Python  ", academic_map)
            self.assertTrue(is_match)
            self.assertEqual(strength, 1.0)

            is_match_ds, _, _ = AcademicBenchmarkService.resolve_academic_match("Data Structures", academic_map)
            self.assertTrue(is_match_ds)

    def test_08_alias_matching_via_skill_alias(self):
        """8. Verify resolution matches taxonomic aliases (e.g. 'Python (computer programming)')."""
        with self.app.app_context():
            academic_map = {
                "python": {"coverage_strength": 1.0, "courses": ["Python Course"]}
            }
            is_match, _, _ = AcademicBenchmarkService.resolve_academic_match("Python (computer programming)", academic_map)
            self.assertTrue(is_match)

    def test_09_deterministic_results_across_runs(self):
        """9. Verify repeated benchmark executions yield identical scores and breakdowns."""
        with self.app.app_context():
            run1 = AcademicBenchmarkService.benchmark_career_curriculum(career_id=3, program_id="bsc_data_science")
            run2 = AcademicBenchmarkService.benchmark_career_curriculum(career_id=3, program_id="bsc_data_science")

            self.assertEqual(run1["academic_alignment_score"], run2["academic_alignment_score"])
            self.assertEqual(run1["academic_foundations"], run2["academic_foundations"])
            self.assertEqual(run1["industry_gaps"], run2["industry_gaps"])
            self.assertEqual(len(run1["priority_actions"]), len(run2["priority_actions"]))

    def test_10_custom_curriculum_and_empty_evidence_handling(self):
        """10. Verify custom curriculum input overrides and empty evidence handling."""
        with self.app.app_context():
            # Test empty courses custom curriculum
            custom_empty = {
                "program_id": "custom_empty",
                "program_name": "Empty Custom Program",
                "degree_level": "Certificate",
                "provenance": PROVENANCE_NOTICE,
                "description": "Empty curriculum",
                "courses": []
            }
            academic_map = AcademicBenchmarkService.extract_academic_skills(custom_empty)
            self.assertEqual(len(academic_map), 0)

            # Test benchmark with custom evidence containing only Python
            custom_ev = [{"course_name": "Only Python", "skills_evidenced": ["Python"], "coverage_strength": 1.0}]
            res = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=1,
                program_id="btech_cs",
                custom_curriculum=custom_ev
            )
            self.assertIn("Python", res["academic_foundations"])

    def test_11_career_not_found_returns_404(self):
        """11. Verify non-existent career ID returns 404 error from endpoint and service."""
        with self.app.app_context():
            res = AcademicBenchmarkService.benchmark_career_curriculum(career_id=99999)
            self.assertIn("error", res)
            self.assertEqual(res["error"], "CAREER_NOT_FOUND")

        response = self.client.get("/api/careers/99999/academic-benchmark")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("not found", data["message"].lower())

    def test_12_jwt_authentication_and_student_personalization(self):
        """12. Verify authenticated JWT request returns is_personalized=True and student gaps."""
        with self.app.app_context():
            user = User(
                name="JWT Academic Student",
                email="jwt_academic@example.com",
                password_hash="testhash"
            )
            db.session.add(user)
            db.session.commit()

            try:
                # Add student skill
                s = Skill(user_id=user.id, skill_name="SQL", proficiency=8)
                db.session.add(s)
                db.session.commit()

                token = create_access_token(identity=str(user.id))
                headers = {"Authorization": f"Bearer {token}"}

                response = self.client.get("/api/careers/1/academic-benchmark", headers=headers)
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertEqual(data["status"], "success")
                self.assertTrue(data["is_personalized"])
                self.assertIn("student_readiness_score", data)
                self.assertIn("curriculum_breakdown", data)

            finally:
                Skill.query.filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.commit()

    def test_13_api_endpoint_schema_validation(self):
        """13. Verify API endpoint GET /api/careers/<id>/academic-benchmark schema."""
        response = self.client.get("/api/careers/1/academic-benchmark?program=btech_cs")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        expected_keys = [
            "status", "career_id", "career_title", "domain", "program_id",
            "program_name", "degree_level", "provenance_notice", "is_personalized",
            "academic_alignment_score", "student_readiness_score", "total_career_skills_count",
            "academic_covered_count", "academic_gap_count", "student_gap_count",
            "academic_foundations", "industry_gaps", "curriculum_breakdown",
            "priority_actions", "benchmark_summary", "available_programs"
        ]
        for key in expected_keys:
            self.assertIn(key, data, f"Key '{key}' missing from API response")

        self.assertIn("DEMO / SAMPLE / PROTOTYPE", data["provenance_notice"])

    def test_14_phase11_module1_skill_roi_integration(self):
        """14. Verify priority actions integrate Phase 11.1 ROI scores and quickest win flags."""
        with self.app.app_context():
            res = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=6,  # Cloud Engineer
                program_id="btech_cs"
            )
            self.assertGreater(len(res["priority_actions"]), 0)
            first_action = res["priority_actions"][0]
            self.assertIn("readiness_gain", first_action)
            self.assertIn("roi_score", first_action)
            self.assertIn("is_quickest_win", first_action)

    def test_15_phase11_module2_portfolio_capstone_integration(self):
        """15. Verify benchmark provides recommended capstone project bridging industry gaps."""
        with self.app.app_context():
            res = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=6,  # Cloud Engineer
                program_id="btech_cs"
            )
            capstone = res.get("recommended_capstone_project")
            self.assertIsNotNone(capstone)
            self.assertIn("title", capstone)
            self.assertIn("difficulty", capstone)

    def test_16_zero_database_mutations(self):
        """16. Verify benchmarking service does not mutate any database tables."""
        with self.app.app_context():
            careers_before = Career.query.count()
            career_skills_before = CareerSkill.query.count()
            skills_before = Skill.query.count()
            users_before = User.query.count()

            # Run service methods
            AcademicBenchmarkService.benchmark_career_curriculum(career_id=1)
            AcademicBenchmarkService.benchmark_career_curriculum(career_id=2, program_id="bca_mca")

            # Run API calls
            self.client.get("/api/careers/1/academic-benchmark")
            self.client.get("/api/careers/3/academic-benchmark?program=bsc_data_science")

            # Assert complete stability
            self.assertEqual(Career.query.count(), careers_before)
            self.assertEqual(CareerSkill.query.count(), career_skills_before)
            self.assertEqual(Skill.query.count(), skills_before)
            self.assertEqual(User.query.count(), users_before)

    def test_17_degree_program_differences(self):
        """17. Verify different degree programs produce distinctly tailored alignment scores."""
        with self.app.app_context():
            # For Data Scientist (Career 4):
            # B.Sc Data Science should have higher alignment than B.Tech IT
            res_ds = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=4,
                program_id="bsc_data_science"
            )
            res_it = AcademicBenchmarkService.benchmark_career_curriculum(
                career_id=4,
                program_id="btech_it"
            )

            self.assertGreater(res_ds["academic_alignment_score"], res_it["academic_alignment_score"])
            self.assertIn("Statistics", res_ds["academic_foundations"])
            self.assertIn("Machine Learning", res_ds["academic_foundations"])

    def test_18_backward_compatibility_unauthenticated(self):
        """18. Verify unauthenticated request succeeds with default B.Tech CS program baseline."""
        response = self.client.get("/api/careers/2/academic-benchmark")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["career_id"], 2)
        self.assertFalse(data["is_personalized"])
        self.assertEqual(data["program_id"], "btech_cs")


if __name__ == "__main__":
    unittest.main()
