"""
Módulo Python de nuestra implementación propia de NIST FIPS 202:
  - SHA3-256, SHA3-512
  - SHAKE128, SHAKE256
  - Permutación Keccak-f[1600]

Proporciona tanto el acceso directo al motor propio en C (fips202.c) como
la implementación algorítmica de referencia en Python puro de la esponja Keccak.
"""

from src.pqc.pqc_wrapper import FIPS202

# Constantes de ronda de Keccak-f[1600] (Sección 3.2.5 de FIPS 202)
KECCAK_RC = (
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
)

# Desplazamientos de rotación rho[x + 5*y]
KECCAK_RHO = (
     0,  1, 62, 28, 27,
    36, 44,  6, 55, 20,
     3, 10, 43, 25, 39,
    41, 45, 15, 21,  8,
    18,  2, 61, 56, 14,
)

MASK64 = 0xFFFFFFFFFFFFFFFF


def _rotl64(x: int, s: int) -> int:
    return x if s == 0 else (((x << s) | (x >> (64 - s))) & MASK64)


def keccak_f1600(state: list[int]) -> None:
    """Permutación Keccak-f[1600] de 24 rondas (theta, rho, pi, chi, iota) en Python puro."""
    for rc in KECCAK_RC:
        # 1. Theta
        c = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
        d = [c[(x + 4) % 5] ^ _rotl64(c[(x + 1) % 5], 1) for x in range(5)]
        for i in range(25):
            state[i] ^= d[i % 5]

        # 2. Rho y Pi
        b = [0] * 25
        for y in range(5):
            for x in range(5):
                idx = x + 5 * y
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rotl64(state[idx], KECCAK_RHO[idx])

        # 3. Chi
        for y in range(5):
            base = 5 * y
            for x in range(5):
                state[base + x] = b[base + x] ^ ((~b[base + ((x + 1) % 5)] & MASK64) & b[base + ((x + 2) % 5)])

        # 4. Iota
        state[0] ^= rc


class KeccakSponge:
    """Construcción esponja incremental FIPS 202 en Python puro."""

    def __init__(self, rate: int, domain_sep: int):
        self.state = [0] * 25
        self.rate = rate
        self.domain_sep = domain_sep
        self.pos = 0
        self.finalized = False

    def absorb(self, data: bytes) -> "KeccakSponge":
        for byte_val in data:
            lane = self.pos >> 3
            shift = (self.pos & 7) << 3
            self.state[lane] ^= byte_val << shift
            self.pos += 1
            if self.pos == self.rate:
                keccak_f1600(self.state)
                self.pos = 0
        return self

    def finalize(self) -> "KeccakSponge":
        if not self.finalized:
            self.state[self.pos >> 3] ^= self.domain_sep << ((self.pos & 7) << 3)
            last = self.rate - 1
            self.state[last >> 3] ^= 0x80 << ((last & 7) << 3)
            keccak_f1600(self.state)
            self.pos = 0
            self.finalized = True
        return self

    def squeeze(self, outlen: int) -> bytes:
        if not self.finalized:
            self.finalize()
        out = bytearray(outlen)
        for i in range(outlen):
            if self.pos == self.rate:
                keccak_f1600(self.state)
                self.pos = 0
            lane = self.pos >> 3
            shift = (self.pos & 7) << 3
            out[i] = (self.state[lane] >> shift) & 0xFF
            self.pos += 1
        return bytes(out)


def sha3_256(data: bytes) -> bytes:
    """Calcula SHA3-256 (32 bytes) mediante nuestra implementación propia de FIPS 202."""
    return FIPS202.sha3_256(data)


def sha3_512(data: bytes) -> bytes:
    """Calcula SHA3-512 (64 bytes) mediante nuestra implementación propia de FIPS 202."""
    return FIPS202.sha3_512(data)


def shake128(data: bytes, outlen: int) -> bytes:
    """Calcula SHAKE128(data, outlen) mediante nuestra implementación propia de FIPS 202."""
    return FIPS202.shake128(data, outlen)


def shake256(data: bytes, outlen: int) -> bytes:
    """Calcula SHAKE256(data, outlen) mediante nuestra implementación propia de FIPS 202."""
    return FIPS202.shake256(data, outlen)

