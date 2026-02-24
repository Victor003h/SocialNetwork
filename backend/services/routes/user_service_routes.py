
from flask import Blueprint, request, jsonify, current_app

user_bp = Blueprint("user_bp", __name__)



@user_bp.route("/users", methods=["GET"])
def list_users():
    
    
    tools = current_app.config["tools"]
    res= tools.call_cluster("GET", "/db/users")
     
    return jsonify(res.json()), res.status_code


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    
    tools = current_app.config["tools"]
    res= tools.call_cluster("GET", f"/db/users/{user_id}")
    return jsonify(res.json()), res.status_code
   

@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    
    tools = current_app.config["tools"]
    bcrypt = current_app.config["bcrypt"]
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
    

@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    
    tools = current_app.config["tools"]
    res = tools.call_cluster("DELETE", f"/db/users/{user_id}")
    return jsonify(res.json()), res.status_code
   

