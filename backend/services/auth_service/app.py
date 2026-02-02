from flask import Flask,request,jsonify
import requests
from model import User
from db_config import db,DB_HOST,DB_NAME,DB_PASSWORD,DB_PORT,DB_USER
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime
import jwt
import os


app = Flask(__name__)



# app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5433/{DB_NAME}"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# db.init_app(app)
bcrypt = Bcrypt(app)

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretkey")

DB_CLUSTER_URL="http://cluster_net_serv:5000"


@app.route("/conected",methods=["GET"])
def conected():
    res = requests.get(
    f"{DB_CLUSTER_URL}/info", timeout=3)
    
    res.raise_for_status()
    return res.json()


@app.route("/create-user",methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    res = requests.post(
        f"{DB_CLUSTER_URL}/db/users",
        json={
            "username": username,
            "password": bcrypt.generate_password_hash(password).decode("utf-8")
        },
        timeout=3
    )
    res.raise_for_status()
    return res.json()



@app.route("/check",methods=["GET"])
def check():
    return jsonify({"message": "todo bien"}), 201

#  Registrar usuario
@app.route("/register", methods=["POST"])
def register():
    print(DB_PORT)
    print(DB_HOST)
    print(DB_NAME)
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

    token = jwt.encode({
        "user_id": user.id,
        "username": user.username,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48)
    }, JWT_SECRET, algorithm="HS256")
    
    return jsonify({"access_token": token, "user": user.to_dict()}), 200



@app.route("/")
def index():
    return {"msg": " Auth Service running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
