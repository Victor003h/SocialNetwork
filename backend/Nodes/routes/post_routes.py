
from flask import jsonify, Blueprint, request,current_app
from datetime import datetime
import requests

post_bp = Blueprint("post_bp", __name__)


def Call_leader(cluster,url):
  
    redirect= False
    if not cluster.local_node.is_leader():
        leader_address=cluster.peers[cluster.leader_id].address # type: ignore
        redirect=True
        requests.request(method=request.method, url=f"https://{leader_address}/db/".join(url), json=request.json, timeout=2, **cluster.secure_args)
        return jsonify({"msg":f"leader address: {leader_address}" }), 307
    if redirect:
        return jsonify({"msg":f"leader address: {leader_address}" }), 307 # type: ignore

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
    cluster.replicate_to_followers(wal)
    
    
@post_bp.route("/db/posts", methods=["POST"])
def create_post():
    
    cluster = current_app.config["cluster"]
    WALLog = current_app.config["WALLog"]
    Post = current_app.config["Post"]
    User = current_app.config["User"]
    
    data = request.get_json()
    
    Call_leader(cluster,"post")
    
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
        
        Call_leader(cluster,"posts")
        
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
      
    Call_leader(cluster,f"posts/{post_id}")
    
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
    
    Call_leader(cluster,f"posts/{user_id}")
   
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
    
    data = request.get_json()
    
    Call_leader(cluster,f"posts/{post_id}")
    
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
    
    Call_leader(cluster,f"posts/{post_id}")
    
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
    
    