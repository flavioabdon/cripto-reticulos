"""
Módulo Python de nuestra implementación propia de NIST FIPS 204 (ML-DSA-65).
Expone la interfaz orientada a objetos y funcional de nuestra implementación propia
en C (src/pqc/fips204.c) sobre el anillo R_q = Z_8380417[X]/(X^256 + 1).
"""

from src.pqc.pqc_wrapper import (
    MLDSA65,
    MLDSA65_PUBLIC_KEY_BYTES,
    MLDSA65_SECRET_KEY_BYTES,
    MLDSA65_SIGNATURE_BYTES,
)

# Parámetros matemáticos de ML-DSA-65 (Tabla 1 de FIPS 204)
FIPS204_PARAMS = {
    "algoritmo": "ML-DSA-65",
    "estandar": "NIST FIPS 204",
    "n": 256,
    "q": 8380417,
    "d": 13,
    "tau": 49,
    "gamma_1": 1 << 19,
    "gamma_2": (8380417 - 1) // 32,
    "k": 6,
    "l": 5,
    "eta": 4,
    "beta": 196,
    "omega": 55,
    "pk_bytes": MLDSA65_PUBLIC_KEY_BYTES,
    "sk_bytes": MLDSA65_SECRET_KEY_BYTES,
    "sig_bytes": MLDSA65_SIGNATURE_BYTES,
}


def keygen() -> tuple[bytes, bytes]:
    """Algoritmo 1 de FIPS 204: ML-DSA.KeyGen() -> (pk, sk)."""
    return MLDSA65.keypair()


def keygen_internal(xi: bytes) -> tuple[bytes, bytes]:
    """Algoritmo 6 de FIPS 204: ML-DSA.KeyGen_internal(xi) -> (pk, sk)."""
    return MLDSA65.keypair_derand(xi)


def sign(msg: bytes, sk: bytes) -> bytes:
    """Algoritmo 2 de FIPS 204: ML-DSA.Sign(sk, M) -> sig."""
    return MLDSA65.sign(msg, sk)


def verify(msg: bytes, sig: bytes, pk: bytes) -> bool:
    """Algoritmo 3 de FIPS 204: ML-DSA.Verify(pk, M, sig) -> bool."""
    return MLDSA65.verify(msg, sig, pk)

