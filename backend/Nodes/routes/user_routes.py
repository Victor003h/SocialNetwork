import requests
from flask import jsonify, Blueprint, request,current_app
from datetime import datetime


user_bp = Blueprint("user_bp", __name__)
    

def Call_leader(cluster,url,method):
  
    redirect= False
    if not cluster.local_node.is_leader():
        leader_address= cluster.peers[cluster.leader_id].address if (
                    cluster.leader_id in cluster.peers) else None
        redirect=True
        requests.request(method=method, url=f"https://{leader_address}/db/".join(url), json=request.json, timeout=2, **cluster.secure_args)
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    if redirect:
        return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore

def Save_Wallog(cluster, WALLog,operation,table_name,user,session):
    lsn = cluster.next_lsn()
    wal=WALLog(
    wal_id=f"{cluster.local_node.node_id}:{lsn}",
    node_id=cluster.local_node.node_id,
    lsn=lsn,
    operation=operation,
    table_name=table_name,
    entity_id=str(user.id),
    payload=user.to_dict(),
    timestamp=datetime.now()
    )
    if operation == "DELETE":
        session.delete(user)
    session.add(wal)
    session.commit()
    cluster.replicate_to_followers(wal)
    
    

  
@user_bp.route("/db/users", methods=["POST"])
def create_user():
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    User = current_app.config["User"]
    
    data = request.get_json()
    
    
    session=cluster.database.get_session()
    user_id=cluster.database.generate_user_id(session)
    user = User(
        username=data["username"],
        password_hash=data["password"], 
        id=user_id
    )
    session.add(user) 
     
    Save_Wallog(cluster,WALLog,"INSERT","users",user,session)

    return jsonify({"id": user.id}), 201


@user_bp.route("/db/users", methods=["GET"])
def list_users():
    
    cluster= current_app.config["cluster"]
    User = current_app.config["User"]
    
    Call_leader(cluster,"users","GET")
    
    session = cluster.database.get_session()
    try:
        users = session.query(User).all()
        list_users = [user.to_dict() for user in users]
        
        return jsonify(list_users), 200
    finally:
        session.close()

@user_bp.route("/db/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    cluster= current_app.config["cluster"]
    User = current_app.config["User"]
    
    Call_leader(cluster,f"users/{user_id}","GET")
    
    session = cluster.database.get_session()
    try:
        user = session.get(User, user_id)
        if not user:
            return jsonify({"error": "user not found"}), 404
        
        return jsonify(user.to_dict()), 200
    finally:
        session.close()

@user_bp.route("/db/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    
    cluster= current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    User = current_app.config["User"]
    
    data = request.get_json()
    
    Call_leader(cluster,f"users/{user_id}","PUT")
    
    session = cluster.database.get_session()
    try:
        user = session.get(User, user_id)
        if not user:
            return jsonify({"error": "user not found"}), 404
        if "username" in data: 
            user.username = data["username"]   
        if "password" in data: 
            user.password_hash = data["password"] 
        
        Save_Wallog(cluster,WALLog,"UPDATE","users",user,session)  
         
        return jsonify({"status": "updated"}), 200
    finally:
        session.close()


@user_bp.route("/db/users/<int:user_id>", methods=["DELETE"]) 
def delete_user(user_id):
 
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    User = current_app.config["User"]
    
    Call_leader(cluster,f"users/{user_id}","DELETE")
    
    session = cluster.database.get_session()
    try:
        user = session.get(User, user_id)
        if not user:
            print("user with id :{user_id} not found")
            return jsonify({"error": f"user with id :{user_id} not found"}), 404
        
        Save_Wallog(cluster,WALLog,"DELETE","users",user,session)
       
        return jsonify({"status": "deleted"}), 200
    finally:
        session.close()

