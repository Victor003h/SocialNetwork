from sqlalchemy import (
    Column, String, Integer, Boolean,
    DateTime, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from models.Base import Base

class WALLog(Base):
    __tablename__ = "wal_log"

    wal_id = Column(String, primary_key=True)
    node_id = Column(String, nullable=False)
    lsn = Column(Integer, nullable=False)
    # Epoch (term) del leader global que originó la entrada. Junto con lsn forma
    # la clave de orden global (epoch, lsn) usada para idempotencia y fencing.
    epoch = Column(Integer, nullable=False, default=0)

    operation = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    payload = Column(JSON)

    timestamp = Column(DateTime, default=datetime.now())
    applied = Column(Boolean, default=False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.timestamp is None:
            self.timestamp = datetime.now() # O datetime.utcnow() si usas UTC
            
    def to_dict(self):
        return {
            "wal_id": self.wal_id,
            "node_id": self.node_id,
            "lsn": self.lsn,
            "epoch": self.epoch,
            "operation": self.operation,
            "table_name": self.table_name,
            "entity_id": self.entity_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }
