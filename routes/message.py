from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Message, User


message_bp = Blueprint("message_bp", __name__)

# Crear mensaje
@message_bp.route("/messages", methods=["POST"])
@jwt_required()
def create_message():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    content = data.get("content")

    if not content:
        return jsonify({"error": "El contenido del mensaje es requerido"}), 400

    user = User.query.get(current_user_id)
    message = Message(content=content, user=user)
    db.session.add(message)
    db.session.commit()
    return jsonify(message.to_dict()), 201

# Listar todos los mensajes
@message_bp.route("/messages", methods=["GET"])
@jwt_required()
def get_messages():
    messages = Message.query.all()
    return jsonify([m.to_dict() for m in messages])

# Obtener mensaje por ID
@message_bp.route("/messages/<int:message_id>", methods=["GET"])
@jwt_required()
def get_message(message_id):
    message = Message.query.get(message_id)
    if not message:
        return jsonify({"error": "Mensaje no encontrado"}), 404
    return jsonify(message.to_dict())

# Actualizar mensaje 
@message_bp.route("/messages/<int:message_id>", methods=["PUT"])
@jwt_required()
def update_message(message_id):
    current_user_id = get_jwt_identity()
    message = Message.query.get(message_id)
    if not message:
        return jsonify({"error": "Mensaje no encontrado"}), 404

    if str(message.user_id) != current_user_id:
        return jsonify({"error": "No tienes permiso para actualizar este mensaje"}), 403

    data = request.get_json()
    message.content = data.get("content", message.content)
    db.session.commit()
    return jsonify(message.to_dict())

# Eliminar mensaje 
@message_bp.route("/messages/<int:message_id>", methods=["DELETE"])
@jwt_required()
def delete_message(message_id):
    current_user_id = get_jwt_identity()
    message = Message.query.get(message_id)
    if not message:
        return jsonify({"error": "Mensaje no encontrado"}), 404

    if str(message.user_id) != current_user_id:
        return jsonify({"error": "No tienes permiso para eliminar este mensaje"}), 403

    db.session.delete(message)
    db.session.commit()
    return jsonify({"message": "Mensaje eliminado"}), 200

