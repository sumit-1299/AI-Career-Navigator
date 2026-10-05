from flask import Flask
from extensions import db
from config import Config
from flask_jwt_extended import JWTManager

from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.career_preferences import career_preferences_bp
from routes.skills import skills_bp
from routes.careers import careers_bp
from routes.learning_resources import learning_resources_bp
from routes.career_market import career_market_bp
from services.learning_resource_service import LearningResourceService


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    JWTManager(app)

    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(career_preferences_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(careers_bp)
    app.register_blueprint(learning_resources_bp)
    app.register_blueprint(career_market_bp)

    @app.after_request
    def add_cors_headers(response):
        """Add global CORS headers to all responses."""
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
    @app.route("/<path:path>", methods=["OPTIONS"])
    def handle_options_preflight(path):
        """Handle OPTIONS preflight requests gracefully."""
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response, 200

    with app.app_context():
        import models
        db.create_all()
        try:
            LearningResourceService.seed_curated_sample_resources()
        except Exception:
            pass

    @app.route("/")
    def home():
        return {"message": "AI Career Navigator API is running!"}

    @app.route("/db-test")
    def db_test():
        try:
            db.session.execute(db.text("SELECT 1"))
            return {"status": "success", "message": "PostgreSQL connection successful!"}
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
