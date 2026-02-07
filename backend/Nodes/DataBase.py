from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
import os

from models.user import Base
from models.wal import WALLog


class Database:
    def __init__(self):
        self.db_url = self._build_db_url()
        self.engine = create_engine(
            self.db_url,
            pool_pre_ping=True,
            echo=False
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _build_db_url(self) -> str:
        user = os.getenv("POSTGRES_USER", "admin")
        password = os.getenv("POSTGRES_PASSWORD", "secret")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        name = os.getenv("POSTGRES_NAME", "cluster_db")

        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    def setupDatabase(self):
        self.create_tables()
        Table_List=["users","posts"]
        with self.engine.begin() as conn:
            for table in Table_List:
                conn.execute(text(f"""
                    CREATE SEQUENCE IF NOT EXISTS {table}_id_seq;
                """))
            
            

        session=self.get_session()
        self.last_applied_lsn = (
        session.query(func.max(WALLog.lsn)).scalar() or 0
        )

        session.close()
    
    def get_session(self):
        return self.SessionLocal()

    def create_tables(self):
        Base.metadata.create_all(self.engine)
        
    def generate_user_id(self, session):
        result = session.execute(
        text("SELECT nextval('users_id_seq')")
        )
        return result.scalar()
    
    def generate_post_id(self, session):
        result = session.execute(
        text("SELECT nextval('posts_id_seq')")
        )
        return result.scalar()
