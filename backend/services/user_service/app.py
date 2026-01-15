from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from model import User, db




app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{db.DB_USER}:{db.DB_PASSWORD}@{db.DB_HOST}:5432/{db.DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)



@app.route("/")
def index():
    return {"msg": "Service running"}


@app.route("/create", methods=["POST"])
def create_user():
    data = request.get_json()
    user_id = data.get("id")
    username = data.get("username")

    exists = User.query.filter_by(id=user_id).first()
    if exists:
        return {"error": "Usuario ya existe"}, 400

    new_user = User(id=user_id, username=username, bio="")
    db.session.add(new_user)
    db.session.commit()

    return {"msg": "Usuario creado"}, 201


@app.route("/get/<int:user_id>")
def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return {"error": "Usuario no encontrado"}, 404

    return {
        "id": user.id,
        "username": user.username,
        "bio": user.bio
    }, 200


@app.route("/update/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    bio = data.get("bio")

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return {"error": "Usuario no existe"}, 404

    user.bio = bio
    db.session.commit()

    return {"msg": "Perfil actualizado", "bio": user.bio}


@app.route("/")
def index():
    return {"msg": "User Service activo"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)