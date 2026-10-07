import unittest

from flask import Flask
from flask_jwt_extended import JWTManager

from extensions import db
from models.user import User
from models.password_reset_token import PasswordResetToken
from routes.auth import auth_bp


class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY="test-secret",
        )
        db.init_app(self.app)
        JWTManager(self.app)
        self.app.register_blueprint(auth_bp)

        with self.app.app_context():
            db.create_all()

        self.client = self.app.test_client()
        self.client.post(
            "/api/register",
            json={
                "name": "Test User",
                "email": "TEST@EXAMPLE.COM",
                "password": "old-password",
            },
        )

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_forgot_password_returns_generic_response_for_unknown_email(self):
        response = self.client.post(
            "/api/forgot-password",
            json={"email": "missing@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("If an account exists", response.get_json()["message"])
        self.assertNotIn("debug_reset_url", response.get_json())

    def test_forgot_and_reset_password_flow(self):
        response = self.client.post(
            "/api/forgot-password",
            json={"email": "test@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("debug_reset_url", payload)

        reset_url = payload["debug_reset_url"]
        token = reset_url.split("reset_token=", 1)[1]

        reset_response = self.client.post(
            "/api/reset-password",
            json={"token": token, "password": "new-password"},
        )

        self.assertEqual(reset_response.status_code, 200)

        old_login = self.client.post(
            "/api/login",
            json={"email": "test@example.com", "password": "old-password"},
        )
        self.assertEqual(old_login.status_code, 401)

        new_login = self.client.post(
            "/api/login",
            json={"email": "test@example.com", "password": "new-password"},
        )
        self.assertEqual(new_login.status_code, 200)

        reuse_response = self.client.post(
            "/api/reset-password",
            json={"token": token, "password": "another-password"},
        )
        self.assertEqual(reuse_response.status_code, 400)

    def test_second_reset_request_invalidates_first_token(self):
        first = self.client.post(
            "/api/forgot-password",
            json={"email": "test@example.com"},
        ).get_json()
        second = self.client.post(
            "/api/forgot-password",
            json={"email": "test@example.com"},
        ).get_json()

        first_token = first["debug_reset_url"].split("reset_token=", 1)[1]
        second_token = second["debug_reset_url"].split("reset_token=", 1)[1]

        old_response = self.client.post(
            "/api/reset-password",
            json={"token": first_token, "password": "first-password"},
        )
        self.assertEqual(old_response.status_code, 400)

        current_response = self.client.post(
            "/api/reset-password",
            json={"token": second_token, "password": "second-password"},
        )
        self.assertEqual(current_response.status_code, 200)

    def test_password_policy_is_enforced(self):
        response = self.client.post(
            "/api/reset-password",
            json={"token": "not-a-token", "password": "123"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("at least 8", response.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
