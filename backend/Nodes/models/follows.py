from sqlalchemy import Column, Integer, ForeignKey, DateTime
from datetime import datetime
from models.Base import Base
from models.user import User

class Follower(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True,autoincrement=False)
    # El usuario que realiza la acción de seguir
    follower_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    # El usuario que es seguido
    followed_id = Column(Integer, ForeignKey(User.id), primary_key=True)
    
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "follower_id": self.follower_id,
            "followed_id": self.followed_id,
            "created_at":  self.created_at 
        }