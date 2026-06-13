import os
import time
import threading

from flask import Flask

from Failure_Detector import FailureDetector
from HeartbeatSender import HeartbeatSender


from routes.post_routes import post_bp
from routes.user_routes import user_bp
from routes.node_routes import node_bp
from routes.follow_routes import followes_bp

from node import Node

from cluster import ClusterContext

from models.wal import WALLog
from models.user import User
from models.post import Post
from models.follows import Follower


def create_app(cluster: ClusterContext) -> Flask:
    """
    Crea la app Flask que expone endpoints de control del nodo.
    (no endpoints de negocio)
    """
    app = Flask(__name__)
    
    app.config["cluster"] = cluster
    app.config["WALLog"] = WALLog
    app.config["User"] = User
    app.config["Post"] = Post
    app.config["Follower"] = Follower
    
    app.register_blueprint(post_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(node_bp)
    app.register_blueprint(followes_bp)
    
    return app


def main():
    print("=== Starting DB Cluster Node ===")


    # -------------------------
    # 1. Identidad del nodo
    # -------------------------
    local_node = Node.from_env()
    print(f"[INIT] Local node created: {local_node}")

    # -------------------------
    # 2. Inicializar contexto de cluster
    # -------------------------
    cluster = ClusterContext(local_node)
   # cluster.database.create_tables()
    print("[INIT] ClusterContext initialized")

    # -------------------------
    # 3. Descubrimiento inicial de nodos (con reintentos)
    # -------------------------
    # Arranques simultáneos: si descubrimos antes de que los hermanos se hayan
    # registrado en DNS, peers queda vacío y el nodo se auto-promueve a subleader
    # (multi-líder transitorio). Reintentar da tiempo a que el cluster converja:
    # basta con que un peer sea visible para no auto-promoverse a ciegas.
    print("[DISCOVERY] Discovering peers...")
    discovery_retries = int(os.getenv("DISCOVERY_RETRIES", "5"))
    for attempt in range(discovery_retries):
        cluster.discover_peers()
        if len(cluster.peers) > 0:
            break
        print(f"[DISCOVERY] intento {attempt + 1}/{discovery_retries}: sin peers todavía, reintentando...")
        time.sleep(2)

    print(f"[DISCOVERY] Peers found: {len(cluster.peers)}")
    for peer in cluster.get_peers():
        print(f"  - Peer: {peer.address}")


    print("[DISCOVERY] Notifying my existence")
    cluster.Notify_existence(cluster.get_peers())



    # -------------------------
    # 4. Nodo listo 
    # -------------------------
    print("[READY] Node ready for subleader election")
    print(cluster)


    if  len(cluster.peers)==0:
        print(" subleader not found")
        cluster.local_node.set_role("subleader")
        cluster.set_subleader(cluster.local_node.node_id)
          
    else:
        print(f"Found subleader :{cluster.subleader_id}")


    if not cluster.local_node.is_subleader():
        cluster.sync_from_leader(cluster.peers)


    if(cluster.local_node.is_subleader()):
        cluster.heartbeadSender.start()
        cluster.subleader_manager.become_subleader()
    else:
        cluster.faliuredetector.start()

    
    # -------------------------
    # 5. Arrancar servidor de control
    # -------------------------
    app = create_app(cluster)

    port = local_node.port
    print(f"[START] Control server running on port {port}")

    ssl_context = cluster.security.get_mtls_context()

    # Reconciliación de liderazgo post-bootstrap (Bully determinista). En un hilo
    # daemon que espera a que los servidores /info de los hermanos estén arriba y
    # luego colapsa cualquier multi-líder transitorio del arranque a un único
    # subleader (el de mayor node_id). Ver ClusterContext.ensure_single_leader.
    def _bootstrap_reconcile():
        time.sleep(int(os.getenv("BOOTSTRAP_DELAY", "5")))
        try:
            cluster.ensure_single_leader()
        except Exception as e:
            print(f"[BOOTSTRAP] reconciliación de liderazgo falló: {e}")

    threading.Thread(target=_bootstrap_reconcile, daemon=True).start()

    app.run(host="0.0.0.0", port=port,ssl_context=ssl_context)


if __name__ == "__main__":
    main()
    