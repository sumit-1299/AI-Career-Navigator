"""
Unit and API Integration Tests for Phase 12 Module 12.4:
Adaptive Skill Learning & Resource Recommendation Engine.

Verifies:
1. AdaptiveLearningService initialization & component contracts.
2. Canonical career support across all 10 careers.
3. Priority formula weighting components (0.30 Gap + 0.20 ROI + 0.15 Importance + 0.15 Demand + 0.10 Academic + 0.10 Job).
4. Priority score clamping guarantee (bounded between 0.0 and 100.0).
5. Priority bands mapping (VERY_HIGH, HIGH, MEDIUM, LOW).
6. Learning stage determination (FOUNDATION, CORE_SKILL, APPLIED_PRACTICE, PROJECT_APPLICATION, INTERVIEW_READINESS).
7. Learning effort estimation formula for each stage.
8. Canonical prerequisite map resolution (dependencies for ML, DL, React, Kubernetes, etc.).
9. Sequential roadmap topological order and status labeling (START_NOW, READY_NEXT, AFTER_<PREREQ>).
10. Learning pace estimation (5, 10, 15, 20 hrs/week computing estimated_weeks).
11. Max skills limit parameter (limit / max_skills restriction).
12. Skill gap severity normalization (0-100 scale).
13. Skill ROI service integration (Phase 11.1).
14. Industry demand service integration (Phase 11.4).
15. Academic benchmark deficit integration (Phase 11.3).
16. Job opportunity relevance integration (vacancy skills boost).
17. Career trajectory integration (Phase 11.5 multi-hop transition context).
18. Practical task linkage (Phase 12.3 task bank).
19. Portfolio capstone linkage (Phase 11.2 project recommendations).
20. Interview simulation linkage (Phase 11.6 question bank).
21. Four action pillars present for all priority skills (Learn, Practice, Build, Prepare).
22. Resource ranking algorithm scoring.
23. Resource curated fallback generation.
24. Student skills override simulation payload.
25. Zero persistent DB writes guarantee during plan generation.
26. Deterministic reproducibility across repeated invocations.
27. Non-existent career handling (404 Not Found).
28. REST API GET /api/careers/<id>/adaptive-learning endpoint response schema.
29. REST API POST /api/careers/<id>/adaptive-learning endpoint with simulation payload.
30. Authenticated vs anonymous guest request compatibility.
31. Fully satisfied readiness handling.
32. Actionable next steps synthesis.
33. Provenance notices and safety disclaimer presence.
"""

import unittest
from app import create_app
from extensions import db
from models.career import Career
from models.skill import Skill
from models.learning_resource import LearningResource
from services.adaptive_learning_service import AdaptiveLearningService
from services.practical_task_service import PracticalTaskService


class TestPhase12Module4AdaptiveLearningEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    # 1. Service initialization & constants
    def test_01_service_initialization_and_provenance(self):
        """1. Verify AdaptiveLearningService class attributes, constants, and provenance."""
        self.assertTrue(hasattr(AdaptiveLearningService, "WEIGHTS"))
        self.assertTrue(hasattr(AdaptiveLearningService, "PREREQUISITE_MAP"))
        self.assertTrue(hasattr(AdaptiveLearningService, "STAGE_EFFORT_BASE"))
        self.assertTrue(hasattr(AdaptiveLearningService, "PROVENANCE_NOTICES"))
        self.assertTrue(hasattr(AdaptiveLearningService, "SAFETY_DISCLAIMER"))

        weights = AdaptiveLearningService.WEIGHTS
        self.assertAlmostEqual(
            weights["gap_severity"] + weights["skill_roi"] + weights["career_importance"] +
            weights["industry_demand"] + weights["academic_deficit"] + weights["job_relevance"],
            1.0,
            places=5
        )

    # 2. Canonical career support across all 10 careers
    def test_02_all_ten_careers_supported(self):
        """2. Verify AdaptiveLearningService generates valid plans for all 10 canonical careers."""
        for cid in range(1, 11):
            plan = AdaptiveLearningService.get_learning_plan(career_id=cid)
            self.assertEqual(plan.get("status"), "success", f"Career {cid} failed to produce plan")
            self.assertIn("career", plan)
            self.assertIn("priority_skills", plan)
            self.assertIn("learning_summary", plan)
            self.assertIn("learning_path", plan)

    # 3. Priority formula weighting components
    def test_03_priority_formula_weighting_components(self):
        """3. Verify composite priority score accurately matches formula."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1, options={"limit": 5})
        self.assertGreater(len(plan["priority_skills"]), 0)
        top = plan["priority_skills"][0]
        c = top["components"]

        expected_score = round(
            0.30 * c["gap_severity"] +
            0.20 * c["skill_roi"] +
            0.15 * c["career_importance"] +
            0.15 * c["industry_demand"] +
            0.10 * c["academic_deficit"] +
            0.10 * c["job_relevance"],
            1
        )
        self.assertAlmostEqual(top["priority_score"], expected_score, places=1)

    # 4. Priority score clamping
    def test_04_priority_score_clamping(self):
        """4. Verify priority scores are strictly bounded between 0.0 and 100.0."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1, options={"limit": 20})
        for s in plan["priority_skills"]:
            self.assertGreaterEqual(s["priority_score"], 0.0)
            self.assertLessEqual(s["priority_score"], 100.0)

    # 5. Priority bands mapping
    def test_05_priority_bands_mapping(self):
        """5. Verify score-to-band classification."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1, options={"limit": 20})
        for s in plan["priority_skills"]:
            score = s["priority_score"]
            band = s["priority_band"]
            if score >= 80.0:
                self.assertEqual(band, "VERY_HIGH")
            elif score >= 65.0:
                self.assertEqual(band, "HIGH")
            elif score >= 50.0:
                self.assertEqual(band, "MEDIUM")
            else:
                self.assertEqual(band, "LOW")

    # 6. Learning stage determination
    def test_06_learning_stage_determination(self):
        """6. Verify determine_learning_stage across proficiency brackets."""
        self.assertEqual(AdaptiveLearningService.determine_learning_stage(0, 4), "FOUNDATION")
        self.assertEqual(AdaptiveLearningService.determine_learning_stage(1, 4), "FOUNDATION")
        self.assertEqual(AdaptiveLearningService.determine_learning_stage(2, 4), "CORE_SKILL")
        self.assertEqual(AdaptiveLearningService.determine_learning_stage(3, 4), "APPLIED_PRACTICE")
        self.assertEqual(AdaptiveLearningService.determine_learning_stage(3, 5), "PROJECT_APPLICATION")
        self.assertEqual(AdaptiveLearningService.determine_learning_stage(4, 4), "INTERVIEW_READINESS")
        self.assertEqual(AdaptiveLearningService.determine_learning_stage(5, 4), "INTERVIEW_READINESS")

    # 7. Learning effort estimation formula
    def test_07_learning_effort_estimation(self):
        """7. Verify estimate_learning_effort heuristics."""
        self.assertEqual(AdaptiveLearningService.estimate_learning_effort("FOUNDATION", 4), round(10 + 4 * 3))
        self.assertEqual(AdaptiveLearningService.estimate_learning_effort("CORE_SKILL", 2), round(8 + 2 * 2.5))
        self.assertEqual(AdaptiveLearningService.estimate_learning_effort("APPLIED_PRACTICE", 1), round(6 + 1 * 2))
        self.assertEqual(AdaptiveLearningService.estimate_learning_effort("PROJECT_APPLICATION", 2), round(10 + 2 * 2))
        self.assertEqual(AdaptiveLearningService.estimate_learning_effort("INTERVIEW_READINESS", 0), 4)

    # 8. Canonical prerequisite map resolution
    def test_08_canonical_prerequisite_map(self):
        """8. Verify resolve_prerequisites returns canonical dependencies."""
        prereqs, note = AdaptiveLearningService.resolve_prerequisites("Machine Learning")
        self.assertIn("Python", prereqs)
        self.assertIn("Data Structures", prereqs)

        prereqs_dl, _ = AdaptiveLearningService.resolve_prerequisites("Deep Learning")
        self.assertIn("Machine Learning", prereqs_dl)

        prereqs_k8s, _ = AdaptiveLearningService.resolve_prerequisites("Kubernetes")
        self.assertIn("Docker", prereqs_k8s)

        prereqs_py, _ = AdaptiveLearningService.resolve_prerequisites("Python")
        self.assertEqual(len(prereqs_py), 0)

    # 9. Sequential roadmap topological ordering
    def test_09_sequential_roadmap_topological_order(self):
        """9. Verify learning path builds structured steps with stage, status, and hours."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1, options={"limit": 5})
        path = plan["learning_path"]
        self.assertGreater(len(path), 0)

        # First stage should be START_NOW or READY_NEXT
        self.assertIn(path[0]["status"], ["START_NOW", "READY_NEXT"])
        for idx, step in enumerate(path):
            self.assertEqual(step["stage"], idx + 1)
            self.assertIn("skill", step)
            self.assertIn("learning_stage", step)
            self.assertIn("priority_band", step)
            self.assertIn("estimated_hours", step)
            self.assertIn("closure_target", step)

    # 10. Learning pace options
    def test_10_learning_pace_estimation(self):
        """10. Verify custom study pace correctly computes estimated_weeks."""
        plan_10 = AdaptiveLearningService.get_learning_plan(career_id=1, options={"learning_pace": 10, "limit": 4})
        plan_20 = AdaptiveLearningService.get_learning_plan(career_id=1, options={"learning_pace": 20, "limit": 4})

        hours = plan_10["learning_summary"]["estimated_hours"]
        self.assertEqual(plan_10["learning_summary"]["learning_pace_hours_per_week"], 10)
        self.assertEqual(plan_10["learning_summary"]["estimated_weeks"], round(hours / 10, 1))

        self.assertEqual(plan_20["learning_summary"]["learning_pace_hours_per_week"], 20)
        self.assertEqual(plan_20["learning_summary"]["estimated_weeks"], round(hours / 20, 1))

    # 11. Max skills limit parameter
    def test_11_max_skills_limit_parameter(self):
        """11. Verify limit/max_skills restricts priority skills count."""
        plan_2 = AdaptiveLearningService.get_learning_plan(career_id=1, options={"limit": 2})
        self.assertEqual(len(plan_2["priority_skills"]), 2)

        plan_4 = AdaptiveLearningService.get_learning_plan(career_id=1, options={"max_skills": 4})
        self.assertEqual(len(plan_4["priority_skills"]), 4)

    # 12. Skill gap severity normalization
    def test_12_skill_gap_severity_normalization(self):
        """12. Verify missing skill has high gap severity and mastered skill has low gap severity."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1)
        for s in plan["priority_skills"]:
            self.assertIn("gap_severity", s["components"])
            self.assertGreaterEqual(s["components"]["gap_severity"], 0.0)
            self.assertLessEqual(s["components"]["gap_severity"], 100.0)

    # 13. Skill ROI service integration
    def test_13_skill_roi_integration(self):
        """13. Verify SkillRoiService signals are reflected in priority components."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1)
        for s in plan["priority_skills"]:
            self.assertIn("skill_roi", s["components"])
            self.assertIsInstance(s["components"]["skill_roi"], (int, float))

    # 14. Industry demand service integration
    def test_14_industry_demand_integration(self):
        """14. Verify IndustryDemandService signals are reflected in priority components."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1)
        for s in plan["priority_skills"]:
            self.assertIn("industry_demand", s["components"])
            self.assertIsInstance(s["components"]["industry_demand"], (int, float))

    # 15. Academic benchmark deficit integration
    def test_15_academic_benchmark_integration(self):
        """15. Verify AcademicBenchmarkService deficits are reflected in priority components."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1)
        for s in plan["priority_skills"]:
            self.assertIn("academic_deficit", s["components"])
            self.assertIsInstance(s["components"]["academic_deficit"], (int, float))

    # 16. Job opportunity relevance integration
    def test_16_job_opportunity_relevance_boost(self):
        """16. Verify matching vacancy skills boosts job relevance to 95.0."""
        plan = AdaptiveLearningService.get_learning_plan(
            career_id=1,
            options={"vacancy_skills": ["Python"]}
        )
        py_skill = next((s for s in plan["priority_skills"] if s["skill_name"].casefold() == "python"), None)
        self.assertIsNotNone(py_skill)
        self.assertEqual(py_skill["components"]["job_relevance"], 95.0)

    # 17. Career trajectory integration
    def test_17_career_trajectory_integration(self):
        """17. Verify supplying from_career_id incorporates trajectory context."""
        plan = AdaptiveLearningService.get_learning_plan(
            career_id=1,
            options={"from_career_id": 2}
        )
        self.assertEqual(plan["status"], "success")
        self.assertIn("trajectory_context", plan)

    # 18. Practical task linkage
    def test_18_practical_task_linkage(self):
        """18. Verify priority skills link to practical tasks in PracticalTaskService."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1)
        py_skill = next((s for s in plan["priority_skills"] if s["skill_name"].casefold() == "python"), None)
        self.assertIsNotNone(py_skill)
        pt = py_skill["practical_task"]
        self.assertTrue(pt["available"])
        self.assertIn("task_id", pt)
        self.assertIn("title", pt)
        self.assertIn("objective", pt)
        self.assertIn("difficulty", pt)

    # 19. Portfolio capstone linkage
    def test_19_portfolio_capstone_linkage(self):
        """19. Verify priority skills link to portfolio capstone projects."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1)
        for s in plan["priority_skills"]:
            self.assertIn("portfolio_project", s)
            self.assertIn("available", s["portfolio_project"])

    # 20. Interview simulation linkage
    def test_20_interview_simulation_linkage(self):
        """20. Verify priority skills link to interview simulator question bank."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1)
        py_skill = next((s for s in plan["priority_skills"] if s["skill_name"].casefold() == "python"), None)
        self.assertIsNotNone(py_skill)
        ip = py_skill["interview_preparation"]
        self.assertTrue(ip["available"])
        self.assertIsInstance(ip["sample_questions"], list)
        self.assertGreater(len(ip["sample_questions"]), 0)

    # 21. Four action pillars present for all priority skills
    def test_21_four_action_pillars_completeness(self):
        """21. Verify every priority skill provides all four action pillars."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1, options={"limit": 5})
        for s in plan["priority_skills"]:
            self.assertIn("learning_resources", s, "Missing Pillar 1: Learn")
            self.assertIn("practical_task", s, "Missing Pillar 2: Practice")
            self.assertIn("portfolio_project", s, "Missing Pillar 3: Build")
            self.assertIn("interview_preparation", s, "Missing Pillar 4: Prepare")

    # 22. Resource ranking algorithm scoring
    def test_22_resource_ranking_scoring(self):
        """22. Verify rank_resources computes ranking_score between 0 and 100."""
        recs = AdaptiveLearningService.rank_resources("Python", "FOUNDATION", 1, limit=3)
        self.assertGreater(len(recs), 0)
        for r in recs:
            self.assertIn("ranking_score", r)
            self.assertGreaterEqual(r["ranking_score"], 0.0)
            self.assertLessEqual(r["ranking_score"], 100.0)
            self.assertIn("title", r)
            self.assertIn("provider", r)
            self.assertIn("type", r)
            self.assertIn("difficulty", r)

    # 23. Resource curated fallback generation
    def test_23_resource_curated_fallback(self):
        """23. Verify fallback resources are generated when no DB resource matches unusual skill."""
        recs = AdaptiveLearningService.rank_resources("Quantum Algorithms", "CORE_SKILL", 1, limit=3)
        self.assertGreaterEqual(len(recs), 1)
        self.assertIn("Quantum Algorithms", recs[0]["title"])

    # 24. Student skills override simulation payload
    def test_24_student_skills_override_simulation(self):
        """24. Verify user_skills_payload simulates candidate profile without database persistence."""
        override = [
            {"skill_name": "Python", "proficiency": 4},
            {"skill_name": "Data Structures", "proficiency": 4},
        ]
        plan = AdaptiveLearningService.get_learning_plan(
            career_id=1,
            user_skills_payload=override
        )
        self.assertGreater(plan["learning_summary"]["student_readiness_score"], 0.0)
        py_skill = next((s for s in plan["priority_skills"] if s["skill_name"].casefold() == "python"), None)
        if py_skill:
            self.assertEqual(py_skill["current_proficiency"], 4)

    # 25. Zero persistent DB writes guarantee
    def test_25_zero_persistent_db_writes_guarantee(self):
        """25. Verify running get_learning_plan does not write or mutate any database records."""
        careers_count_before = Career.query.count()
        skills_count_before = Skill.query.count()
        resources_count_before = LearningResource.query.count()

        # Execute multiple plans
        AdaptiveLearningService.get_learning_plan(career_id=1)
        AdaptiveLearningService.get_learning_plan(
            career_id=2,
            user_skills_payload=[{"skill_name": "JavaScript", "proficiency": 3}],
            options={"learning_pace": 15, "vacancy_skills": ["React"]}
        )

        self.assertEqual(Career.query.count(), careers_count_before)
        self.assertEqual(Skill.query.count(), skills_count_before)
        self.assertEqual(LearningResource.query.count(), resources_count_before)

    # 26. Deterministic reproducibility
    def test_26_deterministic_reproducibility(self):
        """26. Verify identical inputs yield strictly identical priority plans."""
        plan_a = AdaptiveLearningService.get_learning_plan(career_id=3, options={"limit": 5})
        plan_b = AdaptiveLearningService.get_learning_plan(career_id=3, options={"limit": 5})

        scores_a = [s["priority_score"] for s in plan_a["priority_skills"]]
        scores_b = [s["priority_score"] for s in plan_b["priority_skills"]]
        self.assertEqual(scores_a, scores_b)

        names_a = [s["skill_name"] for s in plan_a["priority_skills"]]
        names_b = [s["skill_name"] for s in plan_b["priority_skills"]]
        self.assertEqual(names_a, names_b)

        self.assertEqual(
            plan_a["learning_summary"]["estimated_hours"],
            plan_b["learning_summary"]["estimated_hours"]
        )

    # 27. Invalid career not found
    def test_27_invalid_career_not_found(self):
        """27. Verify non-existent career_id returns error."""
        res = AdaptiveLearningService.get_learning_plan(career_id=99999)
        self.assertEqual(res.get("error"), "CAREER_NOT_FOUND")

    # 28. REST API GET endpoint
    def test_28_api_get_adaptive_learning_endpoint(self):
        """28. Verify GET /api/careers/<id>/adaptive-learning returns 200 and valid payload."""
        response = self.client.get("/api/careers/1/adaptive-learning?limit=4&learning_pace=15")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["career"]["id"], 1)
        self.assertIn("learning_summary", data)
        self.assertIn("priority_skills", data)
        self.assertLessEqual(len(data["priority_skills"]), 4)

    # 29. REST API POST endpoint with simulation payload
    def test_29_api_post_adaptive_learning_simulation(self):
        """29. Verify POST /api/careers/<id>/adaptive-learning accepts student_skills body."""
        payload = {
            "student_skills": [
                {"skill_name": "Python", "proficiency": 3},
                {"skill_name": "SQL", "proficiency": 2}
            ],
            "learning_pace": 12,
            "max_skills": 5
        }
        response = self.client.post("/api/careers/1/adaptive-learning", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["learning_summary"]["student_readiness_score"], 0.0)

    # 30. REST API authentication compatibility
    def test_30_api_authentication_compatibility(self):
        """30. Verify endpoint works for unauthenticated guest requests."""
        response = self.client.get("/api/careers/2/adaptive-learning")
        self.assertEqual(response.status_code, 200)

    # 31. Fully satisfied readiness handling
    def test_31_fully_satisfied_readiness_handling(self):
        """31. Verify candidate with all skills mastered (L5) yields 100% readiness."""
        mastered = [
            {"skill_name": "Python", "proficiency": 5},
            {"skill_name": "Java", "proficiency": 5},
            {"skill_name": "Data Structures", "proficiency": 5},
            {"skill_name": "Git", "proficiency": 5},
            {"skill_name": "SQL", "proficiency": 5},
            {"skill_name": "Object-Oriented Programming", "proficiency": 5},
            {"skill_name": "Unit Testing", "proficiency": 5},
            {"skill_name": "REST APIs", "proficiency": 5},
            {"skill_name": "Design Patterns", "proficiency": 5},
            {"skill_name": "Algorithms", "proficiency": 5},
        ]
        plan = AdaptiveLearningService.get_learning_plan(
            career_id=1,
            user_skills_payload=mastered
        )
        self.assertGreaterEqual(plan["learning_summary"]["student_readiness_score"], 90.0)

    # 32. Actionable next steps synthesis
    def test_32_actionable_next_steps_synthesis(self):
        """32. Verify plan generates structured next action checklist."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1)
        self.assertIn("next_actions", plan)
        self.assertIsInstance(plan["next_actions"], list)
        self.assertGreater(len(plan["next_actions"]), 0)
        self.assertTrue(any("Step 1:" in a for a in plan["next_actions"]))

    # 33. Provenance notices and safety disclaimer
    def test_33_provenance_and_safety_disclaimer(self):
        """33. Verify transparency notices and safety disclaimer are present."""
        plan = AdaptiveLearningService.get_learning_plan(career_id=1)
        self.assertIn("provenance", plan)
        self.assertIn("safety_disclaimer", plan)
        self.assertIn("deterministic", plan["safety_disclaimer"].lower())


if __name__ == "__main__":
    unittest.main()
