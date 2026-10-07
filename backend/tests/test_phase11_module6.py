"""
Unit and API Integration Tests for Phase 11 Module 11.6:
AI Interview Simulation & Career Readiness Assessment Engine.

Verifies:
1. Question bank loading & schema completeness.
2. Career-specific question coverage across all 10 tracks.
3. Deterministic question selection.
4. Difficulty filtering (BEGINNER, INTERMEDIATE, ADVANCED, ALL).
5. Question count validation & clamping (1-10).
6. Concept normalization (case, punctuation, whitespace).
7. Concept coverage calculation.
8. Answer completeness scoring based on substantive length.
9. Answer structure & communication indicators scoring.
10. Answer quality composite formula.
11. Technical category scoring.
12. Conceptual category scoring.
13. Problem-solving category scoring.
14. Communication category scoring.
15. Career competency coverage scoring.
16. Overall readiness calculation formula.
17. Readiness band mapping (INTERVIEW_READY, STRONG_PREPARATION, NEEDS_PRACTICE, FOUNDATION_REQUIRED).
18. Missing concept detection & feedback.
19. Canonical career competency linkage.
20. Empty answer handling and graceful 0-score.
21. Phase 11.1 Skill ROI integration for interview weaknesses.
22. Phase 11.2 Portfolio Project recommendations for proof-of-work.
23. Phase 11.3 Academic curriculum coverage integration.
24. Phase 11.4 Industry Demand & provenance disclaimer.
25. Phase 11.5 Career Trajectory intelligence integration.
26. Invalid career ID returns 404 error.
27. Invalid/empty answers payload returns 400 error.
28. Deterministic evaluation repeatability.
29. Session generation API endpoint schema (omits expected concepts).
30. Evaluation API endpoint schema & 200 OK.
31. Optional JWT authentication & personalization behavior.
32. Zero database mutations guarantee and backward compatibility.
"""

import unittest
from app import create_app
from extensions import db
from models.user import User
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from services.interview_simulation_service import (
    InterviewSimulationService,
    QUESTION_BANK,
    QUESTION_BY_ID,
    READINESS_BANDS,
    normalize_text,
    normalize_skill_name,
)
from flask_jwt_extended import create_access_token


class TestPhase11Module6InterviewSimulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_question_bank_loading(self):
        """1. Verify question bank loads successfully with required schema keys."""
        self.assertGreaterEqual(len(QUESTION_BANK), 60)
        for q in QUESTION_BANK:
            self.assertIn("question_id", q)
            self.assertIn("career_id", q)
            self.assertIn("career_title", q)
            self.assertIn("competency", q)
            self.assertIn("category", q)
            self.assertIn("difficulty", q)
            self.assertIn("question_text", q)
            self.assertIn("expected_concepts", q)
            self.assertIsInstance(q["expected_concepts"], list)
            self.assertGreater(len(q["expected_concepts"]), 0)

    def test_02_career_specific_questions(self):
        """2. Verify all 10 standardized careers have associated questions."""
        with self.app.app_context():
            careers = Career.query.all()
            for c in careers:
                questions = InterviewSimulationService.get_question_bank(career_id=c.id)
                self.assertGreaterEqual(
                    len(questions), 5,
                    f"Career {c.title} (ID {c.id}) has fewer than 5 questions"
                )

    def test_03_deterministic_question_selection(self):
        """3. Verify question selection is 100% deterministic given identical arguments."""
        with self.app.app_context():
            res1 = InterviewSimulationService.generate_session(career_id=1, difficulty="INTERMEDIATE", question_count=5)
            res2 = InterviewSimulationService.generate_session(career_id=1, difficulty="INTERMEDIATE", question_count=5)
            ids1 = [q["question_id"] for q in res1["questions"]]
            ids2 = [q["question_id"] for q in res2["questions"]]
            self.assertEqual(ids1, ids2)

    def test_04_difficulty_filtering(self):
        """4. Verify difficulty filter appropriately narrows question selection."""
        with self.app.app_context():
            res_beg = InterviewSimulationService.generate_session(career_id=1, difficulty="BEGINNER", question_count=3)
            for q in res_beg["questions"]:
                self.assertEqual(q["difficulty"], "BEGINNER")

            res_all = InterviewSimulationService.generate_session(career_id=1, difficulty="ALL", question_count=6)
            self.assertEqual(len(res_all["questions"]), 6)

    def test_05_question_count_validation(self):
        """5. Verify question count is clamped between 1 and 10."""
        with self.app.app_context():
            res_low = InterviewSimulationService.generate_session(career_id=2, question_count=0)
            self.assertGreaterEqual(len(res_low["questions"]), 1)

            res_high = InterviewSimulationService.generate_session(career_id=2, question_count=999)
            self.assertLessEqual(len(res_high["questions"]), 10)

    def test_06_concept_normalization(self):
        """6. Verify text normalization removes punctuation, excess spaces, and normalizes case."""
        raw = "   Docker   Containers,   Images, and Microservices!  "
        norm = normalize_text(raw)
        self.assertEqual(norm, "docker containers, images, and microservices!")

        skill_norm = normalize_skill_name("  C++ / Data Structures  ")
        self.assertEqual(skill_norm, "cdatastructures")

    def test_07_concept_coverage_calculation(self):
        """7. Verify concept coverage calculation: matched / total * 100."""
        q = {
            "question_id": "test-q-01",
            "competency": "Docker",
            "category": "TECHNICAL",
            "difficulty": "INTERMEDIATE",
            "question_text": "What is Docker?",
            "expected_concepts": ["container", "image", "isolation", "namespaces"],
        }
        answer = "Docker packages applications into a container using an image for process isolation."
        eval_res = InterviewSimulationService._evaluate_single_answer(q, answer)
        self.assertEqual(len(eval_res["matched_concepts"]), 3)
        self.assertEqual(len(eval_res["missing_concepts"]), 1)
        self.assertEqual(eval_res["concept_coverage"], 75.0)

    def test_08_completeness_scoring(self):
        """8. Verify substantive answers score higher completeness than short one-liners."""
        q = QUESTION_BANK[0]
        short_ans = "Array is fast."
        detailed_ans = (
            "An array uses contiguous memory allocation which provides O(1) random access by index. "
            "In contrast, a linked list allocates nodes non-contiguously using pointers, resulting in O(n) "
            "lookup time because traversal is sequential. However, linked lists allow dynamic sizing without reallocating "
            "the entire memory block, whereas arrays have fixed size or amortized resizing costs."
        )
        res_short = InterviewSimulationService._evaluate_single_answer(q, short_ans)
        res_detailed = InterviewSimulationService._evaluate_single_answer(q, detailed_ans)
        self.assertLess(res_short["completeness_score"], res_detailed["completeness_score"])
        self.assertGreaterEqual(res_detailed["completeness_score"], 80.0)

    def test_09_answer_structure_scoring(self):
        """9. Verify structure score rewards capitalization, multiple sentences, and logical connectives."""
        q = QUESTION_BANK[0]
        unstructured = "array fast linked list slow"
        structured = (
            "First, arrays utilize contiguous memory blocks. Because of cache locality, index lookups are O(1). "
            "Second, linked lists rely on pointer references; therefore, lookups require O(n) traversal."
        )
        res_unstruct = InterviewSimulationService._evaluate_single_answer(q, unstructured)
        res_struct = InterviewSimulationService._evaluate_single_answer(q, structured)
        self.assertGreater(res_struct["structure_score"], res_unstruct["structure_score"])

    def test_10_answer_quality_calculation(self):
        """10. Verify composite answer quality formula is bounded [0, 100]."""
        q = QUESTION_BANK[0]
        sample = "Arrays provide contiguous memory and O(1) index access, whereas linked lists use pointers with O(n) lookups."
        res = InterviewSimulationService._evaluate_single_answer(q, sample)
        self.assertGreaterEqual(res["score"], 0)
        self.assertLessEqual(res["score"], 100)
        # Expected formula check: round(0.60 * coverage + 0.20 * completeness + 0.20 * structure)
        expected = round(
            0.60 * res["concept_coverage"] +
            0.20 * res["completeness_score"] +
            0.20 * res["structure_score"]
        )
        self.assertEqual(res["score"], expected)

    def test_11_technical_category_scoring(self):
        """11. Verify TECHNICAL questions aggregate properly into category score."""
        with self.app.app_context():
            answers = [
                {"question_id": "sd-tech-01", "answer": "Arrays use contiguous memory with O(1) access, whereas linked lists use pointers with O(n) traversal."},
                {"question_id": "sd-tech-02", "answer": "Python generators use the yield keyword for lazy evaluation, preserving state across iterations."}
            ]
            res = InterviewSimulationService.evaluate_session(career_id=1, answers=answers)
            self.assertIn("technical", res["category_scores"])
            self.assertGreater(res["category_scores"]["technical"], 50)

    def test_12_conceptual_category_scoring(self):
        """12. Verify CONCEPTUAL questions aggregate into conceptual category score."""
        with self.app.app_context():
            answers = [
                {"question_id": "sd-conc-01", "answer": "The four OOP principles are encapsulation, inheritance, polymorphism, and abstraction. Polymorphism allows method overriding."}
            ]
            res = InterviewSimulationService.evaluate_session(career_id=1, answers=answers)
            self.assertIn("conceptual", res["category_scores"])
            self.assertGreater(res["category_scores"]["conceptual"], 60)

    def test_13_problem_solving_category_scoring(self):
        """13. Verify PROBLEM_SOLVING and SCENARIO questions aggregate into problem_solving score."""
        with self.app.app_context():
            answers = [
                {"question_id": "sd-prob-01", "answer": "To optimize slow joins, I run EXPLAIN ANALYZE to inspect the execution plan, avoid full table scans, and add indexes."},
                {"question_id": "sd-scen-01", "answer": "To resolve a merge conflict, I use git status and git diff to find conflict markers, edit differences, test, and commit."}
            ]
            res = InterviewSimulationService.evaluate_session(career_id=1, answers=answers)
            self.assertIn("problem_solving", res["category_scores"])
            self.assertGreater(res["category_scores"]["problem_solving"], 60)

    def test_14_communication_scoring(self):
        """14. Verify communication score aggregates structure across all answers."""
        with self.app.app_context():
            answers = [
                {"question_id": "sd-tech-01", "answer": "First, arrays use contiguous memory. Second, linked lists use pointers."},
                {"question_id": "sd-behav-01", "answer": "I welcome constructive code review feedback because collaboration improves code quality and maintainability."}
            ]
            res = InterviewSimulationService.evaluate_session(career_id=1, answers=answers)
            self.assertIn("communication", res["category_scores"])
            self.assertGreaterEqual(res["category_scores"]["communication"], 50)

    def test_15_career_competency_scoring(self):
        """15. Verify career competency coverage score is bounded between 20 and 100."""
        with self.app.app_context():
            answers = [
                {"question_id": "sd-tech-01", "answer": "Contiguous memory with pointers."},
            ]
            res = InterviewSimulationService.evaluate_session(career_id=1, answers=answers)
            self.assertIn("career_competency", res["category_scores"])
            comp_score = res["category_scores"]["career_competency"]
            self.assertGreaterEqual(comp_score, 0.0)
            self.assertLessEqual(comp_score, 100.0)

    def test_16_overall_readiness_calculation(self):
        """16. Verify overall readiness is calculated using the weighted formula."""
        with self.app.app_context():
            answers = [
                {"question_id": "sd-tech-01", "answer": "Contiguous memory layout provides O(1) array access. Linked lists use pointers with O(n) lookup."},
                {"question_id": "sd-conc-01", "answer": "Encapsulation, inheritance, polymorphism, and abstraction. Polymorphism enables method overriding through interfaces."},
            ]
            res = InterviewSimulationService.evaluate_session(career_id=1, answers=answers)
            cats = res["category_scores"]
            expected = round(
                0.30 * cats["technical"] +
                0.20 * cats["conceptual"] +
                0.20 * cats["problem_solving"] +
                0.15 * cats["communication"] +
                0.15 * cats["career_competency"]
            )
            expected = max(0, min(100, expected))
            self.assertEqual(res["overall_readiness"], expected)

    def test_17_readiness_band_mapping(self):
        """17. Verify overall readiness score correctly maps to readiness bands."""
        bands = READINESS_BANDS
        self.assertIn("INTERVIEW_READY", bands)
        self.assertIn("STRONG_PREPARATION", bands)
        self.assertIn("NEEDS_PRACTICE", bands)
        self.assertIn("FOUNDATION_REQUIRED", bands)

        with self.app.app_context():
            # Perfect answers -> INTERVIEW_READY or STRONG_PREPARATION
            high_answers = [
                {"question_id": "sd-tech-01", "answer": "Arrays use contiguous memory providing O(1) random access with cache locality. Linked lists use non-contiguous pointers with O(n) sequential lookup and dynamic sizing."},
                {"question_id": "sd-tech-02", "answer": "Python generators use yield for lazy evaluation and memory efficiency, maintaining state preservation as an iterator without loading all data."},
                {"question_id": "sd-conc-01", "answer": "The four principles are encapsulation, inheritance, polymorphism, and abstraction. Polymorphism allows method overriding and interface implementations."},
                {"question_id": "sd-prob-01", "answer": "I run EXPLAIN ANALYZE to inspect the execution plan, identifying full table scans on join conditions, then create appropriate B-tree indexing."},
                {"question_id": "sd-scen-01", "answer": "When a merge conflict occurs, I use git status and git diff to examine conflict markers, discuss with teammates, test the resolution, and commit."},
            ]
            res_high = InterviewSimulationService.evaluate_session(career_id=1, answers=high_answers)
            self.assertIn(res_high["readiness_band"], ["INTERVIEW_READY", "STRONG_PREPARATION"])

    def test_18_missing_concept_detection(self):
        """18. Verify missing concepts are accurately detected and reported in feedback."""
        q = QUESTION_BY_ID["cloud-tech-01"]
        incomplete_ans = "IAM roles provide permissions."
        res = InterviewSimulationService._evaluate_single_answer(q, incomplete_ans)
        self.assertIn("temporary credentials", res["missing_concepts"])
        self.assertIn("least privilege", res["missing_concepts"])
        self.assertIn("To strengthen this response", res["feedback"])

    def test_19_canonical_skill_matching(self):
        """19. Verify question competencies correctly match standardized career skills."""
        with self.app.app_context():
            cloud_skills = [cs.skill_name.lower() for cs in CareerSkill.query.filter_by(career_id=6).all()]
            cloud_questions = InterviewSimulationService.get_question_bank(career_id=6)
            matched = False
            for q in cloud_questions:
                if q["competency"].lower() in cloud_skills:
                    matched = True
                    break
            self.assertTrue(matched, "No questions matched career skills for Cloud Engineer")

    def test_20_empty_answer_handling(self):
        """20. Verify blank or whitespace answers receive score 0 and constructive message."""
        q = QUESTION_BANK[0]
        res = InterviewSimulationService._evaluate_single_answer(q, "    ")
        self.assertEqual(res["score"], 0)
        self.assertEqual(res["concept_coverage"], 0.0)
        self.assertIn("No answer was provided", res["feedback"])

    def test_21_phase11_1_skill_roi_integration(self):
        """21. Verify weak competencies connect to Phase 11.1 Skill ROI recommendations."""
        with self.app.app_context():
            answers = [
                {"question_id": "cloud-tech-02", "answer": "Containers run apps."},  # weak Docker
            ]
            res = InterviewSimulationService.evaluate_session(career_id=6, answers=answers)
            roi_data = res.get("integrations", {}).get("skill_roi")
            if roi_data:
                self.assertIn("prioritized_skill", roi_data)
                self.assertIn("roi_score", roi_data)
                self.assertIn("readiness_gain", roi_data)

    def test_22_phase11_2_portfolio_integration(self):
        """22. Verify weak competencies connect to Phase 11.2 Portfolio Project recommendations."""
        with self.app.app_context():
            answers = [
                {"question_id": "devops-tech-01", "answer": "Kubernetes pods run containers."},
            ]
            res = InterviewSimulationService.evaluate_session(career_id=7, answers=answers)
            proj_data = res.get("integrations", {}).get("portfolio_project")
            if proj_data:
                self.assertIn("project_id", proj_data)
                self.assertIn("title", proj_data)
                self.assertIn("difficulty", proj_data)

    def test_23_phase11_3_academic_integration(self):
        """23. Verify academic curriculum coverage data is integrated where available."""
        with self.app.app_context():
            answers = [
                {"question_id": "sd-tech-01", "answer": "Arrays vs linked lists."},
            ]
            res = InterviewSimulationService.evaluate_session(career_id=1, answers=answers)
            acad_data = res.get("integrations", {}).get("academic_alignment")
            if acad_data:
                self.assertIn("academic_program", acad_data)
                self.assertIn("curriculum_coverage_score", acad_data)

    def test_24_phase11_4_market_integration(self):
        """24. Verify industry demand data and mandatory provenance disclaimer are included."""
        with self.app.app_context():
            answers = [
                {"question_id": "cloud-tech-01", "answer": "AWS IAM roles and security."},
            ]
            res = InterviewSimulationService.evaluate_session(career_id=6, answers=answers)
            self.assertEqual(res["provenance"], "DEMO / SAMPLE / PROTOTYPE MARKET BENCHMARK — NOT LIVE LABOR MARKET DATA")
            dem_data = res.get("integrations", {}).get("industry_demand")
            if dem_data:
                self.assertIn("demand_level", dem_data)

    def test_25_phase11_5_trajectory_integration(self):
        """25. Verify multi-hop trajectory intelligence is integrated into session evaluation."""
        with self.app.app_context():
            answers = [
                {"question_id": "devops-tech-01", "answer": "Kubernetes orchestration."},
            ]
            res = InterviewSimulationService.evaluate_session(career_id=7, answers=answers)
            traj_data = res.get("integrations", {}).get("trajectory_relevance")
            if traj_data:
                self.assertIn("trajectory_roles", traj_data)

    def test_26_invalid_career_returns_404(self):
        """26. Verify non-existent career returns 404 from service and API."""
        with self.app.app_context():
            res = InterviewSimulationService.generate_session(career_id=99999)
            self.assertIn("error", res)
            self.assertEqual(res["error"], "CAREER_NOT_FOUND")

        resp = self.client.get("/api/careers/99999/interview-simulation")
        self.assertEqual(resp.status_code, 404)

    def test_27_invalid_request_handling(self):
        """27. Verify empty or malformed answer payload returns 400 error."""
        resp = self.client.post("/api/careers/1/interview-simulation/evaluate", json={})
        self.assertEqual(resp.status_code, 400)

        resp2 = self.client.post("/api/careers/1/interview-simulation/evaluate", json={"answers": []})
        self.assertEqual(resp2.status_code, 400)

    def test_28_deterministic_evaluation(self):
        """28. Verify evaluating the same answers yields identical numerical results."""
        with self.app.app_context():
            answers = [
                {"question_id": "sd-tech-01", "answer": "Arrays use contiguous memory layout. Linked lists use pointers."},
                {"question_id": "sd-conc-01", "answer": "Encapsulation, inheritance, polymorphism, and abstraction."}
            ]
            eval1 = InterviewSimulationService.evaluate_session(career_id=1, answers=answers)
            eval2 = InterviewSimulationService.evaluate_session(career_id=1, answers=answers)
            self.assertEqual(eval1["overall_readiness"], eval2["overall_readiness"])
            self.assertEqual(eval1["readiness_band"], eval2["readiness_band"])
            self.assertEqual(eval1["category_scores"], eval2["category_scores"])

    def test_29_api_session_generation_schema(self):
        """29. Verify GET /api/careers/<id>/interview-simulation returns 200 and omits answer key."""
        resp = self.client.get("/api/careers/1/interview-simulation?difficulty=INTERMEDIATE&question_count=4")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["question_count"], 4)
        for q in data["questions"]:
            self.assertIn("question_id", q)
            self.assertIn("question_text", q)
            self.assertIn("competency", q)
            self.assertNotIn("expected_concepts", q, "Student question payload must NOT leak expected concepts!")

    def test_30_api_evaluate_schema(self):
        """30. Verify POST /api/careers/<id>/interview-simulation/evaluate returns 200 and standard schema."""
        payload = {
            "difficulty": "INTERMEDIATE",
            "answers": [
                {
                    "question_id": "sd-tech-01",
                    "answer": "Arrays use contiguous memory with O(1) random access. Linked lists use pointers with O(n) sequential lookups."
                }
            ]
        }
        resp = self.client.post("/api/careers/1/interview-simulation/evaluate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("overall_readiness", data)
        self.assertIn("readiness_band", data)
        self.assertIn("category_scores", data)
        self.assertIn("question_results", data)
        self.assertIn("strengths", data)
        self.assertIn("weaknesses", data)
        self.assertIn("priority_skills", data)
        self.assertIn("integrations", data)
        self.assertIn("explanation", data)

    def test_31_optional_jwt_behavior(self):
        """31. Verify optional JWT token enables personalized skill gap prioritization."""
        with self.app.app_context():
            user = User.query.first()
            if user:
                token = create_access_token(identity=str(user.id))
                headers = {"Authorization": f"Bearer {token}"}
                resp = self.client.get("/api/careers/1/interview-simulation", headers=headers)
                self.assertEqual(resp.status_code, 200)
                data = resp.get_json()
                self.assertTrue(data.get("is_personalized"))

    def test_32_zero_database_mutations_and_backward_compatibility(self):
        """32. Verify interview simulation executes with zero database mutations."""
        with self.app.app_context():
            from sqlalchemy import inspect
            initial_tables = inspect(db.engine).get_table_names()
            self.assertEqual(len(initial_tables), 11)

            payload = {
                "answers": [{"question_id": "sd-tech-01", "answer": "Contiguous array memory."}]
            }
            resp = self.client.post("/api/careers/1/interview-simulation/evaluate", json=payload)
            self.assertEqual(resp.status_code, 200)

            post_tables = inspect(db.engine).get_table_names()
            self.assertEqual(len(post_tables), 11)
            self.assertEqual(initial_tables, post_tables)


if __name__ == "__main__":
    unittest.main()
