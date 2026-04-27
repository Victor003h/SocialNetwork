from re import sub
import threading
import time
import requests
from sqlalchemy import PrimaryKeyConstraint




class HeartbeatSender:
    def __init__(self, cluster, interval=2, timeout=6):
        self.cluster = cluster
        self.interval = interval
        self.timeout = timeout  # tiempo máximo sin heartbeat
        self.subleader_running = False
        self.leader_running = False
        self.is_leader= self.cluster.local_node.is_leader()
        self.is_subleader= self.cluster.local_node.is_subleader()
        # peer_id -> last_success_timestamp
        self.last_seen = {}

    def start(self):
        
        if not self.subleader_running and self.is_subleader:
            self.subleader_running = True
            threading.Thread(target=self._loop, args=(self.subleader_running,), daemon=True).start()
        
            return
        if not self.leader_running and self.is_leader:
            self.leader_running = True
            threading.Thread(target=self._loop, args=(self.leader_running,), daemon=True).start()
        
    def stop(self):
        self.subleader_running = False
        self.leader_running = False
        
    def _loop(self,running):
        print(f"[HEARTBEAT] Node {self.cluster.local_node.node_id} started")
    
        while running:
            
            self.is_leader= self.cluster.local_node.is_leader()
            self.is_subleader= self.cluster.local_node.is_subleader()
            
            if not self.is_leader and not self.is_subleader:
                time.sleep(self.interval)
                continue

            now = time.time()
            
            
            peers = self.cluster.get_peers() 
                
            for peer in peers:
                
                try:
                    if self.is_leader:
                        subleader_peers = self.cluster.subleader_manager.subleader_list
                        self.Send_heartbeat_leader(subleader_peers,now)
                     
                   
                    requests.post(
                        f"https://{peer.address}/heartbeat",
                        timeout=1, 
                        **self.cluster.secure_args
                    )

                    # heartbeat OK
                    self.last_seen[peer.node_id] = now
                    if not peer.alive :
                        self.cluster.peers[peer.node_id].alive=True
                        
                except Exception:
                    # no respuesta → se evalúa por timeout
                    last = self.last_seen.get(peer.node_id)

                    if last and (now - last) > self.timeout:
                        print(f"[HEARTBEAT] Peer {peer.node_id} DOWN")
                        self.cluster.mark_peer_down(peer,self.is_leader)

            time.sleep(self.interval)

    def Send_heartbeat_leader(self, peers,now):
        
        for peer in peers:
            try:

                print("leader entro al heartbeat")
                self.cluster.utils.Remote_Comunicate(
                    "POST",
                    "heartbeat_leader",
                    {
                        "ip": peer.ip,
                        "hostname": peer.host,
                        "port": peer.port
                    },
                    self.cluster.secure_args
                )

                # heartbeat OK
                self.last_seen[peer.node_id] = now
                if not peer.alive :
                    self.cluster.peers[peer.node_id].alive=True

            except Exception:
                # no respuesta → se evalúa por timeout
                last = self.last_seen.get(peer.node_id)
                if last and (now - last) > self.timeout:
                    print(f"[HEARTBEAT] Peer {peer.node_id} DOWN")
                    self.cluster.mark_peer_down(peer,self.is_leader)