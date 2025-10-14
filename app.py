from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from models import User,Message
from flask_sqlalchemy import SQLAlchemy
from db import db
from routes.auth import auth_bp
from routes.follow import  follow_bp
from routes.message import message_bp
from config import Config



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    bcrypt = Bcrypt(app)
    jwt = JWTManager(app)
    db.init_app(app)
    migrate = Migrate(app, db)



    app.register_blueprint(auth_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(follow_bp)

    @app.route("/")
    def index():
        return {"msg": "Social Network API running"}


    return app

app=create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000
    )



