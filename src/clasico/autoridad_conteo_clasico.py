"""
Módulo de la Autoridad de Conteo (AC / Tally) — Protocolo Clásico (RSA + ECDSA).
"""

from collections import Counter
from typing import Dict, List, Optional
from cryptography.hazmat.primitives import serialization

from src.clasico.crypto_clasico import RSACipher, ECDSASigner, aes_gcm_decrypt
from src.clasico.votante_clasico import PaqueteVotoClasico
from src.pqc.crypto_utils import sha256


class ResultadoEscrutinioClasico:
    """Resultados consolidados del conteo de votos clásico."""

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


class AutoridadConteoClasico:
    """Autoridad de Conteo (AC) en el esquema clásico."""

    def __init__(self, sk_servidor_rsa: bytes, pk_ar_ecdsa: bytes):
        self._sk_servidor_rsa = sk_servidor_rsa
        self.pk_ar = pk_ar_ecdsa
        # Precargar objeto de clave privada RSA para alto rendimiento en escrutinio masivo
        self._rsa_key_obj = serialization.load_der_private_key(sk_servidor_rsa, password=None)
        self._pk_ar_obj = serialization.load_der_public_key(pk_ar_ecdsa)

    def realizar_escrutinio(self, urna: List[PaqueteVotoClasico]) -> ResultadoEscrutinioClasico:
        """
        Ejecuta el escrutinio sobre el ánfora clásica:
          1. Re-verifica firma ECDSA de AR sobre la credencial.
          2. Re-verifica firma ECDSA del votante sobre la boleta.
          3. Descifra la clave simétrica con RSA-OAEP: K = RSADecrypt(sk_sv_rsa, clave_cifrada_rsa).
          4. Descifra el voto con AES-256-GCM usando K.
          5. Acumula el conteo por candidato.
        """
        conteo = Counter()
        votos_validos = 0
        votos_invalidos = 0
        hashes_auditoria = []

        for idx, paquete in enumerate(urna):
            boleta = paquete.boleta
            cred = boleta.credencial
            payload_boleta = boleta.payload_bytes()
            hash_boleta = sha256(payload_boleta).hex()

            # 1. Re-verificar firma ECDSA de la AR
            payload_cred = cred.payload_bytes()
            if not ECDSASigner.verify(payload_cred, cred.firma_ar, self._pk_ar_obj):
                votos_invalidos += 1
                hashes_auditoria.append({
                    "posicion": idx,
                    "hash_boleta": hash_boleta,
                    "id_votante": cred.id_votante,
                    "estado": "INVALIDO_FIRMA_AR",
                })
                continue

            # 2. Re-verificar firma ECDSA del votante
            if not ECDSASigner.verify(payload_boleta, paquete.firma_votante, cred.pk_votante):
                votos_invalidos += 1
                hashes_auditoria.append({
                    "posicion": idx,
                    "hash_boleta": hash_boleta,
                    "id_votante": cred.id_votante,
                    "estado": "INVALIDO_FIRMA_VOTANTE",
                })
                continue

            # 3. Descifrado RSA-OAEP
            try:
                k_efimera = RSACipher.decrypt(self._rsa_key_obj, boleta.clave_cifrada_rsa)
            except Exception as e:
                votos_invalidos += 1
                hashes_auditoria.append({
                    "posicion": idx,
                    "hash_boleta": hash_boleta,
                    "id_votante": cred.id_votante,
                    "estado": f"ERROR_DESCIFRADO_RSA: {str(e)}",
                })
                continue

            # 4. Descifrado AES-256-GCM
            try:
                voto_bytes = aes_gcm_decrypt(k_efimera, boleta.voto_cifrado, boleta.nonce_aead)
                opcion_voto = voto_bytes.decode("utf-8")
            except Exception as e:
                votos_invalidos += 1
                hashes_auditoria.append({
                    "posicion": idx,
                    "hash_boleta": hash_boleta,
                    "id_votante": cred.id_votante,
                    "estado": f"ERROR_DESCIFRADO_AES: {str(e)}",
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

        return ResultadoEscrutinioClasico(
            conteo=dict(conteo),
            total_votos=len(urna),
            votos_validos=votos_validos,
            votos_invalidos=votos_invalidos,
            hashes_auditoria=hashes_auditoria,
        )
