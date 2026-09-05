"""
Módulo del Servidor de Votación (SV) — Protocolo Clásico (RSA + ECDSA).
Responsable de:
  - Generación de claves RSA para cifrado y claves ECDSA para firma de recibos
  - Recepción de paquetes de voto y verificación de firmas (AR y Votante)
  - Control de unicidad (anti-duplicados)
  - Almacenamiento seguro en la ánfora digital
  - Emisión de recibos firmados con ECDSA
"""

import time
from typing import List, Optional, Tuple

from src.clasico.crypto_clasico import RSACipher, ECDSASigner
from src.clasico.autoridad_registro_clasico import AutoridadRegistroClasico
from src.clasico.votante_clasico import BoletaSufragioClasico, PaqueteVotoClasico
from src.pqc.crypto_utils import canonical_json, sha256


class ReciboVotacionClasico:
    """Recibo digital clásico firmado con ECDSA."""

    def __init__(self, hash_boleta: bytes, timestamp_recibo: float, firma_servidor: bytes):
        self.hash_boleta = hash_boleta
        self.timestamp_recibo = timestamp_recibo
        self.firma_servidor = firma_servidor

    def payload_bytes(self) -> bytes:
        data = {
            "hash_boleta_hex": self.hash_boleta.hex(),
            "timestamp_recibo": self.timestamp_recibo,
        }
        return canonical_json(data)

    def to_dict(self) -> dict:
        return {
            "hash_boleta_hex": self.hash_boleta.hex(),
            "timestamp_recibo": self.timestamp_recibo,
            "firma_servidor_hex": self.firma_servidor.hex(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReciboVotacionClasico":
        return cls(
            hash_boleta=bytes.fromhex(data["hash_boleta_hex"]),
            timestamp_recibo=data["timestamp_recibo"],
            firma_servidor=bytes.fromhex(data["firma_servidor_hex"]),
        )


class ServidorVotacionClasico:
    """Servidor de Votación en el esquema clásico (RSA + ECDSA)."""

    def __init__(self, pk_ar_ecdsa: bytes, autoridad_registro: Optional[AutoridadRegistroClasico] = None, rsa_key_size: int = 2048):
        self.pk_ar = pk_ar_ecdsa
        self.autoridad_registro = autoridad_registro

        # Generar par de claves RSA (2048 bits) para el cifrado del voto
        self.pk_sv_rsa, self._sk_sv_rsa = RSACipher.generate_keypair(key_size=rsa_key_size)

        # Generar par de claves ECDSA del Servidor para emitir recibos
        self.pk_sv_ecdsa, self._sk_sv_ecdsa = ECDSASigner.generate_keypair()

        self.urna: List[PaqueteVotoClasico] = []
        self.votantes_registrados: set = set()
        self.jornada_abierta: bool = True

    def obtener_sk_rsa_para_conteo(self) -> bytes:
        """Transfiere la clave privada RSA a la Autoridad de Conteo fuera de banda."""
        return self._sk_sv_rsa

    def recepcionar_voto(self, paquete: PaqueteVotoClasico) -> Tuple[bool, str, Optional[ReciboVotacionClasico]]:
        """Recepciona, valida firmas ECDSA y almacena la boleta clásica."""
        if not self.jornada_abierta:
            return False, "La jornada electoral está cerrada.", None

        boleta = paquete.boleta
        cred = boleta.credencial
        id_v = cred.id_votante

        # 1. Control de duplicados
        if id_v in self.votantes_registrados:
            return False, f"Voto rechazado: el votante '{id_v}' ya ha emitido su voto.", None

        # 2. Verificar firma ECDSA de la AR sobre la credencial
        payload_cred = cred.payload_bytes()
        if not ECDSASigner.verify(payload_cred, cred.firma_ar, self.pk_ar):
            return False, "Voto rechazado: firma de la AR INVÁLIDA.", None

        # 3. Verificar firma ECDSA del votante sobre la boleta
        payload_boleta = boleta.payload_bytes()
        if not ECDSASigner.verify(payload_boleta, paquete.firma_votante, cred.pk_votante):
            return False, "Voto rechazado: firma digital del votante INVÁLIDA.", None

        # 4. Registrar en el ánfora
        self.urna.append(paquete)
        self.votantes_registrados.add(id_v)

        if self.autoridad_registro:
            self.autoridad_registro.marcar_como_votado(id_v)

        # 5. Generar recibo firmado con ECDSA
        hash_b = sha256(payload_boleta)
        ts_rcp = time.time()
        recibo_temp = ReciboVotacionClasico(hash_boleta=hash_b, timestamp_recibo=ts_rcp, firma_servidor=b"")
        firma_sv = ECDSASigner.sign(recibo_temp.payload_bytes(), self._sk_sv_ecdsa)

        recibo = ReciboVotacionClasico(
            hash_boleta=hash_b,
            timestamp_recibo=ts_rcp,
            firma_servidor=firma_sv,
        )

        return True, "Voto aceptado y registrado exitosamente en la ánfora digital.", recibo

    def cerrar_jornada(self) -> List[PaqueteVotoClasico]:
        self.jornada_abierta = False
        return list(self.urna)
