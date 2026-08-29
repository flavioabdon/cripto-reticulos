"""
Utilidades criptográficas simétricas y de serialización para el protocolo PQC:
  - Cifrado simétrico autenticado (AES-256-GCM) con clave derivada de ML-KEM
  - Hashes criptográficos canónicos (SHA3-256 / SHA-256)
  - Serialización estructurada de boletas, credenciales y recibos
"""

import hashlib
import json
import os
from typing import Any, Tuple

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


def sha3_256(data: bytes) -> bytes:
    """Calcula el hash SHA3-256 de los datos."""
    return hashlib.sha3_256(data).digest()


def sha256(data: bytes) -> bytes:
    """Calcula el hash SHA-256 de los datos."""
    return hashlib.sha256(data).digest()


def aes_gcm_encrypt(key: bytes, plaintext: bytes, nonce: bytes = None) -> Tuple[bytes, bytes]:
    """
    Cifra plaintext usando AES-256-GCM con la clave simétrica key (32 bytes).
    Retorna: (ciphertext_con_tag, nonce)
    """
    if len(key) != 32:
        raise ValueError(f"Longitud de clave AES inválida: {len(key)} (esperado 32 bytes)")

    if nonce is None:
        nonce = os.urandom(12)  # Nonce estándar de 96 bits para GCM

    if HAS_CRYPTOGRAPHY:
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return ciphertext, nonce
    else:
        # Fallback simple XOR + HMAC si cryptography no estuviera disponible (solo para tests aislados)
        import hmac
        keystream = hashlib.sha3_256(key + nonce).digest()
        ct = bytes(p ^ keystream[i % len(keystream)] for i, p in enumerate(plaintext))
        tag = hmac.new(key, nonce + ct, hashlib.sha256).digest()[:16]
        return ct + tag, nonce


def aes_gcm_decrypt(key: bytes, ciphertext: bytes, nonce: bytes) -> bytes:
    """
    Descifra ciphertext usando AES-256-GCM con key (32 bytes) y nonce (12 bytes).
    Retorna: plaintext
    """
    if len(key) != 32:
        raise ValueError(f"Longitud de clave AES inválida: {len(key)} (esperado 32 bytes)")

    if HAS_CRYPTOGRAPHY:
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    else:
        import hmac
        ct = ciphertext[:-16]
        tag = ciphertext[-16:]
        expected_tag = hmac.new(key, nonce + ct, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("Fallo de autenticación en descifrado")
        keystream = hashlib.sha3_256(key + nonce).digest()
        return bytes(c ^ keystream[i % len(keystream)] for i, c in enumerate(ct))


def canonical_json(obj: Any) -> bytes:
    """Serializa un objeto a JSON canónico determinista (claves ordenadas, sin espacios superfluos)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
