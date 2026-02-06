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

def get_leader_address():
    db_cluster_alias=get_db_url()
    res = requests.get(
        f"{db_cluster_alias}/db/leader_address",
        timeout=3,
        **secure_args
    )
    address=res.json().get("leader_address")
    url=f"https://{address}"
    print (f"DB Leader Address: {url}")
    
    return url

DB_LEADER_ADDRESS = get_leader_address()

def call_cluster(method, endpoint, **kwargs):
    """
    Helper que realiza peticiones al cluster. 
    Si falla, intenta buscar al nuevo líder y reintenta la operación.
    """
    global DB_LEADER_ADDRESS
    
    # Fusionar los argumentos de seguridad
    request_kwargs = {**secure_args, **kwargs}

    try:
        if not DB_LEADER_ADDRESS:
            raise Exception("Dirección del líder no disponible")
            
        url = f"{DB_LEADER_ADDRESS}{endpoint}"
        print(f"[CLUSTER-CALL] {method} a {url}")
        res = requests.request(method, url, **request_kwargs)
        res.raise_for_status()
        return res
    except (requests.exceptions.RequestException, Exception) as e:
        print(f"[CLUSTER-CALL] Fallo con el líder {DB_LEADER_ADDRESS}: {e}")
        print("[CLUSTER-CALL] Reintentando descubrimiento de líder...")
        
        # Intentar refrescar la dirección
        new_address = get_leader_address()
        if new_address:
            DB_LEADER_ADDRESS = new_address
            url = f"{DB_LEADER_ADDRESS}{endpoint}"
            print(f"[CLUSTER-CALL] Reintentando {method} a {url}")
            res = requests.request(method, url, **request_kwargs)
            res.raise_for_status()
            return res
        else:
            raise Exception("No se pudo encontrar un líder disponible en el cluster.")
        
        

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
        res = call_cluster("POST", "/db/users", json=payload)
        print(f"Usuario {username} registrado con éxito en el cluster")
        return jsonify({"message": "Usuario registrado correctamente en el cluster"}), 201

    except Exception as e:
        return jsonify({"error": "Error al registrar usuario", "details": str(e)}), 500
    
    
     

@app.route("/conected",methods=["GET"])
def conected():
    res = requests.get(
    f"{DB_LEADER_ADDRESS}/info", timeout=3, **secure_args)
    
    res.raise_for_status()
    return res.json()

############################# esto debe de ir en servicio de usuario######### 
@app.route("/users", methods=["GET"])
def list_users():
    try:
        res = requests.get(
            f"{DB_LEADER_ADDRESS}/db/users",
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
            f"{DB_LEADER_ADDRESS}/db/users/{user_id}",
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
            f"{DB_LEADER_ADDRESS}/db/users/{user_id}",
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
            f"{DB_LEADER_ADDRESS}/db/users/{user_id}",
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

#  Login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    try:
        # Obtenemos los usuarios del cluster (vía helper con reintento)
        res = call_cluster("GET", "/db/users")
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

@app.route("/")
def index():
    return {"msg": " Auth Service running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001,ssl_context=(cert_path, key_path))
