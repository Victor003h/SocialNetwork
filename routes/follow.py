from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Follow, User

follow_bp = Blueprint("follow_bp", __name__)

@follow_bp.route("/follow/<int:user_id>", methods=["POST"])
@jwt_required()
def follow_user(user_id):
    current_user = get_jwt_identity()

    if current_user == user_id:
        return jsonify({"msg": "Can't follow yourself"}), 400

    if Follow.query.filter_by(follower_id=current_user, followed_id=user_id).first():
        return jsonify({"msg": "Already following"}), 400

    f = Follow(follower_id=current_user, followed_id=user_id)
    db.session.add(f)
    db.session.commit()
    return jsonify({"msg": "Followed user"}), 201


@follow_bp.route("/unfollow/<int:user_id>", methods=["DELETE"])
@jwt_required()
def unfollow_user(user_id):
    current_user = get_jwt_identity()
    f = Follow.query.filter_by(follower_id=current_user, followed_id=user_id).first()

    if not f:
        return jsonify({"msg": "Not following"}), 400

    db.session.delete(f)
    db.session.commit()
    return jsonify({"msg": "Unfollowed user"})

@follow_bp.route("/followers", methods=["GET"])
@jwt_required()
def get_followers():
    current_user = get_jwt_identity()
    followers = (
        db.session.query(User)
        .join(Follow, Follow.follower_id == User.id)
        .filter(Follow.followed_id == current_user)
        .all()
    )

    return jsonify({
        "user_id": current_user,
        "followers": [{"id": u.id, "username": u.username} for u in followers]
    }), 200

@follow_bp.route("/following", methods=["GET"])
@jwt_required()
def get_following():
    current_user = get_jwt_identity()
    following = (
        db.session.query(User)
        .join(Follow, Follow.followed_id == User.id)
        .filter(Follow.follower_id == current_user)
        .all()
    )

    return jsonify({
        "user_id": current_user,
        "following": [{"id": u.id, "username": u.username} for u in following]
    }), 200