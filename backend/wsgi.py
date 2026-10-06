"""
WSGI production entrypoint for AI Career Navigator.
Exposes the Flask application instance for Gunicorn.
"""

from app import app

if __name__ == "__main__":
    app.run()
