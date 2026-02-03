import threading
import time
import requests
from sqlalchemy import PrimaryKeyConstraint

from cluster import ClusterContext


class HeartbeatSender:
    def __init__(self, cluster:ClusterContext, interval=2):
        self.cluster = cluster
        self.interval = interval
        self.running = False

    def start(self):
        if self.running  :
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _loop(self):
        print(f"[HEARTBEAT] Node {self.cluster.local_node.node_id} starts sending heartbeat")
        while self.running:
         
            if not self.cluster.local_node.is_leader():
                time.sleep(self.interval)
                continue

            for peer in self.cluster.get_peers():
               
                try:
                    print(f"[HEARTBEAT] manda heartbeat a {peer.address}")
                    print(peer.address)
                    requests.post(f"https://{peer.address}/heartbeat",timeout=1, **self.cluster.secure_args)
                    print(f"[HEARTBEAT] Sent to {peer.address}")

                except Exception as e:
                    print(f"[HEARTBEAT] fallo al mandar heartbeat a  {peer.address}")
                    # no hacemos nada: fallo parcial permitido
                    pass

            time.sleep(self.interval)
