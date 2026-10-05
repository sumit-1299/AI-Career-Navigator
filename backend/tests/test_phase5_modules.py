"""
Phase 5 Comprehensive Verification Test Suite for AI Career Navigator.

Tests:
1. Module 5.1 — Interactive Learning Pathway & Progress Tracking:
   - Resource start, update, complete lifecycle
   - Duplicate prevention / idempotency
   - Automated skill proficiency progression upon completion
   - Querying progress by user and canonical skill
2. Module 5.2 — Resume Ingestion (PDF, DOCX, TXT):
   - Multi-format validation and text extraction
   - Invalid file extension and empty file rejection
   - High-confidence auto-match vs review segregation
   - Ingestion and profile application of extracted skills
3. Module 5.3 — Side-by-Side Career Comparison:
   - Common skills identification
   - Exclusive skills (Career A only vs Career B only)
   - Student competencies categorization (Already Has vs Missing)
   - Overlap percentage, acquisition distance, and comparative narrative
4. Module 5.4 — Student Analytics & Career Readiness Velocity:
   - Baseline readiness vs current readiness
   - Readiness improvement and learning velocity (per day, per week, per resource)
   - Skills acquired and improved tracking
   - Progress timeline generation
5. Phase 5 REST API Endpoints:
   - /api/learning-resources/<id>/start, progress, complete
   - /api/learning-resources/progress
   - /api/skills/canonical/<id>/progress
   - /api/skills/extract-resume (file upload & JSON)
   - /api/skills/extract-resume/apply
   - /api/careers/compare (GET and POST)
   - /api/careers/<id>/analytics & /api/careers/analytics
"""

import io
import os
import sys
import unittest
import zipfile
import zlib
from datetime import datetime

# Ensure backend root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from extensions import db
from models.canonical_skill import CanonicalSkill
from models.career import Career
from models.learning_resource import LearningResource
from models.skill import Skill
from models.user import User
from models.user_learning_progress import UserLearningProgress
from services.career_comparison_service import CareerComparisonService
from services.learning_progress_service import LearningProgressService
from services.resume_extraction_service import ResumeExtractionService
from services.student_analytics_service import StudentAnalyticsService


class BasePhase5TestCase(unittest.TestCase):
    """Base setup for Phase 5 tests with isolated test user."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            # Create a dedicated test user
            test_email = "phase5_student@example.com"
            user = User.query.filter_by(email=test_email).first()
            if not user:
                user = User(
                    name="Phase5 Student",
                    email=test_email,
                    password_hash="test_hashed_pw"
                )
                db.session.add(user)
                db.session.commit()
            cls.test_user_id = user.id

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            # Clean up test user records
            UserLearningProgress.query.filter_by(user_id=cls.test_user_id).delete()
            Skill.query.filter_by(user_id=cls.test_user_id).delete()
            user = User.query.get(cls.test_user_id)
            if user:
                db.session.delete(user)
            db.session.commit()

    def setUp(self):
        with self.app.app_context():
            UserLearningProgress.query.filter_by(user_id=self.test_user_id).delete()
            Skill.query.filter_by(user_id=self.test_user_id).delete()
            db.session.commit()


# =====================================================================
# MODULE 5.1 TESTS: LEARNING PROGRESS TRACKING & PROFICIENCY UPDATE
# =====================================================================

class TestModule51LearningProgressTracking(BasePhase5TestCase):
    """Tests for Module 5.1: Learning Pathway and Progress Tracking."""

    def test_start_learning_resource(self):
        """Starting a learning resource initializes progress tracking."""
        with self.app.app_context():
            resource = LearningResource.query.first()
            self.assertIsNotNone(resource, "Requires at least one seeded resource")

            record = LearningProgressService.start_resource(self.test_user_id, resource.id)
            self.assertIsNotNone(record)
            self.assertEqual(record["user_id"], self.test_user_id)
            self.assertEqual(record["learning_resource_id"], resource.id)
            self.assertEqual(record["status"], "In Progress")
            self.assertGreater(record["progress_percentage"], 0.0)
            self.assertIsNotNone(record["started_at"])

    def test_start_resource_idempotency(self):
        """Starting an already started resource returns existing record without duplicate error."""
        with self.app.app_context():
            resource = LearningResource.query.first()
            rec1 = LearningProgressService.start_resource(self.test_user_id, resource.id)
            rec2 = LearningProgressService.start_resource(self.test_user_id, resource.id)

            self.assertEqual(rec1["id"], rec2["id"])
            count = UserLearningProgress.query.filter_by(
                user_id=self.test_user_id,
                learning_resource_id=resource.id
            ).count()
            self.assertEqual(count, 1, "Duplicate progress record was created")

    def test_update_learning_progress(self):
        """Updating progress percentage and notes."""
        with self.app.app_context():
            resource = LearningResource.query.first()
            LearningProgressService.start_resource(self.test_user_id, resource.id)

            updated = LearningProgressService.update_progress(
                self.test_user_id,
                resource.id,
                progress_percentage=65.5,
                notes="Completed module 3"
            )
            self.assertEqual(updated["progress_percentage"], 65.5)
            self.assertEqual(updated["notes"], "Completed module 3")
            self.assertEqual(updated["status"], "In Progress")

    def test_complete_resource_and_proficiency_advancement(self):
        """Completing a resource triggers skill proficiency increase in student profile."""
        with self.app.app_context():
            resource = LearningResource.query.first()
            canonical_skill = resource.canonical_skill
            self.assertIsNotNone(canonical_skill)

            # Pre-condition: user has no skills recorded
            initial_skill = Skill.query.filter_by(
                user_id=self.test_user_id,
                canonical_skill_id=canonical_skill.id
            ).first()
            self.assertIsNone(initial_skill)

            completed = LearningProgressService.complete_resource(
                self.test_user_id,
                resource.id
            )
            self.assertEqual(completed["status"], "Completed")
            self.assertEqual(completed["progress_percentage"], 100.0)
            self.assertIsNotNone(completed["completed_at"])

            # Verify skill was automatically created and boosted
            student_skill = Skill.query.filter_by(
                user_id=self.test_user_id,
                canonical_skill_id=canonical_skill.id
            ).first()
            self.assertIsNotNone(student_skill)
            self.assertGreaterEqual(student_skill.proficiency, 5)

            # Complete again or complete higher difficulty resource: check further progression
            second_res = LearningResource.query.filter(
                LearningResource.canonical_skill_id == canonical_skill.id,
                LearningResource.id != resource.id
            ).first()
            if second_res:
                prev_prof = student_skill.proficiency
                LearningProgressService.complete_resource(self.test_user_id, second_res.id)
                db.session.refresh(student_skill)
                self.assertGreaterEqual(student_skill.proficiency, prev_prof)

    def test_get_user_progress_and_skill_filtering(self):
        """Retrieve student progress records and filter by canonical skill."""
        with self.app.app_context():
            resources = LearningResource.query.limit(2).all()
            for r in resources:
                LearningProgressService.start_resource(self.test_user_id, r.id)

            user_records = LearningProgressService.get_user_progress(self.test_user_id)
            self.assertEqual(len(user_records), 2)

            skill_id = resources[0].canonical_skill_id
            skill_records = LearningProgressService.get_progress_for_skill(self.test_user_id, skill_id)
            self.assertGreaterEqual(len(skill_records), 1)
            for sr in skill_records:
                self.assertEqual(sr["canonical_skill_id"], skill_id)


# =====================================================================
# MODULE 5.2 TESTS: RESUME INGESTION & TEXT EXTRACTION (TXT, DOCX, PDF)
# =====================================================================

class TestModule52ResumeIngestion(BasePhase5TestCase):
    """Tests for Module 5.2: Multi-format resume ingestion and parsing."""

    def test_txt_resume_extraction(self):
        """Validate and extract skills from a plain text resume."""
        with self.app.app_context():
            resume_content = (
                "EXPERIENCE:\n"
                "Software Engineer at Acme Corp.\n"
                "Built microservices with Python, Docker, and PostgreSQL.\n"
                "Managed cloud infrastructure on AWS and deployed with Git."
            ).encode("utf-8")

            text = ResumeExtractionService.validate_and_extract_file("resume.txt", resume_content)
            self.assertIn("Python", text)
            self.assertIn("Docker", text)

            result = ResumeExtractionService.extract_skills_from_text(text)
            self.assertEqual(result["status"], "success")
            self.assertGreaterEqual(result["detected_skills_count"], 3)

            auto_names = [s["canonical_name"] for s in result["auto_matched_skills"]]
            self.assertIn("Python", auto_names)
            self.assertIn("Docker", auto_names)

    def test_docx_resume_extraction(self):
        """Validate and extract skills from an in-memory DOCX OpenXML file."""
        with self.app.app_context():
            # Construct a valid DOCX container in memory
            docx_buf = io.BytesIO()
            with zipfile.ZipFile(docx_buf, "w") as zf:
                zf.writestr(
                    "[Content_Types].xml",
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                    '<Default Extension="xml" ContentType="application/xml"/></Types>'
                )
                zf.writestr(
                    "word/document.xml",
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    '<w:body><w:p><w:r><w:t>'
                    'Jane Developer. Skills: Python, Docker, Kubernetes, AWS, and Git.'
                    '</w:t></w:r></w:p></w:body></w:document>'
                )
            docx_bytes = docx_buf.getvalue()

            text = ResumeExtractionService.validate_and_extract_file("resume.docx", docx_bytes)
            self.assertIn("Python", text)
            self.assertIn("Kubernetes", text)

            result = ResumeExtractionService.extract_skills_from_text(text)
            self.assertEqual(result["status"], "success")
            detected_names = [s["canonical_name"] for s in result["detected_skills"]]
            self.assertIn("Python", detected_names)
            self.assertIn("Docker", detected_names)

    def test_pdf_resume_extraction(self):
        """Validate and extract skills from a native in-memory PDF stream."""
        with self.app.app_context():
            pdf_stream = "BT /F1 12 Tf 50 700 Td (Software Engineer with Python, Docker, Git and AWS experience) Tj ET".encode("latin1")
            compressed_stream = zlib.compress(pdf_stream)

            pdf_bytes = (
                b"%PDF-1.4\n"
                b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
                b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
                b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>\nendobj\n"
                b"4 0 obj\n<< /Length " + str(len(compressed_stream)).encode() + b" /Filter /FlateDecode >>\nstream\n"
                + compressed_stream + b"\nendstream\nendobj\n"
                b"xref\n0 5\n0000000000 65535 f \n"
                b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n250\n%%EOF"
            )

            text = ResumeExtractionService.validate_and_extract_file("resume.pdf", pdf_bytes)
            self.assertIn("Python", text)
            self.assertIn("Docker", text)

            result = ResumeExtractionService.extract_skills_from_text(text)
            self.assertEqual(result["status"], "success")
            auto_names = [s["canonical_name"] for s in result["auto_matched_skills"]]
            self.assertIn("Python", auto_names)

    def test_invalid_file_extension_rejected(self):
        """Unsupported file extensions raise ValueError."""
        with self.app.app_context():
            with self.assertRaises(ValueError) as ctx:
                ResumeExtractionService.validate_and_extract_file("resume.exe", b"binarycontent")
            self.assertIn("Unsupported file format", str(ctx.exception))

            with self.assertRaises(ValueError) as ctx2:
                ResumeExtractionService.validate_and_extract_file("resume.zip", b"zipcontent")
            self.assertIn("Unsupported file format", str(ctx2.exception))

    def test_empty_and_corrupt_file_handling(self):
        """Empty files (0 bytes) raise ValueError."""
        with self.app.app_context():
            with self.assertRaises(ValueError) as ctx:
                ResumeExtractionService.validate_and_extract_file("empty.txt", b"")
            self.assertIn("empty", str(ctx.exception).lower())

    def test_auto_match_vs_review_segregation(self):
        """Skills are partitioned into auto-match (>=0.75 confidence) and review-required (<0.75)."""
        with self.app.app_context():
            text = (
                "Skills: Python, Docker, AWS.\n"
                "Knowledge of general software programming concepts."
            )
            result = ResumeExtractionService.extract_skills_from_text(text)
            self.assertIn("auto_matched_skills", result)
            self.assertIn("review_required_skills", result)
            self.assertEqual(
                result["detected_skills_count"],
                result["auto_matched_count"] + result["review_required_count"]
            )
            for skill in result["auto_matched_skills"]:
                self.assertGreaterEqual(skill["confidence_score"], 0.75)
                self.assertEqual(skill["decision"], "AUTO_MATCH")


# =====================================================================
# MODULE 5.3 TESTS: SIDE-BY-SIDE CAREER COMPARISON
# =====================================================================

class TestModule53SideBySideCareerComparison(BasePhase5TestCase):
    """Tests for Module 5.3: Side-by-Side Career Comparison."""

    def test_compare_software_developer_and_cloud_engineer(self):
        """Compare Software Developer (ID 1) and Cloud Engineer (ID 6)."""
        with self.app.app_context():
            # Setup student skills
            py_skill = CanonicalSkill.query.filter_by(normalized_name="python").first()
            git_skill = CanonicalSkill.query.filter_by(normalized_name="git").first()

            skills = [
                Skill(user_id=self.test_user_id, skill_name="Python", proficiency=8, canonical_skill_id=py_skill.id if py_skill else 1),
                Skill(user_id=self.test_user_id, skill_name="Git", proficiency=7, canonical_skill_id=git_skill.id if git_skill else 7),
            ]

            comp = CareerComparisonService.compare_careers(
                career_a_id=1,
                career_b_id=6,
                student_skills=skills
            )

            self.assertIsNotNone(comp)
            self.assertEqual(comp["career_a"]["id"], 1)
            self.assertEqual(comp["career_b"]["id"], 6)

            metrics = comp["comparison_metrics"]
            self.assertIn("overlap_percentage", metrics)
            self.assertIn("common_skills_count", metrics)
            self.assertIn("closer_career", metrics)
            self.assertIn("summary", metrics)

            self.assertIsInstance(comp["common_skills"], list)
            self.assertIsInstance(comp["career_a_only"], list)
            self.assertIsInstance(comp["career_b_only"], list)
            self.assertIsInstance(comp["student_already_has"], list)
            self.assertIsInstance(comp["student_missing"], list)

            # Common skills must have requirements for both careers
            for cs in comp["common_skills"]:
                self.assertIn("career_a", cs)
                self.assertIn("career_b", cs)
                self.assertIn("required_level", cs["career_a"])
                self.assertIn("required_level", cs["career_b"])

    def test_compare_careers_invalid_id(self):
        """Comparing non-existent career IDs returns None safely."""
        with self.app.app_context():
            res = CareerComparisonService.compare_careers(
                career_a_id=99999,
                career_b_id=1,
                student_skills=[]
            )
            self.assertIsNone(res)


# =====================================================================
# MODULE 5.4 TESTS: STUDENT ANALYTICS & READINESS VELOCITY
# =====================================================================

class TestModule54StudentAnalyticsAndVelocity(BasePhase5TestCase):
    """Tests for Module 5.4: Career Readiness Velocity & Student Analytics."""

    def test_analytics_baseline_vs_current_and_velocity(self):
        """Calculate baseline readiness, completed resources, improvement, and velocity."""
        with self.app.app_context():
            career = Career.query.get(1)  # Software Developer
            self.assertIsNotNone(career)

            # Initially: student has no learning progress
            initial_analytics = StudentAnalyticsService.get_student_career_analytics(
                user_id=self.test_user_id,
                career_id=career.id
            )
            self.assertIsNotNone(initial_analytics)
            self.assertEqual(initial_analytics["readiness"]["baseline_readiness_percentage"], 0.0)
            self.assertEqual(initial_analytics["readiness"]["readiness_improvement"], 0.0)
            self.assertEqual(initial_analytics["learning_progress_summary"]["completed_resources_count"], 0)

            # Now student starts and completes a resource relevant to the career
            py_skill = CanonicalSkill.query.filter_by(normalized_name="python").first()
            resource = LearningResource.query.filter_by(canonical_skill_id=py_skill.id).first()
            self.assertIsNotNone(resource)

            LearningProgressService.start_resource(self.test_user_id, resource.id)
            LearningProgressService.complete_resource(self.test_user_id, resource.id)

            # Analytics after completion
            updated_analytics = StudentAnalyticsService.get_student_career_analytics(
                user_id=self.test_user_id,
                career_id=career.id
            )
            self.assertIsNotNone(updated_analytics)
            self.assertGreater(updated_analytics["readiness"]["current_readiness_percentage"], 0.0)
            self.assertGreater(updated_analytics["readiness"]["readiness_improvement"], 0.0)

            velocity = updated_analytics["velocity"]
            self.assertGreaterEqual(velocity["days_elapsed"], 1)
            self.assertGreater(velocity["improvement_per_completed_resource"], 0.0)
            self.assertGreater(velocity["readiness_velocity_per_day"], 0.0)
            self.assertGreater(velocity["readiness_velocity_per_week"], 0.0)

            # Check skills acquired
            skills_acquired = updated_analytics["skills_acquired_or_improved"]
            self.assertGreaterEqual(len(skills_acquired), 1)
            self.assertEqual(skills_acquired[0]["canonical_skill_id"], py_skill.id)

            # Check timeline
            timeline = updated_analytics["progress_timeline"]
            self.assertGreaterEqual(len(timeline), 1)
            self.assertEqual(timeline[0]["status"], "Completed")


# =====================================================================
# REST API ENDPOINTS INTEGRATION TESTS
# =====================================================================

class TestPhase5APIEndpoints(BasePhase5TestCase):
    """Integration tests for all newly added and enhanced Phase 5 REST API routes."""

    def test_api_learning_resource_lifecycle(self):
        """Lifecycle: start -> update progress -> complete via API."""
        with self.app.app_context():
            res = LearningResource.query.first()
            res_id = res.id

        # 1. Start resource
        start_resp = self.client.post(
            f"/api/learning-resources/{res_id}/start?user_id={self.test_user_id}"
        )
        self.assertEqual(start_resp.status_code, 200)
        start_data = start_resp.get_json()
        self.assertEqual(start_data["status"], "success")
        self.assertEqual(start_data["progress"]["status"], "In Progress")

        # 2. Update progress
        put_resp = self.client.put(
            f"/api/learning-resources/{res_id}/progress?user_id={self.test_user_id}",
            json={"progress_percentage": 50.0, "notes": "Halfway done"}
        )
        self.assertEqual(put_resp.status_code, 200)
        put_data = put_resp.get_json()
        self.assertEqual(put_data["progress"]["progress_percentage"], 50.0)

        # 3. Complete resource
        comp_resp = self.client.post(
            f"/api/learning-resources/{res_id}/complete?user_id={self.test_user_id}"
        )
        self.assertEqual(comp_resp.status_code, 200)
        comp_data = comp_resp.get_json()
        self.assertEqual(comp_data["progress"]["status"], "Completed")

        # 4. Query progress list
        list_resp = self.client.get(
            f"/api/learning-resources/progress?user_id={self.test_user_id}"
        )
        self.assertEqual(list_resp.status_code, 200)
        list_data = list_resp.get_json()
        self.assertGreaterEqual(list_data["count"], 1)

    def test_api_career_comparison_get_and_post(self):
        """Test GET /api/careers/compare and POST /api/careers/compare."""
        # GET
        get_resp = self.client.get(
            f"/api/careers/compare?career_a_id=1&career_b_id=6&user_id={self.test_user_id}"
        )
        self.assertEqual(get_resp.status_code, 200)
        get_data = get_resp.get_json()
        self.assertEqual(get_data["status"], "success")
        self.assertIn("comparison", get_data)

        # POST
        post_resp = self.client.post(
            "/api/careers/compare",
            json={"career_a_id": 1, "career_b_id": 6, "user_id": self.test_user_id}
        )
        self.assertEqual(post_resp.status_code, 200)
        post_data = post_resp.get_json()
        self.assertEqual(post_data["status"], "success")
        self.assertIn("comparison", post_data)

        # Missing params error
        bad_resp = self.client.get("/api/careers/compare?career_a_id=1")
        self.assertEqual(bad_resp.status_code, 400)

    def test_api_career_analytics(self):
        """Test GET /api/careers/<id>/analytics and GET /api/careers/analytics."""
        # GET /api/careers/1/analytics
        resp1 = self.client.get(f"/api/careers/1/analytics?user_id={self.test_user_id}")
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.get_json()
        self.assertEqual(data1["status"], "success")
        self.assertIn("analytics", data1)
        self.assertIn("readiness", data1["analytics"])
        self.assertIn("velocity", data1["analytics"])

        # GET /api/careers/analytics?career_id=1
        resp2 = self.client.get(f"/api/careers/analytics?career_id=1&user_id={self.test_user_id}")
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertEqual(data2["status"], "success")

        # Missing user_id error
        resp_no_user = self.client.get("/api/careers/1/analytics")
        self.assertEqual(resp_no_user.status_code, 400)

    def test_api_extract_resume_multipart_file_upload(self):
        """Test POST /api/skills/extract-resume with multipart file upload."""
        resume_bytes = (
            "Technical Skills:\n"
            "- Python, Docker, AWS, PostgreSQL, REST APIs\n"
            "Experience:\n"
            "Backend development using Flask and SQL."
        ).encode("utf-8")

        data = {
            "file": (io.BytesIO(resume_bytes), "developer_resume.txt")
        }
        resp = self.client.post(
            "/api/skills/extract-resume",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 200)
        res_data = resp.get_json()
        self.assertEqual(res_data["status"], "success")
        self.assertGreaterEqual(res_data["detected_skills_count"], 3)
        self.assertIn("auto_matched_skills", res_data)

    def test_api_apply_resume_skills(self):
        """Test POST /api/skills/extract-resume/apply to update student skills."""
        payload = {
            "user_id": self.test_user_id,
            "skills": [
                {"canonical_name": "Docker", "proficiency": 7, "canonical_skill_id": 9},
                {"canonical_name": "Python", "proficiency": 8, "canonical_skill_id": 1}
            ]
        }
        resp = self.client.post("/api/skills/extract-resume/apply", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["applied_count"], 2)

        with self.app.app_context():
            skills = Skill.query.filter_by(user_id=self.test_user_id).all()
            self.assertEqual(len(skills), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
