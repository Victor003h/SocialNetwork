
from requests import post
from sqlalchemy import Column, Integer, String, DateTime, column
from datetime import datetime
from models.Base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True,autoincrement=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.created_at is None:
            self.created_at = datetime.now() # O datetime.utcnow() si usas UTC
            
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password_hash":self.password_hash,
            "created_at": self.created_at.isoformat()   
        }
    
    @staticmethod
    def Replicate_user(msg,session):
        try:
            if msg["operation"] == "INSERT":
                user = User(**msg["payload"])
                session.add(user)

            elif msg["operation"] == "UPDATE":
                user = session.get(User, msg["payload"]["id"])
                if user:
                    user.username = msg["payload"]["username"]
                    user.password_hash = msg["payload"]["password_hash"]

            elif msg["operation"] == "DELETE":
                user = session.get(User, msg["payload"]["id"])
                if user:
                    session.delete(user)

            session.commit()

        finally:
            session.close()
        