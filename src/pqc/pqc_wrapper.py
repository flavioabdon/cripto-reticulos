"""
Wrapper Python (ctypes) para nuestras implementaciones propias de:
  - FIPS 202 (Keccak-f[1600]: SHA3-256, SHA3-512, SHAKE128, SHAKE256)
  - FIPS 203 (ML-KEM-768 - Key Encapsulation Mechanism)
  - FIPS 204 (ML-DSA-65  - Module-Lattice Digital Signature Algorithm)

No utiliza librerías externas de NIST ni PQClean.
"""

import ctypes
import os
import platform

# Constantes de longitud de bytes para ML-KEM-768 (FIPS 203)
MLKEM768_PUBLIC_KEY_BYTES = 1184
MLKEM768_SECRET_KEY_BYTES = 2400
MLKEM768_CIPHERTEXT_BYTES = 1088
MLKEM768_SHARED_SECRET_BYTES = 32

# Constantes de longitud de bytes para ML-DSA-65 (FIPS 204)
MLDSA65_PUBLIC_KEY_BYTES = 1952
MLDSA65_SECRET_KEY_BYTES = 4032
MLDSA65_SIGNATURE_BYTES = 3309


def _load_pqc_library():
    """Carga la biblioteca compartida propia libpqc_core."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ext = "dylib" if platform.system() == "Darwin" else "so"
    lib_path = os.path.join(base_dir, f"libpqc_core.{ext}")

    if not os.path.exists(lib_path):
        raise FileNotFoundError(
            f"No se encontró la biblioteca compartida en: {lib_path}. "
            f"Ejecute 'make build' para compilarla."
        )

    lib = ctypes.CDLL(lib_path)

    # Firmas ctypes para FIPS 202 (SHA-3 y SHAKE)
    lib.pqc_sha3_256.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
    ]
    lib.pqc_sha3_256.restype = None

    lib.pqc_sha3_512.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
    ]
    lib.pqc_sha3_512.restype = None

    lib.pqc_shake128.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
    ]
    lib.pqc_shake128.restype = None

    lib.pqc_shake256.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
    ]
    lib.pqc_shake256.restype = None

    # Firmas ctypes para ML-KEM-768 (FIPS 203)
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

    lib.fips203_mlkem768_keygen_internal.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.fips203_mlkem768_keygen_internal.restype = ctypes.c_int

    lib.fips203_mlkem768_encaps_internal.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.fips203_mlkem768_encaps_internal.restype = ctypes.c_int

    # Firmas ctypes para ML-DSA-65 (FIPS 204)
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

    lib.fips204_mldsa65_keygen_internal.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.fips204_mldsa65_keygen_internal.restype = ctypes.c_int

    lib.fips204_mldsa65_sign_ctx.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
    ]
    lib.fips204_mldsa65_sign_ctx.restype = ctypes.c_int

    return lib


_LIB = _load_pqc_library()


class FIPS202:
    """Implementación propia de FIPS 202 (SHA3-256, SHA3-512, SHAKE128, SHAKE256)."""

    @staticmethod
    def sha3_256(data: bytes) -> bytes:
        out_buf = (ctypes.c_uint8 * 32)()
        in_buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data) if data else None
        _LIB.pqc_sha3_256(out_buf, in_buf, len(data))
        return bytes(out_buf)

    @staticmethod
    def sha3_512(data: bytes) -> bytes:
        out_buf = (ctypes.c_uint8 * 64)()
        in_buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data) if data else None
        _LIB.pqc_sha3_512(out_buf, in_buf, len(data))
        return bytes(out_buf)

    @staticmethod
    def shake128(data: bytes, outlen: int) -> bytes:
        out_buf = (ctypes.c_uint8 * outlen)()
        in_buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data) if data else None
        _LIB.pqc_shake128(out_buf, outlen, in_buf, len(data))
        return bytes(out_buf)

    @staticmethod
    def shake256(data: bytes, outlen: int) -> bytes:
        out_buf = (ctypes.c_uint8 * outlen)()
        in_buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data) if data else None
        _LIB.pqc_shake256(out_buf, outlen, in_buf, len(data))
        return bytes(out_buf)


class MLKEM768:
    """Implementación propia de ML-KEM-768 (FIPS 203)."""

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
    def keypair_derand(d: bytes, z: bytes) -> tuple[bytes, bytes]:
        """Genera un par de claves determinista a partir de las semillas d (32 B) y z (32 B)."""
        if len(d) != 32 or len(z) != 32:
            raise ValueError("Las semillas d y z deben medir exactamente 32 bytes")
        pk_buf = (ctypes.c_uint8 * MLKEM768_PUBLIC_KEY_BYTES)()
        sk_buf = (ctypes.c_uint8 * MLKEM768_SECRET_KEY_BYTES)()
        d_buf = (ctypes.c_uint8 * 32).from_buffer_copy(d)
        z_buf = (ctypes.c_uint8 * 32).from_buffer_copy(z)

        res = _LIB.fips203_mlkem768_keygen_internal(pk_buf, sk_buf, d_buf, z_buf)
        if res != 0:
            raise RuntimeError(f"Error en ML-KEM-768 keygen_internal (código {res})")
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
    def enc_derand(pk: bytes, m: bytes) -> tuple[bytes, bytes]:
        """Encapsula de forma determinista con la semilla m (32 bytes)."""
        if len(pk) != MLKEM768_PUBLIC_KEY_BYTES or len(m) != 32:
            raise ValueError("Parámetros inválidos para enc_derand")
        ct_buf = (ctypes.c_uint8 * MLKEM768_CIPHERTEXT_BYTES)()
        ss_buf = (ctypes.c_uint8 * MLKEM768_SHARED_SECRET_BYTES)()
        pk_buf = (ctypes.c_uint8 * len(pk)).from_buffer_copy(pk)
        m_buf = (ctypes.c_uint8 * 32).from_buffer_copy(m)

        res = _LIB.fips203_mlkem768_encaps_internal(ct_buf, ss_buf, pk_buf, m_buf)
        if res != 0:
            raise RuntimeError(f"Error en ML-KEM-768 encaps_internal (código {res})")
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
    """Implementación propia de ML-DSA-65 (FIPS 204)."""

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
    def keypair_derand(xi: bytes) -> tuple[bytes, bytes]:
        """Genera un par de claves determinista a partir de la semilla xi (32 B)."""
        if len(xi) != 32:
            raise ValueError("La semilla xi debe medir 32 bytes")
        pk_buf = (ctypes.c_uint8 * MLDSA65_PUBLIC_KEY_BYTES)()
        sk_buf = (ctypes.c_uint8 * MLDSA65_SECRET_KEY_BYTES)()
        xi_buf = (ctypes.c_uint8 * 32).from_buffer_copy(xi)

        res = _LIB.fips204_mldsa65_keygen_internal(pk_buf, sk_buf, xi_buf)
        if res != 0:
            raise RuntimeError(f"Error en ML-DSA-65 keygen_internal (código {res})")
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
