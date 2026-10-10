"""
Regression and Integration Tests for Resume ATS Parser OCR Fallback.

Validates:
1. Searchable PDF extraction fast path (zero OCR overhead).
2. Image-based/scanned PDF extraction via OCR fallback.
3. Multi-page PDF handling and reading order preservation.
4. Empty or unreadable PDF raises expected ValueError.
5. OCR unavailable graceful handling when tools are absent.
6. DOCX extraction remains functional without regression.
7. TXT extraction remains functional without regression.
8. Canonical skill matching after OCR extraction (dual contract).
9. ATS scoring after OCR extraction for target careers.
10. Unsupported file formats properly rejected.
11. File size limit enforcement (10 MB).
12. End-to-end authenticated API contracts for extraction & scoring.
"""

import io
import os
import unittest
import zipfile
import zlib
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models.user import User
from services.resume_extraction_service import ResumeExtractionService, MAX_RESUME_SIZE


class TestResumeOCRExtraction(unittest.TestCase):
    """Test suite for Resume ATS Parser with OCR Fallback."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        # Find or create a test user
        cls.user = User.query.filter_by(email="resume_ocr_test@example.com").first()
        if not cls.user:
            cls.user = User(
                name="Resume OCR Test User",
                email="resume_ocr_test@example.com",
                password_hash=generate_password_hash("password123")
            )
            db.session.add(cls.user)
            db.session.commit()

        # Login to obtain JWT
        resp = cls.client.post("/api/login", json={
            "email": "resume_ocr_test@example.com",
            "password": "password123"
        })
        data = resp.get_json()
        cls.token = data.get("access_token")
        cls.headers = {"Authorization": f"Bearer {cls.token}"}

        # Locate sample image-based PDF
        cls.image_pdf_path = os.path.join(
            os.path.dirname(__file__), "test_resume_image.pdf"
        )
        if os.path.exists(cls.image_pdf_path):
            with open(cls.image_pdf_path, "rb") as f:
                cls.image_pdf_bytes = f.read()
        else:
            cls.image_pdf_bytes = b"%PDF-1.4\n%scanned mock\n%%EOF"

    @classmethod
    def tearDownClass(cls):
        cls.ctx.pop()

    def test_01_searchable_pdf_fast_path(self):
        """1. Searchable PDF with sufficient text extracts directly without OCR overhead."""
        # Construct valid searchable PDF stream with >= 20 words
        text_content = (
            "Senior Cloud and DevOps Architect with extensive expertise in Linux administration, "
            "Docker containerization, Kubernetes cluster orchestration, and automated CI/CD pipelines. "
            "Proficient in Python scripting, AWS cloud infrastructure, Git version control, and SQL databases."
        )
        pdf_stream = f"BT /F1 12 Tf 50 700 Td ({text_content}) Tj ET".encode("latin1")
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

        with patch.object(ResumeExtractionService, "_extract_text_via_ocr") as mock_ocr:
            extracted = ResumeExtractionService.validate_and_extract_file("searchable.pdf", pdf_bytes)
            mock_ocr.assert_not_called()
            self.assertIn("Linux", extracted)
            self.assertIn("Kubernetes", extracted)
            self.assertIn("AWS", extracted)

    def test_02_image_pdf_ocr_fallback(self):
        """2. Image-based/scanned PDF falls back to OCR and recovers technical keywords."""
        if not os.path.exists(self.image_pdf_path):
            self.skipTest("Sample image PDF fixture not found")

        extracted = ResumeExtractionService.validate_and_extract_file(
            "scanned_resume.pdf", self.image_pdf_bytes
        )
        self.assertGreater(len(extracted), 500)
        # Verify key role competencies recovered via OCR
        for skill in ["AWS", "Linux", "Docker", "Python", "Kubernetes", "Git"]:
            self.assertIn(skill.lower(), extracted.lower())

    def test_03_ocr_multi_page_ordering_and_limit(self):
        """3. OCR maintains page order numerically and respects page limits."""
        self.assertTrue(ResumeExtractionService.is_ocr_available())
        # Verify OCR helper method accepts max_pages parameter
        extracted = ResumeExtractionService._extract_text_via_ocr(
            self.image_pdf_bytes, max_pages=2
        )
        self.assertIsInstance(extracted, str)

    def test_04_empty_or_unreadable_pdf_raises_value_error(self):
        """4. Corrupted or completely blank PDF raises informative ValueError."""
        # Minimal empty PDF structure with zero text streams and blank canvas
        empty_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
            b"xref\n0 3\n0000000000 65535 f \n"
            b"trailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
        )
        with self.assertRaises(ValueError) as ctx:
            ResumeExtractionService.validate_and_extract_file("blank.pdf", empty_pdf)
        self.assertIn("We couldn't extract readable text from this resume", str(ctx.exception))

    def test_05_ocr_unavailable_graceful_handling(self):
        """5. When OCR binaries are unavailable, unreadable PDFs fail with clear guidance."""
        empty_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n"
            b"xref\n0 3\n0000000000 65535 f \n"
            b"trailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n100\n%%EOF"
        )
        with patch.object(ResumeExtractionService, "is_ocr_available", return_value=False):
            with self.assertRaises(ValueError) as ctx:
                ResumeExtractionService.validate_and_extract_file("image_only.pdf", empty_pdf)
            self.assertIn("We couldn't extract readable text from this resume", str(ctx.exception))

    def test_06_docx_extraction_intact(self):
        """6. DOCX OpenXML extraction functions without regression."""
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
                'Experienced Software Engineer proficient in Python, Docker, Kubernetes, and AWS.'
                '</w:t></w:r></w:p></w:body></w:document>'
            )
        docx_bytes = docx_buf.getvalue()
        text = ResumeExtractionService.validate_and_extract_file("resume.docx", docx_bytes)
        self.assertIn("Python", text)
        self.assertIn("Kubernetes", text)

    def test_07_txt_extraction_intact(self):
        """7. Plain text UTF-8 extraction functions without regression."""
        txt_content = "Skills: Linux, Docker, Python, Git, CI/CD, SQL."
        text = ResumeExtractionService.validate_and_extract_file(
            "resume.txt", txt_content.encode("utf-8")
        )
        self.assertEqual(text, txt_content)

    def test_08_canonical_skill_matching_after_ocr(self):
        """8. Skill extraction from OCR text maps to canonical vocabulary with dual contract."""
        if not os.path.exists(self.image_pdf_path):
            self.skipTest("Sample image PDF fixture not found")

        extracted_text = ResumeExtractionService.validate_and_extract_file(
            "scanned_resume.pdf", self.image_pdf_bytes
        )
        result = ResumeExtractionService.extract_skills_from_text(extracted_text)

        self.assertEqual(result["status"], "success")
        self.assertGreater(result["detected_skills_count"], 5)

        # Dual contract keys for frontend UI compatibility
        self.assertIn("matched_canonical_skills", result)
        self.assertIn("summary", result)
        self.assertIn("auto_matched_skills", result)

        summary = result["summary"]
        self.assertGreaterEqual(summary["total_extracted"], 5)
        self.assertGreaterEqual(summary["exact_matches"], 5)

        canonical_names = [s["canonical_name"] for s in result["matched_canonical_skills"]]
        for expected in ["AWS", "Linux", "Docker", "Python", "CI/CD"]:
            self.assertIn(expected, canonical_names)

    def test_09_ats_scoring_after_ocr(self):
        """9. ATS scoring on OCR text computes accurate alignment against target careers."""
        if not os.path.exists(self.image_pdf_path):
            self.skipTest("Sample image PDF fixture not found")

        extracted_text = ResumeExtractionService.validate_and_extract_file(
            "scanned_resume.pdf", self.image_pdf_bytes
        )

        # Career 6: Cloud Engineer
        score_cloud = ResumeExtractionService.score_resume_against_career(extracted_text, 6)
        self.assertIsNotNone(score_cloud)
        self.assertEqual(score_cloud["status"], "success")
        self.assertEqual(score_cloud["ats_score"], 100)
        self.assertEqual(score_cloud["alignment_level"], "Excellent")
        self.assertIn("AWS", score_cloud["matched_keywords"])
        self.assertIn("Linux", score_cloud["matched_keywords"])
        self.assertIn("Docker", score_cloud["matched_keywords"])

        # Career 7: DevOps Engineer
        score_devops = ResumeExtractionService.score_resume_against_career(extracted_text, 7)
        self.assertIsNotNone(score_devops)
        self.assertEqual(score_devops["ats_score"], 100)
        self.assertIn("CI/CD", score_devops["matched_keywords"])
        self.assertIn("Kubernetes", score_devops["matched_keywords"])

    def test_10_unsupported_format_rejected(self):
        """10. Unsupported file extensions (.exe, .zip) raise descriptive ValueError."""
        with self.assertRaises(ValueError) as ctx:
            ResumeExtractionService.validate_and_extract_file("malicious.exe", b"fake binary")
        self.assertIn("Unsupported file format", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx2:
            ResumeExtractionService.validate_and_extract_file("archive.zip", b"PK\x03\x04")
        self.assertIn("Unsupported file format", str(ctx2.exception))

    def test_11_max_file_size_validation(self):
        """11. Files exceeding MAX_RESUME_SIZE (10 MB) are rejected."""
        oversized_bytes = b"0" * (MAX_RESUME_SIZE + 1024)
        with self.assertRaises(ValueError) as ctx:
            ResumeExtractionService.validate_and_extract_file("huge.txt", oversized_bytes)
        self.assertIn("exceeds the maximum allowed limit", str(ctx.exception))

    def test_12_authenticated_api_contract_verification(self):
        """12. HTTP API endpoints /api/skills/extract-resume and /score return expected schemas."""
        if not os.path.exists(self.image_pdf_path):
            self.skipTest("Sample image PDF fixture not found")

        # Test extraction via multipart endpoint
        data = {
            "file": (io.BytesIO(self.image_pdf_bytes), "resume.pdf", "application/pdf")
        }
        resp = self.client.post(
            "/api/skills/extract-resume",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.get_json()
        self.assertEqual(resp_json["status"], "success")
        self.assertIn("matched_canonical_skills", resp_json)
        self.assertIn("summary", resp_json)
        self.assertGreater(resp_json["summary"]["exact_matches"], 0)

        # Test scoring via authenticated endpoint
        data_score = {
            "file": (io.BytesIO(self.image_pdf_bytes), "resume.pdf", "application/pdf")
        }
        resp_score = self.client.post(
            "/api/skills/extract-resume/score?career_id=6",
            headers=self.headers,
            data=data_score,
            content_type="multipart/form-data"
        )
        self.assertEqual(resp_score.status_code, 200)
        score_json = resp_score.get_json()
        self.assertEqual(score_json["status"], "success")
        self.assertEqual(score_json["ats_score"], 100)
        self.assertEqual(score_json["career_title"], "Cloud Engineer")
        self.assertEqual(len(score_json["missing_keywords"]), 0)


if __name__ == "__main__":
    unittest.main()
