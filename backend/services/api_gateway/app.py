from flask import Flask, request, jsonify
import requests
import jwt
import os

app = Flask(__name__)

# Clave para verificar JWT (misma que en Auth Service )
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "supersecretkey")

# ---------------------------
# Helper para reenviar requests
# ---------------------------
def forward_request(service_url):
    try:
        if request.method == "GET":
            response = requests.get(service_url, params=request.args)
        elif request.method == "POST":
            response = requests.post(service_url, json=request.get_json())
        elif request.method == "PUT":
            response = requests.put(service_url, json=request.get_json())
        elif request.method == "DELETE":
            response = requests.delete(service_url, json=request.get_json())
        else:
            return jsonify({"error": "Método no soportado"}), 405

        return jsonify(response.json()), response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Servicio no disponible"}), 503


@app.route("/auth/<path:subpath>", methods=["POST"])
def route_auth(subpath):
    url = f"http://auth-service:5001/{subpath}"
    return forward_request(url)


# ---------------------------
# Middleware de validación JWT
# ---------------------------
def require_jwt():
    token = request.headers.get("Authorization")
    if not token:
        return None, jsonify({"error": "Falta token"}), 401

    try:
        decoded = jwt.decode(token.replace("Bearer ", ""), JWT_SECRET, algorithms=["HS256"])
        return decoded, None, None
    except jwt.exceptions.InvalidTokenError:
        return None, jsonify({"error": "Token inválido"}), 401


# ---------------------------
# Rutas protegidas por servicio
# ---------------------------

@app.route("/users/<path:subpath>", methods=["GET", "POST", "PUT"])
def route_users(subpath):
    _, err, code = require_jwt()
    if err:
        return err, code

    url = f"http://user-service:5002/{subpath}"
    return forward_request(url)


@app.route("/relations/<path:subpath>", methods=["GET", "POST"])
def route_relations(subpath):
    _, err, code = require_jwt()
    if err:
        return err, code

    url = f"http://relation-service:5003/{subpath}"
    return forward_request(url)


@app.route("/posts/<path:subpath>", methods=["GET", "POST", "PUT"])
def route_posts(subpath):
    _, err, code = require_jwt()
    if err:
        return err, code

    url = f"http://post-service:5004/{subpath}"
    return forward_request(url)


@app.route("/feed/<path:subpath>", methods=["GET"])
def route_feed(subpath):
    _, err, code = require_jwt()
    if err:
        return err, code

    url = f"http://feed-service:5005/{subpath}"
    return forward_request(url)


# ---------------------------
@app.route("/")
def index():
    return {"msg": "API Gateway activo"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
