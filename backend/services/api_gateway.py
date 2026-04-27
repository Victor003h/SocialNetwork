import ssl
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os
import jwt

# Importar Blueprints (debes asegurarte de que los archivos se exporten como tales)
from services.routes.auth_service_routes import auth_bp
from services.routes.user_service_routes import user_bp
from services.routes.post_service_routes import post_bp
from services.routes.follows_service_routes import follow_bp

# Importar herramientas compartidas
from security.Cert_Manager import CertManager
from services.utils import utils

app = Flask(__name__)

# Configuración Global
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")

# Inicializar Seguridad para hablar con el Clúster
security = CertManager(cert_dir='certs')
secure_args = security.setupCerts()
ssl_context = security.get_mtls_context()
tools = utils(secure_args)
bcrypt = Bcrypt(app)

# Inyectar 'tools' y 'bcrypt' en la configuración de la app para que los Blueprints accedan
app.config['tools'] = tools
app.config['bcrypt'] = bcrypt
app.config["JWT_SECRET_KEY"]=JWT_SECRET_KEY
# --- Middleware de Autenticación Centralizado ---



@app.before_request
def check_auth():
    # Rutas públicas
    
    if request.path.startswith("/auth") or request.path == "/" or request.method == "OPTIONS":
        return
    print(f"DEBUG: Headers recibidos: {dict(request.headers)}")
    
    token = request.headers.get("Authorization")
    
    if not token:
        return jsonify({"error": "Missing token"}), 401

    try:
        token = token.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        request.user = payload #type: ignore
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

# --- Registro de Blueprints ---
# Ahora las peticiones van directo a la lógica que llama a la BD
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(user_bp)
app.register_blueprint(post_bp)
app.register_blueprint(follow_bp)

@app.route("/")
def health():
    return {"status": "Monolithic API Gateway Online", "cluster_connected": True}

if __name__ == "__main__":
    
    
    CORS(app)
    
    app.run(host="0.0.0.0", port=7000,ssl_context=secure_args["cert"])