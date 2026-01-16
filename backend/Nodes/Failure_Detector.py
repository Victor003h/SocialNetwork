import threading
import time

from cluster import ClusterContext


class FailureDetector:
    def __init__(
        self,
        cluster_context:ClusterContext,
        heartbeat_timeout: float = 5.0,
        check_interval: float = 1.0,
    ):
        """
        cluster_context: objeto que maneja el estado del cluster
        heartbeat_timeout: segundos máximos sin heartbeat antes de sospechar fallo
        check_interval: cada cuántos segundos se chequea
        """
        self.cluster = cluster_context
        self.heartbeat_timeout = heartbeat_timeout
        self.check_interval = check_interval

        self._running = False
        self._thread = None

    # ==============================
    # API pública
    # ==============================

    def start(self):
        if self._running and self.cluster.local_node.is_leader():
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False

    def notify_heartbeat(self):
        """
        Se llama cuando llega un heartbeat del líder
        """
        self._last_heartbeat = time.time()

    # ==============================
    # Lógica interna
    # ==============================

    def _monitor_loop(self):
        while self._running:
            time.sleep(self.check_interval)

            # Si yo soy líder, no monitoreo a nadie
            if self.cluster.local_node.is_leader():
                continue

            elapsed = time.time() - self._last_heartbeat

            if elapsed > self.heartbeat_timeout:
                print("[FailureDetector] Leader timeout detected")
                self._handle_leader_failure()

    def _handle_leader_failure(self):
        """
        Notifica al cluster que el líder falló
        """
        # Evitar múltiples elecciones simultáneas
        if self.cluster.is_election_in_progress:
            return

        print("[FailureDetector] Triggering leader election")
        self.cluster.start_election()
