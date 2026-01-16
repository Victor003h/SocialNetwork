import threading
import time
import requests

from cluster import ClusterContext


class HeartbeatSender:
    def __init__(self, cluster:ClusterContext, interval=2):
        self.cluster = cluster
        self.interval = interval
        self.running = False

    def start(self):
        if self.running and not self.cluster.local_node.is_leader()  :
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            if not self.cluster.local_node.is_leader():
                time.sleep(self.interval)
                continue

            for peer in self.cluster.get_peers():
                try:
                    requests.post(
                        f"{peer.address}/cluster/heartbeat",
                        timeout=1
                    )
                except Exception:
                    # no hacemos nada: fallo parcial permitido
                    pass

            time.sleep(self.interval)
