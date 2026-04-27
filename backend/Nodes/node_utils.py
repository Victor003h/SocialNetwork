from sqlalchemy.orm import remote

from network_tool.Network_adapter import HostHeaderSSLAdapter
import requests
import time
import socket
from Nodes.node import Node

class utils:
    
    @staticmethod
    def get_ips_for_alias(alias):
        try:
            # gethostbyname_ex devuelve (hostname, aliaslist, ipaddrlist)
            _, _, ip_list = socket.gethostbyname_ex(alias)
            Node_info={}
            for ip in ip_list:
                addr,_,_=socket.gethostbyaddr(ip)
                Node_info[addr]={"ip": ip}
            return Node_info
        except socket.gaierror:
            return {}
    
    @staticmethod
    def Remote_Comunicate(method, endpoint, node_data ,secure_args,**kwargs):
        """
        Node_ip: La IP que te devolvió el Representante (ej. '10.0.5.42')
        hostname_lider: El nombre que está en el certificado del líder (ej. 'node-1.cluster_net')
        """
        node_ip=node_data.get("ip")
        Node_hostname=node_data.get("hostname")
        port=node_data.get("port", 5000)
        session = requests.Session()

        # 1. Configuramos el adaptador con el nombre que ESPERAMOS ver en el certificado
        adapter = HostHeaderSSLAdapter(expected_hostname=Node_hostname)

        # 2. Montamos el adaptador para todas las peticiones HTTPS
        session.mount("https://", adapter)

        # 3. Construimos la URL usando la IP REAL, no el hostname
        url = f"https://{node_ip}:{port}/{endpoint}"
        request_kwargs = { **secure_args, **kwargs }
        
        try:
            # 4. Hacemos la petición. 
            # El adaptador se encargará de inyectar el 'hostname_lider' en la validación TLS
            res = session.request(method.upper(), url, **request_kwargs)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.SSLError as e:
            print(f"🚨 Error de seguridad: El nodo en {node_ip} no es quien dice ser ({e})")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")  
    
    @staticmethod
    def Get_Local_Nodes_M1(alias,local_node,secure_args):
        
        nodes_info= utils.get_ips_for_alias(alias)
        
        for node_hostname in nodes_info:
                       
            if node_hostname == local_node.host:
                continue
            
            data_node= {"ip": nodes_info[node_hostname].get("ip"),
                        "hostname": node_hostname, 
                        "port": local_node.port
                        }
            
            data = utils.Remote_Comunicate("GET", "info", data_node, secure_args)
            
            if data is None: continue
            
            peer_node= data.get("local_node",{})
            
            peer_node= utils.Craft_Node(peer_node)
            
            if local_node.node_pc_id != peer_node.node_pc_id: continue
                    
                    
            subleader_id=data.get("subleader_id")

            last_heartbeat= None
            role=peer_node.role
            if role=="subleader" or role=="leader":
                subleader_id=peer_node.node_id
                local_node.role="follower"
                last_heartbeat=time.time()
            
            peers= data.get("peers",{})
            peers = [utils.Craft_Node(v) for v in peers]
            peers = {peer.node_id: peer for peer in peers}
            
            peers[peer_node.node_id]= peer_node
            peers.pop(local_node.node_id,None)
            print(peers)
            cluster_data={
                "peers": peers,
                "subleader_id": subleader_id,
                "last_heartbeat": last_heartbeat 
            }
            return cluster_data
    
    @staticmethod
    def Get_Local_Nodel_M2(alias,local_node,secure_args):
        
        nodes_info= utils.get_ips_for_alias(alias)
        peers= {}
        last_heartbeat= None
        subleader_id= None
        for node_hostname in nodes_info:
                       
            if node_hostname == local_node.host:
                continue
    
            data_node= {
                "ip": nodes_info[node_hostname].get("ip"),
                "hostname": node_hostname, 
                "port": local_node.port
            }
            
            data = utils.Remote_Comunicate("GET", "info", data_node, secure_args)
    
            if data is None: continue
            
            id_pc= data["node_pc_id"]
            
            if not data or local_node.node_pc_id != id_pc :continue
            
            
            subleader_id=data.get("subleader_id")

            node=data.get("local_node",{})

            role=node.get("role")
            if role=="subleader":
                subleader_id=node["node_id"]
                local_node.role="follower"
                last_heartbeat=time.time()
            

            peer = Node(
                node_id=node.get("node_id"),
                service_name=node.get("service_name"),
                port=local_node.port,
                node_pc_id=node.get("node_pc_id")    
            )
            peer.ip=nodes_info[node_hostname].get("ip")
            peer.host = node_hostname
            peer.address = f"{node_hostname}:{peer.port}"
            peer.role=role

            peers[peer.node_id]=peer  
        
        cluster_data={
            "peers": peers,
            "subleader_id":subleader_id,
            "last_heartbeat": last_heartbeat
        }  
        return cluster_data          
                
    @staticmethod
    def Craft_Node(node_data) -> Node:
        node = Node(
            node_id=node_data.get("node_id"),
            service_name=node_data.get("service_name"),
            port=node_data.get("port", 5000),
            node_pc_id=node_data.get("node_pc_id")
            
        )
        node.ip=node_data.get("ip")
        node.host = node_data.get("host")
        node.address = node_data.get("address")
        node.role = node_data.get("role")
        
        return node
        
     