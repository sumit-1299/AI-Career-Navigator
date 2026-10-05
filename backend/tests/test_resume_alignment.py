"""Resume imports, owner isolation, conflict handling and frozen source coverage."""
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4
import zipfile

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "assessment-tests-only-not-a-deployment-secret-2026"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from extensions import db
from services.resume_evidence import analyze_resume
from services.resume_parser import MAX_FILE

TEXT = "Candidate example\nBuilt Python services and SQL reports for a class project.\nUsed Git for version control."


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.owner = self.register("resume-one@example.test")
        self.other = self.register("resume-two@example.test")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register(self, email):
        body = {"name": "Resume test", "email": email, "password": "local-test-only-password"}
        self.client.post("/api/register", json=body)
        token = self.client.post("/api/login", json=body).get_json()["access_token"]
        return {"Authorization": "Bearer " + token}

    def save(self, text=TEXT, version=0, headers=None):
        return self.client.put("/api/resume", headers=headers or self.owner,
                               json={"text": text, "source_name": "resume.txt", "version": version})

    def upload(self, content, filename):
        return self.client.post("/api/resume/extract", headers=self.owner,
                                data={"file": (io.BytesIO(content), filename)})

    def compare(self):
        response = self.client.post("/api/job-matches", headers=self.owner, json={
            "submission_id": str(uuid4()), "title": "Synthetic test role",
            "description": "Requirements:\nPython, SQL, Docker and Git are required.",
            "source_url": "", "mode": "keyword"})
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["comparison"]

    def test_private_routes_require_auth_and_payload_is_owner_scoped(self):
        for method, url in [("GET", "/api/resume"), ("PUT", "/api/resume"), ("DELETE", "/api/resume"), ("POST", "/api/resume/extract")]:
            self.assertEqual(self.client.open(url, method=method).status_code, 401)
        self.assertEqual(self.save().status_code, 200)
        other = self.client.get("/api/resume", headers=self.other)
        self.assertIsNone(other.get_json()["resume"])
        self.assertEqual(other.headers["Cache-Control"], "no-store")

    def test_save_conflict_and_tombstone_do_not_overwrite_newer_text(self):
        first = self.save().get_json()
        self.assertEqual(first["version"], 1)
        self.assertEqual(self.save(TEXT + "\nNew wording.", 0).status_code, 409)
        self.assertEqual(self.save(TEXT + "\nNew wording.", 1).get_json()["version"], 2)
        cleared = self.client.delete("/api/resume", headers=self.owner, json={"version": 2}).get_json()
        self.assertIsNone(cleared["resume"])
        self.assertEqual(cleared["version"], 3)
        self.assertEqual(self.save(version=0).status_code, 409)
        self.assertEqual(self.save(version=3).get_json()["version"], 4)

    def test_validation_rejects_injected_fields_and_bad_types(self):
        for body in ({"text": TEXT, "source_name": "resume", "version": True},
                     {"text": "short", "source_name": "resume", "version": 0},
                     {"text": "x" * 30001, "source_name": "resume", "version": 0},
                     {"text": TEXT, "source_name": "resume", "version": 0, "user_id": 2}):
            self.assertEqual(self.client.put("/api/resume", headers=self.owner, json=body).status_code, 400)

    def test_extraction_is_preview_only_and_file_status_is_explicit(self):
        response = self.upload(TEXT.encode(), "resume.txt")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["text"], TEXT)
        self.assertFalse(response.get_json()["saved"])
        self.assertIsNone(self.client.get("/api/resume", headers=self.owner).get_json()["resume"])

    def test_docx_extraction_reads_paragraphs_and_rejects_entities(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + TEXT + '</w:t></w:r></w:p></w:body></w:document>')
        response = self.upload(stream.getvalue(), "resume.docx")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertIn("Python services", response.get_json()["text"])
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("word/document.xml", '<!DOCTYPE x [<!ENTITY a "unsafe">]><x>&a;</x>')
        self.assertEqual(self.upload(stream.getvalue(), "resume.docx").status_code, 400)

    def test_pdf_text_and_blank_scan_fallback(self):
        from pypdf import PdfWriter
        from pypdf.generic import NameObject, DictionaryObject, DecodedStreamObject
        writer = PdfWriter(); page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
        content = DecodedStreamObject(); content.set_data(b"BT /F1 12 Tf 40 700 Td (Built Python services and SQL reports with Git for a class project.) Tj ET")
        page[NameObject("/Contents")] = content
        stream = io.BytesIO(); writer.write(stream)
        response = self.upload(stream.getvalue(), "resume.pdf")
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertIn("Python services", response.get_json()["text"])
        writer = PdfWriter(); writer.add_blank_page(width=612, height=792)
        stream = io.BytesIO(); writer.write(stream)
        self.assertIn("readable text", self.upload(stream.getvalue(), "scan.pdf").get_json()["message"])

    def test_bad_upload_keeps_previous_resume_and_parser_timeouts_are_handled(self):
        import subprocess
        self.save()
        for data, name in [(b"x" * (MAX_FILE + 1), "large.txt"), (b"invalid", "resume.pdf"), (TEXT.encode(), "resume.html")]:
            self.assertEqual(self.upload(data, name).status_code, 400)
        with patch("routes.resume.subprocess.run", side_effect=subprocess.TimeoutExpired("parser", 10)):
            self.assertEqual(self.upload(TEXT.encode(), "resume.pdf").status_code, 400)
        self.assertEqual(self.client.get("/api/resume", headers=self.owner).get_json()["resume"]["text"], TEXT)

    def test_resume_mentions_respect_boundaries_and_uncertain_wording(self):
        result = analyze_resume("Built JavaScript services with NoSQL and MySQL.\nLearning Docker.\nNo experience with Java.\nBuilt Python services.")
        self.assertEqual({r["skill_key"] for r in result["skills"]}, {"javascript", "python"})
        self.assertEqual(len(result["manual_review"]), 2)

    def test_resume_does_not_create_ratings_and_old_comparison_survives_removal(self):
        self.save()
        saved = self.compare()
        self.assertEqual(saved["result"]["alignment"]["with_resume_mentions"], 3)
        self.assertEqual(saved["result"]["alignment"]["with_self_ratings"], 0)
        self.assertEqual(saved["result"]["alignment"]["without_recorded_support"], ["Docker"])
        self.assertEqual(self.client.get("/api/skills", headers=self.owner).get_json()["skills"], [])
        self.client.delete("/api/resume", headers=self.owner, json={"version": 1})
        fresh = self.compare()
        self.assertIsNone(fresh["candidate_snapshot"]["resume"])
        self.assertEqual(fresh["result"]["alignment"]["with_resume_mentions"], 0)
        old = self.client.get(f"/api/job-matches/{saved['id']}", headers=self.owner).get_json()["comparison"]
        self.assertEqual(old, saved)
        self.assertEqual(self.client.get(f"/api/job-matches/{saved['id']}", headers=self.other).status_code, 404)

    def test_skill_removal_is_owner_scoped_and_preserves_snapshot(self):
        skill = self.client.post("/api/skills", headers=self.owner, json={"skill_name": "Python", "proficiency": 7}).get_json()["skill"]
        saved = self.compare()
        self.assertEqual(self.client.delete(f"/api/skills/{skill['id']}", headers=self.other).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/skills/{skill['id']}", headers=self.owner).status_code, 200)
        old = self.client.get(f"/api/job-matches/{saved['id']}", headers=self.owner).get_json()["comparison"]
        self.assertEqual(old, saved)


if __name__ == "__main__":
    unittest.main()
