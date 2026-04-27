
import json

from flask import jsonify, Blueprint, request,current_app
from datetime import datetime
import requests

post_bp = Blueprint("post_bp", __name__)


def Call_leader(cluster,url,method):


    leader=cluster.subleader_manager.global_leader               
    node_data = {
        "ip": leader.ip,
        "hostname": leader.host,
        "port": cluster.local_node.port,
    } 
    return cluster.utils.Remote_Comunicate(method, url, node_data, cluster.secure_args,json= request.json)

def Save_Wallog(cluster, WALLog,operation, post,session):
    lsn = cluster.next_lsn()
    wal=WALLog(
    wal_id=f"{cluster.local_node.node_id}:{lsn}",
    node_id=cluster.local_node.node_id,
    lsn=lsn,
    operation=operation,
    table_name="posts",
    entity_id=str(post.id),
    payload=post.to_dict(),
    timestamp=datetime.now()
    )
    if operation == "DELETE":
        session.delete(post)
        
    session.add(wal)
    session.commit()
    cluster.subleader_manager.relay_replication(wal)
    
@post_bp.route("/db/posts", methods=["POST"])
def create_post():
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    Post = current_app.config["Post"]

    
    if not cluster.local_node.is_leader():
        return Call_leader(cluster,"/db/posts","POST")
    
    data = request.get_json()
    
    session=cluster.database.get_session()
    post_id=cluster.database.generate_post_id(session)
    post = Post(
        id= post_id,
        user_id=data["user_id"],
        content=data["content"] 
    )
    session.add(post)
    
    Save_Wallog(cluster,WALLog,"INSERT",post,session) 
    
    return jsonify({"id": post.id}), 201


@post_bp.route("/db/posts", methods=["GET"])
def list_posts():
        
        cluster= current_app.config["cluster"]
        Post = current_app.config["Post"]
        
        session = cluster.database.get_session()
        try:
            posts = session.query(Post).all()
            return jsonify([p.to_dict() for p in posts]), 200
        finally:
            session.close()

@post_bp.route("/db/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    cluster= current_app.config["cluster"]
    Post = current_app.config["Post"]
    
    session = cluster.database.get_session()
    try:
        post = session.get(Post, post_id)
        if not post:
            return jsonify({"error": "post not found"}), 404
        return jsonify(post.to_dict()), 200
    finally:
        session.close()
        
@post_bp.route("/db/posts/user/<int:user_id>", methods=["GET"])
def get_user_posts(user_id):
    cluster= current_app.config["cluster"]
    Post = current_app.config["Post"]
   
    session = cluster.database.get_session()
    try:
        posts = session.query(Post).filter_by(user_id=user_id).all()
        if not posts:
            return jsonify({"error": "posts not found"}), 404
        return jsonify([p.to_dict() for p in posts]), 200
    finally:
        session.close()

@post_bp.route("/db/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    Post = current_app.config["Post"]
    
    if not cluster.local_node.is_leader():
        return Call_leader(cluster,f"/db/posts/{post_id}","PUT")
    
    data = request.get_json()
    
    session = cluster.database.get_session()
    try:
        post = session.get(Post, post_id)
        if not post:
            return jsonify({"error": "post not found"}), 404
        if "content" in data: 
            post.content = data["content"]   
        
        Save_Wallog(cluster,WALLog,"PUT",post,session)
        
        return jsonify({"status": "updated"}), 200
    finally:
        session.close()
        
        
@post_bp.route("/db/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
   
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    Post = current_app.config["Post"]
    
    
    if not cluster.local_node.is_leader():
        return Call_leader(cluster,f"/db/posts/{post_id}","DELETE")
    
    session = cluster.database.get_session()
    
    try:
        post = session.get(Post, post_id)
        if not post:
            print("post with id :{post_id} not found")
            return jsonify({"error": f"post with id :{post_id} not found"}), 404
        
        Save_Wallog(cluster,WALLog,"DELETE",post,session)
        
        return jsonify({"status": "deleted"}), 200
    finally:
        session.close()
    
    