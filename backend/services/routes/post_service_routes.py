from json import tool
from flask import Blueprint, request, jsonify, current_app

post_bp = Blueprint("post_bp", __name__)




@post_bp.route("/posts", methods=["POST"])
def create_post():
    print("Petición de creación de post recibida")
    tools = current_app.config["tools"]

    data = request.get_json()
    content = data.get("content")
    user_id = data.get("user_id")

    if not content or not user_id:
        return jsonify({"error": "Faltan campos"}), 400

    try:
        payload = {
            "content": content,
            "user_id": user_id
        }

        # Enviamos la petición de creación al cluster (vía helper con reintento)
        res = tools.call_cluster("POST", "/db/posts", json=payload)
        print(f"Post creado con éxito para el usuario {user_id}")
        return jsonify({
                        "message": "Post creado correctamente", 
                        "post_id": res.json().get("id")}), 201
        
    except Exception as e:
        return jsonify({"error": "Error al crear post", "details": str(e)}), 500
    

@post_bp.route("/posts", methods=["GET"])
def list_posts():

    tools = current_app.config["tools"]

    res= tools.call_cluster("GET", "/db/posts")
    print(res)
    data= res.json()
    for post in data:
        user_id= post["user_id"]
        user= tools.call_cluster("GET", f"/db/users/{user_id}").json() 
        post["UserName"]= user["username"]
        
    return jsonify(data), res.status_code


@post_bp.route("/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    
    tools = current_app.config["tools"]

    res= tools.call_cluster("GET", f"/db/posts/{post_id}")
    return jsonify(res.json()), res.status_code
   

@post_bp.route("/posts/user/<int:user_id>", methods=["GET"])
def get_user_posts(user_id):
    
    tools = current_app.config["tools"]

    res= tools.call_cluster("GET", f"/db/posts/user/{user_id}")
    return jsonify(res.json()), res.status_code
   
   
@post_bp.route("/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    
    tools = current_app.config["tools"]
    data = request.get_json()

    payload = {}
    if "content" in data:
        payload["content"] = data["content"]
        
    if not payload:
        return jsonify({"error": "No hay campos para actualizar"}), 400

    res = tools.call_cluster("PUT", f"/db/posts/{post_id}", json=payload)
    
    return jsonify(res.json()), res.status_code
    

@post_bp.route("/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    
    tools = current_app.config["tools"]

    res = tools.call_cluster("DELETE", f"/db/posts/{post_id}")
    return jsonify(res.json()), res.status_code
