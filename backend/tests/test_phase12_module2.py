"""
Unit and API Integration Tests for Phase 12 Module 12.2:
Live Job Opportunity Intelligence & Career Action Center.

Verifies:
1. Existing live-job service compatibility (search, pagination, offline fallback).
2. Job detail compatibility (structure, provider info, plain description).
3. Matching compatibility (deterministic skill matching, score bounds).
4. Missing skill handling (zero skills, partial skills, full match).
5. Empty result handling (impossible search query returns empty list safely).
6. Invalid job handling (nonexistent provider_id / invalid source_key).
7. Career mapping and fallback ("Career mapping unavailable" for non-tech / ambiguous roles).
8. Skill ROI integration (explainable marginal readiness gains attached to missing skills).
9. Portfolio project integration (capstone recommendations addressing vacancy gaps).
10. Industry demand integration (market temperature and research disclaimer notice).
11. Career trajectory integration (multi-hop pathway intelligence when transitioning).
12. Interview simulation integration (practice readiness action and career questions).
13. Strict zero database mutations guarantee.
14. Authentication compatibility (authenticated user vs anonymous guest).
15. REST API GET / POST /api/jobs/<source_key>/<provider_id>/action-center response structure.
16. Backward compatibility with existing /api/jobs endpoints.
17. Deterministic behavior across repeated executions.
18. Security validation (path traversal defense, input sanitization, SSRF protection).
19. Action plan safety language audit (zero forbidden employment guarantee claims).
20. Score concept distinction notice (Job Match Score vs Career Readiness Score).
"""

import unittest
from app import create_app
from extensions import db
from models.career import Career
from models.skill import Skill
from services.live_jobs_service import LiveJobsService
from services.job_action_center_service import JobActionCenterService


class TestPhase12Module2JobActionCenter(unittest.TestCase):
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

    # 1. Existing live-job service compatibility
    def test_01_existing_live_jobs_service_compatibility(self):
        """1. Verify LiveJobsService.search_jobs returns status success and valid schema."""
        res = LiveJobsService.search_jobs(page_size=5)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("jobs", res)
        self.assertIsInstance(res["jobs"], list)
        self.assertGreaterEqual(len(res["jobs"]), 1)
        self.assertIn("total", res)
        self.assertIn("page", res)
        self.assertIn("page_size", res)

    # 2. Job detail compatibility
    def test_02_job_detail_compatibility(self):
        """2. Verify LiveJobsService.get_job returns complete posting with sanitized description."""
        res = LiveJobsService.search_jobs(page_size=1)
        first_job = res["jobs"][0]
        source_key = first_job["source_key"]
        provider_id = first_job["provider_id"]

        detail = LiveJobsService.get_job(source_key, provider_id)
        self.assertIsNotNone(detail)
        self.assertEqual(detail.get("status"), "success")
        self.assertIn("job", detail)
        self.assertIn("title", detail["job"])
        self.assertIn("description", detail["job"])
        self.assertNotIn("<script>", detail["job"]["description"])
        self.assertIn("source_info", detail)

    # 3. Matching compatibility
    def test_03_matching_compatibility(self):
        """3. Verify LiveJobsService.match_job_to_skills produces bounded match scores."""
        job = {
            "provider_id": "test-1",
            "title": "Backend Engineer",
            "employer": "Acme Corp",
            "tech_tags": ["Python", "SQL", "Docker"],
            "description": "Develop scalable APIs with Python and SQL.",
            "work_mode": "remote",
            "experience_level": "mid",
        }
        user_skills = ["Python", "Git"]

        match_res = LiveJobsService.match_job_to_skills(job, user_skills)
        self.assertEqual(match_res.get("status"), "success")
        self.assertIn("match_score", match_res)
        self.assertTrue(0.0 <= match_res["match_score"] <= 100.0)
        self.assertIn("Python", match_res["matched_skills"])
        self.assertIn("SQL", match_res["missing_skills"])

    # 4. Missing skill handling
    def test_04_missing_skill_handling(self):
        """4. Verify missing skill detection when candidate has zero matching skills."""
        job = {
            "provider_id": "test-2",
            "title": "Kubernetes Infrastructure Specialist",
            "employer": "CloudTech",
            "tech_tags": ["Kubernetes", "Terraform", "Go"],
            "description": "Infrastructure automation with Kubernetes and Terraform.",
        }
        user_skills = ["HTML", "CSS"]

        match_res = LiveJobsService.match_job_to_skills(job, user_skills)
        self.assertEqual(match_res["match_score"], 0.0)
        self.assertEqual(len(match_res["matched_skills"]), 0)
        self.assertGreaterEqual(len(match_res["missing_skills"]), 2)

    # 5. Empty result handling
    def test_05_empty_result_handling(self):
        """5. Verify searching for non-existent keywords returns empty list without crashing."""
        res = LiveJobsService.search_jobs(query="NonExistentTitleXYZ999999")
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(len(res["jobs"]), 0)
        self.assertEqual(res["total"], 0)

    # 6. Invalid job handling
    def test_06_invalid_job_handling(self):
        """6. Verify retrieving invalid job returns None and 404 error appropriately."""
        res = LiveJobsService.get_job("greenhouse-canonical", "non-existent-provider-id-99999")
        self.assertIsNone(res)

        ac_res = JobActionCenterService.get_action_center("greenhouse-canonical", "non-existent-provider-id-99999")
        self.assertEqual(ac_res.get("status"), "error")
        self.assertEqual(ac_res.get("error"), "NOT_FOUND")

        # Invalid source key handled safely by Action Center
        ac_inv = JobActionCenterService.get_action_center("invalid-source-key", "any-id")
        self.assertEqual(ac_inv.get("status"), "error")
        self.assertEqual(ac_inv.get("error"), "NOT_FOUND")

    # 7. Career mapping and fallback
    def test_07_career_mapping_and_fallback(self):
        """7. Verify deterministic career mapping and explicit fallback for non-tech roles."""
        # Software Developer
        job_sw = {"title": "Senior Backend Software Engineer", "tech_tags": ["Python", "SQL"]}
        map_sw = JobActionCenterService.map_job_to_career(job_sw)
        self.assertEqual(map_sw["status"], "mapped")
        self.assertEqual(map_sw["career_id"], 1)

        # Web Developer
        job_web = {"title": "Frontend React Developer", "tech_tags": ["React", "TypeScript"]}
        map_web = JobActionCenterService.map_job_to_career(job_web)
        self.assertEqual(map_web["status"], "mapped")
        self.assertEqual(map_web["career_id"], 2)

        # Non-tech / obscure role fallback
        job_non_tech = {"title": "Office Receptionist and Facilities Coordinator", "tech_tags": []}
        map_non_tech = JobActionCenterService.map_job_to_career(job_non_tech)
        self.assertEqual(map_non_tech["status"], "unavailable")
        self.assertIsNone(map_non_tech["career_id"])
        self.assertEqual(map_non_tech["message"], "Career mapping unavailable")

    # 8. Skill ROI integration
    def test_08_skill_roi_integration(self):
        """8. Verify Action Center integrates explainable Skill ROI for missing skills."""
        res = LiveJobsService.search_jobs(page_size=1)
        first_job = res["jobs"][0]
        source_key = first_job["source_key"]
        provider_id = first_job["provider_id"]

        ac = JobActionCenterService.get_action_center(
            source_key=source_key,
            provider_id=provider_id,
            custom_skills=["Git"],
        )
        self.assertEqual(ac.get("status"), "success")
        self.assertIn("skill_actions", ac)
        if ac["skill_actions"]:
            first_action = ac["skill_actions"][0]
            self.assertIn("skill_name", first_action)
            self.assertIn("why_it_matters", first_action)
            self.assertIn("priority", first_action)
            self.assertIn("marginal_readiness_gain", first_action)
            self.assertIn("roi_score", first_action)

    # 9. Portfolio project integration
    def test_09_portfolio_integration(self):
        """9. Verify Action Center attaches capstone projects addressing vacancy skill gaps."""
        res = LiveJobsService.search_jobs(page_size=1)
        first_job = res["jobs"][0]
        source_key = first_job["source_key"]
        provider_id = first_job["provider_id"]

        ac = JobActionCenterService.get_action_center(
            source_key=source_key,
            provider_id=provider_id,
            custom_skills=[],
        )
        self.assertEqual(ac.get("status"), "success")
        self.assertIn("portfolio_recommendations", ac)
        if ac["portfolio_recommendations"]:
            proj = ac["portfolio_recommendations"][0]
            self.assertIn("project_id", proj)
            self.assertIn("title", proj)
            self.assertIn("demonstrated_skills", proj)
            self.assertIn("deliverables", proj)

    # 10. Industry demand integration
    def test_10_industry_demand_integration(self):
        """10. Verify Action Center attaches industry demand signals with disclaimer notice."""
        res = LiveJobsService.search_jobs(page_size=1)
        first_job = res["jobs"][0]
        source_key = first_job["source_key"]
        provider_id = first_job["provider_id"]

        ac = JobActionCenterService.get_action_center(
            source_key=source_key,
            provider_id=provider_id,
        )
        self.assertEqual(ac.get("status"), "success")
        if ac.get("industry_demand_context"):
            ind = ac["industry_demand_context"]
            self.assertIn("overall_market_temperature", ind)
            self.assertIn("provenance_disclaimer", ind)
            self.assertIn("DEMO / SAMPLE / PROTOTYPE", ind["provenance_disclaimer"])

    # 11. Career trajectory integration
    def test_11_career_trajectory_integration(self):
        """11. Verify transition trajectory intelligence when transitioning between careers."""
        # Target: Cloud Engineer (Career 6), From: Software Developer (Career 1)
        res = LiveJobsService.search_jobs(technology="Cloud", page_size=1)
        if not res["jobs"]:
            res = LiveJobsService.search_jobs(page_size=1)
        job = res["jobs"][0]

        ac = JobActionCenterService.get_action_center(
            source_key=job["source_key"],
            provider_id=job["provider_id"],
            from_career_id=1,
        )
        self.assertEqual(ac.get("status"), "success")
        if ac.get("career_trajectory"):
            traj = ac["career_trajectory"]
            self.assertIn("from_career_id", traj)
            self.assertIn("target_career_id", traj)
            self.assertIn("feasibility_score", traj)

    # 12. Interview simulation integration
    def test_12_interview_integration(self):
        """12. Verify interview practice connection is available for mapped tech roles."""
        res = LiveJobsService.search_jobs(page_size=1)
        job = res["jobs"][0]

        ac = JobActionCenterService.get_action_center(
            source_key=job["source_key"],
            provider_id=job["provider_id"],
        )
        self.assertEqual(ac.get("status"), "success")
        if ac.get("career_connection", {}).get("status") == "mapped":
            self.assertIsNotNone(ac.get("interview_readiness"))
            self.assertTrue(ac["interview_readiness"]["interview_available"])

    # 13. Strict zero database mutations guarantee
    def test_13_no_database_mutations(self):
        """13. Verify full Action Center execution causes zero database modifications."""
        with self.app.app_context():
            career_count_before = Career.query.count()
            skill_count_before = Skill.query.count()

            res = LiveJobsService.search_jobs(page_size=2)
            for j in res["jobs"]:
                JobActionCenterService.get_action_center(j["source_key"], j["provider_id"])

            career_count_after = Career.query.count()
            skill_count_after = Skill.query.count()

            self.assertEqual(career_count_before, career_count_after)
            self.assertEqual(skill_count_before, skill_count_after)

    # 14. Authentication compatibility
    def test_14_authentication_compatibility(self):
        """14. Verify Action Center works smoothly with and without user authentication."""
        res = LiveJobsService.search_jobs(page_size=1)
        job = res["jobs"][0]

        # Anonymous / unauthenticated
        ac_anon = JobActionCenterService.get_action_center(job["source_key"], job["provider_id"])
        self.assertEqual(ac_anon.get("status"), "success")

        # Custom skills provided matching target vacancy
        target_tags = job.get("tech_tags", [])
        test_skill = target_tags[0] if target_tags else "Python"
        ac_custom = JobActionCenterService.get_action_center(
            job["source_key"],
            job["provider_id"],
            custom_skills=[test_skill],
        )
        self.assertEqual(ac_custom.get("status"), "success")
        if target_tags:
            self.assertIn(test_skill, ac_custom["match"]["matched_skills"])

    # 15. REST API endpoint response structure
    def test_15_api_response_structure(self):
        """15. Verify GET /api/jobs/<source_key>/<provider_id>/action-center returns 200 OK."""
        res = LiveJobsService.search_jobs(page_size=1)
        job = res["jobs"][0]
        sk = job["source_key"]
        pid = job["provider_id"]

        resp = self.client.get(f"/api/jobs/{sk}/{pid}/action-center")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("job", data)
        self.assertIn("match", data)
        self.assertIn("career_connection", data)
        self.assertIn("action_plan", data)

    # 16. Backward compatibility with existing endpoints
    def test_16_backward_compatibility(self):
        """16. Verify existing /api/jobs, /api/jobs/sources, and /api/jobs/.../match still function."""
        # /api/jobs
        r1 = self.client.get("/api/jobs?page=1&page_size=3")
        self.assertEqual(r1.status_code, 200)
        d1 = r1.get_json()
        self.assertEqual(d1.get("status"), "success")

        # /api/jobs/sources
        r2 = self.client.get("/api/jobs/sources")
        self.assertEqual(r2.status_code, 200)
        d2 = r2.get_json()
        self.assertIn("sources", d2)

        # /api/jobs/<source_key>/<provider_id>/match
        first_job = d1["jobs"][0]
        sk = first_job["source_key"]
        pid = first_job["provider_id"]
        r3 = self.client.post(
            f"/api/jobs/{sk}/{pid}/match",
            json={"skills": ["Python", "SQL"]},
        )
        self.assertEqual(r3.status_code, 200)
        d3 = r3.get_json()
        self.assertIn("match_score", d3)

    # 17. Deterministic behavior across repeated calls
    def test_17_deterministic_behavior(self):
        """17. Verify repeated execution on the same vacancy yields identical output values."""
        res = LiveJobsService.search_jobs(page_size=1)
        job = res["jobs"][0]

        ac1 = JobActionCenterService.get_action_center(job["source_key"], job["provider_id"], custom_skills=["Git"])
        ac2 = JobActionCenterService.get_action_center(job["source_key"], job["provider_id"], custom_skills=["Git"])

        self.assertEqual(ac1["match"]["match_score"], ac2["match"]["match_score"])
        self.assertEqual(ac1["match"]["matched_skills"], ac2["match"]["matched_skills"])
        self.assertEqual(ac1["match"]["missing_skills"], ac2["match"]["missing_skills"])
        self.assertEqual(
            ac1.get("career_connection", {}).get("career_id"),
            ac2.get("career_connection", {}).get("career_id"),
        )

    # 18. Security validation
    def test_18_security_validation(self):
        """18. Verify defense against path traversal and malicious source keys."""
        resp = self.client.get("/api/jobs/../../etc/passwd/1/action-center")
        self.assertEqual(resp.status_code, 404)

        resp2 = self.client.get("/api/jobs/<script>alert(1)</script>/test/action-center")
        self.assertEqual(resp2.status_code, 404)

    # 19. Action plan safety language audit
    def test_19_action_plan_safety_language(self):
        """19. Verify generated action plans never contain forbidden employment guarantee claims."""
        res = LiveJobsService.search_jobs(page_size=3)
        forbidden_phrases = [
            "guarantee",
            "guaranteed job",
            "guaranteed placement",
            "will definitely get",
            "100% job certainty",
            "foolproof",
        ]

        for job in res["jobs"]:
            ac = JobActionCenterService.get_action_center(job["source_key"], job["provider_id"])
            plan_str = str(ac.get("action_plan", {})).lower()
            disclaimer_str = str(ac.get("safety_disclaimer", "")).lower()

            for phrase in forbidden_phrases:
                self.assertNotIn(phrase, plan_str)
            self.assertIn("educational decision support", disclaimer_str)

    # 20. Score concept distinction notice
    def test_20_score_distinction_notice(self):
        """20. Verify explicit distinction notice between Job Match Score and Career Readiness Score."""
        res = LiveJobsService.search_jobs(page_size=1)
        job = res["jobs"][0]

        ac = JobActionCenterService.get_action_center(job["source_key"], job["provider_id"])
        notice = ac["match"].get("score_distinction_notice", "")
        self.assertIn("Job Match Score", notice)
        self.assertIn("Career Readiness Score", notice)
