"""
Módulo del Votante — Protocolo Clásico (RSA-OAEP + ECDSA).
Responsable de:
  - Cifrado del voto mediante RSA-OAEP + AES-256-GCM
  - Firma digital de la boleta con ECDSA (P-256)
  - Empaquetado y emisión del sufragio
"""

import os
import time
from typing import Optional

from src.clasico.crypto_clasico import RSACipher, ECDSASigner, aes_gcm_encrypt
from src.clasico.autoridad_registro_clasico import CredencialVotanteClasico
from src.pqc.crypto_utils import canonical_json


class BoletaSufragioClasico:
    """Estructura de la boleta clásica con secreto cifrado con RSA y voto cifrado con AES-GCM."""

    def __init__(
        self,
        clave_cifrada_rsa: bytes,
        voto_cifrado: bytes,
        nonce_aead: bytes,
        credencial: CredencialVotanteClasico,
        timestamp_emision: float,
    ):
        self.clave_cifrada_rsa = clave_cifrada_rsa
        self.voto_cifrado = voto_cifrado
        self.nonce_aead = nonce_aead
        self.credencial = credencial
        self.timestamp_emision = timestamp_emision

    def payload_bytes(self) -> bytes:
        data = {
            "clave_cifrada_rsa_hex": self.clave_cifrada_rsa.hex(),
            "voto_cifrado_hex": self.voto_cifrado.hex(),
            "nonce_aead_hex": self.nonce_aead.hex(),
            "credencial": self.credencial.to_dict(),
            "timestamp_emision": self.timestamp_emision,
        }
        return canonical_json(data)

    def to_dict(self) -> dict:
        return {
            "clave_cifrada_rsa_hex": self.clave_cifrada_rsa.hex(),
            "voto_cifrado_hex": self.voto_cifrado.hex(),
            "nonce_aead_hex": self.nonce_aead.hex(),
            "credencial": self.credencial.to_dict(),
            "timestamp_emision": self.timestamp_emision,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BoletaSufragioClasico":
        return cls(
            clave_cifrada_rsa=bytes.fromhex(data["clave_cifrada_rsa_hex"]),
            voto_cifrado=bytes.fromhex(data["voto_cifrado_hex"]),
            nonce_aead=bytes.fromhex(data["nonce_aead_hex"]),
            credencial=CredencialVotanteClasico.from_dict(data["credencial"]),
            timestamp_emision=data["timestamp_emision"],
        )


class PaqueteVotoClasico:
    """Paquete de voto clásico transmitido al Servidor de Votación."""

    def __init__(self, boleta: BoletaSufragioClasico, firma_votante: bytes):
        self.boleta = boleta
        self.firma_votante = firma_votante

    def to_dict(self) -> dict:
        return {
            "boleta": self.boleta.to_dict(),
            "firma_votante_hex": self.firma_votante.hex(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PaqueteVotoClasico":
        return cls(
            boleta=BoletaSufragioClasico.from_dict(data["boleta"]),
            firma_votante=bytes.fromhex(data["firma_votante_hex"]),
        )


class VotanteClasico:
    """Entidad del Votante en el esquema clásico (RSA + ECDSA)."""

    def __init__(self, id_votante: str, sk_votante_ecdsa: bytes, credencial: CredencialVotanteClasico):
        self.id_votante = id_votante
        self._sk_votante = sk_votante_ecdsa
        self.credencial = credencial
        self.recibo_emitido = None

    def emitir_voto(self, opcion_candidato: str, pk_servidor_rsa: bytes) -> PaqueteVotoClasico:
        """
        Emite el voto cifrado con RSA-OAEP + AES-256-GCM y firmado con ECDSA:
          1. Genera una clave simétrica efímera de 32 bytes K.
          2. Cifra K con la clave pública RSA del servidor (RSA-OAEP).
          3. Cifra el contenido del voto con K usando AES-256-GCM.
          4. Construye la boleta y la firma digitalmente con ECDSA (P-256).

        Retorna:
          PaqueteVotoClasico listo para enviar al servidor.
        """
        # 1. Generar secreto simétrico efímero (32 bytes)
        k_efimera = os.urandom(32)

        # 2. Cifrar K con RSA-OAEP
        clave_cifrada_rsa = RSACipher.encrypt(pk_servidor_rsa, k_efimera)

        # 3. Cifrar voto con AES-256-GCM
        voto_bytes = opcion_candidato.encode("utf-8")
        voto_cifrado, nonce = aes_gcm_encrypt(k_efimera, voto_bytes)

        # 4. Construir boleta y firmar con ECDSA
        ts = time.time()
        boleta = BoletaSufragioClasico(
            clave_cifrada_rsa=clave_cifrada_rsa,
            voto_cifrado=voto_cifrado,
            nonce_aead=nonce,
            credencial=self.credencial,
            timestamp_emision=ts,
        )

        payload = boleta.payload_bytes()
        firma_v = ECDSASigner.sign(payload, self._sk_votante)

        return PaqueteVotoClasico(boleta=boleta, firma_votante=firma_v)
