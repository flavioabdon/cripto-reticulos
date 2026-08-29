"""
Módulo de la Autoridad de Registro (AR) — Protocolo Clásico (ECDSA P-256).
Responsable de:
  - Generación de claves de autoridad ECDSA P-256 (sk_AR, pk_AR)
  - Registro de votantes y emisión de credenciales firmadas
  - Mantenimiento del padrón electoral
"""

import time
from typing import Dict, Tuple

from src.clasico.crypto_clasico import ECDSASigner
from src.pqc.crypto_utils import canonical_json


class CredencialVotanteClasico:
    """Credencial de votante emitida con firma digital ECDSA (P-256)."""

    def __init__(self, id_votante: str, pk_votante: bytes, timestamp: float, firma_ar: bytes):
        self.id_votante = id_votante
        self.pk_votante = pk_votante
        self.timestamp = timestamp
        self.firma_ar = firma_ar

    def payload_bytes(self) -> bytes:
        data = {
            "id_votante": self.id_votante,
            "pk_votante_hex": self.pk_votante.hex(),
            "timestamp": self.timestamp,
        }
        return canonical_json(data)

    def to_dict(self) -> dict:
        return {
            "id_votante": self.id_votante,
            "pk_votante_hex": self.pk_votante.hex(),
            "timestamp": self.timestamp,
            "firma_ar_hex": self.firma_ar.hex(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CredencialVotanteClasico":
        return cls(
            id_votante=data["id_votante"],
            pk_votante=bytes.fromhex(data["pk_votante_hex"]),
            timestamp=data["timestamp"],
            firma_ar=bytes.fromhex(data["firma_ar_hex"]),
        )


class AutoridadRegistroClasico:
    """Autoridad de Registro (AR) en el esquema clásico."""

    def __init__(self, nombre: str = "Tribunal Electoral - AR Clásica"):
        self.nombre = nombre
        # Generar par de claves ECDSA P-256 de la AR
        self.pk_ar, self._sk_ar = ECDSASigner.generate_keypair()
        self.padron: Dict[str, dict] = {}

    def registrar_votante(self, id_votante: str, nombre_completo: str = "") -> Tuple[bytes, CredencialVotanteClasico]:
        """
        Registra un votante, genera su par ECDSA P-256, firma su credencial y actualiza el padrón.
        Retorna: (sk_votante_ecdsa, credencial_firmada)
        """
        if id_votante in self.padron:
            raise ValueError(f"El votante '{id_votante}' ya se encuentra registrado.")

        # 1. Generar par de claves ECDSA P-256 para el votante
        pk_v, sk_v = ECDSASigner.generate_keypair()

        # 2. Construir datos y firmar con sk_AR (ECDSA)
        ts = time.time()
        cred_temp = CredencialVotanteClasico(id_votante=id_votante, pk_votante=pk_v, timestamp=ts, firma_ar=b"")
        firma_ar = ECDSASigner.sign(cred_temp.payload_bytes(), self._sk_ar)

        credencial = CredencialVotanteClasico(
            id_votante=id_votante,
            pk_votante=pk_v,
            timestamp=ts,
            firma_ar=firma_ar,
        )

        self.padron[id_votante] = {
            "id_votante": id_votante,
            "nombre": nombre_completo,
            "pk_votante": pk_v,
            "estado": "HABILITADO",
            "timestamp_registro": ts,
        }

        return sk_v, credencial

    def verificar_credencial(self, credencial: CredencialVotanteClasico) -> bool:
        """Verifica la firma ECDSA de la credencial."""
        payload = credencial.payload_bytes()
        return ECDSASigner.verify(payload, credencial.firma_ar, self.pk_ar)

    def esta_habilitado(self, id_votante: str) -> bool:
        return id_votante in self.padron and self.padron[id_votante]["estado"] == "HABILITADO"

    def marcar_como_votado(self, id_votante: str):
        if id_votante not in self.padron:
            raise ValueError(f"Votante {id_votante} no encontrado.")
        self.padron[id_votante]["estado"] = "YA_VOTO"
