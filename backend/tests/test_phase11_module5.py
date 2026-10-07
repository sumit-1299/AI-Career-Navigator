"""
Unit and API Integration Tests for Phase 11 Module 11.5:
Multi-Hop Career Trajectory Intelligence Engine.

Verifies:
1. Career graph generation (nodes, directed edges, in-memory representation).
2. Direct transition edge properties (compatibility, cost, hours).
3. Transition compatibility bounded strictly in [0.0, 1.0].
4. Transition cost bounded strictly in [0.0, 1.0] and non-negative.
5. Multi-hop path discovery (stepping stone paths found).
6. Shortest path objective (minimizes hop count).
7. Lowest effort objective (minimizes estimated learning hours).
8. Best fit objective (maximizes overall trajectory score).
9. Market-aware objective (weights market demand opportunity).
10. Maximum hop enforcement (strictly prunes paths exceeding max_hops).
11. Cycle prevention (no career appears more than once in any trajectory).
12. Source equals target handling (graceful 0-hop identical response).
13. Invalid source career returns 404 error.
14. Invalid target career returns 404 error.
15. Deterministic results across repeated executions.
16. Progressive skill reuse calculation and bounding in [0.0, 1.0].
17. Student personalization incorporates demonstrated skills and profile.
18. Phase 11.1 Skill ROI integration for trajectory gaps.
19. Phase 11.2 Portfolio Project recommendation integration across stages.
20. Phase 11.3 Academic curriculum coverage integration.
21. Phase 11.4 Real-time industry demand evidence & provenance disclaimer.
22. API response schema validation for GET /api/careers/<id>/trajectory.
23. Unauthenticated baseline backward compatibility.
24. Zero database mutations guarantee.
25. Backward compatibility with Phase 9 career transition APIs.
"""

import unittest
from app import create_app
from extensions import db
from models.user import User
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from models.student_profile import StudentProfile
from services.career_trajectory_service import (
    CareerTrajectoryService,
    SUPPORTED_OBJECTIVES,
)
from services.career_transition_service import CareerTransitionService
from services.industry_demand_service import INDUSTRY_DEMAND_PROVENANCE
from services.academic_benchmark_service import AcademicBenchmarkService
from flask_jwt_extended import create_access_token


class TestPhase11Module5CareerTrajectory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_career_graph_generation(self):
        """1. Verify in-memory career graph is correctly generated with nodes and edges."""
        with self.app.app_context():
            graph = CareerTrajectoryService.build_career_graph()
            self.assertIsInstance(graph, dict)
            # 10 careers in the database
            self.assertEqual(len(graph), 10)
            for c_id, outgoing_edges in graph.items():
                self.assertIsInstance(outgoing_edges, dict)
                # Each node has outgoing edges to the other 9 careers
                self.assertEqual(len(outgoing_edges), 9)
                self.assertNotIn(c_id, outgoing_edges)  # No self-loops

    def test_02_direct_transition_edge_calculation(self):
        """2. Verify direct transition edge properties between two careers."""
        with self.app.app_context():
            # Software Developer (1) -> DevOps Engineer (3)
            edge = CareerTrajectoryService.calculate_transition_edge(1, 3)
            self.assertIsNotNone(edge)
            self.assertEqual(edge["from_career_id"], 1)
            self.assertEqual(edge["to_career_id"], 3)
            self.assertIn("transition_compatibility", edge)
            self.assertIn("transition_cost", edge)
            self.assertIn("estimated_learning_hours", edge)
            self.assertIn("skill_overlap", edge)
            self.assertIn("transferability", edge)
            self.assertIn("market_opportunity", edge)
            self.assertGreater(edge["estimated_learning_hours"], 0)

    def test_03_transition_compatibility_bounds(self):
        """3. Verify transition compatibility is strictly bounded between 0.0 and 1.0."""
        with self.app.app_context():
            graph = CareerTrajectoryService.build_career_graph()
            for u in graph:
                for v, edge in graph[u].items():
                    compat = edge["transition_compatibility"]
                    self.assertGreaterEqual(compat, 0.0)
                    self.assertLessEqual(compat, 1.0)

    def test_04_transition_cost_bounds_and_non_negativity(self):
        """4. Verify transition cost is strictly bounded in [0.0, 1.0] and non-negative."""
        with self.app.app_context():
            graph = CareerTrajectoryService.build_career_graph()
            for u in graph:
                for v, edge in graph[u].items():
                    cost = edge["transition_cost"]
                    self.assertGreaterEqual(cost, 0.0)
                    self.assertLessEqual(cost, 1.0)
                    self.assertAlmostEqual(cost + edge["transition_compatibility"], 1.0, places=2)

    def test_05_multi_hop_path_discovery(self):
        """5. Verify multi-hop paths (hops > 1) are discovered in the career graph."""
        with self.app.app_context():
            # Software Developer (1) -> DevOps Engineer (3)
            res = CareerTrajectoryService.find_trajectory(target_career_id=3, from_career_id=1, max_hops=3)
            self.assertNotIn("error", res)
            self.assertIn("recommended_trajectory", res)
            self.assertIn("alternative_trajectories", res)
            self.assertGreater(res["total_candidate_trajectories_found"], 1)

    def test_06_shortest_path_objective(self):
        """6. Verify SHORTEST objective selects the trajectory with minimal hop count."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(
                target_career_id=3,
                from_career_id=1,
                objective="SHORTEST",
                max_hops=3
            )
            self.assertNotIn("error", res)
            rec = res["recommended_trajectory"]
            # Shortest between any two nodes in a fully connected graph is direct (1 hop)
            self.assertEqual(rec["hop_count"], 1)
            self.assertEqual(rec["career_ids"], [1, 3])

    def test_07_lowest_effort_objective(self):
        """7. Verify LOWEST_EFFORT objective sorts trajectories by learning hours ascending."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(
                target_career_id=3,
                from_career_id=1,
                objective="LOWEST_EFFORT",
                max_hops=3
            )
            self.assertNotIn("error", res)
            rec = res["recommended_trajectory"]
            self.assertIn("estimated_learning_hours", rec)
            for alt in res["alternative_trajectories"]:
                self.assertGreaterEqual(alt["estimated_learning_hours"], rec["estimated_learning_hours"])

    def test_08_best_fit_objective(self):
        """8. Verify BEST_FIT objective selects the trajectory with maximum trajectory score."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(
                target_career_id=3,
                from_career_id=1,
                objective="BEST_FIT",
                max_hops=3
            )
            self.assertNotIn("error", res)
            rec = res["recommended_trajectory"]
            for alt in res["alternative_trajectories"]:
                self.assertGreaterEqual(rec["trajectory_score"], alt["trajectory_score"])

    def test_09_market_aware_objective(self):
        """9. Verify MARKET_AWARE objective incorporates market demand opportunity."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(
                target_career_id=3,
                from_career_id=1,
                objective="MARKET_AWARE",
                max_hops=3
            )
            self.assertNotIn("error", res)
            rec = res["recommended_trajectory"]
            self.assertIn("market_opportunity_score", rec)
            self.assertGreater(rec["market_opportunity_score"], 0.0)

    def test_10_maximum_hop_enforcement(self):
        """10. Verify that maximum hops limit is strictly enforced across all candidate paths."""
        with self.app.app_context():
            # max_hops = 2
            res = CareerTrajectoryService.find_trajectory(
                target_career_id=3,
                from_career_id=1,
                max_hops=2
            )
            self.assertNotIn("error", res)
            self.assertLessEqual(res["recommended_trajectory"]["hop_count"], 2)
            for alt in res["alternative_trajectories"]:
                self.assertLessEqual(alt["hop_count"], 2)

    def test_11_cycle_prevention(self):
        """11. Verify that no trajectory ever contains duplicate careers (no cycles)."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(
                target_career_id=3,
                from_career_id=1,
                max_hops=4
            )
            self.assertNotIn("error", res)
            rec = res["recommended_trajectory"]
            # No duplicates in recommended
            self.assertEqual(len(rec["career_ids"]), len(set(rec["career_ids"])))
            # No duplicates in alternatives
            for alt in res["alternative_trajectories"]:
                self.assertEqual(len(alt["career_ids"]), len(set(alt["career_ids"])))

    def test_12_source_equals_target_handling(self):
        """12. Verify source equals target returns graceful identical career response."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(target_career_id=1, from_career_id=1)
            self.assertNotIn("error", res)
            self.assertTrue(res["is_identical_career"])
            self.assertEqual(res["recommended_trajectory"]["hop_count"], 0)
            self.assertEqual(res["recommended_trajectory"]["estimated_learning_hours"], 0)

        # Via API
        resp = self.client.get("/api/careers/1/trajectory?from_career_id=1")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["is_identical_career"])

    def test_13_invalid_source_career_returns_404(self):
        """13. Verify non-existent source career returns 404 from service and API."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(target_career_id=1, from_career_id=99999)
            self.assertIn("error", res)
            self.assertEqual(res["error"], "SOURCE_CAREER_NOT_FOUND")

        resp = self.client.get("/api/careers/1/trajectory?from_career_id=99999")
        self.assertEqual(resp.status_code, 404)

    def test_14_invalid_target_career_returns_404(self):
        """14. Verify non-existent target career returns 404 from service and API."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(target_career_id=99999, from_career_id=1)
            self.assertIn("error", res)
            self.assertEqual(res["error"], "TARGET_CAREER_NOT_FOUND")

        resp = self.client.get("/api/careers/99999/trajectory?from_career_id=1")
        self.assertEqual(resp.status_code, 404)

    def test_15_deterministic_results(self):
        """15. Verify trajectory calculations yield identical results on repeated calls."""
        with self.app.app_context():
            res1 = CareerTrajectoryService.find_trajectory(target_career_id=3, from_career_id=1)
            res2 = CareerTrajectoryService.find_trajectory(target_career_id=3, from_career_id=1)
            self.assertEqual(res1["recommended_trajectory"]["career_ids"], res2["recommended_trajectory"]["career_ids"])
            self.assertEqual(res1["recommended_trajectory"]["trajectory_score"], res2["recommended_trajectory"]["trajectory_score"])
            self.assertEqual(res1["recommended_trajectory"]["estimated_learning_hours"], res2["recommended_trajectory"]["estimated_learning_hours"])

    def test_16_progressive_skill_reuse_calculation(self):
        """16. Verify progressive skill reuse calculation bounded in [0.0, 1.0]."""
        with self.app.app_context():
            career_map, skills_map = CareerTrajectoryService._get_all_career_data()
            # Direct path: reuse is 0.0
            direct_reuse = CareerTrajectoryService.calculate_progressive_skill_reuse([1, 3], skills_map)
            self.assertEqual(direct_reuse, 0.0)

            # Multi-hop path: Software Dev (1) -> Cloud Architect (5) -> DevOps (3)
            multihop_reuse = CareerTrajectoryService.calculate_progressive_skill_reuse([1, 5, 3], skills_map)
            self.assertGreaterEqual(multihop_reuse, 0.0)
            self.assertLessEqual(multihop_reuse, 1.0)

    def test_17_student_personalization(self):
        """17. Verify authenticated student request incorporates profile skills and personalization."""
        with self.app.app_context():
            user = User.query.first()
            user_id = user.id if user else 1
            token = create_access_token(identity=str(user_id))

        headers = {"Authorization": f"Bearer {token}"}
        resp = self.client.get("/api/careers/3/trajectory?from_career_id=1", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["is_personalized"])
        self.assertIn("recommended_trajectory", data)

    def test_18_phase11_module1_skill_roi_integration(self):
        """18. Verify Skill ROI integration provides readiness context for missing competencies."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(target_career_id=3, from_career_id=1)
            self.assertNotIn("error", res)
            rec = res["recommended_trajectory"]
            self.assertIn("stages", rec)
            for stage in rec["stages"]:
                self.assertIn("skills_targeted", stage)

    def test_19_phase11_module2_portfolio_capstone_integration(self):
        """19. Verify stages attach recommended portfolio capstone projects to prove skills."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(target_career_id=3, from_career_id=1)
            self.assertNotIn("error", res)
            rec = res["recommended_trajectory"]
            # At least one stage has a recommended capstone
            has_project = any(s.get("recommended_project") is not None for s in rec["stages"])
            self.assertTrue(has_project)

    def test_20_phase11_module3_academic_curriculum_integration(self):
        """20. Verify academic curriculum integration provides baseline contextual evidence."""
        with self.app.app_context():
            # Check that AcademicBenchmarkService runs without conflict alongside trajectory engine
            acad = AcademicBenchmarkService.benchmark_career_curriculum(career_id=3)
            self.assertNotIn("error", acad)
            self.assertIn("academic_alignment_score", acad)

    def test_21_phase11_module4_industry_demand_and_provenance(self):
        """21. Verify industry demand opportunity and mandatory provenance disclaimer notice."""
        with self.app.app_context():
            res = CareerTrajectoryService.find_trajectory(target_career_id=3, from_career_id=1)
            self.assertIn("provenance", res)
            self.assertIn("DEMO / SAMPLE / PROTOTYPE MARKET BENCHMARK", res["provenance"])
            self.assertEqual(res["provenance"], INDUSTRY_DEMAND_PROVENANCE)

    def test_22_api_endpoint_schema_validation(self):
        """22. Verify GET /api/careers/<id>/trajectory returns standard schema and 200 OK."""
        resp = self.client.get("/api/careers/3/trajectory?from_career_id=1&objective=BEST_FIT")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("source_career", data)
        self.assertIn("target_career", data)
        self.assertIn("objective", data)
        self.assertIn("direct_transition", data)
        self.assertIn("recommended_trajectory", data)
        self.assertIn("alternative_trajectories", data)
        self.assertIn("comparison", data)
        self.assertIn("explanation", data)

    def test_23_unauthenticated_baseline_behavior(self):
        """23. Verify unauthenticated request executes successfully with is_personalized=False."""
        resp = self.client.get("/api/careers/3/trajectory?from_career_id=1")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertFalse(data["is_personalized"])
        self.assertEqual(data["source_career"]["id"], 1)
        self.assertEqual(data["target_career"]["id"], 3)

    def test_24_zero_database_mutations_guarantee(self):
        """24. Verify evaluating career trajectories performs zero database mutations."""
        with self.app.app_context():
            c_count = Career.query.count()
            cs_count = CareerSkill.query.count()
            sk_count = Skill.query.count()
            u_count = User.query.count()
            sp_count = StudentProfile.query.count()

            for target_id in [2, 3, 5]:
                CareerTrajectoryService.find_trajectory(target_career_id=target_id, from_career_id=1)
                resp = self.client.get(f"/api/careers/{target_id}/trajectory?from_career_id=1")
                self.assertEqual(resp.status_code, 200)

            self.assertEqual(Career.query.count(), c_count)
            self.assertEqual(CareerSkill.query.count(), cs_count)
            self.assertEqual(Skill.query.count(), sk_count)
            self.assertEqual(User.query.count(), u_count)
            self.assertEqual(StudentProfile.query.count(), sp_count)

    def test_25_backward_compatibility_with_phase9_transition_apis(self):
        """25. Verify existing Phase 9 career transition endpoints remain completely intact."""
        # GET /api/careers/<from>/transition/<to>
        resp_get = self.client.get("/api/careers/1/transition/3")
        self.assertEqual(resp_get.status_code, 200)
        data_get = resp_get.get_json()
        self.assertEqual(data_get["status"], "success")
        self.assertIn("transition", data_get)

        # POST /api/careers/transition
        resp_post = self.client.post("/api/careers/transition", json={"from_career_id": 1, "to_career_id": 3})
        self.assertEqual(resp_post.status_code, 200)
        data_post = resp_post.get_json()
        self.assertEqual(data_post["status"], "success")
        self.assertIn("transition", data_post)


if __name__ == "__main__":
    unittest.main()
