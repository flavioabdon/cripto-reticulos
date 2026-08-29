"""
Wrapper Python (ctypes) para las primitivas post-cuánticas de PQClean:
  - ML-KEM-768 (FIPS 203 - Key Encapsulation Mechanism)
  - ML-DSA-65  (FIPS 204 - Module-Lattice Digital Signature Algorithm)
"""

import ctypes
import os
import platform
import sys

# Constantes de longitud de bytes
MLKEM768_PUBLIC_KEY_BYTES = 1184
MLKEM768_SECRET_KEY_BYTES = 2400
MLKEM768_CIPHERTEXT_BYTES = 1088
MLKEM768_SHARED_SECRET_BYTES = 32

MLDSA65_PUBLIC_KEY_BYTES = 1952
MLDSA65_SECRET_KEY_BYTES = 4032
MLDSA65_SIGNATURE_BYTES = 3309


def _load_pqc_library():
    """Carga la biblioteca compartida libpqc_core."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ext = "dylib" if platform.system() == "Darwin" else "so"
    lib_path = os.path.join(base_dir, f"libpqc_core.{ext}")

    if not os.path.exists(lib_path):
        raise FileNotFoundError(
            f"No se encontró la biblioteca compartida en: {lib_path}. "
            f"Ejecute 'make build' para compilarla."
        )

    lib = ctypes.CDLL(lib_path)

    # Definir firmas de tipos ctypes para ML-KEM-768
    lib.ml_kem_768_keypair.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.ml_kem_768_keypair.restype = ctypes.c_int

    lib.ml_kem_768_encaps.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.ml_kem_768_encaps.restype = ctypes.c_int

    lib.ml_kem_768_decaps.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.ml_kem_768_decaps.restype = ctypes.c_int

    # Definir firmas de tipos ctypes para ML-DSA-65
    lib.ml_dsa_65_keypair.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.ml_dsa_65_keypair.restype = ctypes.c_int

    lib.ml_dsa_65_sign.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.ml_dsa_65_sign.restype = ctypes.c_int

    lib.ml_dsa_65_verify.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.ml_dsa_65_verify.restype = ctypes.c_int

    return lib


_LIB = _load_pqc_library()


class MLKEM768:
    """Implementación de ML-KEM-768 (FIPS 203)."""

    PUBLIC_KEY_SIZE = MLKEM768_PUBLIC_KEY_BYTES
    SECRET_KEY_SIZE = MLKEM768_SECRET_KEY_BYTES
    CIPHERTEXT_SIZE = MLKEM768_CIPHERTEXT_BYTES
    SHARED_SECRET_SIZE = MLKEM768_SHARED_SECRET_BYTES

    @staticmethod
    def keypair() -> tuple[bytes, bytes]:
        """Genera un par de claves (pk, sk) para ML-KEM-768."""
        pk_buf = (ctypes.c_uint8 * MLKEM768_PUBLIC_KEY_BYTES)()
        sk_buf = (ctypes.c_uint8 * MLKEM768_SECRET_KEY_BYTES)()

        res = _LIB.ml_kem_768_keypair(pk_buf, sk_buf)
        if res != 0:
            raise RuntimeError(f"Error en ML-KEM-768 keypair (código {res})")

        return bytes(pk_buf), bytes(sk_buf)

    @staticmethod
    def enc(pk: bytes) -> tuple[bytes, bytes]:
        """
        Encapsula una clave compartida con la clave pública pk.
        Retorna: (ciphertext, shared_secret)
        """
        if len(pk) != MLKEM768_PUBLIC_KEY_BYTES:
            raise ValueError(
                f"Longitud de clave pública inválida: {len(pk)} (esperado {MLKEM768_PUBLIC_KEY_BYTES})"
            )

        ct_buf = (ctypes.c_uint8 * MLKEM768_CIPHERTEXT_BYTES)()
        ss_buf = (ctypes.c_uint8 * MLKEM768_SHARED_SECRET_BYTES)()
        pk_buf = (ctypes.c_uint8 * len(pk)).from_buffer_copy(pk)

        res = _LIB.ml_kem_768_encaps(ct_buf, ss_buf, pk_buf)
        if res != 0:
            raise RuntimeError(f"Error en ML-KEM-768 encaps (código {res})")

        return bytes(ct_buf), bytes(ss_buf)

    @staticmethod
    def dec(ct: bytes, sk: bytes) -> bytes:
        """
        Desencapsula el ciphertext con la clave secreta sk.
        Retorna: shared_secret
        """
        if len(ct) != MLKEM768_CIPHERTEXT_BYTES:
            raise ValueError(
                f"Longitud de ciphertext inválida: {len(ct)} (esperado {MLKEM768_CIPHERTEXT_BYTES})"
            )
        if len(sk) != MLKEM768_SECRET_KEY_BYTES:
            raise ValueError(
                f"Longitud de clave secreta inválida: {len(sk)} (esperado {MLKEM768_SECRET_KEY_BYTES})"
            )

        ss_buf = (ctypes.c_uint8 * MLKEM768_SHARED_SECRET_BYTES)()
        ct_buf = (ctypes.c_uint8 * len(ct)).from_buffer_copy(ct)
        sk_buf = (ctypes.c_uint8 * len(sk)).from_buffer_copy(sk)

        res = _LIB.ml_kem_768_decaps(ss_buf, ct_buf, sk_buf)
        if res != 0:
            raise RuntimeError(f"Error en ML-KEM-768 decaps (código {res})")

        return bytes(ss_buf)


class MLDSA65:
    """Implementación de ML-DSA-65 (FIPS 204)."""

    PUBLIC_KEY_SIZE = MLDSA65_PUBLIC_KEY_BYTES
    SECRET_KEY_SIZE = MLDSA65_SECRET_KEY_BYTES
    SIGNATURE_SIZE = MLDSA65_SIGNATURE_BYTES

    @staticmethod
    def keypair() -> tuple[bytes, bytes]:
        """Genera un par de claves (pk, sk) para ML-DSA-65."""
        pk_buf = (ctypes.c_uint8 * MLDSA65_PUBLIC_KEY_BYTES)()
        sk_buf = (ctypes.c_uint8 * MLDSA65_SECRET_KEY_BYTES)()

        res = _LIB.ml_dsa_65_keypair(pk_buf, sk_buf)
        if res != 0:
            raise RuntimeError(f"Error en ML-DSA-65 keypair (código {res})")

        return bytes(pk_buf), bytes(sk_buf)

    @staticmethod
    def sign(m: bytes, sk: bytes) -> bytes:
        """Firma el mensaje m con la clave secreta sk."""
        if len(sk) != MLDSA65_SECRET_KEY_BYTES:
            raise ValueError(
                f"Longitud de clave secreta inválida: {len(sk)} (esperado {MLDSA65_SECRET_KEY_BYTES})"
            )

        sig_buf = (ctypes.c_uint8 * MLDSA65_SIGNATURE_BYTES)()
        siglen = ctypes.c_size_t(0)
        m_buf = (ctypes.c_uint8 * len(m)).from_buffer_copy(m) if m else None
        sk_buf = (ctypes.c_uint8 * len(sk)).from_buffer_copy(sk)

        res = _LIB.ml_dsa_65_sign(sig_buf, ctypes.byref(siglen), m_buf, len(m), sk_buf)
        if res != 0:
            raise RuntimeError(f"Error en ML-DSA-65 sign (código {res})")

        return bytes(sig_buf)[: siglen.value]

    @staticmethod
    def verify(m: bytes, sig: bytes, pk: bytes) -> bool:
        """Verifica la firma sig sobre el mensaje m con la clave pública pk."""
        if len(pk) != MLDSA65_PUBLIC_KEY_BYTES:
            raise ValueError(
                f"Longitud de clave pública inválida: {len(pk)} (esperado {MLDSA65_PUBLIC_KEY_BYTES})"
            )

        sig_buf = (ctypes.c_uint8 * len(sig)).from_buffer_copy(sig)
        m_buf = (ctypes.c_uint8 * len(m)).from_buffer_copy(m) if m else None
        pk_buf = (ctypes.c_uint8 * len(pk)).from_buffer_copy(pk)

        res = _LIB.ml_dsa_65_verify(sig_buf, len(sig), m_buf, len(m), pk_buf)
        return res == 0
