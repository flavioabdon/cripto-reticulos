"""
Módulo Python de nuestra implementación propia de NIST FIPS 203 (ML-KEM-768).
Expone la interfaz orientada a objetos y funcional de nuestra implementación propia
en C (src/pqc/fips203.c) sobre el anillo R_q = Z_3329[X]/(X^256 + 1).
"""

from src.pqc.pqc_wrapper import (
    MLKEM768,
    MLKEM768_PUBLIC_KEY_BYTES,
    MLKEM768_SECRET_KEY_BYTES,
    MLKEM768_CIPHERTEXT_BYTES,
    MLKEM768_SHARED_SECRET_BYTES,
)

# Parámetros matemáticos de ML-KEM-768 (Tabla 2 de FIPS 203)
FIPS203_PARAMS = {
    "algoritmo": "ML-KEM-768",
    "estandar": "NIST FIPS 203",
    "n": 256,
    "q": 3329,
    "k": 3,
    "eta_1": 2,
    "eta_2": 2,
    "d_u": 10,
    "d_v": 4,
    "ek_bytes": MLKEM768_PUBLIC_KEY_BYTES,
    "dk_bytes": MLKEM768_SECRET_KEY_BYTES,
    "ct_bytes": MLKEM768_CIPHERTEXT_BYTES,
    "ss_bytes": MLKEM768_SHARED_SECRET_BYTES,
}


def keygen() -> tuple[bytes, bytes]:
    """Algoritmo 19 de FIPS 203: ML-KEM.KeyGen() -> (ek, dk)."""
    return MLKEM768.keypair()


def keygen_internal(d: bytes, z: bytes) -> tuple[bytes, bytes]:
    """Algoritmo 16 de FIPS 203: ML-KEM.KeyGen_internal(d, z) -> (ek, dk)."""
    return MLKEM768.keypair_derand(d, z)


def encaps(ek: bytes) -> tuple[bytes, bytes]:
    """Algoritmo 20 de FIPS 203: ML-KEM.Encaps(ek) -> (ct, K)."""
    return MLKEM768.enc(ek)


def encaps_internal(ek: bytes, m: bytes) -> tuple[bytes, bytes]:
    """Algoritmo 17 de FIPS 203: ML-KEM.Encaps_internal(ek, m) -> (ct, K)."""
    return MLKEM768.enc_derand(ek, m)


def decaps(ct: bytes, dk: bytes) -> bytes:
    """Algoritmo 21 de FIPS 203: ML-KEM.Decaps(dk, ct) -> K."""
    return MLKEM768.dec(ct, dk)

