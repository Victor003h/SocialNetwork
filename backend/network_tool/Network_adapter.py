from requests.adapters import HTTPAdapter
import ssl

class HostHeaderSSLAdapter(HTTPAdapter):
    """
    Un adaptador para requests que permite forzar el SNI y 
    la verificación de hostname para una conexión mTLS.
    """
    def __init__(self, expected_hostname, *args, **kwargs):
        self.expected_hostname = expected_hostname
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        # Creamos un contexto SSL que obliga a verificar contra el nombre esperado
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.load_verify_locations(cafile="certs/ca.crt")
        context.load_cert_chain(certfile="certs/node.crt", keyfile="certs/node.key")
        
        # Aquí forzamos que el hostname a validar sea 'representative'
        # independientemente de la IP a la que estemos llamando
        kwargs['ssl_context'] = context
        kwargs['server_hostname'] = self.expected_hostname
        
        super().init_poolmanager(*args, **kwargs)