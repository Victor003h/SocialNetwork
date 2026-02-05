from sqlalchemy import Column, BigInteger, String, DateTime, JSON
from sqlalchemy.sql import func

from models.Base import Base


class WALLog(Base):
    __tablename__ = "wal_log"

    # Log Sequence Number (reloj lógico global)
    lsn = Column(BigInteger, primary_key=True, index=True)

    # Tipo de operación: INSERT / UPDATE / DELETE
    operation = Column(String(16), nullable=False)

    # Tabla afectada (users, posts, etc.)
    table_name = Column(String(64), nullable=False)

    # Payload de la operación (datos serializados)
    payload = Column(JSON, nullable=False)

    # Timestamp solo informativo
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "lsn": self.lsn,
            "operation": self.operation,
            "table": self.table_name,
            "payload": self.payload,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return (
            f"<WALLog lsn={self.lsn} "
            f"op={self.operation} "
            f"table={self.table_name}>"
        )
