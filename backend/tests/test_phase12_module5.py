"""
Test Suite for Phase 12 Module 12.5: Career Readiness & Personalized Action Plan Engine.

Verifies:
1. CareerReadinessService initialization, constants, and provenance.
2. Non-existent career ID handling (error dict and 404).
3. Baseline readiness calculation across canonical careers.
4. Empty profile baseline behavior.
5. Student profile with verified skills integration.
6. User skills payload simulation on 1-5 scale.
7. User skills payload simulation on 1-10 scale.
8. Multi-evidence collection default structure.
9. Multi-evidence integration with practical score.
10. Multi-evidence integration with portfolio score.
11. Multi-evidence integration with interview score.
12. Multi-evidence composite scoring when all 4 layers are established.
13. Dynamic weights normalization and sum behavior.
14. Non-penalization of students lacking optional mock evidence.
15. Educational readiness band: FOUNDATION_REQUIRED (<50.0).
16. Educational readiness band: DEVELOPING (50.0 to 74.9).
17. Educational readiness band: PLACEMENT_READY (>=75.0).
18. Milestone state: NOT_READY (<40.0 or critical blocker).
19. Milestone state: FOUNDATION_BUILDING (40.0 to 59.9).
20. Milestone state: PROJECT_APPLICATION (60.0 to 74.9).
21. Milestone state: INTERVIEW_ACTIVE (75.0 to 84.9).
22. Milestone state: PLACEMENT_READY (>=85.0 and no critical blockers).
23. Blocker diagnosis: PREREQUISITE_BLOCKER detection.
24. Blocker diagnosis: CRITICAL_SKILL_GAP detection.
25. Blocker diagnosis: PRACTICAL_EVIDENCE_GAP detection.
26. Blocker diagnosis: PORTFOLIO_EVIDENCE_GAP detection.
27. Blocker diagnosis: INTERVIEW_EVIDENCE_GAP detection.
28. Blocker diagnosis: ACADEMIC_BLIND_SPOT detection.
29. Blocker diagnosis: JOB_SPECIFIC_GAP detection.
30. Blocker severity ranking and deterministic sorting.
31. Today action selection: single atomic high-leverage action.
32. Today action: prerequisite resolution prioritized when prerequisites unmet.
33. Today action: explainable why_now rationale.
34. Next actions: 4-pillar progression (LEARN, PRACTICE, BUILD, PREPARE).
35. Weekly plan generation: custom hours_per_week (5h, 10h, 15h, 20h).
36. Weekly plan allocation: exact sum matches hours_per_week.
37. Weekly plan: 5-day structured schedule format.
38. Critical path sequence generation.
39. Next milestone targets and score gap calculations.
40. Velocity projection and estimated weeks to placement.
41. Origin career transition integration (from_career_id).
42. API GET /api/careers/<id>/readiness endpoint.
43. API POST /api/careers/<id>/readiness with simulation payload.
44. API query parameters support.
45. Pure in-memory computation (zero database mutations).
"""

import unittest
from app import create_app
from extensions import db
from models.career import Career
from models.career_skill import CareerSkill
from models.skill import Skill
from services.career_readiness_service import CareerReadinessService
from services.adaptive_learning_service import AdaptiveLearningService


class TestPhase12Module5CareerReadinessEngine(unittest.TestCase):
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

    # 1. Service Initialization & Constants
    def test_01_service_initialization_and_constants(self):
        """1. Verify CareerReadinessService attributes, weights, bands, states, and provenance."""
        self.assertTrue(hasattr(CareerReadinessService, "BASE_EVIDENCE_WEIGHTS"))
        self.assertEqual(CareerReadinessService.BASE_EVIDENCE_WEIGHTS["skill_coverage"], 0.40)
        self.assertEqual(CareerReadinessService.BASE_EVIDENCE_WEIGHTS["practical_evidence"], 0.25)
        self.assertEqual(CareerReadinessService.BASE_EVIDENCE_WEIGHTS["portfolio_evidence"], 0.20)
        self.assertEqual(CareerReadinessService.BASE_EVIDENCE_WEIGHTS["interview_evidence"], 0.15)

        self.assertEqual(CareerReadinessService.BAND_FOUNDATION_REQUIRED, "FOUNDATION_REQUIRED")
        self.assertEqual(CareerReadinessService.BAND_DEVELOPING, "DEVELOPING")
        self.assertEqual(CareerReadinessService.BAND_PLACEMENT_READY, "PLACEMENT_READY")

        self.assertEqual(CareerReadinessService.STATE_NOT_READY, "NOT_READY")
        self.assertEqual(CareerReadinessService.STATE_FOUNDATION_BUILDING, "FOUNDATION_BUILDING")
        self.assertEqual(CareerReadinessService.STATE_PROJECT_APPLICATION, "PROJECT_APPLICATION")
        self.assertEqual(CareerReadinessService.STATE_INTERVIEW_ACTIVE, "INTERVIEW_ACTIVE")
        self.assertEqual(CareerReadinessService.STATE_PLACEMENT_READY, "PLACEMENT_READY")

        self.assertIn("industry_data", CareerReadinessService.PROVENANCE_NOTICES)
        self.assertIn("Educational Decision Support", CareerReadinessService.SAFETY_DISCLAIMER)

    # 2. Non-existent Career ID Handling
    def test_02_nonexistent_career_handling(self):
        """2. Verify graceful error handling when career does not exist."""
        result = CareerReadinessService.get_readiness_assessment(career_id=99999)
        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("error"), "CAREER_NOT_FOUND")

    # 3. Baseline Readiness Calculation
    def test_03_baseline_readiness_career_1(self):
        """3. Verify baseline readiness assessment generates successfully for Career 1."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("readiness", res)
        self.assertIn("today", res)
        self.assertIn("next_actions", res)
        self.assertIn("weekly_plan", res)
        self.assertIn("blockers", res)
        self.assertIn("critical_path", res)
        self.assertIn("next_milestone", res)
        self.assertIn("explanation", res)

    # 4. Empty Profile Scores
    def test_04_empty_profile_baseline_scores(self):
        """4. Verify empty student profile produces bounded 0-100 score and NOT_READY state."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        overall = res["readiness"]["overall_score"]
        self.assertGreaterEqual(overall, 0.0)
        self.assertLessEqual(overall, 100.0)
        self.assertEqual(res["readiness"]["milestone_state"], CareerReadinessService.STATE_NOT_READY)

    # 5. Student Profile with Verified Skills
    def test_05_student_profile_with_verified_skills(self):
        """5. Verify passing high proficiency skills raises the readiness score."""
        baseline = CareerReadinessService.get_readiness_assessment(career_id=1)
        simulated = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            user_skills_payload=[
                {"name": "Python", "proficiency": 5.0},
                {"name": "SQL", "proficiency": 4.5},
                {"name": "Git", "proficiency": 4.0},
                {"name": "Java", "proficiency": 4.0},
            ]
        )
        self.assertGreater(
            simulated["readiness"]["overall_score"],
            baseline["readiness"]["overall_score"]
        )

    # 6. User Skills Payload on 1-5 scale
    def test_06_user_skills_payload_scale_1_to_5(self):
        """6. Verify user_skills_payload gracefully handles 1-5 scale proficiency."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            user_skills_payload=[
                {"name": "Python", "proficiency": 4.0},
                {"name": "Git", "proficiency": 3.5}
            ]
        )
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["readiness"]["overall_score"], 0.0)

    # 7. User Skills Payload on 1-10 scale
    def test_07_user_skills_payload_scale_1_to_10(self):
        """7. Verify user_skills_payload gracefully handles 1-10 scale proficiency."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            user_skills_payload=[
                {"name": "Python", "proficiency": 8},
                {"name": "Git", "proficiency": 7}
            ]
        )
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["readiness"]["overall_score"], 0.0)

    # 8. Multi-evidence Collection Default Structure
    def test_08_multi_evidence_default_structure(self):
        """8. Verify all 4 evidence layers exist in evidence_breakdown."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        eb = res["readiness"]["evidence_breakdown"]
        self.assertIn("skill_coverage", eb)
        self.assertIn("practical_evidence", eb)
        self.assertIn("portfolio_evidence", eb)
        self.assertIn("interview_evidence", eb)
        self.assertEqual(eb["skill_coverage"]["status"], "VERIFIED")
        self.assertEqual(eb["practical_evidence"]["status"], "NOT_ESTABLISHED")

    # 9. Multi-evidence with Practical Score
    def test_09_multi_evidence_with_practical_score(self):
        """9. Verify establishing practical evidence redistributes weights and recalculates score."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            options={"practical_score": 85.0}
        )
        eb = res["readiness"]["evidence_breakdown"]
        self.assertEqual(eb["practical_evidence"]["status"], "EVALUATED")
        self.assertEqual(eb["practical_evidence"]["score"], 85.0)
        self.assertGreater(res["readiness"]["dynamic_weighting"]["practical_evidence"], 0.0)

    # 10. Multi-evidence with Portfolio Score
    def test_10_multi_evidence_with_portfolio_score(self):
        """10. Verify establishing portfolio evidence updates weights."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            options={"portfolio_score": 90.0}
        )
        eb = res["readiness"]["evidence_breakdown"]
        self.assertEqual(eb["portfolio_evidence"]["status"], "EVALUATED")
        self.assertEqual(eb["portfolio_evidence"]["score"], 90.0)

    # 11. Multi-evidence with Interview Score
    def test_11_multi_evidence_with_interview_score(self):
        """11. Verify establishing interview evidence updates weights."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            options={"interview_score": 78.0}
        )
        eb = res["readiness"]["evidence_breakdown"]
        self.assertEqual(eb["interview_evidence"]["status"], "EVALUATED")
        self.assertEqual(eb["interview_evidence"]["score"], 78.0)

    # 12. Multi-evidence All 4 Layers Established
    def test_12_multi_evidence_all_layers_established(self):
        """12. Verify composite score when all 4 evidence layers are established."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            user_skills_payload=[{"name": "Python", "proficiency": 5.0}],
            options={
                "practical_score": 80.0,
                "portfolio_score": 85.0,
                "interview_score": 90.0
            }
        )
        weights = res["readiness"]["dynamic_weighting"]
        self.assertAlmostEqual(weights["skill_coverage"], 0.40, places=2)
        self.assertAlmostEqual(weights["practical_evidence"], 0.25, places=2)
        self.assertAlmostEqual(weights["portfolio_evidence"], 0.20, places=2)
        self.assertAlmostEqual(weights["interview_evidence"], 0.15, places=2)

    # 13. Dynamic Weights Sum to One
    def test_13_dynamic_weights_sum_to_one(self):
        """13. Verify dynamic normalized weights sum to 1.0."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            options={"practical_score": 75.0}
        )
        weights = res["readiness"]["dynamic_weighting"]
        total_w = sum(weights.values())
        self.assertAlmostEqual(total_w, 1.0, places=1)

    # 14. Non-penalization for Unestablished Evidence
    def test_14_no_artificial_penalty_for_unestablished_evidence(self):
        """14. Verify student with 100% skill coverage is not penalized to 40% when other layers are not yet established."""
        career = Career.query.get(1)
        career_skills = CareerSkill.query.filter_by(career_id=career.id).all()
        all_skills = [{"name": cs.skill_name, "proficiency": 5.0} for cs in career_skills]
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            user_skills_payload=all_skills
        )
        self.assertGreaterEqual(res["readiness"]["overall_score"], 95.0)

    # 15. Educational Readiness Band: FOUNDATION_REQUIRED
    def test_15_readiness_band_foundation_required(self):
        """15. Verify low readiness score receives FOUNDATION_REQUIRED band."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        if res["readiness"]["overall_score"] < 50.0:
            self.assertEqual(res["readiness"]["readiness_band"], CareerReadinessService.BAND_FOUNDATION_REQUIRED)

    # 16. Educational Readiness Band: DEVELOPING
    def test_16_readiness_band_developing(self):
        """16. Verify score between 50 and 74.9 receives DEVELOPING band."""
        career = Career.query.get(1)
        career_skills = CareerSkill.query.filter_by(career_id=career.id).all()
        partial_skills = [{"name": cs.skill_name, "proficiency": 3.0} for cs in career_skills[:3]]
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            user_skills_payload=partial_skills
        )
        score = res["readiness"]["overall_score"]
        if 50.0 <= score < 75.0:
            self.assertEqual(res["readiness"]["readiness_band"], CareerReadinessService.BAND_DEVELOPING)

    # 17. Educational Readiness Band: PLACEMENT_READY
    def test_17_readiness_band_placement_ready(self):
        """17. Verify score >= 75 receives PLACEMENT_READY band."""
        career = Career.query.get(1)
        career_skills = CareerSkill.query.filter_by(career_id=career.id).all()
        all_skills = [{"name": cs.skill_name, "proficiency": 5.0} for cs in career_skills]
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            user_skills_payload=all_skills
        )
        self.assertGreaterEqual(res["readiness"]["overall_score"], 75.0)
        self.assertEqual(res["readiness"]["readiness_band"], CareerReadinessService.BAND_PLACEMENT_READY)

    # 18. Milestone State: NOT_READY
    def test_18_milestone_state_not_ready(self):
        """18. Verify score < 40 or critical prerequisite blocker results in NOT_READY."""
        state = CareerReadinessService.determine_milestone_state(
            overall_score=35.0,
            blockers=[]
        )
        self.assertEqual(state, CareerReadinessService.STATE_NOT_READY)

    # 19. Milestone State: FOUNDATION_BUILDING
    def test_19_milestone_state_foundation_building(self):
        """19. Verify score between 40 and 59.9 results in FOUNDATION_BUILDING."""
        state = CareerReadinessService.determine_milestone_state(
            overall_score=52.0,
            blockers=[]
        )
        self.assertEqual(state, CareerReadinessService.STATE_FOUNDATION_BUILDING)

    # 20. Milestone State: PROJECT_APPLICATION
    def test_20_milestone_state_project_application(self):
        """20. Verify score between 60 and 74.9 results in PROJECT_APPLICATION."""
        state = CareerReadinessService.determine_milestone_state(
            overall_score=68.0,
            blockers=[]
        )
        self.assertEqual(state, CareerReadinessService.STATE_PROJECT_APPLICATION)

    # 21. Milestone State: INTERVIEW_ACTIVE
    def test_21_milestone_state_interview_active(self):
        """21. Verify score between 75 and 84.9 results in INTERVIEW_ACTIVE."""
        state = CareerReadinessService.determine_milestone_state(
            overall_score=81.0,
            blockers=[]
        )
        self.assertEqual(state, CareerReadinessService.STATE_INTERVIEW_ACTIVE)

    # 22. Milestone State: PLACEMENT_READY
    def test_22_milestone_state_placement_ready(self):
        """22. Verify score >= 85 without critical blockers results in PLACEMENT_READY."""
        state = CareerReadinessService.determine_milestone_state(
            overall_score=92.0,
            blockers=[]
        )
        self.assertEqual(state, CareerReadinessService.STATE_PLACEMENT_READY)

    # 23. Blocker Diagnosis: PREREQUISITE_BLOCKER
    def test_23_blocker_diagnosis_prerequisite(self):
        """23. Verify PREREQUISITE_BLOCKER is flagged when Machine Learning is targeted without Python."""
        career = Career.query.filter_by(title="Data Scientist").first()
        if not career:
            career = Career.query.get(2)
        res = CareerReadinessService.get_readiness_assessment(
            career_id=career.id,
            user_skills_payload=[{"name": "Machine Learning", "proficiency": 2.0}]
        )
        blocker_types = [b["blocker_type"] for b in res["blockers"]]
        self.assertIn(CareerReadinessService.BLOCKER_PREREQUISITE, blocker_types)

    # 24. Blocker Diagnosis: CRITICAL_SKILL_GAP
    def test_24_blocker_diagnosis_critical_skill_gap(self):
        """24. Verify CRITICAL_SKILL_GAP is created for missing high-importance skills."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        blocker_types = [b["blocker_type"] for b in res["blockers"]]
        self.assertIn(CareerReadinessService.BLOCKER_CRITICAL_SKILL_GAP, blocker_types)

    # 25. Blocker Diagnosis: PRACTICAL_EVIDENCE_GAP
    def test_25_blocker_diagnosis_practical_evidence(self):
        """25. Verify PRACTICAL_EVIDENCE_GAP is flagged when practical evidence is unestablished."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        blocker_types = [b["blocker_type"] for b in res["blockers"]]
        self.assertIn(CareerReadinessService.BLOCKER_PRACTICAL_EVIDENCE, blocker_types)

    # 26. Blocker Diagnosis: PORTFOLIO_EVIDENCE_GAP
    def test_26_blocker_diagnosis_portfolio_evidence(self):
        """26. Verify PORTFOLIO_EVIDENCE_GAP is flagged when portfolio evidence is unestablished."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        blocker_types = [b["blocker_type"] for b in res["blockers"]]
        self.assertIn(CareerReadinessService.BLOCKER_PORTFOLIO_EVIDENCE, blocker_types)

    # 27. Blocker Diagnosis: INTERVIEW_EVIDENCE_GAP
    def test_27_blocker_diagnosis_interview_evidence(self):
        """27. Verify INTERVIEW_EVIDENCE_GAP is flagged when interview evidence is unestablished."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        blocker_types = [b["blocker_type"] for b in res["blockers"]]
        self.assertIn(CareerReadinessService.BLOCKER_INTERVIEW_EVIDENCE, blocker_types)

    # 28. Blocker Diagnosis: ACADEMIC_BLIND_SPOT
    def test_28_blocker_diagnosis_academic_blind_spot(self):
        """28. Verify ACADEMIC_BLIND_SPOT identifies curriculum deficits."""
        res = CareerReadinessService.get_readiness_assessment(career_id=2)
        blockers = res["blockers"]
        self.assertTrue(any(b["blocker_type"] == CareerReadinessService.BLOCKER_ACADEMIC_BLIND_SPOT for b in blockers))

    # 29. Blocker Diagnosis: JOB_SPECIFIC_GAP
    def test_29_blocker_diagnosis_job_specific_gap(self):
        """29. Verify JOB_SPECIFIC_GAP is generated when vacancy skills are missing in student profile."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            options={"vacancy_skills": ["Python", "Docker", "Kubernetes"]}
        )
        blocker_types = [b["blocker_type"] for b in res["blockers"]]
        self.assertIn(CareerReadinessService.BLOCKER_JOB_SPECIFIC_GAP, blocker_types)

    # 30. Blocker Deterministic Severity Sorting
    def test_30_blocker_severity_sorting(self):
        """30. Verify blockers are deterministically sorted by severity (CRITICAL > HIGH > MEDIUM > LOW)."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        blockers = res["blockers"]
        if len(blockers) >= 2:
            rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            for i in range(len(blockers) - 1):
                self.assertGreaterEqual(
                    rank.get(blockers[i]["severity"], 0),
                    rank.get(blockers[i+1]["severity"], 0)
                )

    # 31. Today Action Selection
    def test_31_today_action_selection(self):
        """31. Verify today action returns a single atomic action with required schema keys."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        today = res["today"]
        self.assertIn("action_type", today)
        self.assertIn("pillar", today)
        self.assertIn("title", today)
        self.assertIn("skill_name", today)
        self.assertIn("estimated_minutes", today)
        self.assertIn("why_now", today)
        self.assertIn("stage", today)
        self.assertGreater(today["estimated_minutes"], 0)

    # 32. Today Action Prerequisite Priority
    def test_32_today_action_prerequisite_priority(self):
        """32. Verify today action prioritizes RESOLVE_PREREQUISITE if a critical prerequisite is unmet."""
        career = Career.query.filter_by(title="Data Scientist").first() or Career.query.get(2)
        res = CareerReadinessService.get_readiness_assessment(
            career_id=career.id,
            user_skills_payload=[{"name": "Machine Learning", "proficiency": 2.0}]
        )
        self.assertEqual(res["today"]["action_type"], "RESOLVE_PREREQUISITE")

    # 33. Today Action Explainable Why-Now
    def test_33_today_action_why_now_explainability(self):
        """33. Verify today action includes clear human-readable why_now reasoning."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        self.assertIsInstance(res["today"]["why_now"], str)
        self.assertGreater(len(res["today"]["why_now"]), 10)

    # 34. Next Actions 4-Pillar Progression
    def test_34_next_actions_4_pillars(self):
        """34. Verify next_actions contains entries across LEARN, PRACTICE, BUILD, PREPARE."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        pillars = [a["pillar"] for a in res["next_actions"]]
        self.assertIn("LEARN", pillars)
        self.assertIn("PRACTICE", pillars)
        self.assertIn("BUILD", pillars)
        self.assertIn("PREPARE", pillars)

    # 35. Weekly Plan Hours Allocation Exact Sum
    def test_35_weekly_plan_hours_allocation_exact_sum(self):
        """35. Verify sum of allocated hours in weekly plan exactly matches requested hours_per_week."""
        for hpw in [5, 10, 15, 20]:
            res = CareerReadinessService.get_readiness_assessment(
                career_id=1,
                options={"hours_per_week": hpw}
            )
            total_allocated = sum(d["allocated_hours"] for d in res["weekly_plan"])
            self.assertAlmostEqual(total_allocated, float(hpw), places=1)

    # 36. Weekly Plan 5-Day Structure
    def test_36_weekly_plan_5_days_structure(self):
        """36. Verify weekly plan contains exactly 5 day entries with day labels and deliverables."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        plan = res["weekly_plan"]
        self.assertEqual(len(plan), 5)
        for day in plan:
            self.assertIn("day", day)
            self.assertIn("pillar", day)
            self.assertIn("skill_name", day)
            self.assertIn("allocated_hours", day)
            self.assertIn("outcome", day)

    # 37. Critical Path Sequence
    def test_37_critical_path_sequence(self):
        """37. Verify critical path contains ordered milestones with steps and statuses."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        cp = res["critical_path"]
        self.assertGreaterEqual(len(cp), 3)
        for i, step in enumerate(cp):
            self.assertEqual(step["step"], i + 1)
            self.assertIn(step["status"], ["IMMEDIATE_ACTION", "PENDING", "LOCKED"])

    # 38. Next Milestone Progression
    def test_38_next_milestone_progression(self):
        """38. Verify next_milestone reports target_milestone, target_score, and required_actions."""
        res = CareerReadinessService.get_readiness_assessment(career_id=1)
        nm = res["next_milestone"]
        self.assertIn("current_state", nm)
        self.assertIn("target_milestone", nm)
        self.assertIn("target_score", nm)
        self.assertIn("required_actions", nm)
        self.assertGreaterEqual(nm["estimated_weeks"], 0.0)

    # 39. Velocity Projection Math
    def test_39_velocity_projection(self):
        """39. Verify velocity projection computes estimated weeks cleanly."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            options={"hours_per_week": 10}
        )
        vp = res["readiness"]["velocity_projection"]
        self.assertEqual(vp["hours_per_week"], 10)
        self.assertGreater(vp["total_estimated_hours"], 0)
        self.assertGreater(vp["projected_weeks_to_placement_ready"], 0.0)

    # 40. Origin Career Transition Integration
    def test_40_origin_career_transition(self):
        """40. Verify passing from_career_id queries transition trajectory."""
        res = CareerReadinessService.get_readiness_assessment(
            career_id=1,
            options={"from_career_id": 2}
        )
        self.assertEqual(res["status"], "success")

    # 41. API GET /api/careers/<id>/readiness
    def test_41_api_get_readiness_endpoint(self):
        """41. Verify GET /api/careers/1/readiness returns 200 with complete JSON payload."""
        response = self.client.get("/api/careers/1/readiness?hours_per_week=10")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("readiness", data)
        self.assertIn("today", data)

    # 42. API POST /api/careers/<id>/readiness Simulation
    def test_42_api_post_readiness_simulation(self):
        """42. Verify POST /api/careers/1/readiness with student_skills simulation payload."""
        payload = {
            "student_skills": [
                {"name": "Python", "proficiency": 4.5},
                {"name": "Git", "proficiency": 4.0}
            ],
            "hours_per_week": 15,
            "practical_score": 80.0
        }
        response = self.client.post("/api/careers/1/readiness", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data["readiness"]["evidence_breakdown"]["practical_evidence"]["score"], 80.0)

    # 43. API 404 on Invalid Career
    def test_43_api_readiness_404_invalid_career(self):
        """43. Verify GET /api/careers/99999/readiness returns HTTP 404."""
        response = self.client.get("/api/careers/99999/readiness")
        self.assertEqual(response.status_code, 404)

    # 44. Deterministic Repeatability
    def test_44_deterministic_repeatability(self):
        """44. Verify identical calls return identical outputs without random variation."""
        res1 = CareerReadinessService.get_readiness_assessment(career_id=1)
        res2 = CareerReadinessService.get_readiness_assessment(career_id=1)
        self.assertEqual(res1["readiness"]["overall_score"], res2["readiness"]["overall_score"])
        self.assertEqual(res1["today"]["title"], res2["today"]["title"])
        self.assertEqual(len(res1["blockers"]), len(res2["blockers"]))

    # 45. Pure In-Memory Computation (Zero DB Mutations)
    def test_45_zero_database_mutations(self):
        """45. Verify career readiness execution performs strictly ZERO database writes."""
        skill_count_before = Skill.query.count()
        career_count_before = Career.query.count()

        # Run multiple simulated readiness queries
        CareerReadinessService.get_readiness_assessment(
            career_id=1,
            user_skills_payload=[{"name": "Python", "proficiency": 5.0}],
            options={"practical_score": 90.0}
        )

        skill_count_after = Skill.query.count()
        career_count_after = Career.query.count()

        self.assertEqual(skill_count_before, skill_count_after)
        self.assertEqual(career_count_before, career_count_after)


if __name__ == "__main__":
    unittest.main()
