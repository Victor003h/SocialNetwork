from flask import Flask, request, jsonify
import requests
import os
import jwt

app = Flask(__name__)

# URLs internas de los servicios
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:5001")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:5002")
POST_SERVICE_URL = os.getenv("POST_SERVICE_URL", "http://localhost:5003")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")

# ---------- Utils ----------
def validate_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        return None

# ---------- Auth ----------
@app.route("/auth/<path:path>", methods=["POST"])
def auth_proxy(path):
    try:
        print(f"{AUTH_SERVICE_URL}/{path}")
        resp = requests.post(
            f"{AUTH_SERVICE_URL}/{path}",
            json=request.get_json(),
            timeout=3
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException:
        return jsonify({"error": "Auth service unavailable"}), 503

# ---------- Protected routes ----------
@app.before_request
def check_auth():
    print(request.path)
    
    if request.path.startswith("/auth"):
        return

    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Missing token"}), 401

    token = token.replace("Bearer ", "")
    payload = validate_token(token)
    if not payload:
        return jsonify({"error": "Invalid token"}), 401

    request.user = payload

# ---------- Users ----------
@app.route("/users/<path:path>", methods=["GET", "POST"])
def users_proxy(path):
    try:
        resp = requests.request(
            method=request.method,
            url=f"{USER_SERVICE_URL}/{path}",
            headers=request.headers,
            json=request.get_json(),
            timeout=3
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException:
        return jsonify({"error": "User service unavailable"}), 503

# ---------- Posts ----------
@app.route("/posts/<path:path>", methods=["GET", "POST"])
def posts_proxy(path):
    try:
        resp = requests.request(
            method=request.method,
            url=f"{POST_SERVICE_URL}/{path}",
            headers=request.headers,
            json=request.get_json(),
            timeout=3
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException:
        return jsonify({"error": "Post service unavailable"}), 503


@app.route("/")
def index():
    return {"msg": "API Gateway running"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
