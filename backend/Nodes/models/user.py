
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

    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "password_hash":self.password_hash,
            "created_at": self.created_at   
        }