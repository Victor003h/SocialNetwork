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