import threading
import time

from sqlalchemy import true



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

        self._stop_event = threading.Event()
        self._thread = None

    # ==============================
    # API pública
    # ==============================

    def start(self):
        
        if self._thread and self._thread.is_alive():
            return  # Ya está corriendo

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Detiene el hilo inmediatamente levantando el evento"""
        self._stop_event.set()
        
        # SALVAGUARDA: Solo hacemos join si NO somos el propio hilo que se está ejecutando
        if self._thread and self._thread != threading.current_thread():
            self._thread.join(timeout=1.0)
            self._thread = None
        else:
            # Si se llamó desde el mismo hilo, limpiamos la referencia sin bloquear
            self._thread = None
    # ==============================
    # Lógica interna
    # ==============================

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            
            if self._stop_event.wait(self.check_interval):
                break # Salimos del bucle inmediatamente
            
            # Si yo soy líder, no monitoreo a nadie
            if self.cluster.local_node.is_leader():
                continue
            
            
            is_subleader= self.cluster.local_node.is_subleader()

            # Anti-entropía: en cada ciclo un follower hace un /sync incremental con
            # su subleader para recuperar WAL perdido (p.ej. un /replicate que no
            # llegó mientras estaba caído, o un reingreso sin reinicio). Es idempotente
            # gracias al orden (epoch, lsn), así que repetirlo no causa daño.
            if not is_subleader:
                try:
                    self.cluster.sync_from_leader(self.cluster.peers)
                except Exception as e:
                    print(f"[ANTI-ENTROPY] sync incremental falló: {e}")

            if is_subleader:
                elapsed = time.time() - self.cluster.last_heartbeat_leader.get("timestamp", 0)
            else:
                elapsed = time.time() - self.cluster.last_heartbeat.get("timestamp", 0)
           # print(f"[FailureDetector] In time {time.time()} last heartbeat {self.cluster.last_heartbeat}")
            
            if elapsed > self.heartbeat_timeout:
                if is_subleader:
                    print("[FailureDetector] leader timeout detected")
                else:
                    print("[FailureDetector] subleader timeout detected")
                 
                self._handle_leader_failure(is_subleader)
                
            # Después de detectar un fallo, salimos del loop para evitar múltiples detecciones 
            # simultáneas
                break 

    def _handle_leader_failure(self, is_subleader):
        """
        Notifica al cluster que el líder falló
        """
        # Evitar múltiples elecciones simultáneas
        if self.cluster.election_in_progress:
            return

        print("[FailureDetector] Triggering leader election")

        # El líder dejó de enviar latidos: lo marcamos caído (alive=False, rol
        # ->follower) antes de reelegir, para no seguir llamándolo y para que su rol
        # obsoleto no contamine el estado que heredaría un nodo nuevo.
        if not is_subleader:
            failed = self.cluster.peers.get(self.cluster.subleader_id)
            if failed:
                self.cluster.mark_peer_down(failed, self.cluster.local_node.role)

        if is_subleader:
            peers= self.cluster.subleader_manager.subleader_list
        else:
            peers = self.cluster.get_peers()

        self.cluster.start_election(peers)
