
from json import tool
import json
from flask import Blueprint, request, jsonify, current_app

follow_bp = Blueprint("follow_bp", __name__)

@follow_bp.route("/follows", methods=["POST"])
def create_follows():
    
    tools = current_app.config["tools"]
    data = request.get_json()
    
    payload={}
    
    if "follower_id" in data:
        payload["follower_id"]=data["follower_id"]
    if "followed_id" in data:
        payload["followed_id"]= data["followed_id"]
    
    if len(payload) != 2 :  return {},400  
    
    res = tools.call_cluster("POST", "/db/follows", json=payload)
    return jsonify(res.json()), res.status_code

@follow_bp.route("/follows", methods=["DELETE"])
def delete_follows():
    
    tools = current_app.config["tools"]
    data = request.get_json()
    
    payload={}
    
    if "follower_id" in data:
        payload["follower_id"]=data["follower_id"]
    if "followed_id" in data:
        payload["followed_id"]= data["followed_id"]
    
    if len(payload) != 2 :  return {},400  
    
    res = tools.call_cluster("DELETE", "/db/follows", json=payload)
    return jsonify(res.json()), res.status_code


@follow_bp.route("/follows/followed/<int:user_id>", methods=["GET"])
def get_user_followed(user_id):
    
    
    tools = current_app.config["tools"]
    res= tools.call_cluster("GET", f"/db/follows/followed/{user_id}")
    return jsonify(res.json()), res.status_code


@follow_bp.route("/follows/follower/<int:user_id>", methods=["GET"])
def get_user_followers(user_id):
     
    tools = current_app.config["tools"]
    res= tools.call_cluster("GET", f"/db/follows/follower/{user_id}")
    return jsonify(res.json()), res.status_code


