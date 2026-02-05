import threading
import time
import requests
from sqlalchemy import PrimaryKeyConstraint

from cluster import ClusterContext


class HeartbeatSender:
    def __init__(self, cluster, interval=2, timeout=6):
        self.cluster = cluster
        self.interval = interval
        self.timeout = timeout  # tiempo máximo sin heartbeat
        self.running = False

        # peer_id -> last_success_timestamp
        self.last_seen = {}

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _loop(self):
        print(f"[HEARTBEAT] Node {self.cluster.local_node.node_id} started")

        while self.running:
            if not self.cluster.local_node.is_leader():
                time.sleep(self.interval)
                continue

            now = time.time()

            for peer in self.cluster.get_peers():
                
                try:
                    requests.post(
                        f"https://{peer.address}/heartbeat",
                        timeout=1, 
                        **self.cluster.secure_args
                    )

                    # heartbeat OK
                    self.last_seen[peer.node_id] = now
                    if not peer.alive :
                        self.cluster[peer.node_id].alive=True
                        
                except Exception:
                    # no respuesta → se evalúa por timeout
                    last = self.last_seen.get(peer.node_id)

                    if last and (now - last) > self.timeout:
                        print(f"[HEARTBEAT] Peer {peer.node_id} DOWN")
                        self.cluster.mark_peer_down(peer)

            time.sleep(self.interval)

