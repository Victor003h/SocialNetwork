from datetime import datetime
import threading
import time
from flask import Flask, jsonify, redirect, request
from psycopg2 import Timestamp
from requests import RequestException
import os 
import requests
from sqlalchemy import create_engine, false, select


from Failure_Detector import FailureDetector
from HeartbeatSender import HeartbeatSender

from models.wal import WALLog
from models.user import User
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
        print("[ELECTION] election request received")

        # responder INMEDIATO
        response = {"status": "ok"}

        # iniciar elección en background
        threading.Thread(
            target=cluster.start_election,
            daemon=True
        ).start()

        return response, 200

    
    @app.route("/leader", methods=["POST"])
    def leader_announcement():
        data=request.json
        cluster.set_leader(data["leader_id"]) # type: ignore
        cluster.local_node.set_role("follower")
        print(f"[LEADER] Leader set to {data['leader_id']}") # type: ignore
        return {"status": "ok"}
    
    @app.route("/heartbeat", methods=["POST"])
    def heartbeat():
        cluster.last_heartbeat = time.time()
        print("[HEARTBEAT] Received from leader")
        print(f"[HEARTBEAT] Last heartbeat {cluster.last_heartbeat}")

        return {"status": "ok"}
    

    @app.route("/newNode", methods=["POST"])
    def NewNode():
        data=request.get_json()

        peer = Node(
            node_id=data["node_id"],
            service_name=data["service_name"],
            port=5000,
        )
        if cluster.peers.__contains__(peer.node_id):
            cluster.peers[peer.node_id].alive=True
            print(f"[DISCOVERY] Node {peer.node_id} is back ")
            return {"status":"ok"}

        peer.host =data["host"]
        peer.address = f"{data['host']}:5000"
        peer.alive=data["alive"]
        peer.role=data["role"]
    
        cluster.peers[peer.node_id]=peer
        print(f"[DISCOVERY] Node {peer.node_id} discovered ")
        print(peer.host)
        
        print(peer.address)

        return {"status":"ok"}
    
    @app.route("/start_heartbeat", methods=["POST"])
    def StartHeartBeat():
        heartbead=HeartbeatSender(cluster)
        heartbead.start()
        return {"status":"ok"}
    
    @app.route("/db/users", methods=["POST"])
    def create_user():
        redirect= False          
        leader_address= cluster.peers[cluster.leader_id].address if (
                        cluster.leader_id in cluster.peers) else None
        
        if not cluster.local_node.is_leader():
            redirect=True
            requests.post(f"https://{leader_address}/db/users",json=request.json ,timeout=2,**cluster.secure_args)
            return jsonify({"msg":f"leader address: {leader_address}" }), 307
        if redirect:
            return jsonify({"msg":f"leader address: {leader_address}" }), 307
        
        lsn=cluster.next_lsn()
        data = request.json

        session=cluster.database.get_session()
        user_id=cluster.database.generate_user_id(session)
        user = User(
            username=data["username"],# type: ignore
            password_hash=data["password"], # type: ignore
            id=user_id
        )
        session.add(user) 
         
        wal=WALLog(
            wal_id=f"{cluster.local_node.node_id}:{lsn}",
            node_id=cluster.local_node.node_id,
            lsn=lsn,
            operation="INSERT",
            table_name="users",
            entity_id=str(user.id),
            payload=user.to_dict(),
            timestamp=datetime.now()
            )

       
         
        session.add(wal)
        session.commit()
        
        cluster.replicate_to_followers(wal)

        return jsonify({"id": user.id}), 201

    @app.route("/db/users", methods=["GET"])
    def list_users():
        redirect= False
        if not cluster.local_node.is_leader():
            leader_address=cluster.peers[cluster.leader_id].address # type: ignore
            redirect=True
            requests.get(f"http://{leader_address}/db/users" ,timeout=2)
            return jsonify({"msg":f"leader address: {leader_address}" }), 307
        if redirect:
            return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore




        session = cluster.database.get_session()
        try:
            users = session.query(User).all()
            return jsonify([u.to_dict() for u in users]), 200
        finally:
            session.close()

    @app.route("/db/users/<int:user_id>", methods=["PUT"])
    def update_user(user_id):
        # if not cluster.local_node.is_leader():
        #     leader_address = cluster.peers[cluster.leader_id].address
        #     return jsonify({
        #         "error": "not leader",
        #         "leader": leader_address
        #     }), 307

        redirect= False
        if not cluster.local_node.is_leader():
            leader_address=cluster.peers[cluster.leader_id].address # type: ignore
            redirect=True
            requests.put(f"http://{leader_address}/db/users/{user_id}",json=request.json ,timeout=2)
            return jsonify({"msg":f"leader address: {leader_address}" }), 307
        if redirect:
            return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore
        

        data = request.json
        session = cluster.database.get_session()


        try:
            user = session.get(User, user_id)
            if not user:
                return jsonify({"error": "user not found"}), 404

            if "username" in data: # type: ignore
                user.username = data["username"]   # type: ignore
            if "password" in data: # type: ignore
                user.password_hash = data["password"] # type: ignore

            lsn = cluster.next_lsn()


            wal=WALLog(
                wal_id=f"{cluster.local_node.node_id}:{lsn}",
                node_id=cluster.local_node.node_id,
                lsn=lsn,
                operation="UPDATE",
                table_name="users",
                entity_id=str(user.id),
                payload=user.to_dict(),
                timestamp=datetime.now()
            )

            session.add(wal)
            session.commit()

            cluster.replicate_to_followers(wal)

            return jsonify({"status": "updated"}), 200

        finally:
            session.close()

    @app.route("/db/users/<int:user_id>", methods=["DELETE"])
    def delete_user(user_id):
        # if not cluster.local_node.is_leader():
        #     leader_address = cluster.peers[cluster.leader_id].address
        #     return jsonify({
        #         "error": "not leader",
        #         "leader": leader_address
        #     }), 307

        redirect= False
        if not cluster.local_node.is_leader():
            leader_address=cluster.peers[cluster.leader_id].address # type: ignore
            redirect=True
            requests.delete(f"http://{leader_address}/db/users/{user_id}" ,timeout=2)
            return jsonify({"msg":f"leader address: {leader_address}" }), 307
        if redirect:
            return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore
        

        

        session = cluster.database.get_session()

        try:
            user = session.get(User, user_id)
            if not user:
                print("user with id :{user_id} not found")
                return jsonify({"error": f"user with id :{user_id} not found"}), 404

            lsn = cluster.next_lsn()

            wal=WALLog(
            wal_id=f"{cluster.local_node.node_id}:{lsn}",
            node_id=cluster.local_node.node_id,
            lsn=lsn,
            operation="DELETE",
            table_name="users",
            entity_id=str(user.id),
            payload=user.to_dict(),
            timestamp=datetime.now()
            )


            session.delete(user)
            session.add(wal)
            session.commit()

            cluster.replicate_to_followers(wal)

            return jsonify({"status": "deleted"}), 200

        finally:
            session.close()

    @app.route("/replicate", methods=["POST"])
    def replicate():
        msg = request.json
        lsn = msg["lsn"] # type: ignore

        # Idempotencia
        if lsn <= cluster.last_applied_lsn:
            return {"status": "ignored"}, 200

        session = cluster.database.get_session()

        try:

            # wal = WALLog(
            #     lsn=msg["lsn"],
            #     operation=msg["operation"],
            #     table_name=msg["table"],
            #     payload=msg["payload"]
            # )
            wal = WALLog(**msg) # type: ignore
            session.add(wal)

 
            cluster.apply_operation(msg)

            session.commit()

            cluster.last_applied_lsn = lsn

            return {"status": "ok"}, 200

        except Exception as e:
            session.rollback()
            print(f"[REPLICATE] Error applying WAL {lsn}: {e}")
            return {"error": "replication failed"}, 500

        finally:
            session.close()


    @app.route("/sync", methods=["POST"])
    def sync():
        req = request.json
        from_lsn = req["last_lsn"] # type: ignore
        session= cluster.database.get_session()
        
        try:
            stmt = (
                select(WALLog)
                .where(WALLog.lsn > from_lsn)
                .order_by(WALLog.lsn)
                
            )

            logs = session.execute(stmt).scalars().all()

            return jsonify([log.to_dict() for log in logs]), 200

        finally:
            session.close()    

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

    ssl_context = (cluster.cert_path, cluster.key_path)
    
    app.run(host="0.0.0.0", port=port,ssl_context=ssl_context)


if __name__ == "__main__":
    main()
    