import threading
import time



class FailureDetector:
    def __init__(
        self,
        cluster_context,
        heartbeat_timeout: float = 10.0,
        check_interval: float = 5.0,
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
        if self._running :
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False

    # ==============================
    # Lógica interna
    # ==============================

    def _monitor_loop(self):
        while self._running:
            time.sleep(self.check_interval)
            # Si yo soy líder, no monitoreo a nadie
            if self.cluster.local_node.is_leader():
                continue

            is_subleader= self.cluster.local_node.is_subleader()
            
            if is_subleader:
                elapsed = time.time() - self.cluster.last_heartbeat_leader    
            else:
                elapsed = time.time() - self.cluster.last_heartbeat
           # print(f"[FailureDetector] In time {time.time()} last heartbeat {self.cluster.last_heartbeat}")
            
            if elapsed > self.heartbeat_timeout:
                if is_subleader:
                    print("[FailureDetector] leader timeout detected")
                else:
                    print("[FailureDetector] subleader timeout detected")
                self._handle_leader_failure(is_subleader)

    def _handle_leader_failure(self, is_subleader):
        """
        Notifica al cluster que el líder falló
        """
        # Evitar múltiples elecciones simultáneas
        if self.cluster.election_in_progress:
            return

        print("[FailureDetector] Triggering leader election")
        
        if is_subleader:
            peers= self.cluster.subleader_manager.subleader_list
        else:
            peers = self.cluster.get_peers()
        self.cluster.start_election(peers)
