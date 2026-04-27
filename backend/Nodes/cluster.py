import requests
import time
from typing import Dict, List
import os
import requests
from sqlalchemy import text


from DataBase import Database

from models.post import Post
from models.follows import Follower
from models.user import User
from models.wal import WALLog

from node import Node
from node_utils import utils
from Subleader_manager import subleaderManager
from HeartbeatSender import HeartbeatSender

from security.Cert_Manager import CertManager

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
        self.subleader_id: int | None = None

        self.election_in_progress=False
        
        self.last_heartbeat = time.time()
        
        self.last_heartbeat_leader = time.time()
        
        self.database = Database()
        
        self.subleader_manager= subleaderManager(self)
        
        self.utils=utils()
                
        self.database.setupDatabase()
        
        self.security = CertManager(cert_dir='certs')
        
        self.secure_args= self.security.setupCerts()
    
        self.last_applied_lsn=0
    
   
    def discover_peers(self):
        """
        Descubre nodos pares usando DNS del servicio (Docker Swarm).
        """
        network_name=os.getenv("NETWORK-ALIAS","cluster_net_serv")
        
        cluster_data= self.utils.Get_Local_Nodes_M1(network_name,self.local_node,self.secure_args)
        
        if cluster_data: 
        
            self.peers= cluster_data.get("peers",{})
            
            subleader= cluster_data.get("subleader_id")
            if subleader     :  self.subleader_id= subleader
            
            last_heartbeat = cluster_data.get("last_heartbeat")
            if last_heartbeat: self.last_heartbeat = last_heartbeat
            
        


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

    
    def General_Endpoint(self,peer:Node,method,endpoint,**kwargs):
        
    
        if self.local_node.role == "subleader":
            peer_data={
                "ip": peer.ip,
                "hostname": peer.host,
                "port": peer.port
            }
            res =self.utils.Remote_Comunicate(
                method, 
                endpoint, 
                peer_data ,
                self.secure_args,
                **kwargs
            )
            return  res
        
        request_kwargs = { **self.secure_args, **kwargs }
        res=requests.request(method, 
                             f"https://{peer.host}:{self.local_node.port}/{endpoint}", 
                             timeout=2, 
                             **request_kwargs)
        res.raise_for_status()
        data=res.json()
             
        return data
    
    def start_election(self,peers):
        
        if self.election_in_progress:
            return
        
        self.election_in_progress = True
        local_id = self.local_node.node_id
        higher_nodes = [
            peer for peer in peers if (peer.node_id > local_id) and peer.alive
        ]

        print(f"[ELECTION] Node {local_id} starting election")
       
        for peer in higher_nodes:
            try:
                
                self.General_Endpoint(peer,"POST","election")
                self.election_in_progress = False
                print(f"[ELECTION] recibo respuesta de  {peer.node_id}")
                return
            except requests.RequestException:
                continue

        # Nadie respondió → soy líder
        self.become_leader(peers)

    def become_leader(self, peers):
        
        node = self.local_node
        
        rol= "subleader" if node.role!="subleader" else "leader"
        
        node.set_role(rol)
        

        print(f"[LEADER] Node {node.node_id} became {rol}")

        if rol=="subleader":
            self.set_subleader(node.node_id)
            self.subleader_manager.become_subleader()
        else:
            
            self.set_leader(node.node_id)
            session = self.database.get_session()

            session.execute(text("""
                SELECT setval(
                    'users_id_seq',
                    (SELECT COALESCE(MAX(id), 1) FROM users)
                )
            """))

            session.commit()
            session.close()


        for peer in peers:
            try:
                if not  peer.alive:continue
                self.General_Endpoint(peer,"POST",rol,json={ f"{rol}_id": node.node_id})
                
            except requests.RequestException:
                pass
    
        self.StartHeartBeat()
 
        self.election_in_progress = False
    
    def StartHeartBeat(self):
        heartbead=HeartbeatSender(self)
        heartbead.start()
        return {"status":"ok"}
    def set_leader(self, node_id: int):
        
        if self.local_node.role=="leader":
            self.subleader_manager.global_leader_id = node_id
    
    def set_subleader(self, node_id: int):
        
        if self.local_node.role=="subleader":
            self.subleader_id = node_id

    def exists_leader(self) -> bool:
        return self.subleader_id is not None
       
    def to_dict(self) -> dict:
        """
        Representación del estado del cluster (debug / status endpoint).
        """
        return {
            "local_node": self.local_node.to_dict(),
            "subleader_id": self.subleader_id,
            "node_pc_id": self.local_node.node_pc_id,
            "peers": [peer.to_dict() for peer in self.peers.values()],
        }

    def __repr__(self):
        return (
            f"<ClusterContext local={self.local_node.node_id} "
            f"peers={len(self.peers)} "
            f"leader={self.subleader_id}>"
        )

    def Notify_existence(self, peers):
        for peer in peers:
            if not  peer.alive:continue
            data=self.local_node.to_dict()
            print(f"Notifinando a {peer.address}")
            self.General_Endpoint(peer,"POST","newNode",json=data)
           
    def replicate_to_followers(self,wal):
        for peer in self.peers.values():
            if not  peer.alive:continue
            print (peer)
            data=wal.to_dict()
            self.General_Endpoint(peer,"POST","replicate",json=data)
        
  

    def apply_operation(self,msg):
        session = self.database.get_session()

        table_name= msg["table_name"]
        
        if table_name == "users":
            User.Replicate_user(msg,session)
        elif table_name == "posts":
            Post.Replicate_Post(msg,session)
        elif table_name == "follows":
            Follower.Replicate_Follower(msg,session)
        else:
            print("La tabla a replicar no existe")

        
    def sync_from_leader(self, peers):
        leader = peers[self.subleader_id] # type: ignore
        json={"last_lsn": self.last_applied_lsn}
        
        wal_entries = self.General_Endpoint(leader,"POST","sync", json=json)
        
        if not wal_entries:
            return

        session = self.database.get_session()

        for entry in wal_entries:
            lsn = entry["lsn"]

            # 🔐 defensa crítica: solo WAL nuevos
            if lsn <= self.last_applied_lsn:
                continue

            wal = WALLog(**entry)
            session.add(wal)

            self.apply_operation(entry)
            self.last_applied_lsn = lsn

        session.commit()
        session.close()


    def next_lsn(self):
        self.last_applied_lsn=self.last_applied_lsn+1
        return self.last_applied_lsn
    
    def mark_peer_down(self,peer,is_leader):
        
        if is_leader and self.local_node.role=="subleader":
            self.subleader_manager.subleader_list.remove(peer.node_id)
        else:
            self.peers[peer.node_id].alive=False

    