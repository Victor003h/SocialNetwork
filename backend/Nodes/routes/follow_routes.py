
import requests

from flask import jsonify, Blueprint, request,current_app
from datetime import datetime

followes_bp = Blueprint("followes_bp", __name__)
    

def Call_leader(cluster,url,method):
  

    print("redirigiendo al lider")
    leader = cluster.subleader_manager.get_global_leader()
    if leader is None:
        return jsonify({"error": "global leader unavailable"}), 503
    node_data = {
        "ip": leader.ip,
        "hostname": leader.host,
        "port": cluster.local_node.port,
    }
    return cluster.utils.Remote_Comunicate(method, url, node_data, cluster.secure_args,json= request.json)
    
def Save_Wallog(cluster, WALLog,operation,table_name,follower,session):
    lsn = cluster.next_lsn()
    epoch = cluster.current_epoch
    wal=WALLog(
    wal_id=f"{cluster.local_node.node_id}:{epoch}:{lsn}",
    node_id=cluster.local_node.node_id,
    lsn=lsn,
    epoch=epoch,
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
    # Tras un DELETE la fila ya no existe: refrescar el objeto borrado lanza
    # InvalidRequestError (causaba el 500 aunque el borrado SÍ se aplicaba). Solo
    # refrescamos en INSERT/UPDATE (donde interesa el id/estado generado).
    if operation != "DELETE":
        session.refresh(follower)
    # El relay debe ejecutarse SIEMPRE (incl. DELETE) para que los followers reciban
    # el WAL de borrado y no diverjan.
    cluster.subleader_manager.relay_replication(wal)


@followes_bp.route("/db/follows", methods=["POST"])
def create_follows():
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    Follower = current_app.config["Follower"]
    
    if not cluster.local_node.is_leader():
        return Call_leader(cluster,"/db/follows","POST")
    
    data = request.get_json()
    
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
    
    if not cluster.local_node.is_leader():
        return Call_leader(cluster,"/db/follows","DELETE")
     
    data = request.get_json()
    follower = data ["follower_id"]
    folled   = data ["followed_id"]
    
    session = cluster.database.get_session()
    try:
        # 1. Buscamos la relación concreta (follower -> followed). Nota: hay que pasar
        # las condiciones como argumentos separados del filter; un `and` de Python entre
        # expresiones SQLAlchemy lanza TypeError (booleano no definido) y rompía el unfollow.
        follow = session.query(Follower).filter(
            Follower.follower_id == follower,
            Follower.followed_id == folled
        ).first()

        if not follow:
            return jsonify({"error": f"Follows relations between follower :{follower} and folloed :{folled} not found"}), 404

        # Save_Wallog espera UN objeto (hace .id / to_dict / session.delete sobre él),
        # no una lista; antes se le pasaba .all() y también fallaba.
        Save_Wallog(cluster,WALLog,"DELETE","follows",follow,session)

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
        list_users = [user.to_dict() for user in followed_users]
        
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
        list_users = [user.to_dict() for user in follower_users]
            
        return jsonify(list_users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()