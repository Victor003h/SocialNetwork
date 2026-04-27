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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.created_at is None:
            self.created_at = datetime.now() # O datetime.utcnow() si usas UTC
    
    def to_dict(self):
        return {
            "id": self.id,
            "follower_id": self.follower_id,
            "followed_id": self.followed_id,
            "created_at":  self.created_at.isoformat() 
        }
    @staticmethod
    def Replicate_Follower(msg,session):
        try:
            if msg["operation"] == "INSERT":
                Follows = Follower(**msg["payload"])
                session.add(Follows)

            elif msg["operation"] == "DELETE":
                follower= msg["payload"]["follower_id"]
                folled =  msg["payload"]["followed_id"]
                Follows = session.query(Follower).filter(
                                            Follower.follower_id ==  follower and
                                            Follower.followed_id ==  folled
                                            ).all()
                if Follows:
                    session.delete(Follows)

            session.commit()

        finally:
            session.close()