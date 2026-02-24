
import requests

from flask import jsonify, Blueprint, request,current_app
from datetime import datetime

followes_bp = Blueprint("followes_bp", __name__)
    

def Call_leader(cluster,url,method):
  
    redirect= False
    if not cluster.local_node.is_leader():
        leader_address= cluster.peers[cluster.leader_id].address if (
                    cluster.leader_id in cluster.peers) else None
        redirect=True
        requests.request(method=method, url=f"https://{leader_address}/db/"+ url, json=request.json, timeout=2, **cluster.secure_args)
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    if redirect:
        return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore
    
    return True
def Save_Wallog(cluster, WALLog,operation,table_name,follower,session):
    lsn = cluster.next_lsn()
    wal=WALLog(
    wal_id=f"{cluster.local_node.node_id}:{lsn}",
    node_id=cluster.local_node.node_id,
    lsn=lsn,
    operation=operation,
    table_name=table_name,
    entity_id=str(follower.id),
    payload=follower.to_dict(),
    timestamp=datetime.now()
    )
    if operation == "DELETE":
        session.delete(follower)
    session.add(wal)
    session.commit()
    session.refresh(follower)
    cluster.replicate_to_followers(wal)
    
    
@followes_bp.route("/db/follows", methods=["POST"])
def create_follows():
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    Follower = current_app.config["Follower"]
    
    data = request.get_json()
    
    Call_leader(cluster,"follows","POST")
    
    
    session=cluster.database.get_session()
    id=cluster.database.generate_follower_id(session)
    follower = Follower(
        id=id,
        follower_id=data["follower_id"],
        followed_id=data["followed_id"]
    )
    session.add(follower)
    
    Save_Wallog(cluster,WALLog,"INSERT","follows",follower,session) 
    
    
    return jsonify({"msg": "Follower created successfully"}), 201


@followes_bp.route("/db/follows", methods=["DELETE"])
def delete_follow():
    """
     el usuario elimna una relacion de su lista de amigo
    
    """
    cluster = current_app.config["cluster"]
    Follower = current_app.config["Follower"]
    WALLog = current_app.config["WALLog"]
    
    data = request.get_json()
    
    follower = data ["follower_id"]
    folled   = data ["followed_id"]
    
    session = cluster.database.get_session()
    try:
        # 1. Buscamos en la tabla de asociación los IDs que sigue este usuario
        follows = session.query(Follower).filter(
            Follower.follower_id ==  follower and
            Follower.followed_id ==  folled
        ).all()
        
        print(len(follows))
        if not follows:
            return jsonify({"error": f"Follows relations between follower :{follower} and folloed :{folled} not found"}), 404
        
        Save_Wallog(cluster,WALLog,"DELETE","follows",follows,session) 
        
        return jsonify({"status": "deleted"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
        
        
        
        

@followes_bp.route("/db/follows/followed/<int:user_id>", methods=["GET"])
def get_user_followed(user_id):
    """
    Obtiene la lista de usuarios que sigue el user_id.
    """
    cluster = current_app.config["cluster"]
    User = current_app.config["User"]
    Follower = current_app.config["Follower"]
    
    print("entro a call_leader",flush=True)
    Call_leader(cluster,f"follows/followed/{user_id}","GET")
    print("el error es en call_leader",flush=True)
    session = cluster.database.get_session()
    try:
        # 1. Buscamos en la tabla de asociación los IDs que sigue este usuario
        followed_ids_query = session.query(Follower).filter(
            Follower.follower_id == user_id
        ).all()
        
        print(len(followed_ids_query))
        if not followed_ids_query:
            return jsonify([]), 200
        
        followed_ids = [f.followed_id for f in followed_ids_query]
        # 2. Obtenemos la información de esos usuarios
        followed_users = session.query(User).filter(User.id.in_(followed_ids)).all()
        list_users = []
        for user in followed_users:
            user =user.to_dict()
            list_users.append(user.username)
        return jsonify(list_users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
        

@followes_bp.route("/db/follows/follower/<int:user_id>", methods=["GET"])
def get_user_follower(user_id):
    """
    Obtiene la lista de usuarios que siguen al user_id.
    """
    cluster = current_app.config["cluster"]
    User = current_app.config["User"]
    Follower = current_app.config["Follower"] # Asegúrate de pasar el modelo al config
    
    Call_leader(cluster,f"follows/follower/{user_id}","GET")
    
    session = cluster.database.get_session()
    try:
        # 1. Buscamos en la tabla de asociación los IDs que siguen a este usuario
        follower_ids_query = session.query(Follower).filter(
            Follower.followed_id == user_id
        ).all()
        
        follower_ids = [f.follower_id for f in follower_ids_query]
        if not follower_ids:
            return jsonify([]), 200

        # 2. Obtenemos la información de esos usuarios
        follower_users = session.query(User).filter(User.id.in_(follower_ids)).all()
        list_users = []
        for user in follower_users:
            user =user.to_dict()
            list_users.append(user.username)
            
        return jsonify(list_users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()