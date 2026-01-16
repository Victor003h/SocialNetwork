import os
import socket


class Node:
    """
    Representa un nodo lógico del cluster distribuido.
    """

    def __init__(self, node_id: int, service_name: str, port: int):
        self.node_id = node_id
        self.service_name = service_name
        self.port = port
        

        # Estado del nodo
        self.role = "unknown"     # unknown | leader | follower
        self.alive = True

        # Dirección del nodo
        self.host = self._get_host()
        self.address = f"{self.host}:{self.port}"
        print(self.address)

    def _get_host(self) -> str:
        """
        Obtiene el hostname/IP del contenedor.
        En Docker Swarm esto corresponde al endpoint interno.
        """
        print("Busca el host")
        try:

            host_id= socket.gethostname()
            host=socket.gethostbyname(host_id)
            
            return host
        except:
            print("Fallo al enconcontrar host")
            return "falta_implementar"

    def set_role(self, role: str):
        if role not in ("unknown", "leader", "follower"):
            raise ValueError(f"Invalid role: {role}")
        self.role = role

    def is_leader(self) -> bool:
        return self.role == "leader"

    def is_follower(self) -> bool:
        return self.role == "follower"

    def to_dict(self) -> dict:
        """
        Representación serializable del nodo (útil para /info).
        """
        return {
            "node_id": self.node_id,
            "host":self.host,
            "port":self.port,
            "service_name": self.service_name,
            "address": self.address,
            "role": self.role,
            "alive": self.alive,

        }

    @classmethod
    def from_env(cls):
        """
        Crea un nodo a partir de variables de entorno.
        Esto es clave para Swarm.
        """
        node_id = int(os.getenv("NODE_ID", "0"))
        service_name = os.getenv("SERVICE_NAME", "unknown-service")
        port = int(os.getenv("NODE_PORT", "5432"))

        if node_id <= 0:
            raise RuntimeError("NODE_ID must be defined and > 0")

        return cls(
            node_id=node_id,
            service_name=service_name,
            port=port,
        )

    def __repr__(self):
        return (
            f"<Node id={self.node_id} "
            f"service={self.service_name} "
            f"address={self.address} "
            f"role={self.role}>"
        )

