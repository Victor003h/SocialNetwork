import requests
import socket
from Nodes.node_utils import utils as remote_utils
class utils:
    
    def __init__(self,secure_args) :

        self.secure_args=secure_args
        self.utils=remote_utils()
        # Modelo push: el subleader del grupo informa al gateway a quién llamar
        # (set_leader). Como auto-curación intentamos además una resolución pull
        # inicial, sin bloquear el arranque si el cluster aún no eligió subleader.
        self.db_leader_data = None
        try:
            self.db_leader_data = self.get_leader_data()
        except Exception as e:
            print(f"[GATEWAY] Sin subleader al arranque (se esperará push): {e}")

    def set_leader(self, data):
        """Push del subleader: fija a qué nodo dirige la api sus peticiones."""
        if data and data.get("address"):
            self.db_leader_data = data
            print(f"[GATEWAY] Subleader activo = {data.get('address')}")

    def _ensure_leader(self):
        """Devuelve el subleader vigente; si no hay (aún sin push o el anterior
        cayó) intenta una resolución pull de auto-curación."""
        if not self.db_leader_data:
            try:
                self.db_leader_data = self.get_leader_data()
            except Exception:
                self.db_leader_data = None
        return self.db_leader_data

    def get_db_url(self):
      _,_,addres= socket.gethostbyname_ex('cluster_net_serv')
      host,_,_ = socket.gethostbyaddr(addres[0])
      return f"https://{host}:5000"

    def get_leader_data(self):
        db_cluster_alias=self.get_db_url()
        res = requests.get(
            f"{db_cluster_alias}/db/subleader_address",
            timeout=3,
            **self.secure_args
        )
        data=res.json()
        return data
    def _mock_empty_response(self):
        """Genera una respuesta artificial con un array vacío para evitar que el front se rompa."""
        mock_res = requests.Response()
        mock_res.status_code = 200
        mock_res._content = b"[]"  # Contenido en bytes de un array vacío
        return mock_res
    
    def call_cluster(self,method, endpoint, **kwargs):
        """
        Helper que realiza peticiones al SUBLEADER del grupo (a quien la api dirige
        todo). El subleader sirve las lecturas y reenvía las escrituras al leader
        global. Si el subleader cae, se invalida y se reintenta una vez tras
        re-resolver (fallback pull); en failover el nuevo subleader además hace push.
        """

        # Fusionar los argumentos de seguridad. timeout acotado: sin él una llamada
        # a un subleader caído colgaba indefinidamente el (único) worker del gateway.
        request_kwargs = {**self.secure_args, **kwargs}
        headers = {'Accept': 'application/json'}
        if method.upper() in ['POST', 'PUT']:
            headers['Content-Type'] = 'application/json'

        if not self._ensure_leader():
            raise Exception("Subleader desconocido: el gateway aún no fue informado por el cluster")

        try:
            url = f"https://{self.db_leader_data.get('address')}{endpoint}"
            print(f"[CLUSTER-CALL] {method} a {url}")
            res = requests.request(method, url, headers=headers, timeout=5, **request_kwargs)
            if res.status_code == 404 and method.upper() == "GET":
                return self._mock_empty_response()
            res.raise_for_status()
            return res

        except (requests.exceptions.RequestException, Exception) as e:
            print(f"[CLUSTER-CALL] Fallo con subleader {self.db_leader_data}: {e}")
            # El subleader cacheado cayó o cambió: lo invalidamos y reintentamos una
            # sola vez tras re-resolver al subleader vigente.
            self.db_leader_data = None
            if self._ensure_leader():
                url = f"https://{self.db_leader_data.get('address')}{endpoint}"
                print(f"[CLUSTER-CALL] Reintentando {method} a {url}")
                res = requests.request(method, url, headers=headers, timeout=5, **request_kwargs)
                if res.status_code == 404 and method.upper() == "GET":
                    return self._mock_empty_response()
                res.raise_for_status()
                return res
            raise Exception("Subleader no disponible; esperando aviso del nuevo subleader")

 