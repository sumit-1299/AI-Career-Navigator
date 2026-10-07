#!/usr/bin/env python3
"""
AI Career Navigator — Production Deployment Smoke Test Suite
============================================================
Automated end-to-end verification script for multi-container production deployments.
Validates:
  1. Frontend SPA serving and client-side route fallbacks (Nginx).
  2. Backend health and database connectivity probe (/api/health).
  3. Authentication lifecycle (Registration -> Login -> JWT issuance).
  4. Core business API routes (Careers, Pathways, Compare, Simulator, Learning).
  5. Negative security and boundary conditions (401 Unauthorized, 404 Not Found).

Usage:
  python scripts/production_smoke_test.py [--url http://localhost] [--verbose]
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEFAULT_BASE_URL = os.getenv("BASE_URL", "http://localhost")


class SmokeTestRunner:
    def __init__(self, base_url: str, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.jwt_token = None
        self.test_user_id = None

    def _log(self, msg: str):
        print(msg)

    def _debug(self, msg: str):
        if self.verbose:
            print(f"    [DEBUG] {msg}")

    def request(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict = None,
        token: str = None,
        expected_status: int = 200,
    ):
        url = f"{self.base_url}{endpoint}"
        headers = {"Accept": "application/json"}

        encoded_data = None
        if data is not None:
            encoded_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(
            url, data=encoded_data, headers=headers, method=method
        )
        self._debug(f"{method} {url}")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.getcode()
                body_bytes = resp.read()
                content_type = resp.headers.get("Content-Type", "")

                try:
                    body = json.loads(body_bytes.decode("utf-8"))
                except Exception:
                    body = body_bytes.decode("utf-8", errors="replace")

                return status, body, content_type

        except urllib.error.HTTPError as e:
            status = e.code
            body_bytes = e.read()
            content_type = e.headers.get("Content-Type", "")
            try:
                body = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                body = body_bytes.decode("utf-8", errors="replace")
            return status, body, content_type

        except Exception as e:
            return 0, str(e), ""

    def run_test(
        self,
        name: str,
        endpoint: str,
        method: str = "GET",
        data: dict = None,
        token: str = None,
        expected_status: int = 200,
        validate_fn=None,
    ) -> bool:
        status, body, content_type = self.request(
            endpoint=endpoint,
            method=method,
            data=data,
            token=token,
            expected_status=expected_status,
        )

        success = (status == expected_status)
        extra_err = ""

        if success and validate_fn:
            try:
                val_ok, msg = validate_fn(body)
                if not val_ok:
                    success = False
                    extra_err = f" (Validation failed: {msg})"
            except Exception as e:
                success = False
                extra_err = f" (Validator exception: {e})"

        if success:
            self._log(f"  [PASS] {name} (HTTP {status})")
            self.passed += 1
            return True
        else:
            self._log(f"  [FAIL] {name} -> Expected HTTP {expected_status}, got {status}{extra_err}")
            if self.verbose or not success:
                self._debug(f"Response: {body}")
            self.failed += 1
            return False

    def test_frontend_spa(self):
        self._log("\n--- Category 1: Frontend SPA & Nginx Routing ---")

        def check_spa_root(body):
            if isinstance(body, str) and '<div id="root">' in body:
                return True, ""
            return False, 'Missing <div id="root"> element'

        self.run_test(
            name="Root Landing Page (index.html)",
            endpoint="/",
            expected_status=200,
            validate_fn=check_spa_root,
        )

        spa_routes = [
            "/careers",
            "/compare",
            "/simulator",
            "/analytics",
            "/learning",
            "/skills",
            "/resume",
            "/profile",
            "/login",
            "/register",
        ]
        for route in spa_routes:
            self.run_test(
                name=f"SPA Route Fallback: {route}",
                endpoint=route,
                expected_status=200,
                validate_fn=check_spa_root,
            )

    def test_health_check(self):
        self._log("\n--- Category 2: Backend Health & Database Connectivity ---")

        def check_health(body):
            if not isinstance(body, dict):
                return False, "Non-dict JSON payload"
            if body.get("status") != "healthy":
                return False, f"Expected status 'healthy', got '{body.get('status')}'"
            if body.get("database") != "connected":
                return False, f"Expected database 'connected', got '{body.get('database')}'"
            return True, ""

        self.run_test(
            name="Health Endpoint (/api/health)",
            endpoint="/api/health",
            expected_status=200,
            validate_fn=check_health,
        )

    def test_authentication(self):
        self._log("\n--- Category 3: User Authentication Lifecycle ---")

        unique_id = uuid.uuid4().hex[:8]
        test_email = f"smoketest_{unique_id}@example.com"
        test_password = "SmokeTestPassword123!"
        test_name = f"Smoke Test User {unique_id}"

        # 1. Registration
        def validate_registration(body):
            if isinstance(body, dict) and body.get("status") == "success":
                user_data = body.get("user", {})
                self.test_user_id = user_data.get("id")
                return True, ""
            return False, f"Unexpected body structure: {body}"

        reg_ok = self.run_test(
            name="User Registration (POST /api/register)",
            endpoint="/api/register",
            method="POST",
            data={
                "name": test_name,
                "email": test_email,
                "password": test_password,
            },
            expected_status=201,
            validate_fn=validate_registration,
        )

        if not reg_ok:
            self._log("  [WARN] Skipping login and authenticated tests due to registration failure.")
            return

        # 2. Login & Token acquisition
        def validate_login(body):
            if isinstance(body, dict) and "access_token" in body:
                self.jwt_token = body["access_token"]
                return True, ""
            return False, "Missing access_token in response"

        self.run_test(
            name="User Login (POST /api/login)",
            endpoint="/api/login",
            method="POST",
            data={
                "email": test_email,
                "password": test_password,
            },
            expected_status=200,
            validate_fn=validate_login,
        )

    def test_authenticated_endpoints(self):
        self._log("\n--- Category 4: Authenticated User Operations ---")
        if not self.jwt_token:
            self._log("  [SKIP] Skipping authenticated tests (no valid token)")
            return

        # Recommendations
        def validate_recs(body):
            if isinstance(body, dict) and "recommendations" in body:
                return True, ""
            return False, "Missing 'recommendations' list"

        self.run_test(
            name="Career Recommendations (GET /api/careers/recommendations)",
            endpoint="/api/careers/recommendations",
            token=self.jwt_token,
            expected_status=200,
            validate_fn=validate_recs,
        )

        # Profile
        def validate_profile(body):
            if isinstance(body, dict) and "profile" in body:
                return True, ""
            return False, "Missing 'profile' object"

        self.run_test(
            name="Student Profile (GET /api/profile)",
            endpoint="/api/profile",
            token=self.jwt_token,
            expected_status=200,
            validate_fn=validate_profile,
        )

        # Skills
        def validate_skills(body):
            if isinstance(body, dict) and "skills" in body:
                return True, ""
            return False, "Missing 'skills' array"

        self.run_test(
            name="Student Skills (GET /api/skills)",
            endpoint="/api/skills",
            token=self.jwt_token,
            expected_status=200,
            validate_fn=validate_skills,
        )

    def test_core_career_features(self):
        self._log("\n--- Category 5: Career Intelligence & Simulation ---")

        # Careers Catalog
        def validate_careers(body):
            if isinstance(body, dict) and isinstance(body.get("careers"), list) and len(body["careers"]) > 0:
                return True, ""
            return False, "Empty or missing 'careers' list"

        self.run_test(
            name="Careers Catalog (GET /api/careers)",
            endpoint="/api/careers",
            expected_status=200,
            validate_fn=validate_careers,
        )

        # Career Detail
        def validate_career_detail(body):
            if isinstance(body, dict) and body.get("career", {}).get("id") == 1:
                return True, ""
            return False, f"Expected body['career']['id'] == 1, got {body}"

        self.run_test(
            name="Career Detail (GET /api/careers/1)",
            endpoint="/api/careers/1",
            expected_status=200,
            validate_fn=validate_career_detail,
        )

        # Career Pathways Tree (Module 9.3)
        def validate_pathway(body):
            if isinstance(body, dict) and body.get("status") == "success" and "pathways" in body:
                return True, ""
            return False, f"Missing 'pathways' in response: {list(body.keys()) if isinstance(body, dict) else body}"

        self.run_test(
            name="Career Pathways Tree (GET /api/careers/1/pathways)",
            endpoint="/api/careers/1/pathways",
            token=self.jwt_token,
            expected_status=200,
            validate_fn=validate_pathway,
        )

        # Dual Career Comparison (Module 9.2)
        def validate_compare(body):
            if isinstance(body, dict) and body.get("status") == "success" and "comparison" in body:
                return True, ""
            return False, "Missing 'comparison' in response"

        self.run_test(
            name="Dual Career Comparison (POST /api/careers/compare)",
            endpoint="/api/careers/compare",
            method="POST",
            data={"career_a_id": 1, "career_b_id": 2},
            token=self.jwt_token,
            expected_status=200,
            validate_fn=validate_compare,
        )

        # What-If Skill Simulator (Module 9.4)
        def validate_simulator(body):
            if isinstance(body, dict) and body.get("status") == "success" and "simulation" in body:
                return True, ""
            return False, "Missing 'simulation' object in response"

        self.run_test(
            name="What-If Skill Simulator (POST /api/careers/1/simulate-skill)",
            endpoint="/api/careers/1/simulate-skill",
            method="POST",
            data={"skill_id": 1, "simulated_level": 4},
            token=self.jwt_token,
            expected_status=200,
            validate_fn=validate_simulator,
        )

        # Learning Resources Catalog (Module 8)
        def validate_learning_resources(body):
            if isinstance(body, dict) and body.get("status") == "success" and "resources" in body:
                return True, ""
            return False, "Missing 'resources' in response"

        self.run_test(
            name="Learning Resources (GET /api/learning-resources)",
            endpoint="/api/learning-resources",
            expected_status=200,
            validate_fn=validate_learning_resources,
        )

    def test_security_and_boundaries(self):
        self._log("\n--- Category 6: Security & Boundary Verification ---")

        # 401 Unauthorized check
        self.run_test(
            name="Protected Route Rejection (POST /api/skills without auth)",
            endpoint="/api/skills",
            method="POST",
            data={"skill_name": "Unauthorized Test"},
            expected_status=401,
        )

        # Nonexistent route check (Flask OPTIONS wildcard returns 405 Method Not Allowed for unmatched GET routes)
        status, body, _ = self.request(endpoint="/api/nonexistent-route-check", method="GET")
        if status in (404, 405):
            self._log(f"  [PASS] Nonexistent Route Rejection (/api/nonexistent-route-check) (HTTP {status})")
            self.passed += 1
        else:
            self._log(f"  [FAIL] Nonexistent Route Rejection -> Expected HTTP 404 or 405, got {status}")
            self.failed += 1

    def run_all(self) -> bool:
        start_time = time.time()
        self._log("=" * 70)
        self._log(f"AI CAREER NAVIGATOR — PRODUCTION DEPLOYMENT SMOKE TEST SUITE")
        self._log(f"Target Base URL: {self.base_url}")
        self._log("=" * 70)

        self.test_frontend_spa()
        self.test_health_check()
        self.test_authentication()
        self.test_authenticated_endpoints()
        self.test_core_career_features()
        self.test_security_and_boundaries()

        duration = time.time() - start_time
        total_tests = self.passed + self.failed

        self._log("\n" + "=" * 70)
        self._log("SMOKE TEST SUMMARY")
        self._log("=" * 70)
        self._log(f"Total Tests Executed : {total_tests}")
        self._log(f"Total Passed         : {self.passed}")
        self._log(f"Total Failed         : {self.failed}")
        self._log(f"Duration             : {duration:.2f}s")

        if self.failed == 0:
            self._log("RESULT: ALL PRODUCTION SMOKE TESTS PASSED [100% OK]")
            self._log("=" * 70)
            return True
        else:
            self._log(f"RESULT: {self.failed} TEST(S) FAILED")
            self._log("=" * 70)
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Run production deployment smoke tests for AI Career Navigator"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL of deployment (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output with request/response debugging",
    )
    args = parser.parse_args()

    runner = SmokeTestRunner(base_url=args.url, verbose=args.verbose)
    success = runner.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
