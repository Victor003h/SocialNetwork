from re import sub
import threading
import requests
import time
from Failure_Detector import FailureDetector
from node import Node

class subleaderManager:
    def __init__(self, cluster):
        self.cluster = cluster
        self.pc_map = {}  # {pc_id: {"subleader": info, "nodes": [ips]}}
        self.subleader_list = []  # Lista de sublíderes descubiertos
        self.global_leader_id :int 
        self.is_global_leader = False
        self.global_heartbeat = None
        self.global_detector : FailureDetector

    def become_subleader(self):
        """Activa las funciones de nivel de red del Sublíder"""
        print(f"[subleader] Node {self.cluster.local_node.node_id} is now a subleader.")

        # Push al api_gateway: a la api solo le importa quién es el subleader de su
        # grupo. Al volverse subleader (arranque o tras la caída del anterior) se
        # anuncia para que la api dirija sus peticiones a este nodo.
        self.cluster.notify_gateway()

        self.global_leader_id = -1
        # 1. Descubrimiento de la topología de red (Otras PCs)
        self.discover_global_topology()
        
        # 2. Determinar si existe un Líder Global o iniciar elección
        self.check_global_leadership()

    def discover_global_topology(self):
        """Implementa tu algoritmo de poda de lista de IPs"""
        potential_ips = self.cluster.utils.get_ips_for_alias("cluster_net")
        search_list = list(potential_ips.keys()) # Lista de hostnames/IPs
        
        discovered_pcs = {}

        while search_list:
            target_host = search_list.pop(0)
            try:  
                
                data_node= {
                    "ip": potential_ips[target_host].get("ip"),
                    "hostname": target_host, 
                    "port": self.cluster.local_node.port
                }

                data = self.cluster.utils.Remote_Comunicate("GET", "info", data_node, self.cluster.secure_args)

                if data is None: continue

                pc_id = data["node_pc_id"]
                # Obtenemos la lista de todos los nodos en esa PC remota
                remote_peers = data.get("peers", {})
                subleader_id = data.get("subleader_id")
                
                if not subleader_id:  continue
                
                remote_peers = [self.cluster.utils.Craft_Node(v) for v in remote_peers]
                remote_peers = {peer.node_id: peer for peer in remote_peers}
                
                subleader_node= remote_peers.get(subleader_id)
                
                if subleader_node is None:
                    print(f"[DISCOVERY] No subleader found in PC {pc_id} (host {target_host})")
                    continue
                # Guardamos la estructura
                discovered_pcs[pc_id] = {
                    "subleader": subleader_node ,
                    "nodes": remote_peers,
                    "address": subleader_node.address
                }

                # OPTIMIZACIÓN: Quitamos de la búsqueda todos los IPs que pertenecen a esa PC
                for p_id, p_info in remote_peers.items():
                    p_host = p_info.host
                    if p_host in search_list:
                        search_list.remove(p_host)
                
            except Exception as e:
                print(f"[DISCOVERY] Could not reach {target_host}: {e}")

        self.pc_map = discovered_pcs
        print(f"[DISCOVERY] Topology discovered: {list(self.pc_map.keys())}")

    def check_global_leadership(self):
        """Paso 2: Buscar al líder global entre los sublíderes descubiertos"""
        leader_found = False
        print(f"[LEADERSHIP] Checking for global leader among {len(self.pc_map)} PCs")
        
        for pc_id, info in self.pc_map.items():
            # Si alguien reporta ser leader, es el líder global
            subleader= info.get("subleader", {})
            subleader_role= subleader.role
            if subleader_role == "leader":
                self.global_leader_id = subleader.node_id
                leader_found = True
            self.subleader_list.append(subleader)

        if not leader_found:
             print("[LEADERSHIP] No global leader found, starting election among subleaders")
             self.cluster.start_election(self.subleader_list)
        else:
            self.start_global_failure_detector()

    def start_global_failure_detector(self):
        """Paso 3: Si hay líder global, empezar a monitorear su salud"""
        print(f"[subleader] Starting failure detector for global leader {self.global_leader_id }")
        self.global_detector = FailureDetector(self.cluster)
        self.global_detector.start()

    def relay_replication(self, wal):
        """El leader global propaga el WAL en dos saltos:
        1) a sus followers locales (mismo PC), y
        2) a los demás subleaders (otros PCs), que a su vez lo re-replican a sus
           propios followers en el handler /replicate.
        """
        print(f"[RELAY] Replicating WAL {wal.lsn} to local followers")
        self.cluster.replicate_to_followers(wal)

        # Salto cross-PC: solo el leader global propaga hacia los otros subleaders.
        if not self.cluster.local_node.is_leader():
            return

        for sub in self.subleader_list:
            if sub.node_id == self.global_leader_id:
                continue  # ese subleader soy yo (leader global)
            if not getattr(sub, "alive", True):
                continue
            try:
                node_data = {
                    "ip": sub.ip,
                    "hostname": sub.host,
                    "port": self.cluster.local_node.port,
                }
                self.cluster.utils.Remote_Comunicate(
                    "POST", "replicate", node_data,
                    self.cluster.secure_args, json=wal.to_dict()
                )
                print(f"[RELAY] WAL {wal.lsn} enviado al subleader {sub.node_id}")
            except Exception as e:
                print(f"[RELAY] Error replicando al subleader {sub.node_id}: {e}")
    
    def get_global_leader(self):
        """Devuelve el Node del leader global, o None si aún no se conoce.

        subleader_list es una lista de Nodes (uno por PC); global_leader_id es un
        node_id, NO un índice de lista, por eso se busca por coincidencia de id.
        """
        leader_id = getattr(self, "global_leader_id", -1)
        if leader_id in (None, -1):
            return None
        for sub in self.subleader_list:
            if sub.node_id == leader_id:
                return sub
        return None

    def get_leader_address(self):
        leader = self.get_global_leader()
        return leader.address if leader else None
    
    def remove_leader(self):
        
        if self.global_leader_id != -1:
            self.subleader_list.pop(self.global_leader_id)
            self.global_leader_id= -1
            self.global_detector.stop()
        
        