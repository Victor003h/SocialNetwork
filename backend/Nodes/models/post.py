
from sqlalchemy import Column, Integer, String, DateTime,ForeignKey
from datetime import datetime

from models.Base import Base
from models.user import User


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True,autoincrement=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    content = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None  # type: ignore
        }