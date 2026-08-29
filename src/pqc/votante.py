"""
Módulo del Votante — Protocolo Post-Cuántico PQC.
Responsable de:
  - Cifrado del voto mediante encapsulamiento ML-KEM-768 + AES-256-GCM
  - Firma digital de la boleta con ML-DSA-65
  - Empaquetado y emisión del sufragio
"""

import time
from typing import Dict, Optional

from src.pqc.pqc_wrapper import MLKEM768, MLDSA65
from src.pqc.crypto_utils import canonical_json, aes_gcm_encrypt
from src.pqc.autoridad_registro import CredencialVotante


class BoletaSufragio:
    """Estructura de la boleta de sufragio con voto cifrado y credencial."""

    def __init__(
        self,
        ciphertext_kem: bytes,
        voto_cifrado: bytes,
        nonce_aead: bytes,
        credencial: CredencialVotante,
        timestamp_emision: float,
    ):
        self.ciphertext_kem = ciphertext_kem
        self.voto_cifrado = voto_cifrado
        self.nonce_aead = nonce_aead
        self.credencial = credencial
        self.timestamp_emision = timestamp_emision

    def payload_bytes(self) -> bytes:
        """Serialización canónica de los datos de la boleta para ser firmados."""
        data = {
            "ciphertext_kem_hex": self.ciphertext_kem.hex(),
            "voto_cifrado_hex": self.voto_cifrado.hex(),
            "nonce_aead_hex": self.nonce_aead.hex(),
            "credencial": self.credencial.to_dict(),
            "timestamp_emision": self.timestamp_emision,
        }
        return canonical_json(data)

    def to_dict(self) -> dict:
        return {
            "ciphertext_kem_hex": self.ciphertext_kem.hex(),
            "voto_cifrado_hex": self.voto_cifrado.hex(),
            "nonce_aead_hex": self.nonce_aead.hex(),
            "credencial": self.credencial.to_dict(),
            "timestamp_emision": self.timestamp_emision,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BoletaSufragio":
        return cls(
            ciphertext_kem=bytes.fromhex(data["ciphertext_kem_hex"]),
            voto_cifrado=bytes.fromhex(data["voto_cifrado_hex"]),
            nonce_aead=bytes.fromhex(data["nonce_aead_hex"]),
            credencial=CredencialVotante.from_dict(data["credencial"]),
            timestamp_emision=data["timestamp_emision"],
        )


class PaqueteVoto:
    """Paquete de voto completo transmitido al Servidor de Votación."""

    def __init__(self, boleta: BoletaSufragio, firma_votante: bytes):
        self.boleta = boleta
        self.firma_votante = firma_votante

    def to_dict(self) -> dict:
        return {
            "boleta": self.boleta.to_dict(),
            "firma_votante_hex": self.firma_votante.hex(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PaqueteVoto":
        return cls(
            boleta=BoletaSufragio.from_dict(data["boleta"]),
            firma_votante=bytes.fromhex(data["firma_votante_hex"]),
        )


class Votante:
    """Entidad del Votante en el protocolo PQC."""

    def __init__(self, id_votante: str, sk_votante: bytes, credencial: CredencialVotante):
        self.id_votante = id_votante
        self._sk_votante = sk_votante
        self.credencial = credencial
        self.recibo_emitido = None

    def emitir_voto(self, opcion_candidato: str, ek_servidor: bytes) -> PaqueteVoto:
        """
        Emite el voto cifrado y firmado:
          1. Encapsula una clave efímera con ML-KEM-768 usando la clave pública del servidor (ek_servidor).
          2. Cifra la opción de candidato con AES-256-GCM usando el secreto compartido de ML-KEM.
          3. Construye la boleta conteniendo (ciphertext_kem, voto_cifrado, nonce, credencial, timestamp).
          4. Firma digitalmente la boleta completa con ML-DSA-65 usando la clave privada del votante.

        Retorna:
          PaqueteVoto listo para enviar al Servidor de Votación.
        """
        # 1. Encapsulamiento ML-KEM-768
        ct_kem, shared_secret = MLKEM768.enc(ek_servidor)

        # 2. Cifrado simétrico autenticado del contenido del voto (AES-256-GCM)
        voto_bytes = opcion_candidato.encode("utf-8")
        voto_cifrado, nonce = aes_gcm_encrypt(shared_secret, voto_bytes)

        # 3. Construir la boleta
        ts = time.time()
        boleta = BoletaSufragio(
            ciphertext_kem=ct_kem,
            voto_cifrado=voto_cifrado,
            nonce_aead=nonce,
            credencial=self.credencial,
            timestamp_emision=ts,
        )

        # 4. Firmar la boleta con ML-DSA-65
        payload = boleta.payload_bytes()
        firma_v = MLDSA65.sign(payload, self._sk_votante)

        return PaqueteVoto(boleta=boleta, firma_votante=firma_v)
