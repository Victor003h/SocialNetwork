import datetime
import jwt
from flask import jsonify, Blueprint, request,current_app


auth_bp = Blueprint("auth_bp", __name__)




@auth_bp.route("/register", methods=["POST"])
def register():
    print("Petición de registro recibida")
    data = request.get_json()
    
    tools = current_app.config["tools"]
    bcrypt = current_app.config["bcrypt"]
    
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
@auth_bp.route("/login", methods=["POST"])
def login():
    
    tools = current_app.config["tools"]
    bcrypt = current_app.config["bcrypt"]
    JWT_SECRET = current_app.config["JWT_SECRET_KEY"]

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

@auth_bp.route("/check",methods=["GET"])
def check():
    return jsonify({"message": "todo bien"}), 201

