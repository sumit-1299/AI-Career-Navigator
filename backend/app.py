import os
from flask import Flask, request
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


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
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
        """Add CORS headers to responses based on configuration."""
        allowed_origins = app.config.get("CORS_ORIGINS", ["*"])
        origin = request.headers.get("Origin")

        if "*" in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"

        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

    @app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
    @app.route("/<path:path>", methods=["OPTIONS"])
    def handle_options_preflight(path):
        """Handle OPTIONS preflight requests gracefully."""
        response = app.make_default_options_response()
        allowed_origins = app.config.get("CORS_ORIGINS", ["*"])
        origin = request.headers.get("Origin")

        if "*" in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"

        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Max-Age"] = "86400"
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

    @app.route("/api/health")
    @app.route("/health")
    def health_check():
        """Standardized health check endpoint for container orchestrators and monitoring probes."""
        db_status = "connected"
        http_code = 200
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            http_code = 503

        return {
            "status": "healthy" if http_code == 200 else "degraded",
            "service": "ai-career-navigator",
            "environment": app.config.get("ENV", "production"),
            "database": db_status
        }, http_code

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
    debug_mode = app.config.get("DEBUG", False)
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
