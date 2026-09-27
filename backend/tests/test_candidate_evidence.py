"""Evidence provenance, owner isolation and update safety on isolated SQLite."""

from copy import deepcopy
from datetime import datetime, timedelta
import os
from pathlib import Path
import sys
import unittest
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "assessment-tests-only-not-a-deployment-secret-2026"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from extensions import db
from flask_jwt_extended import create_access_token
from models.candidate_evidence import CandidateEvidence
from services.sql_assessment import QUESTIONS


class CandidateEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.headers = self.register("evidence-one@example.test")
        self.other = self.register("evidence-two@example.test")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register(self, email):
        account = {"name": "Evidence Demo", "email": email, "password": "test-only-credential"}
        self.assertEqual(self.client.post("/api/register", json=account).status_code, 201)
        token = self.client.post("/api/login", json=account).get_json()["access_token"]
        return {"Authorization": "Bearer " + token}

    def payload(self, kind="project"):
        body = {
            "submission_id": str(uuid4()), "kind": kind,
            "title": " Library management database ",
            "description": "A team project recording books, loans and returns.",
            "source_url": "https://github.com/example/library-project",
            "skills": ["SQL", " sql ", "REST   APIs"],
        }
        if kind == "project":
            body["contribution"] = "I designed the schema and tested the loan queries."
        else:
            body.update(title="Introduction to SQL", issuer="Example Issuer", issued_on="2026-01-15",
                        source_url="https://example.com/credentials/demo")
        return body

    def create(self, body=None, headers=None):
        response = self.client.post("/api/evidence", json=body or self.payload(), headers=headers or self.headers)
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["evidence"]

    def update_payload(self, record):
        keys = ("kind", "title", "description", "source_url", "skills", "version")
        result = {key: deepcopy(record[key]) for key in keys}
        if record["kind"] == "project":
            result["contribution"] = record["contribution"]
        else:
            result.update(issuer=record["issuer"], issued_on=record["issued_on"])
        return result

    def test_authentication_and_missing_account(self):
        routes = [("GET", "/api/evidence"), ("POST", "/api/evidence"),
                  ("GET", f"/api/evidence/{uuid4()}"), ("PUT", f"/api/evidence/{uuid4()}"),
                  ("PATCH", f"/api/evidence/{uuid4()}/archive")]
        with self.app.app_context():
            missing = {"Authorization": "Bearer " + create_access_token(identity="999999")}
        for method, path in routes:
            for headers in ({}, missing):
                self.assertEqual(self.client.open(path, method=method, headers=headers, json={}).status_code, 401)

    def test_projects_and_certifications_have_unverified_provenance(self):
        for kind in ("project", "certification"):
            item = self.create(self.payload(kind))
            self.assertEqual(item["kind"], kind)
            self.assertEqual(item["verification_status"], "unverified")
            self.assertEqual(item["source"], "candidate_submission")
            self.assertEqual(item["skills"], ["SQL", "REST APIs"])
            self.assertEqual(item["version"], 1)
            self.assertFalse(item["archived"])
            self.assertEqual(datetime.fromisoformat(item["created_at"]).utcoffset(), timedelta(0))
            self.assertNotIn("user_id", item)
            self.assertEqual(item["title"], item["title"].strip())
        response = self.client.get("/api/evidence", headers=self.headers)
        self.assertEqual(len(response.get_json()["evidence"]), 2)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_other_candidate_cannot_list_read_edit_or_archive(self):
        item = self.create()
        self.assertEqual(self.client.get("/api/evidence", headers=self.other).get_json()["evidence"], [])
        path = f"/api/evidence/{item['id']}"
        for method, route, body in [("GET", path, {}), ("PUT", path, self.update_payload(item)),
                                    ("PATCH", path + "/archive", {"version": 1, "archived": True})]:
            self.assertEqual(self.client.open(route, method=method, headers=self.other, json=body).status_code, 404)
        self.assertEqual(self.client.get(path, headers=self.headers).get_json()["evidence"], item)

    def test_creation_retry_reuses_one_record_and_key_is_owner_scoped(self):
        body = self.payload()
        item = self.create(body)
        repeat = self.client.post("/api/evidence", json=body, headers=self.headers)
        self.assertEqual(repeat.status_code, 200)
        self.assertEqual(repeat.get_json()["evidence"], item)
        second_owner = self.create(body, self.other)
        self.assertNotEqual(item["id"], second_owner["id"])
        changed = dict(body, title="Different data for the same submission")
        self.assertEqual(self.client.post("/api/evidence", json=changed, headers=self.headers).status_code, 409)
        with self.app.app_context():
            self.assertEqual(db.session.query(CandidateEvidence).count(), 2)

    def test_server_owned_fields_and_unknown_fields_are_rejected(self):
        for key, value in [("user_id", 2), ("verification_status", "verified"), ("score", 100),
                           ("source", "expert_review"), ("created_at", "2026-01-01"), ("archived", True)]:
            body = dict(self.payload(), **{key: value})
            self.assertEqual(self.client.post("/api/evidence", json=body, headers=self.headers).status_code, 400)
        item = self.create()
        body = dict(self.update_payload(item), verification_status="verified")
        self.assertEqual(self.client.put(f"/api/evidence/{item['id']}", json=body, headers=self.headers).status_code, 400)

    def test_malformed_and_wrong_type_payloads(self):
        for body in ([], True, "text", {}, {"kind": []}, {"kind": "unknown"}):
            self.assertEqual(self.client.post("/api/evidence", json=body, headers=self.headers).status_code, 400)
        for raw in ("{", "null", ""):
            response = self.client.post("/api/evidence", data=raw, content_type="application/json", headers=self.headers)
            self.assertEqual(response.status_code, 400)
        for key in ("title", "description", "contribution", "source_url"):
            for value in (None, 12, True, [], "   "):
                body = dict(self.payload(), **{key: value})
                self.assertEqual(self.client.post("/api/evidence", json=body, headers=self.headers).status_code, 400, (key, value))

    def test_field_limits_and_skill_validation(self):
        for key, value in [("title", "x" * 161), ("description", "x" * 2001),
                           ("contribution", "x" * 2001), ("source_url", "https://example.com/" + "x" * 2048),
                           ("skills", []), ("skills", "SQL"), ("skills", ["SQL", ""]),
                           ("skills", [None]), ("skills", ["x" * 41]), ("skills", ["SQL"] * 11),
                           ("title", "bad\x00text")]:
            body = dict(self.payload(), **{key: value})
            self.assertEqual(self.client.post("/api/evidence", json=body, headers=self.headers).status_code, 400, key)

    def test_unsafe_and_malformed_links_are_rejected(self):
        for url in ("javascript:alert(1)", "data:text/html,hello", "file:///tmp/a", "http://github.com/a",
                    "https://user:password@github.com/a", "https://github.com:8080/a", "https://github.com:bad/a",
                    "https://localhost/a", "https://host.local/a", "https://127.0.0.1/a", "https://[::1]/a",
                    "https://10.1.1.1/a", "https://8.8.8.8/a", "https://2130706433/a", "https://0x7f000001/a",
                    "https://github.com/a b", "https://github.com/a\nb", "https://github.com\\@localhost/a",
                    "https://a..com/a", "https://-a.com/a", "https://github.com./a", "https://[bad/a"):
            body = dict(self.payload(), source_url=url)
            self.assertEqual(self.client.post("/api/evidence", json=body, headers=self.headers).status_code, 400, url)

    def test_valid_https_link_is_stored_without_network_verification(self):
        url = "https://example.com:443/credential?id=demo#details"
        item = self.create(dict(self.payload(), source_url=url))
        self.assertEqual(item["source_url"], url)
        self.assertEqual(item["verification_status"], "unverified")

    def test_certificate_date_issuer_and_kind_specific_fields(self):
        for value in ("2026-02-30", "9999-01-01", "20260101", "2026-1-1", None, True, 2026):
            body = dict(self.payload("certification"), issued_on=value)
            self.assertEqual(self.client.post("/api/evidence", json=body, headers=self.headers).status_code, 400)
        for value in ("", "x" * 161, []):
            self.assertEqual(self.client.post("/api/evidence", json=dict(self.payload("certification"), issuer=value), headers=self.headers).status_code, 400)
        body = dict(self.payload("certification"), contribution="Extra field")
        self.assertEqual(self.client.post("/api/evidence", json=body, headers=self.headers).status_code, 400)

    def test_invalid_submission_ids_are_rejected(self):
        for value in ("123", 1, None, str(uuid4()).upper(), "00000000-0000-0000-0000-000000000000"):
            self.assertEqual(self.client.post("/api/evidence", json=dict(self.payload(), submission_id=value), headers=self.headers).status_code, 400)

    def test_edit_keeps_identity_creation_time_and_unverified_status(self):
        item = self.create()
        body = dict(self.update_payload(item), contribution="I also added database constraints and tests.")
        response = self.client.put(f"/api/evidence/{item['id']}", json=body, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        edited = response.get_json()["evidence"]
        self.assertEqual(edited["contribution"], body["contribution"])
        self.assertEqual(edited["id"], item["id"])
        self.assertEqual(edited["created_at"], item["created_at"])
        self.assertEqual(edited["version"], 2)
        self.assertEqual(edited["verification_status"], "unverified")

    def test_stale_edits_and_archives_cannot_overwrite_newer_changes(self):
        item = self.create()
        path = f"/api/evidence/{item['id']}"
        new = dict(self.update_payload(item), title="Newer title")
        updated = self.client.put(path, json=new, headers=self.headers).get_json()["evidence"]
        self.assertEqual(self.client.put(path, json=dict(new, title="Old stale edit"), headers=self.headers).status_code, 409)
        self.assertEqual(self.client.patch(path + "/archive", json={"version": 1, "archived": True}, headers=self.headers).status_code, 409)
        self.assertEqual(self.client.get(path, headers=self.headers).get_json()["evidence"], updated)

    def test_versions_require_positive_integers_and_kind_cannot_change(self):
        item = self.create()
        path = f"/api/evidence/{item['id']}"
        for value in (True, 0, -1, "1", 1.5, None, 2147483647):
            self.assertEqual(self.client.put(path, json=dict(self.update_payload(item), version=value), headers=self.headers).status_code, 400)
        certificate = self.payload("certification")
        del certificate["submission_id"]
        certificate["version"] = 1
        self.assertEqual(self.client.put(path, json=certificate, headers=self.headers).status_code, 400)

    def test_archive_restore_preserves_content_and_blocks_edit_while_archived(self):
        item = self.create()
        path = f"/api/evidence/{item['id']}"
        archived = self.client.patch(path + "/archive", json={"version": 1, "archived": True}, headers=self.headers).get_json()["evidence"]
        self.assertTrue(archived["archived"])
        self.assertEqual(self.client.put(path, json=self.update_payload(archived), headers=self.headers).status_code, 409)
        self.assertTrue(self.client.get("/api/evidence", headers=self.headers).get_json()["evidence"][0]["archived"])
        restored = self.client.patch(path + "/archive", json={"version": 2, "archived": False}, headers=self.headers).get_json()["evidence"]
        self.assertFalse(restored["archived"])
        self.assertEqual(restored["version"], 3)
        for key in ("title", "source_url", "skills", "contribution", "created_at", "verification_status"):
            self.assertEqual(restored[key], item[key])

    def test_archive_validation(self):
        item = self.create()
        for body in ({}, [], {"version": 1, "archived": 1}, {"version": 1, "archived": "true"},
                     {"version": True, "archived": True}, {"version": 1, "archived": True, "user_id": 2}):
            response = self.client.patch(f"/api/evidence/{item['id']}/archive", json=body, headers=self.headers)
            self.assertEqual(response.status_code, 400)

    def test_evidence_does_not_change_skill_rating_result_or_roadmap(self):
        self.client.post("/api/skills", headers=self.headers, json={"skill_name": "SQL", "proficiency": 7})
        attempt = self.client.post("/api/assessments/sql/attempts", headers=self.headers, json={}).get_json()["attempt"]
        answers = [{"question_id": question["id"], "option_id": option} for question, option in zip(QUESTIONS, ("b", "c", "a", "b", "b", None))]
        path = f"/api/assessments/attempts/{attempt['id']}"
        attempt = self.client.post(path + "/submit", headers=self.headers, json={"answers": answers}).get_json()["attempt"]
        roadmap_path = f"/api/roadmaps/attempts/{attempt['id']}"
        roadmap = self.client.post(roadmap_path, headers=self.headers, json={}).get_json()["roadmap"]
        item = self.create()
        edited = self.client.put(f"/api/evidence/{item['id']}", json=dict(self.update_payload(item), skills=["SQL", "Python"]), headers=self.headers).get_json()["evidence"]
        self.client.patch(f"/api/evidence/{item['id']}/archive", json={"version": edited["version"], "archived": True}, headers=self.headers)
        self.assertEqual(self.client.get(path, headers=self.headers).get_json()["attempt"], attempt)
        self.assertEqual(self.client.get(roadmap_path, headers=self.headers).get_json()["roadmap"], roadmap)
        skills = self.client.get("/api/skills", headers=self.headers).get_json()["skills"]
        self.assertEqual([(skill["skill_name"], skill["proficiency"]) for skill in skills], [("SQL", 7)])


if __name__ == "__main__":
    unittest.main()
