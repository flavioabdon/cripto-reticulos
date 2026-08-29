"""
Capa Criptográfica Clásica:
  - Cifrado Asimétrico: RSA-OAEP (2048 / 3072 bits, MGF1-SHA256, SHA256)
  - Firma Digital: ECDSA (Curva NIST P-256 / secp256r1 con SHA-256)
  - Cifrado Simétrico: AES-256-GCM
  - Hash: SHA-256
"""

import os
from typing import Tuple, Union

from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class RSACipher:
    """Implementación de RSA-OAEP para cifrado de clave simétrica efímera."""

    def __init__(self, key_size: int = 2048):
        self.key_size = key_size

    @staticmethod
    def generate_keypair(key_size: int = 2048) -> Tuple[bytes, bytes]:
        """Genera un par de claves RSA en formato DER (pk_bytes, sk_bytes)."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        public_key = private_key.public_key()

        sk_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pk_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pk_bytes, sk_bytes

    @staticmethod
    def encrypt(pk_or_bytes: Union[bytes, rsa.RSAPublicKey], plaintext: bytes) -> bytes:
        """Cifra el mensaje con RSA-OAEP (MGF1-SHA256, SHA256)."""
        if isinstance(pk_or_bytes, bytes):
            public_key = serialization.load_der_public_key(pk_or_bytes)
        else:
            public_key = pk_or_bytes
        return public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    @staticmethod
    def decrypt(sk_or_bytes: Union[bytes, rsa.RSAPrivateKey], ciphertext: bytes) -> bytes:
        """Descifra el ciphertext con RSA-OAEP."""
        if isinstance(sk_or_bytes, bytes):
            private_key = serialization.load_der_private_key(sk_or_bytes, password=None)
        else:
            private_key = sk_or_bytes
        return private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )


class ECDSASigner:
    """Implementación de firmas digitales ECDSA (Curva NIST P-256 con SHA-256)."""

    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """Genera un par de claves ECDSA en formato DER (pk_bytes, sk_bytes)."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        sk_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pk_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pk_bytes, sk_bytes

    @staticmethod
    def sign(m: bytes, sk_or_bytes: Union[bytes, ec.EllipticCurvePrivateKey]) -> bytes:
        """Firma el mensaje m con la clave privada ECDSA (P-256 + SHA-256)."""
        if isinstance(sk_or_bytes, bytes):
            private_key = serialization.load_der_private_key(sk_or_bytes, password=None)
        else:
            private_key = sk_or_bytes
        return private_key.sign(m, ec.ECDSA(hashes.SHA256()))

    @staticmethod
    def verify(m: bytes, sig: bytes, pk_or_bytes: Union[bytes, ec.EllipticCurvePublicKey]) -> bool:
        """Verifica la firma ECDSA sobre el mensaje m."""
        try:
            if isinstance(pk_or_bytes, bytes):
                public_key = serialization.load_der_public_key(pk_or_bytes)
            else:
                public_key = pk_or_bytes
            public_key.verify(sig, m, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False


def aes_gcm_encrypt(key: bytes, plaintext: bytes, nonce: bytes = None) -> Tuple[bytes, bytes]:
    """Cifra con AES-256-GCM."""
    if len(key) != 32:
        raise ValueError("La clave AES debe tener 32 bytes.")
    if nonce is None:
        nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return ciphertext, nonce


def aes_gcm_decrypt(key: bytes, ciphertext: bytes, nonce: bytes) -> bytes:
    """Descifra con AES-256-GCM."""
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
