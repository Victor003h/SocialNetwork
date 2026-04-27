import threading
import time

from flask import  jsonify, Blueprint, request,current_app
from sqlalchemy import select



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
    if cluster.local_node.is_subleader():
        peers = cluster.subleader_manager.subleader_list
    else:
        peers = cluster.get_peers()

    threading.Thread(
        target=cluster.start_election,
        args=(peers,),
        daemon=True
    ).start()
    return response, 200

@node_bp.route("/db/subleader_address", methods=["GET"])
def get_leader_address():
    
    cluster= current_app.config["cluster"]
    subleader_data={}
    if cluster.subleader_id :
        if cluster.subleader_id==cluster.local_node.node_id:
            subleader_data["address"]  = cluster.local_node.address
            subleader_data["ip"]       = cluster.local_node.ip
        else:
            peer= cluster.peers.get(cluster.subleader_id) 
            if peer:
                subleader_data["address"]  = peer.address
                subleader_data["ip"]       = peer.ip
                
        return jsonify(subleader_data), 200
    else:
        return jsonify({"error": "subleader not found"}), 404


@node_bp.route("/leader", methods=["POST"])
def leader_announcement():
    
    cluster= current_app.config["cluster"]
    
    data=request.json
    if not data: return {},400
    
    cluster.set_leader(data["leader_id"]) 
    cluster.local_node.set_role("follower")
    print(f"[LEADER] Leader set to {data['leader_id']}") 
    return {"status": "ok"}

@node_bp.route("/subleader", methods=["POST"])
def subleader_announcement():
    
    cluster= current_app.config["cluster"]
    
    data=request.json
    if not data: return {},400
    
    cluster.set_subleader(data["subleader_id"]) 
    cluster.local_node.set_role("follower")
    print(f"[subleader] subleader set to {data['subleader_id']}") 
    return {"status": "ok"}

@node_bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    
    cluster= current_app.config["cluster"]
    
    cluster.last_heartbeat = time.time()
    print("[HEARTBEAT] Received from subleader")
    print(f"[HEARTBEAT] Last heartbeat {cluster.last_heartbeat}")
    return {"status": "ok"}

@node_bp.route("/heartbeat_leader", methods=["POST"])
def heartbeat_leader():
    
    cluster= current_app.config["cluster"]
    
    cluster.last_heartbeat_leader = time.time()
    print("[HEARTBEAT] Received from leader")
    print(f"[HEARTBEAT] Last heartbeat {cluster.last_heartbeat_leader}")
    return {"status": "ok"}

@node_bp.route("/newNode", methods=["POST"])
def NewNode():
    
    cluster= current_app.config["cluster"]
    data=request.get_json()
    
    peer = Node(
        node_id=data["node_id"],
        service_name=data["service_name"],
        port=5000,
        node_pc_id=data["node_pc_id"]
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
        wal = WALLog(**msg) 
        session.add(wal)
        cluster.apply_operation(msg)
        session.commit()
        cluster.last_applied_lsn = lsn
        if cluster.local_node.role == "subleader":
            cluster.replicate_to_followers(wal)
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
