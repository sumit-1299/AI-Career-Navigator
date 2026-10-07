"""
Unit and API Integration Tests for Phase 12 Module 12.1:
End-to-End Recommendation Evaluation & Research Validation Engine.

Verifies:
1. Benchmark dataset loading & schema completeness.
2. Dataset determinism across repeated loads.
3. Prototype research disclaimer notice presence.
4. Precision@K calculation for K in {1, 3, 5}.
5. Recall@K calculation for K in {1, 3, 5}.
6. Hit Rate@K calculation for K in {1, 3, 5}.
7. Mean Reciprocal Rank (MRR) formula and rank-1 edge cases.
8. NDCG@K formula with graded relevance and ideal ranking normalization.
9. Metric boundary handling with empty recommendation list.
10. Metric boundary handling with zero relevant careers.
11. Metric boundary handling when all recommendations are relevant.
12. Skill-gap precision calculation (True Gaps / Predicted Gaps).
13. Skill-gap recall calculation (True Gaps / Expected Gaps).
14. Skill-gap harmonic F1-score calculation.
15. Skill-gap curriculum coverage calculation.
16. Canonical skill ID resolution in EvaluationSkill.
17. Skill alias and character casing normalization.
18. Duplicate skill deduplication and stability.
19. Profile order invariance under list shuffling.
20. Profile casing invariance (UPPERCASE vs lowercase).
21. Proficiency monotonicity (higher proficiency yields non-decreasing readiness).
22. Irrelevant skill addition stability.
23. Cross-module pipeline consistency validation across all 8 intelligence layers.
24. Explanation factual grounding verification.
25. Explanation forbidden safety claims detection and zero-tolerance filtering.
26. Full benchmark suite execution and metric aggregation.
27. Per-career performance breakdown across all 10 tracks.
28. Deterministic repeated evaluation producing identical floating point values.
29. REST API GET /api/careers/evaluation/benchmark response schema & 200 OK.
30. REST API case_id filtering support.
31. REST API invalid case_id error handling & 404 response.
32. Zero database mutations guarantee and backward compatibility.
"""

import unittest
from app import create_app
from extensions import db
from models.career import Career
from models.skill import Skill
from services.career_recommendation_service import CareerRecommendationService
from services.recommendation_evaluation_service import (
    RecommendationEvaluationService,
    EvaluationSkill,
)


class TestPhase12Module1RecommendationEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    # 1. Benchmark dataset schema
    def test_01_benchmark_dataset_loads_and_schema_valid(self):
        """1. Verify benchmark dataset loads successfully and conforms to schema."""
        data = RecommendationEvaluationService.load_benchmark_dataset()
        self.assertIn("benchmark_name", data)
        self.assertIn("cases", data)
        self.assertGreaterEqual(len(data["cases"]), 20)

        for case in data["cases"]:
            self.assertIn("case_id", case)
            self.assertIn("target_profile", case)
            self.assertIn("current_skills", case)
            self.assertIn("expected_career_ids", case)
            self.assertIsInstance(case["current_skills"], list)
            self.assertIsInstance(case["expected_career_ids"], list)

    # 2. Dataset determinism
    def test_02_dataset_determinism(self):
        """2. Verify loading dataset repeatedly produces byte-identical content."""
        data1 = RecommendationEvaluationService.load_benchmark_dataset()
        data2 = RecommendationEvaluationService.load_benchmark_dataset()
        self.assertEqual(len(data1["cases"]), len(data2["cases"]))
        for c1, c2 in zip(data1["cases"], data2["cases"]):
            self.assertEqual(c1["case_id"], c2["case_id"])
            self.assertEqual(c1["expected_career_ids"], c2["expected_career_ids"])

    # 3. Prototype disclaimer present
    def test_03_prototype_disclaimer_present(self):
        """3. Verify dataset and metadata explicitly carry DEMO / SAMPLE / PROTOTYPE disclaimer."""
        meta = RecommendationEvaluationService.get_benchmark_metadata()
        self.assertIn("DEMO / SAMPLE / PROTOTYPE", meta["dataset_type"])
        self.assertIn("NOT REAL STUDENT GROUND TRUTH", meta["disclaimer"])

    # 4. Precision@K calculation
    def test_04_precision_at_k_calculation(self):
        """4. Verify Precision@K formula for K in {1, 3, 5}."""
        rec = [1, 2, 3, 4, 5]
        rel = [1, 3]  # Relevant: 1, 3

        p1 = RecommendationEvaluationService.calculate_precision_at_k(rec, rel, 1)
        self.assertEqual(p1, 1.0)  # [1] -> 1/1 = 1.0

        p3 = RecommendationEvaluationService.calculate_precision_at_k(rec, rel, 3)
        self.assertAlmostEqual(p3, 2.0 / 3.0, places=3)  # [1, 2, 3] -> 2/3 = 0.6667

        p5 = RecommendationEvaluationService.calculate_precision_at_k(rec, rel, 5)
        self.assertEqual(p5, 0.4)  # [1, 2, 3, 4, 5] -> 2/5 = 0.4

    # 5. Recall@K calculation
    def test_05_recall_at_k_calculation(self):
        """5. Verify Recall@K formula for K in {1, 3, 5}."""
        rec = [1, 2, 3, 4, 5]
        rel = [1, 3, 8]  # 3 relevant items

        r1 = RecommendationEvaluationService.calculate_recall_at_k(rec, rel, 1)
        self.assertAlmostEqual(r1, 1.0 / 3.0, places=3)

        r3 = RecommendationEvaluationService.calculate_recall_at_k(rec, rel, 3)
        self.assertAlmostEqual(r3, 2.0 / 3.0, places=3)

        r5 = RecommendationEvaluationService.calculate_recall_at_k(rec, rel, 5)
        self.assertAlmostEqual(r5, 2.0 / 3.0, places=3)

    # 6. Hit Rate@K calculation
    def test_06_hit_rate_at_k_calculation(self):
        """6. Verify Hit Rate@K formula correctly returns binary 1.0 or 0.0."""
        rec = [2, 3, 4, 5]
        rel = [1, 4]

        # Top 1 has [2] -> no hit
        self.assertEqual(RecommendationEvaluationService.calculate_hit_rate_at_k(rec, rel, 1), 0.0)
        # Top 3 has [2, 3, 4] -> 4 is hit
        self.assertEqual(RecommendationEvaluationService.calculate_hit_rate_at_k(rec, rel, 3), 1.0)

    # 7. MRR calculation
    def test_07_mrr_calculation(self):
        """7. Verify Mean Reciprocal Rank (MRR) handles ranks 1, 2, and missing items."""
        self.assertEqual(RecommendationEvaluationService.calculate_mrr([1, 2, 3], [1]), 1.0)
        self.assertEqual(RecommendationEvaluationService.calculate_mrr([2, 1, 3], [1]), 0.5)
        self.assertAlmostEqual(RecommendationEvaluationService.calculate_mrr([2, 3, 1], [1]), 0.3333, places=3)
        self.assertEqual(RecommendationEvaluationService.calculate_mrr([2, 3, 4], [1]), 0.0)

    # 8. NDCG@K calculation
    def test_08_ndcg_at_k_calculation(self):
        """8. Verify NDCG@K formula with graded relevance and ideal ranking."""
        relevance_grades = {1: 3.0, 2: 2.0, 3: 1.0}

        # Perfect ranking: [1, 2, 3] -> NDCG = 1.0
        ndcg_perfect = RecommendationEvaluationService.calculate_ndcg_at_k([1, 2, 3], relevance_grades, 3)
        self.assertEqual(ndcg_perfect, 1.0)

        # Inverted ranking: [3, 2, 1] -> NDCG < 1.0
        ndcg_suboptimal = RecommendationEvaluationService.calculate_ndcg_at_k([3, 2, 1], relevance_grades, 3)
        self.assertLess(ndcg_suboptimal, 1.0)
        self.assertGreater(ndcg_suboptimal, 0.0)

    # 9. Metric boundary: empty recommendations
    def test_09_metric_boundary_empty_recommendations(self):
        """9. Verify all ranking metrics handle empty recommendations gracefully without division by zero."""
        self.assertEqual(RecommendationEvaluationService.calculate_precision_at_k([], [1, 2], 3), 0.0)
        self.assertEqual(RecommendationEvaluationService.calculate_recall_at_k([], [1, 2], 3), 0.0)
        self.assertEqual(RecommendationEvaluationService.calculate_hit_rate_at_k([], [1, 2], 3), 0.0)
        self.assertEqual(RecommendationEvaluationService.calculate_mrr([], [1, 2]), 0.0)
        self.assertEqual(RecommendationEvaluationService.calculate_ndcg_at_k([], {1: 3.0}, 3), 0.0)

    # 10. Metric boundary: no relevant careers
    def test_10_metric_boundary_no_relevant_careers(self):
        """10. Verify handling when no relevant careers exist."""
        self.assertEqual(RecommendationEvaluationService.calculate_precision_at_k([1, 2], [], 2), 0.0)
        self.assertEqual(RecommendationEvaluationService.calculate_recall_at_k([1, 2], [], 2), 0.0)
        self.assertEqual(RecommendationEvaluationService.calculate_hit_rate_at_k([1, 2], [], 2), 0.0)
        self.assertEqual(RecommendationEvaluationService.calculate_mrr([1, 2], []), 0.0)
        self.assertEqual(RecommendationEvaluationService.calculate_ndcg_at_k([1, 2], {}, 2), 0.0)

    # 11. Metric boundary: all relevant careers
    def test_11_metric_boundary_all_relevant_careers(self):
        """11. Verify 1.0 boundary when recommendations match all relevant items."""
        self.assertEqual(RecommendationEvaluationService.calculate_precision_at_k([1, 2], [1, 2], 2), 1.0)
        self.assertEqual(RecommendationEvaluationService.calculate_recall_at_k([1, 2], [1, 2], 2), 1.0)
        self.assertEqual(RecommendationEvaluationService.calculate_hit_rate_at_k([1, 2], [1, 2], 2), 1.0)

    # 12. Skill-gap precision calculation
    def test_12_skill_gap_precision_calculation(self):
        """12. Verify skill gap precision = True Positives / (True Positives + False Positives)."""
        pred = ["Java", "Docker", "Git"]
        exp = ["Java", "Docker"]
        res = RecommendationEvaluationService.evaluate_skill_gaps(pred, exp)
        self.assertAlmostEqual(res["precision"], 2.0 / 3.0, places=3)
        self.assertEqual(res["true_positives"], 2)
        self.assertEqual(res["false_positives"], 1)

    # 13. Skill-gap recall calculation
    def test_13_skill_gap_recall_calculation(self):
        """13. Verify skill gap recall = True Positives / (True Positives + False Negatives)."""
        pred = ["Java"]
        exp = ["Java", "Docker"]
        res = RecommendationEvaluationService.evaluate_skill_gaps(pred, exp)
        self.assertEqual(res["recall"], 0.5)
        self.assertEqual(res["false_negatives"], 1)

    # 14. Skill-gap F1 calculation
    def test_14_skill_gap_f1_calculation(self):
        """14. Verify harmonic mean F1 formula."""
        pred = ["Java", "Docker"]
        exp = ["Java", "Docker"]
        res = RecommendationEvaluationService.evaluate_skill_gaps(pred, exp)
        self.assertEqual(res["f1"], 1.0)

    # 15. Skill-gap coverage calculation
    def test_15_skill_gap_coverage_calculation(self):
        """15. Verify skill gap coverage of required competencies."""
        pred = ["Java", "SQL"]
        exp = ["Java", "SQL", "Git", "Python"]
        res = RecommendationEvaluationService.evaluate_skill_gaps(pred, exp)
        self.assertEqual(res["coverage"], 0.5)

    # 16. Canonical skill handling
    def test_16_canonical_skill_handling(self):
        """16. Verify EvaluationSkill preserves canonical_skill_id and attributes."""
        skill = EvaluationSkill("Python", 8, canonical_skill_id=1)
        self.assertEqual(skill.skill_name, "Python")
        self.assertEqual(skill.proficiency, 8)
        self.assertEqual(skill.canonical_skill_id, 1)

    # 17. Alias and casing handling
    def test_17_alias_and_casing_handling(self):
        """17. Verify skill gap evaluation is case and whitespace invariant."""
        pred = ["  pYtHoN  ", "dOcKeR"]
        exp = ["python", "docker"]
        res = RecommendationEvaluationService.evaluate_skill_gaps(pred, exp)
        self.assertEqual(res["precision"], 1.0)
        self.assertEqual(res["recall"], 1.0)
        self.assertEqual(res["f1"], 1.0)

    # 18. Duplicate skill handling
    def test_18_duplicate_skill_handling(self):
        """18. Verify duplicates in predicted or expected gaps do not distort metrics."""
        pred = ["Java", "Java", "Docker"]
        exp = ["Java", "Docker", "Docker"]
        res = RecommendationEvaluationService.evaluate_skill_gaps(pred, exp)
        self.assertEqual(res["precision"], 1.0)
        self.assertEqual(res["recall"], 1.0)
        self.assertEqual(res["true_positives"], 2)

    # 19. Profile order invariance
    def test_19_order_invariance_robustness(self):
        """19. Verify reversing input skills list produces identical top recommendation."""
        with self.app.app_context():
            skills = [
                {"skill_name": "Python", "proficiency": 8, "canonical_skill_id": 1},
                {"skill_name": "Java", "proficiency": 8, "canonical_skill_id": 2},
                {"skill_name": "Data Structures", "proficiency": 8, "canonical_skill_id": 20}
            ]
            res = RecommendationEvaluationService.run_robustness_tests(skills, target_career_id=1)
            self.assertTrue(res["order_invariance"])

    # 20. Profile casing invariance
    def test_20_casing_invariance_robustness(self):
        """20. Verify casing changes produce identical recommendations and scores."""
        with self.app.app_context():
            skills = [
                {"skill_name": "python", "proficiency": 8, "canonical_skill_id": 1},
                {"skill_name": "java", "proficiency": 8, "canonical_skill_id": 2}
            ]
            res = RecommendationEvaluationService.run_robustness_tests(skills, target_career_id=1)
            self.assertTrue(res["casing_invariance"])

    # 21. Proficiency monotonicity
    def test_21_monotonicity_robustness(self):
        """21. Verify increasing skill proficiency yields non-decreasing readiness."""
        with self.app.app_context():
            skills = [
                {"skill_name": "Python", "proficiency": 4, "canonical_skill_id": 1},
                {"skill_name": "Java", "proficiency": 4, "canonical_skill_id": 2}
            ]
            res = RecommendationEvaluationService.run_robustness_tests(skills, target_career_id=1)
            self.assertTrue(res["monotonicity"])

    # 22. Irrelevant skill stability
    def test_22_irrelevant_skill_stability(self):
        """22. Verify adding irrelevant skill does not penalize target career recommendation."""
        with self.app.app_context():
            skills = [
                {"skill_name": "Python", "proficiency": 8, "canonical_skill_id": 1},
                {"skill_name": "Java", "proficiency": 8, "canonical_skill_id": 2}
            ]
            res = RecommendationEvaluationService.run_robustness_tests(skills, target_career_id=1)
            self.assertTrue(res["irrelevant_skill_stability"])

    # 23. Cross-module consistency
    def test_23_cross_module_consistency_validation(self):
        """23. Verify cross-module validation executes across all 8 intelligence layers."""
        with self.app.app_context():
            res = RecommendationEvaluationService.validate_cross_module_consistency(career_id=1)
            self.assertEqual(res["total_checks"], 8)
            self.assertEqual(res["passed_checks"], 8)
            self.assertEqual(res["consistency_rate"], 100.0)
            self.assertTrue(res["all_passed"])

    # 24. Explanation factual grounding
    def test_24_explanation_factual_grounding(self):
        """24. Verify explainability text cites computed career title, readiness, or skills."""
        text = "Your existing Python skills provide a strong foundation for Software Developer (readiness: 75.0%)."
        res = RecommendationEvaluationService.validate_explanation(
            explanation_text=text,
            career_title="Software Developer",
            readiness_pct=75.0,
            matched_skills=["Python"]
        )
        self.assertTrue(res["factually_grounded"])
        self.assertTrue(res["educational_tone_compliant"])
        self.assertTrue(res["is_valid"])

    # 25. Explanation forbidden safety claims
    def test_25_explanation_forbidden_claims_absence(self):
        """25. Verify detection of forbidden claims (guaranteed employment, intelligence)."""
        bad_text = "This career guarantees employment and proves you will definitely get this job."
        res = RecommendationEvaluationService.validate_explanation(
            explanation_text=bad_text,
            career_title="Software Developer",
            readiness_pct=80.0
        )
        self.assertFalse(res["is_valid"])
        self.assertGreater(res["forbidden_claims_count"], 0)
        self.assertIn("guarantees employment", res["forbidden_claims_detected"])

    # 26. Full benchmark execution
    def test_26_full_benchmark_execution(self):
        """26. Verify run_full_benchmark_evaluation executes across dataset and populates metrics."""
        with self.app.app_context():
            report = RecommendationEvaluationService.run_full_benchmark_evaluation(limit_cases=5)
            self.assertEqual(report["total_cases_evaluated"], 5)
            self.assertIn("career_ranking_metrics", report)
            self.assertIn("precision_at_1", report["career_ranking_metrics"])
            self.assertIn("skill_gap_metrics", report)
            self.assertIn("robustness", report)
            self.assertIn("cross_module_consistency", report)
            self.assertIn("explanation_validation", report)

    # 27. Per-career performance breakdown
    def test_27_benchmark_per_career_breakdown(self):
        """27. Verify per-career performance metrics are populated for all 10 tracks."""
        with self.app.app_context():
            report = RecommendationEvaluationService.run_full_benchmark_evaluation(limit_cases=5)
            per_career = report.get("per_career_performance", {})
            self.assertEqual(len(per_career), 10)
            for cid in range(1, 11):
                self.assertIn(cid, per_career)
                self.assertIn("career_title", per_career[cid])

    # 28. Deterministic repeated evaluation
    def test_28_deterministic_repeated_evaluation(self):
        """28. Verify repeated benchmark executions yield exactly identical ranking metrics."""
        with self.app.app_context():
            rep1 = RecommendationEvaluationService.run_full_benchmark_evaluation(limit_cases=3)
            rep2 = RecommendationEvaluationService.run_full_benchmark_evaluation(limit_cases=3)
            p1_first = rep1["career_ranking_metrics"]["precision_at_1"]
            p1_second = rep2["career_ranking_metrics"]["precision_at_1"]
            self.assertEqual(p1_first, p1_second)

    # 29. API endpoint GET /api/careers/evaluation/benchmark
    def test_29_api_endpoint_benchmark_get(self):
        """29. Verify GET /api/careers/evaluation/benchmark returns 200 OK and expected schema."""
        resp = self.client.get("/api/careers/evaluation/benchmark?limit=2")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "success")
        bench = data.get("benchmark", {})
        self.assertIn("career_ranking_metrics", bench)
        self.assertIn("skill_gap_metrics", bench)
        self.assertEqual(bench.get("total_cases_evaluated"), 2)

    # 30. API endpoint case_id filtering support
    def test_30_api_endpoint_case_id_filtering(self):
        """30. Verify filtering by specific case_id evaluates only that case."""
        resp = self.client.get("/api/careers/evaluation/benchmark?case_id=BENCH-001")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        bench = data.get("benchmark", {})
        self.assertEqual(bench.get("total_cases_evaluated"), 1)
        self.assertEqual(bench["per_case_results"][0]["case_id"], "BENCH-001")

    # 31. API endpoint invalid case_id error handling
    def test_31_api_endpoint_invalid_query_params(self):
        """31. Verify invalid case_id returns 404 with structured error message."""
        resp = self.client.get("/api/careers/evaluation/benchmark?case_id=NONEXISTENT_999")
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("not found", data.get("message", "").lower())

    # 32. Zero database mutations and backward compatibility
    def test_32_zero_database_mutations_and_backward_compatibility(self):
        """32. Verify benchmark evaluation produces zero DB table mutations and preserves existing routes."""
        with self.app.app_context():
            initial_career_count = Career.query.count()
            initial_skill_count = Skill.query.count()

            # Execute evaluation
            report = RecommendationEvaluationService.run_full_benchmark_evaluation(limit_cases=2)
            self.assertIsNotNone(report)

            final_career_count = Career.query.count()
            final_skill_count = Skill.query.count()

            self.assertEqual(initial_career_count, final_career_count)
            self.assertEqual(initial_skill_count, final_skill_count)

        # Existing routes remain functional
        resp = self.client.get("/api/careers")
        self.assertEqual(resp.status_code, 200)

        resp2 = self.client.get("/api/careers/1/skill-gap")
        self.assertEqual(resp2.status_code, 200)


if __name__ == "__main__":
    unittest.main()
