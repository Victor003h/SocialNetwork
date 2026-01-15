from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from model import Post, db


app= Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{db.DB_USER}:{db.DB_PASSWORD}@{db.DB_HOST}:5432/{db.DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)



@app.route("/create", methods=["POST"])
def create_post():
    data = request.get_json()
    user_id = data.get("user_id")
    content = data.get("content")

    if not user_id or not content:
        return {"error": "Datos incompletos"}, 400

    new_post = Post(user_id=user_id, content=content)
    db.session.add(new_post)
    db.session.commit()

    return {"msg": "Post creado correctamente", "post_id": new_post.id}, 201


@app.route("/user/<int:user_id>")
def get_user_posts(user_id):
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()

    return jsonify([
        {
            "id": p.id,
            "user_id": p.user_id,
            "content": p.content,
            "created_at": p.created_at.isoformat()
        }
        for p in posts
    ])


@app.route("/delete/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    post = Post.query.get(post_id)

    if not post:
        return {"error": "Post no encontrado"}, 404

    db.session.delete(post)
    db.session.commit()

    return {"msg": "Post eliminado"}


@app.route("/")
def index():
    return {"msg": "Post Service activo"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)