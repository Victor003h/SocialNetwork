
from flask import jsonify, Blueprint, request,current_app
from datetime import datetime
import requests

post_bp = Blueprint("post_bp", __name__)

@post_bp.route("/db/post", methods=["POST"])
def create_post():
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    Post = current_app.config["Post"]
    
    data = request.json
    
    if not data: return {},400
    
    redirect= False          
    leader_address= cluster.peers[cluster.leader_id].address if (
                    cluster.leader_id in cluster.peers) else None
    
    if not cluster.local_node.is_leader():
        redirect=True
        requests.post(
            f"https://{leader_address}/db/post",
            json=request.json ,
            timeout=2,
            **cluster.secure_args
        )
        
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    if redirect:
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    
    lsn=cluster.next_lsn()
    
     
    session=cluster.database.get_session()
    post_id=cluster.database.generate_post_id(session)
    post = Post(
        id= post_id,
        user_id=data["user_id"],
        content=data["content"] 
    )
    session.add(post) 
     
    wal=WALLog(
        wal_id=f"{cluster.local_node.node_id}:{lsn}",
        node_id=cluster.local_node.node_id,
        lsn=lsn,
        operation="INSERT",
        table_name="posts",
        entity_id=str(post.id),
        payload=post.to_dict(),
        timestamp=datetime.now()
        )
   
     
    session.add(wal)
    session.commit()
    
    cluster.replicate_to_followers(wal)
    return jsonify({"id": post.id}), 201


@post_bp.route("/db/posts", methods=["GET"])
def list_posts():
        
        cluster= current_app.config["cluster"]
        Post = current_app.config["Post"]
        
        redirect= False
        if not cluster.local_node.is_leader():
            leader_address=cluster.peers[cluster.leader_id].address # type: ignore
            redirect=True
            requests.get(f"https://{leader_address}/db/posts" ,timeout=2, **cluster.secure_args)
            return jsonify({"msg":f"leader address: {leader_address}" }), 307
        if redirect:
            return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore


        session = cluster.database.get_session()
        try:
            posts = session.query(Post).all()
            return jsonify([p.to_dict() for p in posts]), 200
        finally:
            session.close()


@post_bp.route("/db/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    Post = current_app.config["Post"]
    
    data = request.json
    
    if not data: return {},400
    
    redirect= False
    if not cluster.local_node.is_leader():
        leader_address=cluster.peers[cluster.leader_id].address # type: ignore
        redirect=True
        requests.put(f"https://{leader_address}/db/posts/{post_id}",json=request.json ,timeout=2, **cluster.secure_args)
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    if redirect:
        return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore
    
    session = cluster.database.get_session()
    try:
        post = session.get(Post, post_id)
        if not post:
            return jsonify({"error": "post not found"}), 404
        if "content" in data: 
            post.content = data["content"]   
        lsn = cluster.next_lsn()
        wal=WALLog(
            wal_id=f"{cluster.local_node.node_id}:{lsn}",
            node_id=cluster.local_node.node_id,
            lsn=lsn,
            operation="UPDATE",
            table_name="posts",
            entity_id=str(post.id),
            payload=post.to_dict(),
            timestamp=datetime.now()
        )
        session.add(wal)
        session.commit()
        cluster.replicate_to_followers(wal)
        return jsonify({"status": "updated"}), 200
    finally:
        session.close()
        
        
@post_bp.route("/db/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
   
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    Post = current_app.config["Post"]
    
    redirect= False
    if not cluster.local_node.is_leader():
        leader_address=cluster.peers[cluster.leader_id].address # type: ignore
        redirect=True
        requests.delete(f"https://{leader_address}/db/posts/{post_id}" ,timeout=2, **cluster.secure_args)
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    if redirect:
        return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore
    
    
    session = cluster.database.get_session()
    
    try:
        post = session.get(Post, post_id)
        if not post:
            print("post with id :{post_id} not found")
            return jsonify({"error": f"post with id :{post_id} not found"}), 404
        lsn = cluster.next_lsn()
        wal=WALLog(
        wal_id=f"{cluster.local_node.node_id}:{lsn}",
        node_id=cluster.local_node.node_id,
        lsn=lsn,
        operation="DELETE",
        table_name="posts",
        entity_id=str(post.id),
        payload=post.to_dict(),
        timestamp=datetime.now()
        )
        session.delete(post)
        session.add(wal)
        session.commit()
        cluster.replicate_to_followers(wal)
        return jsonify({"status": "deleted"}), 200
    finally:
        session.close()
    
    