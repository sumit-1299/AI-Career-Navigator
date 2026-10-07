"""
Unit and API Integration Tests for Phase 11 Module 11.2:
Actionable Portfolio & Capstone Project Recommendation Engine.

Verifies:
1. Unauthenticated baseline project recommendations for career tracks.
2. Authenticated user project recommendations reflecting user's skill gaps.
3. Project skill matching with canonical skills and aliases.
4. Gap closure calculation (missing and weak skills properly prioritized).
5. High-ROI / Quickest Win bonus weighting.
6. Difficulty fit scoring based on readiness level.
7. Deterministic project ranking across repeated executions.
8. Explainable recommendation reasoning generated for each project.
9. Deliverables checklist and extension ideas present.
10. Filter by difficulty (e.g. beginner, intermediate, advanced).
11. Limit parameter limiting number of returned recommendations.
12. 404 for non-existent career ID.
13. Quickest gap closer identification.
14. All 10 careers have suitable projects in catalog.
15. User with 100% readiness gets appropriate portfolio-focused recommendations.
16. Zero database mutations (catalog is purely in-memory/deterministic).
17. API endpoint returns valid status, schema, and HTTP 200 with/without JWT.
"""

import unittest
from app import create_app
from extensions import db
from models.user import User
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from services.portfolio_project_service import (
    PortfolioProjectService,
    PORTFOLIO_PROJECTS_CATALOG
)
from flask_jwt_extended import create_access_token


class TestPhase11Module2PortfolioProjects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_unauthenticated_baseline_recommendations(self):
        """1. Verify unauthenticated baseline recommendations return catalog projects for target career."""
        with self.app.app_context():
            result = PortfolioProjectService.recommend_projects_for_career(career_id=1, user_id=None)
            self.assertNotIn("error", result)
            self.assertEqual(result["career_id"], 1)
            self.assertEqual(result["career_title"], "Software Developer")
            self.assertFalse(result["is_personalized"])
            self.assertGreater(result["total_projects_count"], 0)
            self.assertIsInstance(result["recommendations"], list)

            first_project = result["recommendations"][0]
            self.assertIn("project_id", first_project)
            self.assertIn("title", first_project)
            self.assertIn("difficulty", first_project)
            self.assertIn("recommendation_score", first_project)
            self.assertIn("deliverables", first_project)
            self.assertIn("recommendation_reason", first_project)

    def test_02_authenticated_user_recommendations_reflect_gaps(self):
        """2. Verify authenticated user recommendations reflect student missing and weak skills."""
        with self.app.app_context():
            # Create a test user with a subset of skills
            user = User(
                name="Test Capstone Student",
                email="capstone_student@example.com",
                password_hash="testhash"
            )
            db.session.add(user)
            db.session.commit()

            try:
                # Add weak Python (level 2) - Career 1 requires level 4
                s_py = Skill(user_id=user.id, skill_name="Python", proficiency=2)
                db.session.add(s_py)
                db.session.commit()

                result = PortfolioProjectService.recommend_projects_for_career(
                    career_id=1,
                    user_id=user.id
                )
                self.assertNotIn("error", result)
                self.assertTrue(result["is_personalized"])
                self.assertGreater(result["total_projects_count"], 0)

                # Find projects that address Python as weak or other skills as missing
                has_gap_addressed = any(
                    len(p["missing_skills_addressed"]) > 0 or len(p["weak_skills_addressed"]) > 0
                    for p in result["recommendations"]
                )
                self.assertTrue(has_gap_addressed)

                # Check that Python is identified in weak skills addressed where relevant
                py_projects = [
                    p for p in result["recommendations"]
                    if "Python" in p["weak_skills_addressed"]
                ]
                self.assertGreater(len(py_projects), 0)

            finally:
                Skill.query.filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.commit()

    def test_03_project_skill_matching_canonical_and_aliases(self):
        """3. Verify project skill matching handles canonical names and case/alias variations."""
        with self.app.app_context():
            career = Career.query.get(1)  # Software Developer: Python, Java, Data Structures, Git, SQL
            career_skills = CareerSkill.query.filter_by(career_id=career.id).all()

            match = PortfolioProjectService.match_project_skills(
                project_skills=["Python (computer programming)", "SQL", "git", "c++"],
                career_skills=career_skills,
                missing_skills_norm={"sql", "git"},
                weak_skills_norm={"python"}
            )

            self.assertGreater(match["coverage_count"], 0)
            self.assertIn("Python", match["covered_career_skills"])
            self.assertIn("SQL", match["covered_career_skills"])
            self.assertIn("Git", match["covered_career_skills"])
            self.assertIn("Python", match["weak_addressed"])
            self.assertIn("SQL", match["missing_addressed"])
            self.assertIn("Git", match["missing_addressed"])

    def test_04_gap_closure_calculation(self):
        """4. Verify projects that close missing and weak skills achieve higher gap closure score."""
        with self.app.app_context():
            career = Career.query.get(1)
            career_skills = CareerSkill.query.filter_by(career_id=career.id).all()

            project_all_gaps = {
                "portfolio_value": 85,
                "target_career_ids": [1],
                "domain": "Software Development",
                "difficulty": "Intermediate"
            }
            match_all_gaps = {
                "covered_career_skills": ["Python", "Java", "SQL"],
                "missing_addressed": ["Python", "Java"],
                "weak_addressed": ["SQL"],
                "coverage_count": 3
            }

            score_high = PortfolioProjectService.calculate_project_score(
                project=project_all_gaps,
                career=career,
                match_info=match_all_gaps,
                total_career_skills_count=len(career_skills),
                student_readiness=30.0,
                quickest_win_norm=None,
                top_roi_norms=set(),
                is_personalized=True
            )

            match_no_gaps = {
                "covered_career_skills": ["Python"],
                "missing_addressed": [],
                "weak_addressed": [],
                "coverage_count": 1
            }

            score_low = PortfolioProjectService.calculate_project_score(
                project=project_all_gaps,
                career=career,
                match_info=match_no_gaps,
                total_career_skills_count=len(career_skills),
                student_readiness=30.0,
                quickest_win_norm=None,
                top_roi_norms=set(),
                is_personalized=True
            )

            self.assertGreater(score_high, score_low)

    def test_05_quickest_win_bonus_weighting(self):
        """5. Verify project addressing Quickest Win competency receives higher score."""
        with self.app.app_context():
            career = Career.query.get(1)
            career_skills = CareerSkill.query.filter_by(career_id=career.id).all()

            project = {
                "portfolio_value": 85,
                "target_career_ids": [1],
                "domain": "Software Development",
                "difficulty": "Intermediate",
                "demonstrated_skills": ["Python", "Git"]
            }
            match_info = {
                "covered_career_skills": ["Python", "Git"],
                "missing_addressed": ["Python"],
                "weak_addressed": [],
                "coverage_count": 2
            }

            score_with_qw = PortfolioProjectService.calculate_project_score(
                project=project,
                career=career,
                match_info=match_info,
                total_career_skills_count=len(career_skills),
                student_readiness=40.0,
                quickest_win_norm="python",
                top_roi_norms={"python"},
                is_personalized=True
            )

            score_without_qw = PortfolioProjectService.calculate_project_score(
                project=project,
                career=career,
                match_info=match_info,
                total_career_skills_count=len(career_skills),
                student_readiness=40.0,
                quickest_win_norm="java",
                top_roi_norms={"java"},
                is_personalized=True
            )

            self.assertGreater(score_with_qw, score_without_qw)

    def test_06_difficulty_fit_scoring_based_on_readiness(self):
        """6. Verify Novice readiness prefers Beginner projects, while Advanced prefers Advanced."""
        with self.app.app_context():
            career = Career.query.get(1)
            match_info = {
                "covered_career_skills": ["Python"],
                "missing_addressed": ["Python"],
                "weak_addressed": [],
                "coverage_count": 1
            }

            p_beginner = {"portfolio_value": 80, "target_career_ids": [1], "domain": "Software Development", "difficulty": "Beginner"}
            p_advanced = {"portfolio_value": 80, "target_career_ids": [1], "domain": "Software Development", "difficulty": "Advanced"}

            # For Novice student (readiness = 20%)
            score_novice_beg = PortfolioProjectService.calculate_project_score(
                project=p_beginner, career=career, match_info=match_info,
                total_career_skills_count=5, student_readiness=20.0,
                quickest_win_norm=None, top_roi_norms=set(), is_personalized=True
            )
            score_novice_adv = PortfolioProjectService.calculate_project_score(
                project=p_advanced, career=career, match_info=match_info,
                total_career_skills_count=5, student_readiness=20.0,
                quickest_win_norm=None, top_roi_norms=set(), is_personalized=True
            )
            self.assertGreater(score_novice_beg, score_novice_adv)

            # For Advanced student (readiness = 85%)
            score_adv_beg = PortfolioProjectService.calculate_project_score(
                project=p_beginner, career=career, match_info=match_info,
                total_career_skills_count=5, student_readiness=85.0,
                quickest_win_norm=None, top_roi_norms=set(), is_personalized=True
            )
            score_adv_adv = PortfolioProjectService.calculate_project_score(
                project=p_advanced, career=career, match_info=match_info,
                total_career_skills_count=5, student_readiness=85.0,
                quickest_win_norm=None, top_roi_norms=set(), is_personalized=True
            )
            self.assertGreater(score_adv_adv, score_adv_beg)

    def test_07_deterministic_project_ranking(self):
        """7. Verify deterministic project ranking yields identical ordering and scores across calls."""
        with self.app.app_context():
            run1 = PortfolioProjectService.recommend_projects_for_career(career_id=2, user_id=None)
            run2 = PortfolioProjectService.recommend_projects_for_career(career_id=2, user_id=None)

            self.assertEqual(len(run1["recommendations"]), len(run2["recommendations"]))
            for p1, p2 in zip(run1["recommendations"], run2["recommendations"]):
                self.assertEqual(p1["project_id"], p2["project_id"])
                self.assertEqual(p1["recommendation_score"], p2["recommendation_score"])

    def test_08_explainable_recommendation_reasoning_generated(self):
        """8. Verify explainable natural-language reasoning is generated for each project."""
        with self.app.app_context():
            reason = PortfolioProjectService.generate_recommendation_reason(
                project_title="Distributed Task Engine",
                career_title="Software Developer",
                covered_skills=["Python", "Java", "SQL"],
                missing_addressed=["Python", "Java"],
                weak_addressed=["SQL"],
                is_quickest_win=True,
                difficulty="Advanced"
            )
            self.assertIsInstance(reason, str)
            self.assertIn("Python", reason)
            self.assertIn("Software Developer", reason)
            self.assertIn("advanced", reason.lower())

    def test_09_deliverables_and_extensions_present(self):
        """9. Verify all catalog projects contain non-empty deliverables checklist and extension ideas."""
        with self.app.app_context():
            for p in PORTFOLIO_PROJECTS_CATALOG:
                self.assertIn("deliverables", p)
                self.assertIsInstance(p["deliverables"], list)
                self.assertGreaterEqual(len(p["deliverables"]), 3, f"Project {p['project_id']} has fewer than 3 deliverables")
                self.assertIn("extension_ideas", p)
                self.assertIsInstance(p["extension_ideas"], list)
                self.assertGreaterEqual(len(p["extension_ideas"]), 1)

    def test_10_filter_by_difficulty(self):
        """10. Verify difficulty filter strictly filters projects to requested level."""
        with self.app.app_context():
            for diff in ["Beginner", "Intermediate", "Advanced"]:
                res = PortfolioProjectService.recommend_projects_for_career(
                    career_id=1,
                    difficulty_filter=diff
                )
                self.assertNotIn("error", res)
                self.assertGreater(len(res["recommendations"]), 0)
                for p in res["recommendations"]:
                    self.assertEqual(p["difficulty"].lower(), diff.lower())

    def test_11_limit_parameter(self):
        """11. Verify limit parameter bounds the number of returned recommendations."""
        with self.app.app_context():
            res = PortfolioProjectService.recommend_projects_for_career(
                career_id=1,
                limit=2
            )
            self.assertNotIn("error", res)
            self.assertLessEqual(len(res["recommendations"]), 2)

    def test_12_career_not_found_returns_404(self):
        """12. Verify non-existent career ID returns 404 error response."""
        response = self.client.get("/api/careers/99999/portfolio-recommendations")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["status"], "error")
        self.assertIn("not found", data["message"].lower())

    def test_13_quickest_gap_closer_identified(self):
        """13. Verify quickest gap closer project is identified in results."""
        with self.app.app_context():
            res = PortfolioProjectService.recommend_projects_for_career(career_id=3)
            self.assertNotIn("error", res)
            self.assertIsNotNone(res.get("quickest_gap_closer"))
            qgc = res["quickest_gap_closer"]
            self.assertIn("project_id", qgc)
            self.assertIn("recommendation_score", qgc)

    def test_14_all_ten_careers_have_catalog_projects(self):
        """14. Verify all 10 careers have suitable projects in the catalog."""
        with self.app.app_context():
            for cid in range(1, 11):
                res = PortfolioProjectService.recommend_projects_for_career(career_id=cid)
                self.assertNotIn("error", res, f"Career {cid} returned error")
                self.assertGreaterEqual(
                    len(res["recommendations"]), 3,
                    f"Career {cid} has fewer than 3 project recommendations"
                )

    def test_15_user_with_full_readiness_gets_portfolio_recommendations(self):
        """15. Verify student with 100% readiness still gets appropriate portfolio projects."""
        with self.app.app_context():
            user = User(
                name="Proficient Student",
                email="proficient_student@example.com",
                password_hash="testhash"
            )
            db.session.add(user)
            db.session.commit()

            try:
                # Add all 5 required skills for Career 1 at maximum level 10 (normalized 5/5)
                career = Career.query.get(1)
                career_skills = CareerSkill.query.filter_by(career_id=career.id).all()
                for cs in career_skills:
                    s = Skill(user_id=user.id, skill_name=cs.skill_name, proficiency=10)
                    db.session.add(s)
                db.session.commit()

                res = PortfolioProjectService.recommend_projects_for_career(
                    career_id=1,
                    user_id=user.id
                )
                self.assertNotIn("error", res)
                self.assertTrue(res["is_personalized"])
                self.assertGreaterEqual(res["student_readiness"], 95.0)
                self.assertGreater(len(res["recommendations"]), 0)
                # First recommendation should be Advanced due to readiness level fit
                self.assertEqual(res["recommendations"][0]["difficulty"], "Advanced")

            finally:
                Skill.query.filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.commit()

    def test_16_zero_database_mutations(self):
        """16. Verify recommendations engine performs zero database mutations (pure read-only)."""
        with self.app.app_context():
            careers_before = Career.query.count()
            career_skills_before = CareerSkill.query.count()
            skills_before = Skill.query.count()
            users_before = User.query.count()

            # Execute recommendation service
            PortfolioProjectService.recommend_projects_for_career(career_id=1)
            PortfolioProjectService.recommend_projects_for_career(career_id=2, difficulty_filter="Advanced")

            # Execute API endpoint
            self.client.get("/api/careers/1/portfolio-recommendations")
            self.client.get("/api/careers/2/portfolio-recommendations?difficulty=Beginner")

            # Assert exact database stability
            self.assertEqual(Career.query.count(), careers_before)
            self.assertEqual(CareerSkill.query.count(), career_skills_before)
            self.assertEqual(Skill.query.count(), skills_before)
            self.assertEqual(User.query.count(), users_before)

    def test_17_api_endpoint_success_and_jwt_integration(self):
        """17. Verify GET /api/careers/<id>/portfolio-recommendations returns 200 with and without JWT."""
        with self.app.app_context():
            # 1. Unauthenticated request
            res_anon = self.client.get("/api/careers/1/portfolio-recommendations")
            self.assertEqual(res_anon.status_code, 200)
            data_anon = res_anon.get_json()
            self.assertEqual(data_anon["status"], "success")
            self.assertEqual(data_anon["career_id"], 1)
            self.assertFalse(data_anon["is_personalized"])

            # 2. Authenticated JWT request
            user = User(
                name="JWT Project Student",
                email="jwt_project_student@example.com",
                password_hash="testhash"
            )
            db.session.add(user)
            db.session.commit()

            try:
                token = create_access_token(identity=str(user.id))
                headers = {"Authorization": f"Bearer {token}"}

                res_auth = self.client.get("/api/careers/1/portfolio-recommendations", headers=headers)
                self.assertEqual(res_auth.status_code, 200)
                data_auth = res_auth.get_json()
                self.assertEqual(data_auth["status"], "success")
                self.assertTrue(data_auth["is_personalized"])
                self.assertIn("recommendations", data_auth)

            finally:
                db.session.delete(user)
                db.session.commit()


if __name__ == "__main__":
    unittest.main()
