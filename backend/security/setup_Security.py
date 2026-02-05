import os
import shutil
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import ipaddress

class SecuritySetup:
    def __init__(self, base_dir="deploy_certs"):
        self.base_dir = base_dir
        self.ca_key = None
        self.ca_cert = None

    def generate_ca(self):
        """Genera la CA Raíz (Offline)."""
        print("🔐 Generando CA Raíz...")
        self.ca_key = rsa.generate_private_key(public_exponent=65537, key_size=4096, backend=default_backend())
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"SocialNet-Root-CA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Distributed-Systems-Lab"),
        ])
        
        self.ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.ca_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=3650) # 10 años
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True,
        ).sign(self.ca_key, hashes.SHA256(), default_backend())

        # Guardar CA
        os.makedirs(self.base_dir, exist_ok=True)
        self._save_pem(self.base_dir, "ca.crt", self.ca_cert)
        self._save_pem(self.base_dir, "ca.key", self.ca_key, is_private=True) # ¡Solo para el admin!

    def generate_node_kit(self, node_id, service_name_prefix="node"):
        """Genera par de llaves firmado por la CA para un nodo específico."""
        if not self.ca_cert or not self.ca_key:
            raise Exception("CA no inicializada.")

        node_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        node_name = f"{service_name_prefix}-{node_id}"
        
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, node_name)
        ])
        
        # SANs: Vitales para que los nodos se hablen entre sí por nombre de servicio o localhost
        san =   x509.SubjectAlternativeName([
                x509.DNSName(f"node{node_id}.cluster_net"), # Nombre de servicio en Swarm
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ])      
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(self.ca_cert.subject)
        builder = builder.public_key(node_key.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(datetime.utcnow())
        builder = builder.not_valid_after(datetime.utcnow() + timedelta(days=365))
        
        builder = builder.add_extension(san, critical=False)
        
        
        builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            content_commitment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False
        ),
        critical=True
        )
        # Indica que este certificado sirve tanto para ser Servidor como Cliente (mTLS)
        builder = builder.add_extension(
            x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.SERVER_AUTH,
                ExtendedKeyUsageOID.CLIENT_AUTH
            ]),
        critical=False
        )
        cert = builder.sign(self.ca_key, hashes.SHA256(), default_backend())      
        
        
        # Guardar Kit
        node_dir = os.path.join(self.base_dir, f"node_{node_id}")
        os.makedirs(node_dir, exist_ok=True)
        
        self._save_pem(node_dir, "node.crt", cert)
        self._save_pem(node_dir, "node.key", node_key, is_private=True)
        
        # Copiar CA pública al nodo (necesaria para validar a otros peers)
        shutil.copy(os.path.join(self.base_dir, "ca.crt"), os.path.join(node_dir, "ca.crt"))
        print(f"✅ Kit generado para {node_name} en {node_dir}")

    def _save_pem(self, path, filename, obj, is_private=False):
        full_path = os.path.join(path, filename)
        with open(full_path, "wb") as f:
            if is_private:
                f.write(obj.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            else:
                f.write(obj.public_bytes(serialization.Encoding.PEM))

if __name__ == "__main__":
    # Limpieza previa
    if os.path.exists("/backend/deploy_certs"):
        shutil.rmtree("/backend/deploy_certs")
    
    setup = SecuritySetup()
    setup.generate_ca()
    
    # Generar kits para 5 nodos (ajustar según necesidad)
    for i in range(1, 6):
        setup.generate_node_kit(i)
        
    print("\n🚀 Seguridad Inicializada. Monta ./deploy_certs/node_X en /app/certs en tus contenedores.")