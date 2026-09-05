"""
Módulo de la Autoridad de Registro (AR) — Protocolo Post-Cuántico PQC.
Responsable de:
  - Generación de claves de autoridad ML-DSA-65 (sk_AR, pk_AR)
  - Registro de votantes y emisión de credenciales firmadas
  - Mantenimiento del padrón electoral oficial
"""

import time
from typing import Dict, Optional, Tuple

from src.pqc.pqc_wrapper import MLDSA65
from src.pqc.crypto_utils import canonical_json, sha256


class CredencialVotante:
    """Credencial de votante emitida y firmada por la Autoridad de Registro."""

    def __init__(self, id_votante: str, pk_votante: bytes, timestamp: float, firma_ar: bytes):
        self.id_votante = id_votante
        self.pk_votante = pk_votante
        self.timestamp = timestamp
        self.firma_ar = firma_ar

    def payload_bytes(self) -> bytes:
        """Retorna la representación canónica en bytes de los datos de la credencial (sin firma)."""
        data = {
            "id_votante": self.id_votante,
            "pk_votante_hex": self.pk_votante.hex(),
            "timestamp": self.timestamp,
        }
        return canonical_json(data)

    def to_dict(self) -> dict:
        """Serializa la credencial completa a diccionario."""
        return {
            "id_votante": self.id_votante,
            "pk_votante_hex": self.pk_votante.hex(),
            "timestamp": self.timestamp,
            "firma_ar_hex": self.firma_ar.hex(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CredencialVotante":
        """Reconstruye una CredencialVotante desde diccionario."""
        return cls(
            id_votante=data["id_votante"],
            pk_votante=bytes.fromhex(data["pk_votante_hex"]),
            timestamp=data["timestamp"],
            firma_ar=bytes.fromhex(data["firma_ar_hex"]),
        )


class AutoridadRegistro:
    """Autoridad de Registro (AR) encargada del padrón electoral y emisión de credenciales."""

    def __init__(self, nombre: str = "Tribunal Electoral - AR"):
        self.nombre = nombre
        # Generar par de claves ML-DSA-65 de la AR
        self.pk_ar, self._sk_ar = MLDSA65.keypair()
        # Padrón electoral: id_votante -> {pk_votante, estado, fecha_registro}
        self.padron: Dict[str, dict] = {}

    def registrar_votante(self, id_votante: str, nombre_completo: str = "") -> Tuple[bytes, CredencialVotante]:
        """
        Registra a un ciudadano en el padrón electoral.
        Genera el par de claves ML-DSA-65 para el votante, firma su credencial y actualiza el padrón.

        Retorna:
          (sk_votante, credencial_firmada)
        """
        if id_votante in self.padron:
            raise ValueError(f"El votante '{id_votante}' ya se encuentra registrado en el padrón electoral.")

        # 1. Generar par de claves ML-DSA-65 para el votante
        pk_v, sk_v = MLDSA65.keypair()

        # 2. Construir datos de la credencial
        ts = time.time()
        cred_temp = CredencialVotante(id_votante=id_votante, pk_votante=pk_v, timestamp=ts, firma_ar=b"")

        # 3. Firmar la credencial con la clave privada de la AR (ML-DSA-65)
        payload = cred_temp.payload_bytes()
        firma_ar = MLDSA65.sign(payload, self._sk_ar)

        credencial = CredencialVotante(
            id_votante=id_votante,
            pk_votante=pk_v,
            timestamp=ts,
            firma_ar=firma_ar,
        )

        # 4. Registrar en el padrón electoral
        self.padron[id_votante] = {
            "id_votante": id_votante,
            "nombre": nombre_completo,
            "pk_votante": pk_v,
            "estado": "HABILITADO",
            "timestamp_registro": ts,
        }

        return sk_v, credencial

    def verificar_credencial(self, credencial: CredencialVotante) -> bool:
        """Verifica criptográficamente que la credencial fue firmada por esta AR."""
        payload = credencial.payload_bytes()
        return MLDSA65.verify(payload, credencial.firma_ar, self.pk_ar)

    def esta_habilitado(self, id_votante: str) -> bool:
        """Verifica si el votante existe y está habilitado para votar."""
        return id_votante in self.padron and self.padron[id_votante]["estado"] == "HABILITADO"

    def marcar_como_votado(self, id_votante: str):
        """Actualiza el estado del votante en el padrón electoral a 'YA_VOTO'."""
        if id_votante not in self.padron:
            raise ValueError(f"Votante {id_votante} no encontrado.")
        self.padron[id_votante]["estado"] = "YA_VOTO"
