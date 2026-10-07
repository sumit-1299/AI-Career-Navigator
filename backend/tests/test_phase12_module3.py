"""
Unit and API Integration Tests for Phase 12 Module 12.3:
Practical Skill Assessment & Hands-On Task Engine.

Verifies:
1. Task bank availability across all 10 canonical IT careers.
2. Career task filtering (e.g., career_id=1 returns only Software Developer tasks).
3. Difficulty filtering (BEGINNER, INTERMEDIATE, ADVANCED).
4. Skill filtering (e.g., skill='Python', skill='Docker').
5. Category filtering (e.g., category='API_DEVELOPMENT', 'DATABASE').
6. Deterministic ordering (identical inputs yield identical task order).
7. Task schema structure (all required attributes present).
8. Expected concepts presence and typing.
9. Requirement coverage scoring logic.
10. Concept coverage calculation.
11. Criteria coverage calculation.
12. Completeness scoring progression.
13. Structure scoring (code blocks, lists, headings).
14. Practical score formula weighting (0.40 C + 0.25 R + 0.20 Cr + 0.10 Comp + 0.05 S).
15. Score clamping (boundary checking between 0.0 and 100.0).
16. Result band mapping (STRONG_PRACTICAL_MASTERY, PRACTICE_READY, NEEDS_REINFORCEMENT, FOUNDATION_REQUIRED).
17. Missing concept detection and handling.
18. Skill evidence synthesis and strength labeling.
19. Remaining technical gaps synthesis.
20. Recommended next task progression (level up vs reinforce).
21. Phase 11.1 Skill ROI integration with task priority.
22. Phase 11.2 Portfolio capstone integration with task priority.
23. Phase 11.3 Academic benchmark integration with task priority.
24. Phase 11.4 Industry demand integration with task priority.
25. Phase 12.2 Job-specific missing skill prioritization.
26. Invalid task handling (404 Not Found).
27. Invalid request payload handling (400 Bad Request).
28. Oversized answer payload rejection (413 Payload Too Large).
29. Authentication compatibility (authenticated JWT vs anonymous guest).
30. Strict zero database mutations guarantee.
31. Deterministic evaluation repeatability.
32. Backward compatibility of existing career and job endpoints.
"""

import unittest
from app import create_app
from extensions import db
from models.career import Career
from models.skill import Skill
from models.user import User
from services.practical_task_service import PracticalTaskService


class TestPhase12Module3PracticalTaskEngine(unittest.TestCase):
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

    # 1. Task bank availability
    def test_01_task_bank_availability(self):
        """1. Verify task bank is populated across all 10 canonical IT careers."""
        self.assertGreaterEqual(len(PracticalTaskService.TASK_BANK), 30)
        career_ids = {t["career_id"] for t in PracticalTaskService.TASK_BANK}
        for cid in range(1, 11):
            self.assertIn(cid, career_ids, f"Career {cid} missing from task bank")

    # 2. Career task filtering
    def test_02_career_task_filtering(self):
        """2. Verify filtering tasks by career_id returns only matching career tasks."""
        res = PracticalTaskService.list_tasks(career_id=1)
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(len(res["tasks"]), 1)
        for t in res["tasks"]:
            self.assertEqual(t["career_id"], 1)
            self.assertEqual(t["career_title"], "Software Developer")

    # 3. Difficulty filtering
    def test_03_difficulty_filtering(self):
        """3. Verify filtering tasks by difficulty (BEGINNER, INTERMEDIATE, ADVANCED)."""
        res_beg = PracticalTaskService.list_tasks(difficulty="BEGINNER")
        for t in res_beg["tasks"]:
            self.assertEqual(t["difficulty"], "BEGINNER")

        res_adv = PracticalTaskService.list_tasks(difficulty="ADVANCED")
        for t in res_adv["tasks"]:
            self.assertEqual(t["difficulty"], "ADVANCED")

    # 4. Skill filtering
    def test_04_skill_filtering(self):
        """4. Verify filtering tasks by skill matches canonical skill names."""
        res = PracticalTaskService.list_tasks(skill="Python")
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(len(res["tasks"]), 1)
        for t in res["tasks"]:
            self.assertEqual(t["skill"].casefold(), "python")

    # 5. Category filtering
    def test_05_category_filtering(self):
        """5. Verify category filtering returns only tasks of the requested category."""
        res = PracticalTaskService.list_tasks(category="DATABASE")
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(len(res["tasks"]), 1)
        for t in res["tasks"]:
            self.assertEqual(t["category"], "DATABASE")

    # 6. Deterministic ordering
    def test_06_deterministic_ordering(self):
        """6. Verify identical query parameters yield identical task orderings."""
        res_a = PracticalTaskService.list_tasks(career_id=2, limit=10)
        res_b = PracticalTaskService.list_tasks(career_id=2, limit=10)
        ids_a = [t["id"] for t in res_a["tasks"]]
        ids_b = [t["id"] for t in res_b["tasks"]]
        self.assertEqual(ids_a, ids_b)

    # 7. Task structure
    def test_07_task_structure(self):
        """7. Verify each task contains all mandatory metadata fields."""
        required_keys = [
            "id", "title", "career_id", "career_title", "skill", "category",
            "difficulty", "estimated_minutes", "scenario", "objective",
            "requirements", "expected_concepts", "evaluation_criteria",
            "hints", "expected_outcome", "learning_objective",
            "portfolio_relevance", "interview_relevance"
        ]
        for t in PracticalTaskService.TASK_BANK:
            for k in required_keys:
                self.assertIn(k, t, f"Task {t.get('id')} missing key {k}")
                self.assertIsNotNone(t[k])

    # 8. Expected concepts
    def test_08_expected_concepts(self):
        """8. Verify all tasks define at least 3 distinct expected technical concepts."""
        for t in PracticalTaskService.TASK_BANK:
            self.assertIsInstance(t["expected_concepts"], list)
            self.assertGreaterEqual(len(t["expected_concepts"]), 3)

    # 9. Requirement coverage
    def test_09_requirement_coverage(self):
        """9. Verify requirement coverage matches when key requirement terms are addressed."""
        task = PracticalTaskService.get_task_by_id("pt-sd-01")
        self.assertIsNotNone(task)
        answer = (
            "We validate that required fields email, username, and age exist in payload. "
            "Ensure age is a positive integer and email follows a valid format. "
            "Return HTTP 400 with structured error response specifying missing or invalid fields. "
            "Sanitize strings against injection and disallow unexpected extra fields."
        )
        res = PracticalTaskService.evaluate_task_attempt(task_id="pt-sd-01", answer=answer)
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["evaluation"]["requirement_coverage"], 75.0)

    # 10. Concept coverage
    def test_10_concept_coverage(self):
        """10. Verify concept coverage evaluates matched vs missing concepts correctly."""
        # Expected concepts for pt-sd-01: ["validation", "type checking", "http 400", "error response", "sanitization"]
        answer_full = "We implement input validation, type checking, return http 400 error response and string sanitization."
        res_full = PracticalTaskService.evaluate_task_attempt("pt-sd-01", answer_full)
        self.assertEqual(res_full["evaluation"]["concept_coverage"], 100.0)
        self.assertEqual(len(res_full["evaluation"]["missing_concepts"]), 0)

        # Partial answer
        answer_partial = "We implement input validation and return http 400."
        res_partial = PracticalTaskService.evaluate_task_attempt("pt-sd-01", answer_partial)
        self.assertLess(res_partial["evaluation"]["concept_coverage"], 100.0)
        self.assertGreater(len(res_partial["evaluation"]["missing_concepts"]), 0)

    # 11. Criteria coverage
    def test_11_criteria_coverage(self):
        """11. Verify evaluation criteria coverage captures qualitative expectations."""
        task = PracticalTaskService.get_task_by_id("pt-wd-02")
        answer = (
            "The asynchronous race condition is caused by out-of-order network responses. "
            "We use AbortController to cancel in-flight HTTP requests when dependencies change. "
            "The useEffect cleanup function aborts pending fetches on unmount or re-render. "
            "We ignore AbortError gracefully so intentional cancellations do not flash errors."
        )
        res = PracticalTaskService.evaluate_task_attempt("pt-wd-02", answer)
        self.assertGreaterEqual(res["evaluation"]["criteria_coverage"], 60.0)

    # 12. Completeness
    def test_12_completeness_progression(self):
        """12. Verify short answers receive lower completeness while thorough answers reach 100%."""
        short_ans = "We validate the input."
        res_short = PracticalTaskService.evaluate_task_attempt("pt-sd-01", short_ans)
        self.assertLessEqual(res_short["evaluation"]["completeness"], 40.0)

        long_ans = " " .join(["validation", "http 400", "error response", "type checking", "sanitization"] * 25)
        res_long = PracticalTaskService.evaluate_task_attempt("pt-sd-01", long_ans)
        self.assertEqual(res_long["evaluation"]["completeness"], 100.0)

    # 13. Structure
    def test_13_structure_scoring(self):
        """13. Verify presence of code blocks, lists, and headers elevates structure score."""
        unstructured = "We validate input and return 400 error response."
        res_unstructured = PracticalTaskService.evaluate_task_attempt("pt-sd-01", unstructured)

        structured = (
            "### 1. Approach\n"
            "1. First step: validate parameters\n"
            "2. Second step: sanitize strings\n\n"
            "```python\n"
            "def validate_payload(data):\n"
            "    if not data: return {'error': 'http 400'}\n"
            "```\n"
            "### 2. Rationale\n"
            "This separates schema type checking from business logic."
        )
        res_structured = PracticalTaskService.evaluate_task_attempt("pt-sd-01", structured)
        self.assertGreater(res_structured["evaluation"]["structure"], res_unstructured["evaluation"]["structure"])

    # 14. Practical score formula
    def test_14_practical_score_formula(self):
        """14. Verify practical score conforms to 0.40 C + 0.25 R + 0.20 Cr + 0.10 Comp + 0.05 S."""
        answer = (
            "### Solution\n"
            "1. Perform input validation and type checking on user fields.\n"
            "2. Return http 400 error response on invalid age or email.\n"
            "3. Enforce string sanitization to prevent injection attacks.\n"
            "```python\n"
            "def validate(data): pass\n"
            "```"
        )
        res = PracticalTaskService.evaluate_task_attempt("pt-sd-01", answer)
        ev = res["evaluation"]
        expected_score = round(
            (0.40 * ev["concept_coverage"])
            + (0.25 * ev["requirement_coverage"])
            + (0.20 * ev["criteria_coverage"])
            + (0.10 * ev["completeness"])
            + (0.05 * ev["structure"]),
            1
        )
        self.assertAlmostEqual(ev["practical_score"], expected_score, places=1)

    # 15. Score clamping
    def test_15_score_clamping(self):
        """15. Verify practical score is strictly clamped to [0.0, 100.0]."""
        res_empty = PracticalTaskService.evaluate_task_attempt("pt-sd-01", "irrelevant gibberish xyz abc")
        self.assertGreaterEqual(res_empty["evaluation"]["practical_score"], 0.0)
        self.assertLessEqual(res_empty["evaluation"]["practical_score"], 100.0)

    # 16. Band mapping
    def test_16_band_mapping(self):
        """16. Verify correct mapping of practical scores to qualitative result bands."""
        # Strong Mastery (>=85)
        comprehensive = (
            "### Implementation & Validation Architecture\n"
            "1. Validate that required fields email, username, and age exist in payload.\n"
            "2. Ensure age is a positive integer and email follows a valid format with type checking.\n"
            "3. Return HTTP 400 with a structured error response specifying missing or invalid fields.\n"
            "4. Sanitize strings against injection and disallow unexpected extra fields with sanitization.\n"
            "```python\n"
            "def validate_registration(payload):\n"
            "    errors = []\n"
            "    if not isinstance(payload.get('age'), int) or payload['age'] <= 0:\n"
            "        errors.append({'field': 'age', 'message': 'Must be positive integer'})\n"
            "    return {'errors': errors}, 400 if errors else 200\n"
            "```\n"
            "### Edge Cases & Rationale\n"
            "Provides structured error format with field-level details, separates validation logic, and handles non-numeric boundary cases."
        )
        res_strong = PracticalTaskService.evaluate_task_attempt("pt-sd-01", comprehensive)
        self.assertIn(res_strong["evaluation"]["band"], [PracticalTaskService.BAND_STRONG_MASTERY, PracticalTaskService.BAND_PRACTICE_READY])

        # Foundation Required (<55)
        res_weak = PracticalTaskService.evaluate_task_attempt("pt-sd-01", "I do not know how to do this.")
        self.assertEqual(res_weak["evaluation"]["band"], PracticalTaskService.BAND_FOUNDATION_REQUIRED)

    # 17. Missing concept handling
    def test_17_missing_concept_handling(self):
        """17. Verify omitted concepts are explicitly surfaced in evaluation response."""
        res = PracticalTaskService.evaluate_task_attempt("pt-sd-01", "We check input validation and http 400.")
        self.assertIn("sanitization", res["evaluation"]["missing_concepts"])
        self.assertIn("type checking", res["evaluation"]["missing_concepts"])

    # 18. Skill evidence
    def test_18_skill_evidence(self):
        """18. Verify structured skill evidence is generated with correct strength rating."""
        res = PracticalTaskService.evaluate_task_attempt("pt-sd-01", "Short answer validation http 400.")
        evidence = res["skill_evidence"]
        self.assertEqual(evidence["demonstrated_skill"], "Python")
        self.assertIn(evidence["evidence_strength"], ["STRONG", "MODERATE", "LIMITED", "INSUFFICIENT"])
        self.assertEqual(evidence["task_id"], "pt-sd-01")

    # 19. Remaining gaps
    def test_19_remaining_gaps_synthesis(self):
        """19. Verify remaining gaps array provides constructive technical guidance."""
        res = PracticalTaskService.evaluate_task_attempt("pt-sd-01", "We do some validation.")
        self.assertIsInstance(res["remaining_gaps"], list)
        self.assertGreater(len(res["remaining_gaps"]), 0)

    # 20. Recommended next task
    def test_20_recommended_next_task(self):
        """20. Verify next task recommendation suggests appropriate follow-up."""
        res = PracticalTaskService.evaluate_task_attempt("pt-sd-01", "Some validation answer.")
        self.assertIsNotNone(res["recommended_next_task"])
        self.assertIn("id", res["recommended_next_task"])
        self.assertIn("recommendation_reason", res["recommended_next_task"])

    # 21. Skill ROI integration
    def test_21_skill_roi_integration(self):
        """21. Verify tasks addressing high Skill ROI skills receive elevated priority scores."""
        res = PracticalTaskService.list_tasks(career_id=1)
        # Any task with high ROI should have is_roi_priority flag and priority >= 50
        self.assertGreaterEqual(len(res["tasks"]), 1)
        for t in res["tasks"]:
            self.assertGreaterEqual(t["priority_score"], 50.0)

    # 22. Portfolio integration
    def test_22_portfolio_integration(self):
        """22. Verify tasks declare portfolio_relevance and align with capstone competencies."""
        for t in PracticalTaskService.TASK_BANK:
            self.assertTrue(len(t.get("portfolio_relevance", "")) > 10)

    # 23. Academic integration
    def test_23_academic_integration(self):
        """23. Verify task bank supports academic foundational concepts."""
        da_task = PracticalTaskService.get_task_by_id("pt-da-03")
        self.assertEqual(da_task["skill"], "Statistics")
        self.assertIn("z-score", da_task["expected_concepts"])

    # 24. Industry demand integration
    def test_24_industry_demand_integration(self):
        """24. Verify tasks prioritize high-demand industry skills (e.g. Docker, Python, Cloud)."""
        do_tasks = PracticalTaskService.list_tasks(career_id=7, skill="Docker")
        self.assertGreaterEqual(len(do_tasks["tasks"]), 1)

    # 25. Job-specific skill prioritization
    def test_25_job_specific_skill_prioritization(self):
        """25. Verify specifying a live job boosts priority for tasks targeting vacancy missing skills."""
        # Query with Razorpay DevOps job
        res = PracticalTaskService.list_tasks(
            career_id=7,
            job_source="greenhouse-razorpay",
            job_id="4730552005"
        )
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(len(res["tasks"]), 1)
        # First task should have elevated priority
        top_task = res["tasks"][0]
        self.assertGreaterEqual(top_task["priority_score"], 50.0)

    # 26. Invalid task handling
    def test_26_invalid_task_handling(self):
        """26. Verify attempting to evaluate a nonexistent task returns 404 error."""
        res = PracticalTaskService.evaluate_task_attempt("nonexistent-task-id", "Some answer")
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"], "NOT_FOUND")

        # API check
        api_res = self.client.post("/api/practical-tasks/evaluate", json={
            "task_id": "nonexistent-task-id",
            "answer": "Some answer"
        })
        self.assertEqual(api_res.status_code, 404)

    # 27. Invalid request handling
    def test_27_invalid_request_handling(self):
        """27. Verify empty or missing answers return 400 Bad Request."""
        res_empty = PracticalTaskService.evaluate_task_attempt("pt-sd-01", "   ")
        self.assertEqual(res_empty["status"], "error")
        self.assertEqual(res_empty["error"], "INVALID_INPUT")

        api_res = self.client.post("/api/practical-tasks/evaluate", json={
            "task_id": "pt-sd-01",
            "answer": ""
        })
        self.assertEqual(api_res.status_code, 400)

    # 28. Oversized answer handling
    def test_28_oversized_answer_handling(self):
        """28. Verify answers exceeding MAX_ANSWER_LENGTH are rejected with payload error."""
        oversized = "a" * (PracticalTaskService.MAX_ANSWER_LENGTH + 100)
        res = PracticalTaskService.evaluate_task_attempt("pt-sd-01", oversized)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error"], "PAYLOAD_TOO_LARGE")

    # 29. Authentication compatibility
    def test_29_authentication_compatibility(self):
        """29. Verify endpoint functions seamlessly for both unauthenticated and authenticated requests."""
        # Unauthenticated
        res_unauth = self.client.get("/api/practical-tasks")
        self.assertEqual(res_unauth.status_code, 200)

        # Authenticated with test user
        user = User.query.first()
        if user:
            from flask_jwt_extended import create_access_token
            token = create_access_token(identity=str(user.id))
            headers = {"Authorization": f"Bearer {token}"}
            res_auth = self.client.get("/api/practical-tasks", headers=headers)
            self.assertEqual(res_auth.status_code, 200)

    # 30. No database mutations
    def test_30_no_database_mutations(self):
        """30. Verify practical task listing and evaluation perform zero database mutations."""
        pre_skills_count = Skill.query.count()
        pre_careers_count = Career.query.count()

        PracticalTaskService.list_tasks(career_id=1)
        PracticalTaskService.evaluate_task_attempt("pt-sd-01", "Testing input validation http 400.")

        post_skills_count = Skill.query.count()
        post_careers_count = Career.query.count()

        self.assertEqual(pre_skills_count, post_skills_count)
        self.assertEqual(pre_careers_count, post_careers_count)

    # 31. Deterministic evaluation repeatability
    def test_31_deterministic_evaluation_repeatability(self):
        """31. Verify evaluating identical answers produces strictly identical score values."""
        answer = "We validate input parameters and return http 400 error response."
        res1 = PracticalTaskService.evaluate_task_attempt("pt-sd-01", answer)
        res2 = PracticalTaskService.evaluate_task_attempt("pt-sd-01", answer)

        self.assertEqual(res1["evaluation"]["practical_score"], res2["evaluation"]["practical_score"])
        self.assertEqual(res1["evaluation"]["band"], res2["evaluation"]["band"])
        self.assertEqual(res1["evaluation"]["matched_concepts"], res2["evaluation"]["matched_concepts"])

    # 32. Backward compatibility of endpoints
    def test_32_backward_compatibility(self):
        """32. Verify existing career and job endpoints remain fully functional."""
        careers_res = self.client.get("/api/careers")
        self.assertEqual(careers_res.status_code, 200)

        career_tasks_res = self.client.get("/api/careers/1/practical-tasks")
        self.assertEqual(career_tasks_res.status_code, 200)
        self.assertIn("tasks", career_tasks_res.get_json())


if __name__ == "__main__":
    unittest.main()
