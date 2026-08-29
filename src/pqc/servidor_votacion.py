"""
Módulo del Servidor de Votación (SV) — Protocolo Post-Cuántico PQC.
Responsable de:
  - Generación de claves de encapsulamiento ML-KEM-768 (ek_SV) y firma ML-DSA-65 (sk_SV)
  - Recepción de paquetes de voto y verificación de firmas (AR y Votante)
  - Control de unicidad (prevención de votos duplicados)
  - Almacenamiento seguro en la urna digital (sin descifrar)
  - Emisión de recibos firmados para los votantes
"""

import time
from typing import Dict, List, Optional, Tuple

from src.pqc.pqc_wrapper import MLKEM768, MLDSA65
from src.pqc.crypto_utils import canonical_json, sha3_256, sha256
from src.pqc.autoridad_registro import AutoridadRegistro, CredencialVotante
from src.pqc.votante import BoletaSufragio, PaqueteVoto


class ReciboVotacion:
    """Recibo digital emitido por el Servidor de Votación al votante."""

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
    def from_dict(cls, data: dict) -> "ReciboVotacion":
        return cls(
            hash_boleta=bytes.fromhex(data["hash_boleta_hex"]),
            timestamp_recibo=data["timestamp_recibo"],
            firma_servidor=bytes.fromhex(data["firma_servidor_hex"]),
        )


class ServidorVotacion:
    """Servidor de Votación (SV) que recepciona y custodia los votos cifrados."""

    def __init__(self, pk_ar: bytes, autoridad_registro: Optional[AutoridadRegistro] = None):
        self.pk_ar = pk_ar
        self.autoridad_registro = autoridad_registro

        # Generar par de claves ML-KEM-768: ek_sv (pública) y dk_sv (privada)
        # La clave dk_sv se transfiere a la Autoridad de Conteo fuera de banda
        self.ek_sv, self._dk_sv = MLKEM768.keypair()

        # Generar par de claves ML-DSA-65 del Servidor para emitir recibos
        self.pk_sv, self._sk_sv = MLDSA65.keypair()

        # Urna Digital: lista de boletas válidas registradas
        self.urna: List[PaqueteVoto] = []
        # Registro de IDs que ya emitieron voto (control anti-duplicados)
        self.votantes_registrados: set = set()
        # Estado de la jornada electoral
        self.jornada_abierta: bool = True

    def obtener_dk_para_conteo(self) -> bytes:
        """
        Transfiere la clave de desencapsulamiento dk_sv a la Autoridad de Conteo.
        (En un despliegue real, esto se hace fuera de banda).
        """
        return self._dk_sv

    def recepcionar_voto(self, paquete: PaqueteVoto) -> Tuple[bool, str, Optional[ReciboVotacion]]:
        """
        Recepciona, verifica y almacena una boleta de sufragio:
          1. Verifica que la jornada electoral esté abierta.
          2. Verifica la firma de la AR sobre la credencial del votante (ML-DSA-65).
          3. Verifica la firma del votante sobre la boleta (ML-DSA-65).
          4. Verifica que el votante no haya emitido sufragio previamente (unicidad).
          5. Almacena el paquete en la urna digital.
          6. Emite un recibo firmado criptográficamente.

        Retorna:
          (exito, mensaje, recibo)
        """
        if not self.jornada_abierta:
            return False, "La jornada electoral está cerrada. No se admiten votos.", None

        boleta = paquete.boleta
        cred = boleta.credencial
        id_v = cred.id_votante

        # 1. Control de duplicados en el servidor
        if id_v in self.votantes_registrados:
            return False, f"Voto rechazado: el votante '{id_v}' ya ha emitido su voto.", None

        # 2. Verificar firma de la Autoridad de Registro sobre la credencial
        payload_cred = cred.payload_bytes()
        if not MLDSA65.verify(payload_cred, cred.firma_ar, self.pk_ar):
            return False, "Voto rechazado: firma de la Autoridad de Registro INVÁLIDA.", None

        # 3. Verificar firma del Votante sobre la boleta completa
        payload_boleta = boleta.payload_bytes()
        if not MLDSA65.verify(payload_boleta, paquete.firma_votante, cred.pk_votante):
            return False, "Voto rechazado: firma digital del votante INVÁLIDA.", None

        # 4. Registrar en la urna y marcar como votado
        self.urna.append(paquete)
        self.votantes_registrados.add(id_v)

        if self.autoridad_registro:
            self.autoridad_registro.marcar_como_votado(id_v)

        # 5. Generar y firmar el recibo de votación
        hash_b = sha3_256(payload_boleta)
        ts_rcp = time.time()
        recibo_temp = ReciboVotacion(hash_boleta=hash_b, timestamp_recibo=ts_rcp, firma_servidor=b"")
        firma_sv = MLDSA65.sign(recibo_temp.payload_bytes(), self._sk_sv)

        recibo = ReciboVotacion(
            hash_boleta=hash_b,
            timestamp_recibo=ts_rcp,
            firma_servidor=firma_sv,
        )

        return True, "Voto aceptado y registrado exitosamente en la urna digital.", recibo

    def cerrar_jornada(self) -> List[PaqueteVoto]:
        """Cierra la recepción de votos y entrega la urna para el escrutinio."""
        self.jornada_abierta = False
        return list(self.urna)
