"""
Unit tests for Phase 10 Module 10.1:
- Production configuration & environment hardening
- Health check endpoints (/api/health and /health)
- Dynamic CORS headers and preflight handling
- Analytics authorization tightening (IDOR prevention)
- Gunicorn dependency availability
"""

import os
import unittest
from app import create_app
from extensions import db
from config import Config, ProductionConfig, DevelopmentConfig
from flask_jwt_extended import create_access_token


class Phase10Module1TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_gunicorn_dependency_available(self):
        """Verify gunicorn package is installed and importable."""
        import gunicorn
        self.assertTrue(hasattr(gunicorn, "__version__"))

    def test_health_endpoints(self):
        """Verify /api/health and /health return 200 OK with database connectivity status."""
        for endpoint in ["/api/health", "/health"]:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, f"Failed for {endpoint}")
            data = response.get_json()
            self.assertEqual(data.get("status"), "healthy")
            self.assertEqual(data.get("service"), "ai-career-navigator")
            self.assertEqual(data.get("database"), "connected")
            self.assertIn("environment", data)

    def test_config_profiles(self):
        """Verify Config, ProductionConfig, and DevelopmentConfig behavior."""
        self.assertFalse(ProductionConfig.DEBUG)
        self.assertTrue(DevelopmentConfig.DEBUG)
        self.assertIsInstance(Config.CORS_ORIGINS, list)

    def test_cors_headers_and_preflight(self):
        """Verify CORS headers on standard requests and OPTIONS preflight."""
        # Standard GET
        resp = self.client.get("/api/health")
        self.assertIn("Access-Control-Allow-Origin", resp.headers)
        self.assertIn("Access-Control-Allow-Methods", resp.headers)

        # Preflight OPTIONS
        options_resp = self.client.options("/api/health")
        self.assertEqual(options_resp.status_code, 200)
        self.assertIn("Access-Control-Allow-Origin", options_resp.headers)
        self.assertIn("Access-Control-Allow-Headers", options_resp.headers)
        self.assertIn("Access-Control-Max-Age", options_resp.headers)

    def test_analytics_idor_prevention(self):
        """Verify IDOR prevention on /api/careers/<id>/analytics."""
        with self.app.app_context():
            token_user_1 = create_access_token(identity="1")
            headers_user_1 = {"Authorization": f"Bearer {token_user_1}"}

            # Authenticated user 1 requesting user 1's analytics -> allowed (200 or 404 if data not seeded, but NOT 403)
            resp_own = self.client.get("/api/careers/1/analytics?user_id=1", headers=headers_user_1)
            self.assertNotEqual(resp_own.status_code, 403)

            # Authenticated user 1 requesting user 2's analytics -> 403 Forbidden
            resp_spoofed = self.client.get("/api/careers/1/analytics?user_id=2", headers=headers_user_1)
            self.assertEqual(resp_spoofed.status_code, 403)
            data = resp_spoofed.get_json()
            self.assertIn("Forbidden", data.get("message", ""))


if __name__ == "__main__":
    unittest.main()
