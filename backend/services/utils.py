import requests
import socket

class utils:
    
    def __init__(self,secure_args) -> None:
        
        self.secure_args=secure_args
        self.db_leader_address = self.get_leader_address()

    def get_db_url(self):
      _,_,addres= socket.gethostbyname_ex('cluster_net_serv')
      host,_,_ = socket.gethostbyaddr(addres[0])
      return f"https://{host}:5000"

    def get_leader_address(self):
        db_cluster_alias=self.get_db_url()
        res = requests.get(
            f"{db_cluster_alias}/db/leader_address",
            timeout=3,
            **self.secure_args
        )
        address=res.json().get("leader_address")
        url=f"https://{address}"
        print (f"DB Leader Address: {url}")

        return url

    

    def call_cluster(self,method, endpoint, **kwargs):
        """
        Helper que realiza peticiones al cluster. 
        Si falla, intenta buscar al nuevo líder y reintenta la operación.
        """

        # Fusionar los argumentos de seguridad
        request_kwargs = {**self.secure_args, **kwargs}

        try:
            if not self.db_leader_address:
                raise Exception("Dirección del líder no disponible")

            url = f"{self.db_leader_address}{endpoint}"
            print(f"[CLUSTER-CALL] {method} a {url}")
            res = requests.request(method, url, **request_kwargs)
            res.raise_for_status()
            return res
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"[CLUSTER-CALL] Fallo con el líder {self.db_leader_address}: {e}")
            print("[CLUSTER-CALL] Reintentando descubrimiento de líder...")

            # Intentar refrescar la dirección
            new_address = self.get_leader_address()
            if new_address:
                self.db_leader_address = new_address
                url = f"{self.db_leader_address}{endpoint}"
                print(f"[CLUSTER-CALL] Reintentando {method} a {url}")
                res = requests.request(method, url, **request_kwargs)
                res.raise_for_status()
                return res
            else:
                raise Exception("No se pudo encontrar un líder disponible en el cluster.")

 