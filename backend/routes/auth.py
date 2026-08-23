from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from extensions import db
from models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api")
@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return {
            "status": "error",
            "message": "Name, email and password are required"
        }, 400

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return {
            "status": "error",
            "message": "Email already registered"
        }, 409

    password_hash = generate_password_hash(password)

    user = User(
        name=name,
        email=email,
        password_hash=password_hash
    )

    db.session.add(user)
    db.session.commit()

    return {
        "status": "success",
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }, 201

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {
            "status": "error",
            "message": "Email and password are required"
        }, 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return {
            "status": "error",
            "message": "Invalid email or password"
        }, 401

    if not check_password_hash(user.password_hash, password):
        return {
            "status": "error",
            "message": "Invalid email or password"
        }, 401

    access_token = create_access_token(
        identity=str(user.id)
    )

    return {
        "status": "success",
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }, 200