import requests

from flask import Flask, jsonify, Blueprint, request,current_app
from datetime import datetime


user_bp = Blueprint("user_bp", __name__)
    
  
@user_bp.route("/db/users", methods=["POST"])
def create_user():
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    User = current_app.config["User"]
    
    data = request.json
    
    if not data: return {},400
    redirect= False          
    
    leader_address= cluster.peers[cluster.leader_id].address if (
                    cluster.leader_id in cluster.peers) else None
    
    if not cluster.local_node.is_leader():
        redirect=True
        requests.post(
            f"https://{leader_address}/db/users",
            json=request.json ,
            timeout=2,
            **cluster.secure_args
        )
        
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    if redirect:
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    
    lsn=cluster.next_lsn()
    
    session=cluster.database.get_session()
    user_id=cluster.database.generate_user_id(session)
    user = User(
        username=data["username"],
        password_hash=data["password"], 
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


@user_bp.route("/db/users", methods=["GET"])
def list_users():
    
    cluster= current_app.config["cluster"]
    User = current_app.config["User"]
    
    redirect= False
    
    if not cluster.local_node.is_leader():
        leader_address=cluster.peers[cluster.leader_id].address # type: ignore
        redirect=True
        requests.get(f"https://{leader_address}/db/users" ,timeout=2, **cluster.secure_args)
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    if redirect:
        return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore
    session = cluster.database.get_session()
    try:
        users = session.query(User).all()
        return jsonify([u.to_dict() for u in users]), 200
    finally:
        session.close()


@user_bp.route("/db/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    
    cluster= current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    User = current_app.config["User"]
    
    data = request.json
    if not data: return {},400
    
    redirect= False
    if not cluster.local_node.is_leader():
        leader_address=cluster.peers[cluster.leader_id].address # type: ignore
        redirect=True
        requests.put(f"https://{leader_address}/db/users/{user_id}",json=request.json ,timeout=2, **cluster.secure_args)
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    if redirect:
        return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore
    
    session = cluster.database.get_session()
    try:
        user = session.get(User, user_id)
        if not user:
            return jsonify({"error": "user not found"}), 404
        if "username" in data: 
            user.username = data["username"]   
        if "password" in data: 
            user.password_hash = data["password"] 
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


@user_bp.route("/db/users/<int:user_id>", methods=["DELETE"]) 
def delete_user(user_id):
 
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    User = current_app.config["User"]
    
    redirect= False
    if not cluster.local_node.is_leader():
        leader_address=cluster.peers[cluster.leader_id].address # type: ignore
        redirect=True
        requests.delete(f"https://{leader_address}/db/users/{user_id}" ,timeout=2, **cluster.secure_args)
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
