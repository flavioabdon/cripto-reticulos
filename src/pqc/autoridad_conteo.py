"""
Módulo de la Autoridad de Conteo (AC / Tally) — Protocolo Post-Cuántico PQC.
Responsable de:
  - Custodia de la clave privada de desencapsulamiento ML-KEM-768 (dk_SV)
  - Apertura de el ánfora tras el cierre de la jornada electoral
  - Desencapsulamiento y descifrado seguro de cada voto
  - Re-verificación de integridad y correspondencia de firmas
  - Escrutinio final y publicación de resultados auditables
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple

from src.pqc.pqc_wrapper import MLKEM768, MLDSA65
from src.pqc.crypto_utils import aes_gcm_decrypt, sha3_256
from src.pqc.votante import PaqueteVoto


class ResultadoEscrutinio:
    """Resultados consolidados del conteo de votos."""

    def __init__(
        self,
        conteo: Dict[str, int],
        total_votos: int,
        votos_validos: int,
        votos_invalidos: int,
        hashes_auditoria: List[dict],
    ):
        self.conteo = conteo
        self.total_votos = total_votos
        self.votos_validos = votos_validos
        self.votos_invalidos = votos_invalidos
        self.hashes_auditoria = hashes_auditoria

    def to_dict(self) -> dict:
        return {
            "total_votos": self.total_votos,
            "votos_validos": self.votos_validos,
            "votos_invalidos": self.votos_invalidos,
            "conteo": self.conteo,
            "hashes_auditoria": self.hashes_auditoria,
        }


class AutoridadConteo:
    """Autoridad de Conteo (AC) responsable del escrutinio final."""

    def __init__(self, dk_servidor: bytes, pk_ar: bytes):
        self._dk_servidor = dk_servidor
        self.pk_ar = pk_ar

    def realizar_escrutinio(self, urna: List[PaqueteVoto]) -> ResultadoEscrutinio:
        """
        Ejecuta el escrutinio sobre la lista de paquetes en la ánfora digital:
          1. Para cada boleta en el ánfora:
             a. Re-verifica la firma de la AR sobre la credencial.
             b. Re-verifica la firma del votante sobre la boleta (integridad).
             c. Desencapsula la clave simétrica con ML-KEM-768: K = decaps(dk_sv, ct_kem).
             d. Descifra el voto con AES-256-GCM usando K.
             e. Acumula el conteo del candidato.
          2. Genera la lista de hashes de auditoría pública.

        Retorna:
          ResultadoEscrutinio con los totales por candidato y registros de auditoría.
        """
        conteo = Counter()
        votos_validos = 0
        votos_invalidos = 0
        hashes_auditoria = []

        for idx, paquete in enumerate(urna):
            boleta = paquete.boleta
            cred = boleta.credencial
            payload_boleta = boleta.payload_bytes()
            hash_boleta = sha3_256(payload_boleta).hex()

            # 1. Re-verificar firma de AR sobre la credencial
            payload_cred = cred.payload_bytes()
            if not MLDSA65.verify(payload_cred, cred.firma_ar, self.pk_ar):
                votos_invalidos += 1
                hashes_auditoria.append({
                    "posicion": idx,
                    "hash_boleta": hash_boleta,
                    "id_votante": cred.id_votante,
                    "estado": "INVALIDO_FIRMA_AR",
                })
                continue

            # 2. Re-verificar firma del votante sobre la boleta (integridad / correspondencia)
            if not MLDSA65.verify(payload_boleta, paquete.firma_votante, cred.pk_votante):
                votos_invalidos += 1
                hashes_auditoria.append({
                    "posicion": idx,
                    "hash_boleta": hash_boleta,
                    "id_votante": cred.id_votante,
                    "estado": "INVALIDO_FIRMA_VOTANTE",
                })
                continue

            # 3. Desencapsulamiento ML-KEM-768
            try:
                shared_secret = MLKEM768.dec(boleta.ciphertext_kem, self._dk_servidor)
            except Exception as e:
                votos_invalidos += 1
                hashes_auditoria.append({
                    "posicion": idx,
                    "hash_boleta": hash_boleta,
                    "id_votante": cred.id_votante,
                    "estado": f"ERROR_DESENCAPSULAMIENTO: {str(e)}",
                })
                continue

            # 4. Descifrado simétrico AES-256-GCM
            try:
                voto_bytes = aes_gcm_decrypt(shared_secret, boleta.voto_cifrado, boleta.nonce_aead)
                opcion_voto = voto_bytes.decode("utf-8")
            except Exception as e:
                votos_invalidos += 1
                hashes_auditoria.append({
                    "posicion": idx,
                    "hash_boleta": hash_boleta,
                    "id_votante": cred.id_votante,
                    "estado": f"ERROR_DESCIFRADO: {str(e)}",
                })
                continue

            # 5. Acumular en el escrutinio
            conteo[opcion_voto] += 1
            votos_validos += 1
            hashes_auditoria.append({
                "posicion": idx,
                "hash_boleta": hash_boleta,
                "id_votante": cred.id_votante,
                "estado": "VALIDO_CONTABILIZADO",
            })

        return ResultadoEscrutinio(
            conteo=dict(conteo),
            total_votos=len(urna),
            votos_validos=votos_validos,
            votos_invalidos=votos_invalidos,
            hashes_auditoria=hashes_auditoria,
        )
