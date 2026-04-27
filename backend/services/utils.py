import requests
import socket
from Nodes.node_utils import utils as remote_utils
class utils:
    
    def __init__(self,secure_args) :
        
        self.secure_args=secure_args
        self.db_leader_data = self.get_leader_data()
        self.utils=remote_utils()

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
        Helper que realiza peticiones al cluster. 
        Si falla, intenta buscar al nuevo líder y reintenta la operación.
        """

        # Fusionar los argumentos de seguridad
        request_kwargs = {**self.secure_args, **kwargs}
        headers={
            'Accept': 'application/json'
        }
        
        if method.upper() in ['POST', 'PUT']:
            headers['Content-Type'] = 'application/json'
        try:
            if not self.db_leader_data:
                raise Exception("Información del líder no disponible")
               
            url = f"https://{self.db_leader_data.get('address')}{endpoint}"
            print(f"[CLUSTER-CALL] {method} a {url} con {headers}")
            res = requests.request(method, url, headers=headers,**request_kwargs)
            if res.status_code == 404 and method.upper() == "GET":
                print(f"[CLUSTER-CALL] Recurso no encontrado en el líder {self.db_leader_data.get('address')}, devolviendo respuesta vacía.")
                return self._mock_empty_response()
            res.raise_for_status()
            return res
       
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"[CLUSTER-CALL] Fallo con el líder {self.db_leader_data.get('address')}: {e}")
            print("[CLUSTER-CALL] Reintentando descubrimiento de líder...")

            # Intentar refrescar la dirección
            new_data = self.get_leader_data()
            if new_data:
                
                self.db_leader_data = new_data
                url = f"https://{self.db_leader_data.get('address')}{endpoint}"
                print(f"[CLUSTER-CALL] Reintentando {method} a {url}")
                res = requests.request(method, url, headers=headers,**request_kwargs )
                if res.status_code == 404 and method.upper() == "GET":
                    print(f"[CLUSTER-CALL] Recurso no encontrado en el nuevo líder {self.db_leader_data.get('address')}, devolviendo respuesta vacía.")
                    return self._mock_empty_response()
                res.raise_for_status()
                return res
              
            else:
                raise Exception("No se pudo encontrar un líder disponible en el cluster.")

 