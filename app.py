from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import User,Message
from flask_sqlalchemy import SQLAlchemy
from db import db
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)

# data base confg
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "redsocial")

app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "secret-key-flask"


jwt = JWTManager(app)

db.init_app(app)

# Crear tablas automáticamente
@app.before_request
def create_tables():
    db.create_all()

#  Registrar usuario
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan campos"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Usuario ya existe"}), 409

    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password_hash=hashed)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Usuario registrado correctamente"}), 201

#  Login 
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()}), 200

# 👥 Listar usuarios (requiere token)
@app.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    current_user = get_jwt_identity()
    users = User.query.all()
    return jsonify({
        "current_user": current_user,
        "users": [{"id": u.id, "username": u.username} for u in users]
    }), 200


# ===============================
# CRUD de Mensajes
# ===============================

# Crear mensaje
@app.route("/messages", methods=["POST"])
@jwt_required()
def create_message():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    content = data.get("content")

    if not content:
        return jsonify({"error": "El contenido del mensaje es requerido"}), 400

    user = User.query.get(current_user_id)
    message = Message(content=content, user=user)
    db.session.add(message)
    db.session.commit()
    return jsonify(message.to_dict()), 201

# Listar todos los mensajes
@app.route("/messages", methods=["GET"])
@jwt_required()
def get_messages():
    messages = Message.query.all()
    return jsonify([m.to_dict() for m in messages])

# Obtener mensaje por ID
@app.route("/messages/<int:message_id>", methods=["GET"])
@jwt_required()
def get_message(message_id):
    message = Message.query.get(message_id)
    if not message:
        return jsonify({"error": "Mensaje no encontrado"}), 404
    return jsonify(message.to_dict())

# Actualizar mensaje 
@app.route("/messages/<int:message_id>", methods=["PUT"])
@jwt_required()
def update_message(message_id):
    current_user_id = get_jwt_identity()
    message = Message.query.get(message_id)
    if not message:
        return jsonify({"error": "Mensaje no encontrado"}), 404

    if str(message.user_id) != current_user_id:
        return jsonify({"error": "No tienes permiso para actualizar este mensaje"}), 403

    data = request.get_json()
    message.content = data.get("content", message.content)
    db.session.commit()
    return jsonify(message.to_dict())

# Eliminar mensaje 
@app.route("/messages/<int:message_id>", methods=["DELETE"])
@jwt_required()
def delete_message(message_id):
    current_user_id = get_jwt_identity()
    message = Message.query.get(message_id)
    if not message:
        return jsonify({"error": "Mensaje no encontrado"}), 404

    if str(message.user_id) != current_user_id:
        return jsonify({"error": "No tienes permiso para eliminar este mensaje"}), 403

    db.session.delete(message)
    db.session.commit()
    return jsonify({"message": "Mensaje eliminado"}), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000
    )



