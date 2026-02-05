from email.headerregistry import Address
import socket
import ssl
from flask import Flask,request,jsonify
from flask_cors import CORS
import requests
from model import User
from security.Cert_Manager import CertManager
from db_config import db,DB_HOST,DB_NAME,DB_PASSWORD,DB_PORT,DB_USER
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime
import jwt
import os


app = Flask(__name__)
CORS(app)

#app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5433/{DB_NAME}"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#db.init_app(app)
bcrypt = Bcrypt(app)

security = CertManager(cert_dir='certs')
        
(cert_path, key_path),ca_path = security.get_context()

# Diccionario para reutilizar en todos los requests.post/get
# Esto permite que el Auth Service hable HTTPS con el Cluster
secure_args = {
    "cert": (cert_path, key_path),
    "verify": ca_path
}

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretkey")


def get_db_url():
  _,_,addres= socket.gethostbyname_ex('cluster_net_serv')
  host,_,_ = socket.gethostbyaddr(addres[0])
  return f"https://{host}:5000"

DB_CLUSTER_URL= get_db_url()
    

@app.route("/conected",methods=["GET"])
def conected():
    res = requests.get(
    f"{DB_CLUSTER_URL}/info", timeout=3)
    
    res.raise_for_status()
    return res.json()


@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan campos"}), 400

    res = requests.post(
        f"{DB_CLUSTER_URL}/db/users",
        json={
            "username": username,
            "password": bcrypt.generate_password_hash(password).decode("utf-8")
        },
        timeout=3,
        **secure_args
    )
    res.raise_for_status()
    return res.json()

############################# esto debe de ir en servicio de usuario######### 
@app.route("/users", methods=["GET"])
def list_users():
    try:
        res = requests.get(
            f"{DB_CLUSTER_URL}/db/users",
            timeout=3,
            **secure_args
        )
        return jsonify(res.json()), res.status_code

    except requests.RequestException:
        return jsonify({"error": "DB cluster unavailable"}), 503


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        res = requests.get(
            f"{DB_CLUSTER_URL}/db/users/{user_id}",
            timeout=3,
            **secure_args
        )
        return jsonify(res.json()), res.status_code

    except requests.RequestException:
        return jsonify({"error": "DB cluster unavailable"}), 503


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()

    payload = {}
    if "username" in data:
        payload["username"] = data["username"]
    if "password" in data:
        payload["password"] = bcrypt.generate_password_hash(
            data["password"]
        ).decode("utf-8")

    if not payload:
        return jsonify({"error": "No hay campos para actualizar"}), 400

    try:
        res = requests.put(
            f"{DB_CLUSTER_URL}/db/users/{user_id}",
            json=payload,
            timeout=3,
            **secure_args
        )
        return jsonify(res.json()), res.status_code

    except requests.RequestException:
        return jsonify({"error": "DB cluster unavailable"}), 503


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        res = requests.delete(
            f"{DB_CLUSTER_URL}/db/users/{user_id}",
            timeout=3,
            **secure_args
        )
        return jsonify(res.json()), res.status_code

    except requests.RequestException:
        return jsonify({"error": "DB cluster unavailable"}), 503




#############################


@app.route("/check",methods=["GET"])
def check():
    return jsonify({"message": "todo bien"}), 201

#  Registrar usuario
# @app.route("/register", methods=["POST"])
# def register():

#     data = request.get_json()
#     username = data.get("username")
#     password = data.get("password")

#     if not username or not password:
#         return jsonify({"error": "Faltan campos"}), 400

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

############################# esto debe de ir en servicio de usuario######### 
@app.route("/users", methods=["GET"])
def list_users():
    try:
        res = requests.get(
            f"{DB_CLUSTER_URL}/db/users",
            timeout=3
        )
        return jsonify(res.json()), res.status_code

    except requests.RequestException:
        return jsonify({"error": "DB cluster unavailable"}), 503


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        res = requests.get(
            f"{DB_CLUSTER_URL}/db/users/{user_id}",
            timeout=3
        )
        return jsonify(res.json()), res.status_code

    except requests.RequestException:
        return jsonify({"error": "DB cluster unavailable"}), 503


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()

    payload = {}
    if "username" in data:
        payload["username"] = data["username"]
    if "password" in data:
        payload["password"] = bcrypt.generate_password_hash(
            data["password"]
        ).decode("utf-8")

    if not payload:
        return jsonify({"error": "No hay campos para actualizar"}), 400

    try:
        res = requests.put(
            f"{DB_CLUSTER_URL}/db/users/{user_id}",
            json=payload,
            timeout=3
        )
        return jsonify(res.json()), res.status_code

    except requests.RequestException:
        return jsonify({"error": "DB cluster unavailable"}), 503


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        res = requests.delete(
            f"{DB_CLUSTER_URL}/db/users/{user_id}",
            timeout=3
        )
        return jsonify(res.json()), res.status_code

    except requests.RequestException:
        return jsonify({"error": "DB cluster unavailable"}), 503




#############################


@app.route("/check",methods=["GET"])
def check():
    return jsonify({"message": "todo bien"}), 201

#  Registrar usuario
# @app.route("/register", methods=["POST"])
# def register():

#     data = request.get_json()
#     username = data.get("username")
#     password = data.get("password")

#     if not username or not password:
#         return jsonify({"error": "Faltan campos"}), 400

#     if User.query.filter_by(username=username).first():
#         return jsonify({"error": "Usuario ya existe"}), 409

#     hashed = bcrypt.generate_password_hash(password).decode("utf-8")
#     user = User(username=username, password_hash=hashed)
#     db.session.add(user)
#     db.session.commit()

#     return jsonify({"message": "Usuario registrado correctamente"}), 201

#  Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # 1. En lugar de User.query, pedimos el usuario al Cluster
    try:
        # Nota: Asumiendo que tu cluster tiene un endpoint para buscar por username
        # o puedes usar el listado de usuarios para validar.
        res = requests.get(
            f"{DB_CLUSTER_URL}/db/users", 
            timeout=3,
            **secure_args
        )
        res.raise_for_status()
        users = res.json()
        
        # 2. Buscamos al usuario manualmente en la respuesta del cluster
        user_data = next((u for u in users if u['username'] == username), None)

        if not user_data or not bcrypt.check_password_hash(user_data['password_hash'], password):
            return jsonify({"error": "Credenciales incorrectas"}), 401

        # 3. Generamos el token con los datos que nos dio el Cluster
        token = jwt.encode({
            "user_id": user_data['id'],
            "username": user_data['username'],
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48)
        }, JWT_SECRET, algorithm="HS256")
        print("Generated JWT:", token)
        return jsonify({"access_token": token, "user": user_data}), 200

    except Exception as e:
        return jsonify({"error": f"Error conectando al DB Cluster: {str(e)}"}), 500
    



@app.route("/")
def index():
    return {"msg": " Auth Service running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001,ssl_context=(cert_path, key_path))
