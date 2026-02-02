from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from models.user import Base



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

    def get_session(self):
        return self.SessionLocal()

    def create_tables(self):
        Base.metadata.create_all(self.engine)
        