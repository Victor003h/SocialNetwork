import threading
import time
from flask import Flask, jsonify, request
from requests import RequestException


from Failure_Detector import FailureDetector
from HeartbeatSender import HeartbeatSender

from node import Node
from cluster import ClusterContext


def create_app(cluster: ClusterContext) -> Flask:
    """
    Crea la app Flask que expone endpoints de control del nodo.
    (no endpoints de negocio)
    """
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "node_id": cluster.local_node.node_id,
            "role": cluster.local_node.role
        })

    @app.route("/info", methods=["GET"])
    def info():
        return jsonify(cluster.to_dict()),200
    

    @app.route("/election", methods=["POST"])
    def election_request():
        cluster.start_election()
        return {"status": "ok"}
    
    @app.route("/leader", methods=["POST"])
    def leader_announcement():
        data=request.json
        cluster.set_leader(data["leader_id"])
        cluster.local_node.set_role("follower")
        print(f"[LEADER] Leader set to {data['leader_id']}")
        return {"status": "ok"}
    
    @app.route("/cluster/heartbeat", methods=["POST"])
    def heartbeat():
        cluster.last_heartbeat = time.time()
        return {"status": "ok"}
    
    @app.route("/newNode", methods=["POST"])
    def NewNode():
        data=request.get_json()

        peer = Node(
            node_id=data["node_id"],
            service_name=data["service_name"],
            port="5000",
        )
        peer.host =data["host"],
        peer.address = data["host"],
        peer.alive=data["alive"],
        peer.role=data["role"],
    
        cluster.peers[peer.node_id]=peer
        print(f"[DISCOVERY] Node {peer.node_id} discovered ")
        return {"status":"ok"}
    
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


    if not cluster.exists_leader():
        print(" Leader not found")
        cluster.start_election()
    else:
        print(f"Found Leader :{cluster.leader_id}")


    heartbead=HeartbeatSender(cluster)
    heartbead.start()

    failure_detector=FailureDetector(cluster)
    failure_detector.start()

    
    # -------------------------
    # 5. Arrancar servidor de control
    # -------------------------
    app = create_app(cluster)

    port = local_node.port
    print(f"[START] Control server running on port {port}")

    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
