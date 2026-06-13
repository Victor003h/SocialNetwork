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
        
    
        self._stop_event = threading.Event()
        self._thread = None
      
        self.is_leader= self.cluster.local_node.is_leader()
        self.is_subleader= self.cluster.local_node.is_subleader()
      
        # peer_id -> last_success_timestamp
        self.last_seen = {}

    def start(self):
        
        if self._thread and self._thread.is_alive():
            return
        
        self.is_leader = self.cluster.local_node.is_leader()
        self.is_subleader = self.cluster.local_node.is_subleader()
        
        if self.is_subleader or self.is_leader:
            self._stop_event.clear()
            # Ya no pasamos argumentos booleanos por valor para evitar el bug del freeze
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
        
    def stop(self):
        """Despierta al hilo de su sleep y lo apaga en el acto"""
        self._stop_event.set()
        
        # Salvaguarda idéntica para evitar el RuntimeError en el Heartbeat
        if self._thread and self._thread != threading.current_thread():
            self._thread.join(timeout=1.0)
            self._thread = None
        else:
            self._thread = None
    def _loop(self):
        print(f"[HEARTBEAT] Node {self.cluster.local_node.node_id} started")
    
        while not self._stop_event.is_set():
            
            self.is_leader= self.cluster.local_node.is_leader()
            self.is_subleader= self.cluster.local_node.is_subleader()
            
            if not self.is_leader and not self.is_subleader:
                if self._stop_event.wait(self.interval):
                    break
                continue

            now = time.time()
            
            if self.cluster.local_node.is_leader():
                subleader_peers = self.cluster.subleader_manager.subleader_list
                self.Send_heartbeat_leader(subleader_peers, now)
            
            peers = self.cluster.get_peers() 
                
            for peer in peers:
                
                if self._stop_event.is_set():
                    return
                
                try:
                    
                    data = {
                        "id": self.cluster.local_node.node_id,
                        "epoch": self.cluster.current_epoch
                    }
                    requests.post(
                        f"https://{peer.address}/heartbeat",
                        json=data,
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
                        self.cluster.mark_peer_down(peer,self.cluster.local_node.role)
                        self.cluster.Notify_peer_down(peers,peer.node_id)

            if self._stop_event.wait(self.interval):
                break

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
                    self.cluster.secure_args,
                    json={
                        "id": self.cluster.local_node.node_id,
                        "epoch": self.cluster.current_epoch
                    }
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
                    self.cluster.mark_peer_down(peer,self.cluster.local_node.role)