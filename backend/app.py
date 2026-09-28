from routes.skills import skills_bp

from flask import Flask, make_response, render_template
from extensions import db
from config import Config
from routes.auth import auth_bp
from flask_jwt_extended import JWTManager
from routes.profile import profile_bp
from routes.career_preferences import career_preferences_bp
from routes.assessments import assessments_bp
from routes.roadmaps import roadmaps_bp
from routes.evidence import evidence_bp
from routes.job_matches import job_matches_bp
from routes.jobs import jobs_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(career_preferences_bp)
    app.register_blueprint(skills_bp)
    app.config.from_object(Config)
    db.init_app(app)
    JWTManager(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(assessments_bp)
    app.register_blueprint(roadmaps_bp)
    app.register_blueprint(evidence_bp)
    app.register_blueprint(job_matches_bp)
    app.register_blueprint(jobs_bp)

    with app.app_context():
        from models.user import User
        from models.student_profile import StudentProfile
        db.create_all()

    @app.route("/")
    def home():
        return {
            "message": "AI Career Navigator API is running!"
        }

    @app.route("/db-test")
    def db_test():
        try:
            db.session.execute(db.text("SELECT 1"))

            return {
                "status": "success",
                "message": "PostgreSQL connection successful!"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }, 500

    @app.route("/app")
    def candidate_workspace():
        response = make_response(render_template("workspace.html"))
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
