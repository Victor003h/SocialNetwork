import requests
import datetime
import jwt
import os

from email.headerregistry import Address

from flask import Flask,request,jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


from security.Cert_Manager import CertManager
from db_config import db,DB_HOST,DB_NAME,DB_PASSWORD,DB_PORT,DB_USER
from services.utils import utils


app = Flask(__name__)
CORS(app)

#app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5433/{DB_NAME}"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#db.init_app(app)
bcrypt = Bcrypt(app)

security = CertManager(cert_dir='certs')
 
secure_args = security.setupCerts()

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretkey")

tools= utils(secure_args)

   
@app.route("/register", methods=["POST"])
def register():
    print("Petición de registro recibida")
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")


    if not username or not password:
        return jsonify({"error": "Faltan campos"}), 400

    try:
        # Encriptamos la contraseña antes de enviarla al cluster
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        print(f"Hashed password for {username}: {hashed_password}")
        payload = {
            "username": username,
            "password": hashed_password,
            "created_at": datetime.datetime.now().isoformat()
        }

        # Enviamos la petición de creación al cluster (vía helper con reintento)
        res = tools.call_cluster("POST", "/db/users", json=payload)
        print(f"Usuario {username} registrado con éxito en el cluster")
        return jsonify({"message": "Usuario registrado correctamente en el cluster"}), 201

    except Exception as e:
        return jsonify({"error": "Error al registrar usuario", "details": str(e)}), 500
    
#  Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    try:
        # Obtenemos los usuarios del cluster (vía helper con reintento)
        res = tools.call_cluster("GET", "/db/users")
        users = res.json()
        
        # Buscamos al usuario en la lista devuelta por el cluster
        user_data = next((u for u in users if u['username'] == username), None)

        if not user_data or not bcrypt.check_password_hash(user_data['password_hash'], password):
            return jsonify({"error": "Credenciales incorrectas"}), 401

        # Generación del JWT
        token = jwt.encode({
            "user_id": user_data.get('id'),
            "username": user_data['username'],
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48)
        }, JWT_SECRET, algorithm="HS256")
        
        return jsonify({
            "access_token": token, 
            "user": {
                "id": user_data.get('id'),
                "username": user_data['username']
            }
        }), 200

    except Exception as e:
        return jsonify({"error": "Error conectando al cluster", "details": str(e)}), 500

@app.route("/conected",methods=["GET"])
def conected():
    res = requests.get(
    f"{tools.db_leader_address}/info", timeout=3, **secure_args)
    
    res.raise_for_status()
    return res.json()

@app.route("/check",methods=["GET"])
def check():
    return jsonify({"message": "todo bien"}), 201

@app.route("/")
def index():
    return {"msg": " Auth Service running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001,ssl_context=secure_args["cert"])
