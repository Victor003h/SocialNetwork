from flask import Flask,request,jsonify
from model import User, db
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime
import jwt
import os

app = Flask(__name__)



app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{db.DB_USER}:{db.DB_PASSWORD}@{db.DB_HOST}:5432/{db.DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretkey")


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
    if not user or not bcrypt.check_password_hash(user.password, password):
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
