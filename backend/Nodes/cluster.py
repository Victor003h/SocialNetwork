import requests
import time
import socket
from typing import Dict, List
import os
import requests
from sqlalchemy import text


from DataBase import Database

from models.post import Post
from models.follows import Follower
from models.user import User
from models.wal import WALLog

from node import Node
from node_utils import utils
from Subleader_manager import subleaderManager
from HeartbeatSender import HeartbeatSender
from Failure_Detector import FailureDetector

from security.Cert_Manager import CertManager

class ClusterContext:
    """
    Mantiene la vista local del cluster distribuido.
    Encapsula descubrimiento, estado de nodos y topología.
    """

    def __init__(self, local_node: Node):
        self.local_node = local_node

        # Nodos remotos indexados por node_id
        self.peers: Dict[int, Node] = {}

        # Información global del cluster
        self.subleader_id= -1

        self.election_in_progress=False
        
        self.heartbeadSender=HeartbeatSender(self)
        
        self.faliuredetector=FailureDetector(self)
        
        self.last_heartbeat =  {"id": "", "timestamp": time.time()}
        
        self.last_heartbeat_leader = {"id": "", "timestamp": time.time()}
        
        self.database = Database()
        
        self.subleader_manager= subleaderManager(self)
        
        self.utils=utils()
                
        self.database.setupDatabase()
        
        self.security = CertManager(cert_dir='certs')
        
        self.secure_args= self.security.setupCerts()

        # Watermark de orden global (epoch, lsn) reconstruido del WAL durable.
        # Antes last_applied_lsn estaba fijado a 0 ignorando la BD: bug corregido.
        self.current_epoch, self.last_applied_lsn = self.database.get_watermark()

        # Quórum de liderazgo: nº de PCs esperados en el cluster. Con 1 (default,
        # despliegue de un solo PC como la prueba §5) el quórum es trivial.
        self.expected_pcs = int(os.getenv("EXPECTED_PCS", "1"))
        # En modo solo-lectura el nodo sirve lecturas pero rechaza escrituras
        # (se activa si un aspirante a leader global no alcanza mayoría de subleaders).
        self.read_only = False
    
   
    def discover_peers(self):
        """
        Descubre nodos pares usando DNS del servicio (Docker Swarm).
        """
        network_name=os.getenv("NETWORK-ALIAS","cluster_net_serv")
        
        cluster_data= self.utils.Get_Local_Nodes_M1(network_name,self.local_node,self.secure_args)
        
        if cluster_data: 
        
            self.peers= cluster_data.get("peers",{})
            
            subleader= cluster_data.get("subleader_id")
            if subleader     :  self.subleader_id= subleader
            
            last_heartbeat = cluster_data.get("last_heartbeat")
            if last_heartbeat: self.last_heartbeat = last_heartbeat
            
        


    def _register_peer(self, peer: Node):
        """
        Registra un peer si no existe ya.
        """
        for existing in self.peers.values():
            if existing.address == peer.address:
                return

        temp_id = len(self.peers) + 1
        peer.node_id = temp_id
        self.peers[temp_id] = peer

    # -------------------------
    # Accesores
    # -------------------------

    def get_peers(self) -> List[Node]:
        return list(self.peers.values())

    def get_all_nodes(self) -> List[Node]:
        return [self.local_node] + self.get_peers()

    def is_single_node(self) -> bool:
        return len(self.peers) == 0

    
    def General_Endpoint(self,peer:Node,method,endpoint,**kwargs):
        
    
        if self.local_node.role == "subleader":
            peer_data={
                "ip": peer.ip,
                "hostname": peer.host,
                "port": peer.port
            }
            res =self.utils.Remote_Comunicate(
                method, 
                endpoint, 
                peer_data ,
                self.secure_args,
                **kwargs
            )
            return  res
        
        request_kwargs = { **self.secure_args, **kwargs }
        res=requests.request(method, 
                             f"https://{peer.host}:{self.local_node.port}/{endpoint}", 
                             timeout=2, 
                             **request_kwargs)
        res.raise_for_status()
        data=res.json()
             
        return data
    
    def start_election(self,peers):
        
        if self.election_in_progress:
            return
        
        self.election_in_progress = True
        local_id = self.local_node.node_id
        higher_nodes = [
            peer for peer in peers if (peer.node_id > local_id) and peer.alive
        ]

        print(f"[ELECTION] Node {local_id} starting election")
       
        for peer in higher_nodes:
            try:
                
                self.General_Endpoint(peer,"POST","election")
                self.election_in_progress = False
                print(f"[ELECTION] recibo respuesta de  {peer.node_id}")
                return
            except requests.RequestException:
                continue

        # Nadie respondió → soy líder
        self.become_leader(peers)

    def become_leader(self, peers):

        node = self.local_node

        rol= "subleader" if node.role!="subleader" else "leader"

        # Quórum de liderazgo global: sin mayoría de subleaders no se asume el rol de
        # leader (evita un segundo leader en una partición minoritaria). El nodo
        # permanece como subleader sirviendo solo lecturas hasta recuperar quórum.
        if rol == "leader" and not self.has_leadership_quorum():
            print("[LEADER] Sin quórum de subleaders -> modo SOLO-LECTURA; permanezco subleader")
            self.read_only = True
            self.election_in_progress = False
            return

        node.set_role(rol)

        self.StartHeartBeat()
 
        print(f"[{rol}] Node {node.node_id} became {rol}")

        for peer in peers:
            try:
                if not  peer.alive:continue
                self.General_Endpoint(peer,"POST",rol,json={ f"{rol}_id": node.node_id})

            except requests.RequestException:
                pass

        # La elección LOCAL ya terminó. Hay que liberar el flag ANTES de entrar a
        # become_subleader, porque allí se dispara la elección GLOBAL (otra capa de
        # Bully entre subleaders) que también llama a start_election; si el flag
        # siguiera activo, esa segunda elección se auto-bloquearía y el nodo se
        # quedaría atascado en 'subleader' sin llegar a 'leader' (bug de failover).
        self.election_in_progress = False

        if rol=="subleader":
            self.set_subleader(node.node_id)
            self.faliuredetector.stop()
            self.subleader_manager.become_subleader()
        else:

            # Liderazgo global asumido con quórum: salgo de solo-lectura.
            self.read_only = False
            # Nuevo leader global: sube el epoch para que sus escrituras superen
            # (fencing) a cualquier leader obsoleto que reaparezca tras una partición.
            self.current_epoch = self.current_epoch + 1
            print(f"[LEADER] Nuevo epoch global: {self.current_epoch}")

            self.set_leader(node.node_id)
            # Al promoverse, las secuencias de id pueden ir retrasadas respecto a las
            # filas recibidas por replicación/sync (que insertan ids EXPLÍCITOS sin
            # tocar la secuencia). Hay que avanzar TODAS las secuencias a MAX(id) o el
            # primer nextval del nuevo leader colisiona con una PK existente
            # (UniqueViolation en posts/follows tras un failover con datos).
            session = self.database.get_session()
            for table in ("users", "posts", "follows"):
                session.execute(text(
                    f"SELECT setval('{table}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {table}))"
                ))
            session.commit()
            session.close()
    
    def StartHeartBeat(self):
        
        self.heartbeadSender.start()
        return {"status":"ok"}
    def set_leader(self, node_id: int):
        
        if self.last_heartbeat_leader.get("id") != node_id :
           self.subleader_manager.remove_leader()
        
        self.subleader_manager.global_leader_id = node_id
        
    
    def set_subleader(self, node_id: int):
        
        if self.last_heartbeat.get("id") != node_id and self.subleader_id != -1:
            self.mark_peer_down(self.peers[self.subleader_id], self.local_node.role)
            
        self.subleader_id = node_id

    def exists_leader(self) -> bool:
        return self.subleader_id is not None
       
    def to_dict(self) -> dict:
        """
        Representación del estado del cluster (debug / status endpoint).
        """
        return {
            "local_node": self.local_node.to_dict(),
            "subleader_id": self.subleader_id,
            "node_pc_id": self.local_node.node_pc_id,
            "peers": [peer.to_dict() for peer in self.peers.values()],
            # Estado de orden global y modo (útil como evidencia en la prueba §5).
            "epoch": self.current_epoch,
            "last_applied_lsn": self.last_applied_lsn,
            "read_only": self.read_only,
        }

    def __repr__(self):
        return (
            f"<ClusterContext local={self.local_node.node_id} "
            f"peers={len(self.peers)} "
            f"leader={self.subleader_id}>"
        )

    def Notify_existence(self, peers):
        for peer in peers:
            if not  peer.alive:continue
            data=self.local_node.to_dict()
            print(f"Notifinando a {peer.address}")
            try:
                # Un nodo que reingresa cuando otros ya cayeron (p.ej. el "nodo nuevo"
                # de la prueba §5) recibe peers obsoletos del descubrimiento: algunos
                # ya no resuelven en DNS. Tolerar el fallo por peer evita que el boot
                # entero se aborte por un peer muerto; basta con avisar a los vivos.
                self.General_Endpoint(peer,"POST","newNode",json=data)
            except Exception as e:
                print(f"[DISCOVERY] No se pudo notificar a {peer.address}: {e}")
           
    def replicate_to_followers(self,wal):
        for peer in self.peers.values():
            if not  peer.alive:continue
            print (peer)
            data=wal.to_dict()
            try:
                self.General_Endpoint(peer,"POST","replicate",json=data)
            except Exception as e:
                # Replicación best-effort (eventual consistency, sin ack de quórum):
                # un follower caído NO debe abortar una escritura ya confirmada en el
                # leader. Se marca abajo (alive=False, rol->follower); la anti-entropía
                # /sync lo pondrá al día al reingresar.
                print(f"[REPLICATE] follower {peer.node_id} inalcanzable: {e}")
                self.mark_peer_down(peer, self.local_node.role)
        
  

    def apply_operation(self,msg):
        session = self.database.get_session()

        table_name= msg["table_name"]
        
        if table_name == "users":
            User.Replicate_user(msg,session)
        elif table_name == "posts":
            Post.Replicate_Post(msg,session)
        elif table_name == "follows":
            Follower.Replicate_Follower(msg,session)
        else:
            print("La tabla a replicar no existe")

        
    def sync_from_leader(self, peers):
        if self.subleader_id == self.local_node.node_id: return

        # peers es un dict {node_id: Node}; .get evita KeyError si aún no conocemos
        # al subleader (p.ej. justo tras un reingreso o durante una reelección).
        leader = peers.get(self.subleader_id)
        if leader is None:
            return
        json={"last_epoch": self.current_epoch, "last_lsn": self.last_applied_lsn}

        try:
            wal_entries = self.General_Endpoint(leader,"POST","sync", json=json)
        except Exception as e:
            # El subleader del que sincronizamos puede haber caído justo ahora; no
            # propagamos el error (la reelección/anti-entropía lo resolverá).
            print(f"[SYNC] subleader {self.subleader_id} inalcanzable: {e}")
            return

        if not wal_entries:
            return

        session = self.database.get_session()

        for entry in wal_entries:
            epoch = entry.get("epoch", 0)
            lsn = entry["lsn"]

            # 🔐 defensa crítica: solo WAL estrictamente más nuevo en orden (epoch, lsn)
            if not self.is_newer(epoch, lsn):
                continue

            wal = WALLog(**entry)
            session.add(wal)

            self.apply_operation(entry)
            self.advance_watermark(epoch, lsn)

        session.commit()
        session.close()


    def next_lsn(self):
        # lsn monótono global: nunca se reinicia, ni siquiera al cambiar de epoch.
        self.last_applied_lsn=self.last_applied_lsn+1
        return self.last_applied_lsn

    def is_newer(self, epoch, lsn) -> bool:
        """True si la entrada (epoch, lsn) es estrictamente posterior al watermark.

        Una sola comparación lexicográfica resuelve a la vez idempotencia (ignorar
        lo ya aplicado) y fencing (ignorar a un leader viejo de epoch inferior).
        """
        return (epoch, lsn) > (self.current_epoch, self.last_applied_lsn)

    def advance_watermark(self, epoch, lsn):
        """Avanza el watermark a (epoch, lsn) si es más reciente."""
        if (epoch, lsn) > (self.current_epoch, self.last_applied_lsn):
            self.current_epoch = epoch
            self.last_applied_lsn = lsn

    def has_leadership_quorum(self) -> bool:
        """¿Puede este nodo asumir el liderazgo global con mayoría de subleaders?

        Con expected_pcs <= 1 (despliegue de un solo PC, p.ej. la prueba §5) el
        quórum es trivial. En multi-PC exige alcanzar > mitad de los PCs esperados,
        para que una partición minoritaria no pueda elegir un segundo leader.
        """
        if self.expected_pcs <= 1:
            return True
        reachable = 1 + len(self.subleader_manager.subleader_list)  # yo + subleaders vistos
        return reachable > self.expected_pcs // 2

    def adopt_higher_epoch(self, epoch: int, leader_id: int):
        """Reacción de fencing al ver evidencia de un epoch superior.

        Si este nodo se creía leader global pero aparece un epoch mayor (otro leader
        ganó tras una partición), cede el liderazgo y vuelve a follower. Resuelve el
        split-brain cuando la partición se cura: el leader de menor epoch se rinde.
        """
        if epoch <= self.current_epoch:
            return
        self.current_epoch = epoch
        if self.local_node.is_leader():
            print(f"[FENCING] Epoch superior {epoch} detectado (leader {leader_id}); cedo liderazgo")
            self.local_node.set_role("follower")
            self.heartbeadSender.stop()
            self.set_leader(leader_id)
            self.faliuredetector.start()
    
    def mark_peer_down(self,peer,node_rol):
        # Caída de un subleader vista por el leader global (multi-PC): sale de la
        # lista de subleaders (por id, porque la lista contiene Nodes).
        if node_rol == "leader" and peer.role == "subleader":
            self.subleader_manager.subleader_list = [
                s for s in self.subleader_manager.subleader_list if s.node_id != peer.node_id
            ]
        # Estado uniforme del nodo caído: no-vivo y rol degradado a 'follower' (el
        # rol con el que reaparecería al relevantarse). Así su rol obsoleto (p.ej.
        # 'leader') no contamina el descubrimiento de un nodo nuevo, que hereda el
        # 'alive' real vía Craft_Node.
        target = self.peers.get(peer.node_id)
        if target:
            target.alive = False
            target.role = "follower"
            print(f"[FAILURE DETECTOR] Marked peer {peer.node_id} as down")

    def Notify_peer_down(self,peers,failure_id):

        for peer in peers:
            if not  peer.alive:continue
            data= {"failure_id":failure_id}
            print(f"Notifinando a {peer.address}")
            try:
                self.General_Endpoint(peer,"POST","PeerDown",json=data)
            except Exception as e:
                # Difusión best-effort: si un peer al que avisamos también está caído,
                # no abortamos el aviso al resto; lo marcamos abajo.
                print(f"[PeerDown] {peer.node_id} inalcanzable: {e}")
                self.mark_peer_down(peer, self.local_node.role)

    def notify_gateway(self):
        """Push: informa al api_gateway que ESTE nodo es el subleader de su PC.

        La api dirige TODA su comunicación al subleader del grupo (no a followers
        ni directo al leader global). En cada (re)elección de subleader -p.ej. tras
        la caída del anterior- el nuevo subleader se reanuncia, de modo que la api
        siempre apunta al vigente. Reúsa el patrón mTLS Remote_Comunicate: resuelve
        la IP del gateway por DNS de Docker y fija el SAN de su certificado.
        """
        service = os.getenv("API_GATEWAY_SERVICE", "api_services")     # nombre DNS -> IP
        host = os.getenv("API_GATEWAY_HOST", "node9.cluster_net")       # SAN del cert de api
        port = int(os.getenv("API_GATEWAY_PORT", "7000"))
        try:
            ip = socket.gethostbyname(service)
        except Exception as e:
            print(f"[GATEWAY] No se pudo resolver {service}: {e}")
            return
        node_data = {"ip": ip, "hostname": host, "port": port}
        payload = {
            "address": f"{self.local_node.host}:{self.local_node.port}",
            "ip": self.local_node.ip,
        }
        try:
            self.utils.Remote_Comunicate(
                "POST", "cluster/subleader", node_data, self.secure_args, json=payload
            )
            print(f"[GATEWAY] Notificado a api: subleader = {payload['address']}")
        except Exception as e:
            print(f"[GATEWAY] Fallo notificando a api: {e}")

    def ensure_single_leader(self, attempts: int = 3, delay: int = 2):
        """Reconciliación de liderazgo determinista (Bully) tras el bootstrap.

        Mitiga la ventana de carrera del arranque simultáneo: varios nodos del mismo
        PC pueden auto-promoverse a subleader a la vez. Sondea vía /info a todos los
        nodos vivos de su node_pc_id SIN mutar su propio rol durante el sondeo, los
        registra como peers y aplica la regla Bully: el de mayor node_id sobrevive
        como subleader único; el resto cede a follower y re-sincroniza. Determinista
        ⇒ exactamente un líder converge. Reúsa get_ips_for_alias / Remote_Comunicate
        / Craft_Node y sync_from_leader; no introduce un protocolo de consenso nuevo.
        """
        alias = os.getenv("NETWORK-ALIAS", "cluster_net_serv")
        local_id = self.local_node.node_id

        for _ in range(attempts):
            nodes_info = self.utils.get_ips_for_alias(alias)
            for host, info in nodes_info.items():
                if host == self.local_node.host:
                    continue
                node_data = {"ip": info.get("ip"), "hostname": host, "port": self.local_node.port}
                try:
                    data = self.utils.Remote_Comunicate("GET", "info", node_data, self.secure_args)
                except Exception:
                    continue
                if not data:
                    continue
                peer = self.utils.Craft_Node(data.get("local_node", {}))
                if peer.node_id is None or peer.node_pc_id != self.local_node.node_pc_id:
                    continue
                # Registrar/refrescar el peer sin tocar mi rol.
                self.peers[peer.node_id] = peer

            # Regla Bully: ¿existe un peer vivo de mi PC con mayor id?
            higher = [
                p for p in self.peers.values()
                if p.alive and p.node_pc_id == self.local_node.node_pc_id and p.node_id > local_id
            ]
            if self.local_node.is_subleader() and higher:
                winner = max(higher, key=lambda p: p.node_id)
                print(f"[BOOTSTRAP] Multi-líder detectado; el mayor id {winner.node_id} gana")
                self.step_down_to_follower(winner.node_id)
                return

            time.sleep(delay)

        # Si soy el de mayor id (o ya soy follower) no hay nada que ceder: el líder
        # único es el de mayor node_id, que permanece como subleader.
        print(f"[BOOTSTRAP] Reconciliación completa; rol estable = {self.local_node.role}")

        # Durante la carrera de arranque varios nodos pudieron auto-anunciarse como
        # subleader a la api; el ganador (sigo siendo subleader) re-anuncia al final
        # para que la api quede apuntando al subleader definitivo, no a un perdedor
        # que ya cedió a follower.
        if self.local_node.is_subleader():
            self.notify_gateway()

    def step_down_to_follower(self, winner_id: int):
        """Cede el liderazgo local a winner_id y se reintegra como follower.

        Variante de arranque de adopt_higher_epoch a nivel subleader: para el
        HeartbeatSender, fija el subleader, re-sincroniza el WAL del ganador y arranca
        el FailureDetector para monitorear al nuevo líder.
        """
        print(f"[BOOTSTRAP] Nodo {self.local_node.node_id} cede liderazgo a {winner_id}; me vuelvo follower")
        self.local_node.set_role("follower")
        self.read_only = False
        try:
            self.heartbeadSender.stop()
        except Exception:
            pass
        self.subleader_id = winner_id
        try:
            self.sync_from_leader(self.peers)
        except Exception as e:
            print(f"[BOOTSTRAP] sync inicial tras step-down falló: {e}")
        self.faliuredetector.start()
