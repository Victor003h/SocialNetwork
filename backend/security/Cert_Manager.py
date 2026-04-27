import ssl
import os
from cryptography import x509
from cryptography.hazmat.backends import default_backend

class CertManager:
    """
    Gestiona la carga de certificados pre-aprovisionados (Hybrid Proposal).
    No genera llaves, asume que 'setup_security.py' ya corrió y 
    los archivos están montados en cert_dir.
    """
    def __init__(self, cert_dir='certs'):
        # Rutas esperadas dentro del contenedor
        self.ca_cert_path = os.path.join(cert_dir, 'ca.crt')
        self.node_cert_path = os.path.join(cert_dir, 'node.crt')
        self.node_key_path = os.path.join(cert_dir, 'node.key')
        
        self._validate_deployment()

    def get_mtls_context(self, require_client_auth=True):
        """
        Crea un contexto SSL que obliga al cliente a presentar un certificado válido.
        """
        # 1. Crear contexto para autenticación de cliente (mTLS)
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        # 2. Cargar mi propia llave y cert (identidad del servidor)
        context.load_cert_chain(certfile=self.node_cert_path, keyfile=self.node_key_path)

        # 3. Cargar la CA para verificar a los clientes
        context.load_verify_locations(cafile=self.ca_cert_path)

        # 4. CRÍTICO: Exigir certificado al cliente
        if require_client_auth:
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            context.verify_mode = ssl.CERT_NONE
        return context

    def setupCerts(self):
        
        (self.cert_path, self.key_path), self.ca_path = self.get_context()
        
        # Definimos los argumentos estándar para requests seguros
        secure_args = {
            "cert": (self.cert_path, self.key_path), # Mi carta de presentación
            "verify": self.ca_path    # Contra qué valido a los demás
        }
        return secure_args   
    def _validate_deployment(self):
        """Verifica que el kit de seguridad exista."""
        missing = []
        if not os.path.exists(self.ca_cert_path): missing.append(self.ca_cert_path)
        if not os.path.exists(self.node_cert_path): missing.append(self.node_cert_path)
        if not os.path.exists(self.node_key_path): missing.append(self.node_key_path)
        
        if missing:
            raise RuntimeError(f"CRITICAL: Security Kit incomplete. Missing: {missing}. "
                               f"Run setup_security.py and mount volumes correctly.")
        
        print(f"[CertManager] Security Kit loaded from {os.path.dirname(self.node_cert_path)}")

    def get_context(self):
        """
        Devuelve las rutas necesarias para Requests o SSLContext.
        Retorna: (cert_path, key_path), ca_path
        """
        # Validar expiración (opcional pero recomendado)
        self._check_expiry()
        
        return (self.node_cert_path, self.node_key_path), self.ca_cert_path

    def _check_expiry(self):
        try:
            with open(self.node_cert_path, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())
                # Aquí podrías añadir lógica de alerta si está por vencer
                pass
        except Exception as e:
            print(f"[CertManager] Warning: Could not validate cert expiry: {e}")