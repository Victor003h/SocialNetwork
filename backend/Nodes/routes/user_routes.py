from typing import Self

import requests
from flask import jsonify, Blueprint, request,current_app
from datetime import datetime


user_bp = Blueprint("user_bp", __name__)
    

def Call_leader(cluster,url,method):

        leader=cluster.subleader_manager.global_leader               
        node_data = {
            "ip": leader.ip,
            "hostname": leader.host,
            "port": cluster.local_node.port,
        } 
        return cluster.utils.Remote_Comunicate(method, url, node_data, cluster.secure_args,json= request.json)
        

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
    cluster.subleader_manager.relay_replication(wal)
    

  
@user_bp.route("/db/users", methods=["POST"])
def create_user():
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    User = current_app.config["User"]
    
    
    print(f"El nodo que recibio la peticion tiene el rol de {cluster.local_node.role} ")
    
    if not cluster.local_node.is_leader():
        return Call_leader(cluster,"/db/users","POST")
    
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
    
    if not cluster.local_node.is_leader():
        return Call_leader(cluster,f"/db/users/{user_id}","PUT")
    
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
    
    if not cluster.local_node.is_leader():
        return Call_leader(cluster,f"/db/users/{user_id}","DELETE")
    
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

