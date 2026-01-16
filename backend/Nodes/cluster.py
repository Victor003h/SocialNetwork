import socket
from typing import Dict, List

import requests

from node import Node


class ClusterContext:
    """
    Mantiene la vista local del cluster distribuido.
    Encapsula descubrimiento, estado de nodos y topología.
    """

    def __init__(self, local_node: Node):
        self.local_node = local_node

        # Nodos remotos indexados por node_id
        self.peers: Dict[int, Node] = {}

        # Información global del cluster
        self.leader_id: int | None = None

        self.election_in_progress=False
        self.last_heartbeat = 0

    # -------------------------
    # Discovery
    # -------------------------

    def discover_peers(self):
        """
        Descubre nodos pares usando DNS del servicio (Docker Swarm).
        """
        service_name = self.local_node.service_name

        try:
            print("nsdfsdfsdf")
            _, _, addresses = socket.gethostbyname_ex(self.local_node.host)
            print(len(addresses))
        except socket.gaierror as e:
            print( e.errno )
            print (e.strerror)
            addresses = []

        for addr in addresses:
            # Excluirse a sí mismo
            if addr == self.local_node.host:
                continue

            # Node ID desconocido aún (se resolverá luego)
            peer = Node(
                node_id=-1,
                service_name=service_name,
                port=self.local_node.port,
            )
            peer.host = addr
            peer.address = f"{addr}:{peer.port}"

            self._register_peer(peer)

    def _register_peer(self, peer: Node):
        """
        Registra un peer si no existe ya.
        """
        # node_id aún no es confiable, se ajustará en fase 2
        for existing in self.peers.values():
            if existing.address == peer.address:
                return

        temp_id = len(self.peers) + 1
        peer.node_id = temp_id
        self.peers[temp_id] = peer

    # -------------------------
    # Accesores
    # -------------------------

    def get_peers(self) -> List[Node]:
        return list(self.peers.values())

    def get_all_nodes(self) -> List[Node]:
        return [self.local_node] + self.get_peers()

    def is_single_node(self) -> bool:
        return len(self.peers) == 0

    

    def start_election(self):
        if self.election_in_progress:
            return

        self.election_in_progress = True
        local_id = self.local_node.node_id
        higher_nodes = [
            peer for peer in self.get_peers() if peer.node_id > local_id
        ]

        print(f"[ELECTION] Node {local_id} starting election")

        for peer in higher_nodes:
            try:
                requests.post(f"http://{peer.address}/election", timeout=2)
                print(f"[ELECTION] Higher node {peer.node_id} responded")
                self.election_in_progress = False
                return
            except requests.RequestException:
                continue

        # Nadie respondió → soy líder
        self.become_leader()

    def become_leader(self):
        node = self.local_node
        node.set_role("leader")
        self.set_leader(node.node_id)

        print(f"[LEADER] Node {node.node_id} became leader")

        for peer in self.get_peers():
            try:
                requests.post(
                    f"http://{peer.address}/leader",
                    json={"leader_id": node.node_id},
                    timeout=2
                )
            except requests.RequestException:
                pass

        self.election_in_progress = False

    



    def set_leader(self, node_id: int):
        self.leader_id = node_id

    def get_leader(self) -> Node | None:
        if self.leader_id == self.local_node.node_id:
            return self.local_node
        return self.peers.get(self.leader_id)

    def to_dict(self) -> dict:
        """
        Representación del estado del cluster (debug / status endpoint).
        """
        return {
            "local_node": self.local_node.to_dict(),
            "leader_id": self.leader_id,
            "peers": [peer.to_dict() for peer in self.peers.values()],
        }

    def __repr__(self):
        return (
            f"<ClusterContext local={self.local_node.node_id} "
            f"peers={len(self.peers)} "
            f"leader={self.leader_id}>"
        )
