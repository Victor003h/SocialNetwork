import threading
import time

from flask import Flask, jsonify, Blueprint, request,current_app
from sqlalchemy import select


from HeartbeatSender import HeartbeatSender
from node import Node

node_bp = Blueprint("node_bp", __name__)

@node_bp.route("/health", methods=["GET"])
def health():
    
    cluster= current_app.config["cluster"]
    return jsonify({
        "status": "ok",
        "node_id": cluster.local_node.node_id,
        "role": cluster.local_node.role
    })
    
    
@node_bp.route("/info", methods=["GET"])
def info():
    
    cluster= current_app.config["cluster"]
    return jsonify(cluster.to_dict()),200

@node_bp.route("/election", methods=["POST"])
def election_request():
    
    cluster= current_app.config["cluster"]
    print("[ELECTION] election request received")
    # responder INMEDIATO
    response = {"status": "ok"}
    # iniciar elección en background
    threading.Thread(
        target=cluster.start_election,
        daemon=True
    ).start()
    return response, 200

@node_bp.route("/db/leader_address", methods=["GET"])
def get_leader_address():
    
    cluster= current_app.config["cluster"]
    
    if cluster.leader_id :
        if cluster.leader_id==cluster.local_node.node_id:
            leader_address = cluster.local_node.address # type: ignore
        else:
            leader_address = cluster.peers[cluster.leader_id].address # type: ignore
        return jsonify({"leader_address": leader_address}), 200
    else:
        return jsonify({"error": "Leader not found"}), 404


@node_bp.route("/leader", methods=["POST"])
def leader_announcement():
    
    cluster= current_app.config["cluster"]
    
    data=request.json
    if not data: return {},400
    
    cluster.set_leader(data["leader_id"]) 
    cluster.local_node.set_role("follower")
    print(f"[LEADER] Leader set to {data['leader_id']}") 
    return {"status": "ok"}


@node_bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    
    cluster= current_app.config["cluster"]
    
    cluster.last_heartbeat = time.time()
    print("[HEARTBEAT] Received from leader")
    print(f"[HEARTBEAT] Last heartbeat {cluster.last_heartbeat}")
    return {"status": "ok"}


@node_bp.route("/newNode", methods=["POST"])
def NewNode():
    
    cluster= current_app.config["cluster"]
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


@node_bp.route("/start_heartbeat", methods=["POST"])
def StartHeartBeat():
    
    cluster= current_app.config["cluster"]
    
    heartbead=HeartbeatSender(cluster)
    heartbead.start()
    return {"status":"ok"}


@node_bp.route("/replicate", methods=["POST"])
def replicate():
    
    cluster= current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    msg = request.json
    if not msg: return {},400
    
    
    lsn = msg["lsn"] 
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
        wal = WALLog(**msg) 
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
        
        
@node_bp.route("/sync", methods=["POST"])
def sync():
    
    cluster= current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    
    req = request.json
    if not req: return {},400
    
    from_lsn = req["last_lsn"] 
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
