import select
from operator import add
import select
import socket
from tarfile import data_filter
import time
from typing import Dict, List
import os
from flask import session
import requests
from sqlalchemy import Boolean

from DataBase import Database

from node import Node
from security.Cert_Manager import CertManager
from models.user import User
from models.wal import WALLog


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
        self.last_applied_lsn=0

        self.database = Database()
        
        self.security = CertManager(cert_dir='certs')
        
        (self.cert_path, self.key_path), self.ca_path = self.security.get_context()
        
        # Definimos los argumentos estándar para requests seguros
        self.secure_args = {
            "cert": (self.cert_path, self.key_path), # Mi carta de presentación
            "verify": self.ca_path    # Contra qué valido a los demás
            
        }
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
            addr,_,_=socket.gethostbyaddr(addr)
            print(f"Descubriendo nodo en {addr}")
            # Excluirse a sí mismo
           
            if addr == self.local_node.host:
                continue

            response=  requests.get(f"https://{addr}:{self.local_node.port}/info", timeout=2, **self.secure_args)

            data=response.json()
            
            leader_id=data.get("leader_id")

            node=data.get("local_node",{})

            role=node.get("role")
            if role=="leader":
                self.leader_id=leader_id
                self.local_node.role="follower"
                self.last_heartbeat=time.time()
            

            peer = Node(
                node_id=node.get("node_id"),
                service_name=node.get("service_name"),
                port=self.local_node.port,
            )
            peer.host = addr
            peer.address = f"{addr}:{peer.port}"
            peer.role=role

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

        self.discover_peers()
        self.election_in_progress = True
        local_id = self.local_node.node_id
        higher_nodes = [
            peer for peer in self.get_peers() if peer.node_id > local_id
        ]

        print(f"[ELECTION] Node {local_id} starting election")
       
        for peer in higher_nodes:
            try:
                requests.post(f"https://{peer.address}/election", timeout=2, **self.secure_args)
                self.election_in_progress = False
                print(f"[ELECTION] recibo respuesta de  {peer.node_id}")
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
                    f"https://{peer.address}/leader",
                    json={"leader_id": node.node_id},
                    timeout=2,
                    **self.secure_args
                )
            except requests.RequestException:
                pass


        requests.post(f"https://{self.local_node.address}/start_heartbeat" ,timeout=2, **self.secure_args)  

 
        self.election_in_progress = False

    def set_leader(self, node_id: int):
        self.leader_id = node_id

    def exists_leader(self) -> bool:
        return self.leader_id is not None
       
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
            print(f"Notifinando a {peer.address}")
            requests.post(f"https://{peer.address}/newNode",json=data ,timeout=2, **self.secure_args)

    
    def replicate_to_followers(self,wal):
        for peer in self.peers.values():
            data=wal.to_dict()
            requests.post(f"https://{peer.address}/replicate",json=data ,timeout=2, **self.secure_args)

  

    def apply_operation(self,msg):
        session = self.database.get_session()

        try:
            if msg["operation"] == "INSERT":
                user = User(**msg["payload"])
                session.add(user)

            elif msg["operation"] == "UPDATE":
                user = session.get(User, msg["payload"]["id"])
                if user:
                    user.username = msg["payload"]["username"]
                    user.password_hash = msg["payload"]["password_hash"]

            elif msg["operation"] == "DELETE":
                user = session.get(User, msg["payload"]["id"])
                if user:
                    session.delete(user)

            session.commit()

        finally:
            session.close()
        
    def sync_from_leader(self):
        leader=self.peers[self.leader_id] # type: ignore
        res = requests.post( 
            f"https://{leader.address}/sync",
            json={"last_lsn": self.last_applied_lsn},
            **self.secure_args
        )

        session=self.database.get_session()
        for entry in res.json():
            wal = WALLog(
                lsn=entry["lsn"],
                operation=entry["operation"],
                table_name=entry["table"],
                payload=entry["payload"]
            )
            session.add(wal)

            self.apply_operation(entry)
            self.last_applied_lsn = entry["lsn"]

        session.commit()
        session.close()

    def next_lsn(self):
        self.last_applied_lsn=self.last_applied_lsn+1
        return self.last_applied_lsn