import ssl
import time
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
    
    # /cluster: canal interno por el que el subleader se registra (push). No lleva
    # JWT (lo invoca un nodo del cluster, no el navegador) -> ruta pública.
    if request.path.startswith("/auth") or request.path.startswith("/cluster") \
       or request.path == "/" or request.method == "OPTIONS":
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

# --- Presencia en la web (efímera, en memoria del gateway) ---
# Mapa user_id -> last_seen (epoch). "Online" = visto dentro de PRESENCE_TTL.
PRESENCE_TTL = 30  # segundos
_presence = {}


@app.route("/presence/ping", methods=["POST"])
def presence_ping():
    """Heartbeat del navegador: marca al usuario autenticado como conectado."""
    user_id = getattr(request, "user", {}).get("user_id")
    if user_id is None:
        return jsonify({"error": "Missing user"}), 401
    _presence[user_id] = time.time()
    return jsonify({"ok": True}), 200


@app.route("/presence/online", methods=["GET"])
def presence_online():
    """Lista de user_id conectados (last_seen dentro de la ventana)."""
    now = time.time()
    online = [uid for uid, ts in list(_presence.items()) if now - ts <= PRESENCE_TTL]
    return jsonify({"online": online}), 200


@app.route("/cluster/status", methods=["GET"])
def cluster_status():
    """Observabilidad read-only del clúster: reenvía el cluster.to_dict() que
    publica el subleader vigente (endpoint /info de los nodos). Se usa en el
    panel admin de la web para ver nodos y roles, y reflejar el failover."""
    try:
        res = tools.call_cluster("GET", "/info")
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": "Clúster no disponible", "details": str(e)}), 503


@app.route("/cluster/subleader", methods=["POST"])
def register_subleader():
    """Push del cluster: el subleader vigente del grupo se anuncia y la api fija
    a quién dirigir todas sus peticiones. Se invoca en cada (re)elección de
    subleader (arranque y failover)."""
    data = request.get_json(silent=True) or {}
    if not data.get("address"):
        return jsonify({"error": "address requerido"}), 400
    tools.set_leader({"address": data.get("address"), "ip": data.get("ip")})
    return jsonify({"status": "ok"}), 200


@app.route("/")
def health():
    return {"status": "Monolithic API Gateway Online", "cluster_connected": True}

if __name__ == "__main__":
    
    
    CORS(app)
    
    app.run(host="0.0.0.0", port=7000,ssl_context=secure_args["cert"])