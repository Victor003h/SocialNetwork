import requests

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

from model import User
from db_config import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER

from services.utils import utils
from security.Cert_Manager import CertManager

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

security = CertManager(cert_dir='certs')

secure_args = security.setupCerts()

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
tools = utils(secure_args)


@app.route("/users", methods=["GET"])
def list_users():
    
    res= tools.call_cluster("GET", "/db/users")
     
    return jsonify(res.json()), res.status_code


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    
    res= tools.call_cluster("GET", f"/db/users/{user_id}")
    return jsonify(res.json()), res.status_code
   

@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()

    payload = {}
    if "username" in data:
        payload["username"] = data["username"]
    if "password" in data:
        payload["password"] = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    if not payload:
        return jsonify({"error": "No hay campos para actualizar"}), 400

    res = tools.call_cluster("PUT", f"/db/users/{user_id}", json=payload)
    
    return jsonify(res.json()), res.status_code
    

@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    
    res = tools.call_cluster("DELETE", f"/db/users/{user_id}")
    return jsonify(res.json()), res.status_code
   

@app.route("/")
def index():
    return {"msg": "User Service activo"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)