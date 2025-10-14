
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from models import db, User


auth_bp=Blueprint("auth_db",__name__)


#  Registrar usuario
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan campos"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Usuario ya existe"}), 409

    hashed = generate_password_hash(password)
    user = User(username=username, password_hash=hashed)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Usuario registrado correctamente"}), 201

#  Login 
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()}), 200

# Listar usuarios (requiere token)
@auth_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    current_user = get_jwt_identity()
    users = User.query.all()
    return jsonify({
        "current_user": current_user,
        "users": [{"id": u.id, "username": u.username} for u in users]
    }), 200


