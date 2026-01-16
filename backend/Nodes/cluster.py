import socket
from tarfile import data_filter
import time
from typing import Dict, List
import os
import requests
from sqlalchemy import Boolean

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
        self.last_heartbeat = time.time()

    # -------------------------
    # Discovery
    # -------------------------

    def discover_peers(self):
        """
        Descubre nodos pares usando DNS del servicio (Docker Swarm).
        """
        service_name = self.local_node.service_name
        network_name=os.getenv("NETWORK-ALIAS","cluster_net_serv")

        try:
            _, _, addresses = socket.gethostbyname_ex(network_name)
        except socket.gaierror as e:
            print( e.errno )
            print (e.strerror)
            addresses = []
        
        self.peers={}
        for addr in addresses:
            # Excluirse a sí mismo
           
            if addr == self.local_node.host:
                continue

            response=  requests.get(f"http://{addr}:{self.local_node.port}/info", timeout=2)

            data=response.json()
            leader_id=data.get("leader_id")

            if leader_id : 
                self.leader_id=leader_id
                self.local_node.role="follower"

            node=data.get("local_node",{})
            peer = Node(
                node_id=node.get("node_id"),
                service_name=node.get("service_name"),
                port=self.local_node.port,
            )
            peer.host = addr
            peer.address = f"{addr}:{peer.port}"

            self.peers[peer.node_id]=peer


    def _register_peer(self, peer: Node):
        """
        Registra un peer si no existe ya.
        """
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

    def exists_leader(self) -> Boolean:
        return self.leader_id!=None
       

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

    def Notify_existence(self):
        for peer in self.peers.values():
            data=self.local_node.to_dict()
            requests.post(f"http://{peer.address}/newNode",json=data ,timeout=2)
