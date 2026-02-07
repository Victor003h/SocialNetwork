from flask import Flask
from Failure_Detector import FailureDetector
from HeartbeatSender import HeartbeatSender


from routes.post_routes import post_bp
from routes.user_routes import user_bp
from routes.node_routes import node_bp

from node import Node

from cluster import ClusterContext

from models.wal import WALLog
from models.user import User
from models.post import Post


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
    
    app.register_blueprint(post_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(node_bp)
    
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
    # 3. Descubrimiento inicial de nodos
    # -------------------------
    print("[DISCOVERY] Discovering peers...")
    cluster.discover_peers()

    print(f"[DISCOVERY] Peers found: {len(cluster.peers)}")
    for peer in cluster.get_peers():
        print(f"  - Peer: {peer.address}")


    print("[DISCOVERY] Notifying my existence")
    cluster.Notify_existence()



    # -------------------------
    # 4. Nodo listo 
    # -------------------------
    print("[READY] Node ready for leader election")
    print(cluster)


    if  len(cluster.peers)==0:
        print(" Leader not found")
        cluster.local_node.set_role("leader")
        cluster.set_leader(cluster.local_node.node_id)
        
    else:
        print(f"Found Leader :{cluster.leader_id}")


    if not cluster.local_node.is_leader():
        cluster.sync_from_leader()


    if(cluster.local_node.is_leader()):
        heartbead=HeartbeatSender(cluster)
        heartbead.start()
    else:
        failure_detector=FailureDetector(cluster)
        failure_detector.start()

    
    # -------------------------
    # 5. Arrancar servidor de control
    # -------------------------
    app = create_app(cluster)

    port = local_node.port
    print(f"[START] Control server running on port {port}")

    ssl_context = cluster.secure_args["cert"]
    
    app.run(host="0.0.0.0", port=port,ssl_context=ssl_context)


if __name__ == "__main__":
    main()
    