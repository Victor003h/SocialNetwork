from re import sub
import threading
import requests
import time
from Failure_Detector import FailureDetector
from Nodes.node import Node

class subleaderManager:
    def __init__(self, cluster):
        self.cluster = cluster
        self.pc_map = {}  # {pc_id: {"subleader": info, "nodes": [ips]}}
        self.subleader_list = []  # Lista de sublíderes descubiertos
        self.global_leader_id : int | None = None
        self.is_global_leader = False
        self.global_heartbeat = None
        self.global_detector = None
        self.global_leader : Node 

    def become_subleader(self):
        """Activa las funciones de nivel de red del Sublíder"""
        print(f"[subleader] Node {self.cluster.local_node.node_id} is now a subleader.")
        
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
                    p_host = p_info.get("host")
                    if p_host in search_list:
                        search_list.remove(p_host)
                
            except Exception as e:
                print(f"[DISCOVERY] Could not reach {target_host}: {e}")

        self.pc_map = discovered_pcs
        print(f"[DISCOVERY] Topology discovered: {list(self.pc_map.keys())}")

    def check_global_leadership(self):
        """Paso 2: Buscar al líder global entre los sublíderes descubiertos"""
        leader_found = False

        for pc_id, info in self.pc_map.items():
            # Si alguien reporta ser leader, es el líder global
            subleader= info.get("subleader", {})
            subleader_role= subleader.get("role")
            if subleader_role == "leader":
                self.global_leader = subleader
                leader_found = True
            self.subleader_list.append(subleader)

        if not leader_found:
             self.cluster.start_election(self.subleader_list)
        else:
            self.start_global_failure_detector()

    def start_global_failure_detector(self):
        """Paso 3: Si hay líder global, empezar a monitorear su salud"""
        print(f"[subleader] Starting failure detector for global leader {self.global_leader.address }")
        self.global_detector = FailureDetector(self.cluster)
        self.global_detector.start()

    def relay_replication(self, wal):
        """Paso 4: El sublíder recibe del líder global y envía a sus locales"""
        print(f"[RELAY] Replicating WAL {wal.lsn} to local followers")
        self.cluster.replicate_to_followers(wal)
    def get_leader_address(self):
        if self.global_leader_id:
            return self.global_leader.address
        return None