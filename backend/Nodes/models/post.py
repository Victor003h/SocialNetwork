
from requests import post
from sqlalchemy import Column, Integer, String, DateTime,ForeignKey
from datetime import datetime

from models.Base import Base
from models.user import User


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True,autoincrement=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    content = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.created_at is None:
            self.created_at = datetime.now() # O datetime.utcnow() si usas UTC
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "created_at": self.created_at.isoformat()        
            }
    @staticmethod
    def Replicate_Post(msg,session):
        try:
            if msg["operation"] == "INSERT":
                post = Post(**msg["payload"])
                session.add(post)

            elif msg["operation"] == "UPDATE":
                post = session.get(Post, msg["payload"]["id"])
                if post:
                    post.content = msg["payload"]["content"]
                    
            elif msg["operation"] == "DELETE":
                post = session.get(Post, msg["payload"]["id"])
                if post:
                    session.delete(post)

            session.commit()

        finally:
            session.close()  