/**
 * @file fips202.c
 * @brief Implementación propia del estándar NIST FIPS 202 (Keccak-f[1600], SHA-3 y SHAKE).
 *
 * Proyecto de Grado - Universidad Mayor de San Andrés (UMSA)
 * Implementación matemática directa de las transformaciones paso a paso de FIPS 202
 * Sección 3.2 (theta, rho, pi, chi, iota) y Sección 4 (construcción esponja).
 */

#include "fips202.h"
#include <fcntl.h>
#include <string.h>
#include <unistd.h>

/* Rotación circular de 64 bits hacia la izquierda */
static inline uint64_t rotl64(uint64_t x, unsigned int s) {
    return (s == 0) ? x : ((x << s) | (x >> (64U - s)));
}

/* Constantes de ronda de Keccak-f[1600] (Sección 3.2.5 de FIPS 202) */
static const uint64_t KECCAK_RC[24] = {
    0x0000000000000001ULL, 0x0000000000008082ULL,
    0x800000000000808aULL, 0x8000000080008000ULL,
    0x000000000000808bULL, 0x0000000080000001ULL,
    0x8000000080008081ULL, 0x8000000000008009ULL,
    0x000000000000008aULL, 0x0000000000000088ULL,
    0x0000000080008009ULL, 0x000000008000000aULL,
    0x000000008000808bULL, 0x800000000000008bULL,
    0x8000000000008089ULL, 0x8000000000008003ULL,
    0x8000000000008002ULL, 0x8000000000000080ULL,
    0x000000000000800aULL, 0x800000008000000aULL,
    0x8000000080008081ULL, 0x8000000000008080ULL,
    0x0000000080000001ULL, 0x8000000080008008ULL
};

/* Desplazamientos de rotación rho[x + 5*y] (Tabla 2 de FIPS 202) */
static const unsigned int KECCAK_RHO[25] = {
     0,  1, 62, 28, 27,
    36, 44,  6, 55, 20,
     3, 10, 43, 25, 39,
    41, 45, 15, 21,  8,
    18,  2, 61, 56, 14
};

/**
 * Permutación Keccak-f[1600] de 24 rondas sobre el arreglo de estado A[25].
 * Cada elemento A[x + 5*y] representa un carril (lane) de 64 bits en formato little-endian.
 */
static void keccak_f1600_permute(uint64_t A[25]) {
    uint64_t C[5], D[5], B[25];

    for (int round = 0; round < 24; round++) {
        /* 1. Paso Theta (Sección 3.2.1): difusión entre columnas */
        for (int x = 0; x < 5; x++) {
            C[x] = A[x] ^ A[x + 5] ^ A[x + 10] ^ A[x + 15] ^ A[x + 20];
        }
        for (int x = 0; x < 5; x++) {
            D[x] = C[(x + 4) % 5] ^ rotl64(C[(x + 1) % 5], 1);
        }
        for (int y = 0; y < 5; y++) {
            for (int x = 0; x < 5; x++) {
                A[x + 5 * y] ^= D[x];
            }
        }

        /* 2. Pasos Rho y Pi (Secciones 3.2.2 y 3.2.3): rotación de bits y permutación de carriles */
        for (int y = 0; y < 5; y++) {
            for (int x = 0; x < 5; x++) {
                int new_x = y;
                int new_y = (2 * x + 3 * y) % 5;
                B[new_x + 5 * new_y] = rotl64(A[x + 5 * y], KECCAK_RHO[x + 5 * y]);
            }
        }

        /* 3. Paso Chi (Sección 3.2.4): capa no lineal sobre cada fila */
        for (int y = 0; y < 5; y++) {
            for (int x = 0; x < 5; x++) {
                A[x + 5 * y] = B[x + 5 * y] ^
                               ((~B[((x + 1) % 5) + 5 * y]) & B[((x + 2) % 5) + 5 * y]);
            }
        }

        /* 4. Paso Iota (Sección 3.2.5): ruptura de simetría mediante constante de ronda */
        A[0] ^= KECCAK_RC[round];
    }
}

/* XOR de un byte en la posición byte_idx del arreglo de estado de 64 bits (little-endian) */
static inline void state_xor_byte(uint64_t state[25], size_t byte_idx, uint8_t val) {
    size_t lane = byte_idx >> 3;
    unsigned int shift = (unsigned int)((byte_idx & 7U) << 3);
    state[lane] ^= ((uint64_t)val) << shift;
}

/* Lectura de un byte desde la posición byte_idx del arreglo de estado de 64 bits (little-endian) */
static inline uint8_t state_get_byte(const uint64_t state[25], size_t byte_idx) {
    size_t lane = byte_idx >> 3;
    unsigned int shift = (unsigned int)((byte_idx & 7U) << 3);
    return (uint8_t)((state[lane] >> shift) & 0xFFU);
}

void fips202_sponge_init(fips202_sponge_ctx *ctx, size_t rate) {
    memset(ctx->state, 0, sizeof(ctx->state));
    ctx->rate = rate;
    ctx->pos = 0;
    ctx->finalized = 0;
}

void fips202_sponge_absorb(fips202_sponge_ctx *ctx, const uint8_t *in, size_t inlen) {
    for (size_t i = 0; i < inlen; i++) {
        state_xor_byte(ctx->state, ctx->pos, in[i]);
        ctx->pos++;
        if (ctx->pos == ctx->rate) {
            keccak_f1600_permute(ctx->state);
            ctx->pos = 0;
        }
    }
}

void fips202_sponge_finalize(fips202_sponge_ctx *ctx, uint8_t domain_sep) {
    if (ctx->finalized) {
        return;
    }
    /* Padding pad10*1 con sufijo de dominio (Sección 5.1 de FIPS 202) */
    state_xor_byte(ctx->state, ctx->pos, domain_sep);
    state_xor_byte(ctx->state, ctx->rate - 1, 0x80U);
    keccak_f1600_permute(ctx->state);
    ctx->pos = 0;
    ctx->finalized = 1;
}

void fips202_sponge_squeeze(fips202_sponge_ctx *ctx, uint8_t *out, size_t outlen) {
    for (size_t i = 0; i < outlen; i++) {
        if (ctx->pos == ctx->rate) {
            keccak_f1600_permute(ctx->state);
            ctx->pos = 0;
        }
        out[i] = state_get_byte(ctx->state, ctx->pos);
        ctx->pos++;
    }
}

/* ============================================================
 * Implementación SHAKE128
 * ============================================================ */
void fips202_shake128_init(fips202_shake128_ctx *ctx) {
    fips202_sponge_init(ctx, FIPS202_SHAKE128_RATE);
}

void fips202_shake128_absorb(fips202_shake128_ctx *ctx, const uint8_t *in, size_t inlen) {
    fips202_sponge_absorb(ctx, in, inlen);
}

void fips202_shake128_finalize(fips202_shake128_ctx *ctx) {
    fips202_sponge_finalize(ctx, FIPS202_DOMAIN_SHAKE);
}

void fips202_shake128_squeeze(uint8_t *out, size_t outlen, fips202_shake128_ctx *ctx) {
    if (!ctx->finalized) {
        fips202_shake128_finalize(ctx);
    }
    fips202_sponge_squeeze(ctx, out, outlen);
}

void fips202_shake128(uint8_t *out, size_t outlen, const uint8_t *in, size_t inlen) {
    fips202_shake128_ctx ctx;
    fips202_shake128_init(&ctx);
    fips202_shake128_absorb(&ctx, in, inlen);
    fips202_shake128_finalize(&ctx);
    fips202_shake128_squeeze(out, outlen, &ctx);
}

/* ============================================================
 * Implementación SHAKE256
 * ============================================================ */
void fips202_shake256_init(fips202_shake256_ctx *ctx) {
    fips202_sponge_init(ctx, FIPS202_SHAKE256_RATE);
}

void fips202_shake256_absorb(fips202_shake256_ctx *ctx, const uint8_t *in, size_t inlen) {
    fips202_sponge_absorb(ctx, in, inlen);
}

void fips202_shake256_finalize(fips202_shake256_ctx *ctx) {
    fips202_sponge_finalize(ctx, FIPS202_DOMAIN_SHAKE);
}

void fips202_shake256_squeeze(uint8_t *out, size_t outlen, fips202_shake256_ctx *ctx) {
    if (!ctx->finalized) {
        fips202_shake256_finalize(ctx);
    }
    fips202_sponge_squeeze(ctx, out, outlen);
}

void fips202_shake256(uint8_t *out, size_t outlen, const uint8_t *in, size_t inlen) {
    fips202_shake256_ctx ctx;
    fips202_shake256_init(&ctx);
    fips202_shake256_absorb(&ctx, in, inlen);
    fips202_shake256_finalize(&ctx);
    fips202_shake256_squeeze(out, outlen, &ctx);
}

/* ============================================================
 * Implementación SHA3-256 y SHA3-512
 * ============================================================ */
void fips202_sha3_256(uint8_t out[32], const uint8_t *in, size_t inlen) {
    fips202_sha3_256_ctx ctx;
    fips202_sponge_init(&ctx, FIPS202_SHA3_256_RATE);
    fips202_sponge_absorb(&ctx, in, inlen);
    fips202_sponge_finalize(&ctx, FIPS202_DOMAIN_SHA3);
    fips202_sponge_squeeze(&ctx, out, 32);
}

void fips202_sha3_512(uint8_t out[64], const uint8_t *in, size_t inlen) {
    fips202_sha3_512_ctx ctx;
    fips202_sponge_init(&ctx, FIPS202_SHA3_512_RATE);
    fips202_sponge_absorb(&ctx, in, inlen);
    fips202_sponge_finalize(&ctx, FIPS202_DOMAIN_SHA3);
    fips202_sponge_squeeze(&ctx, out, 64);
}

/* ============================================================
 * Generador de Bytes Aleatorios Criptográficamente Seguros
 * ============================================================ */
int pqc_randombytes(uint8_t *out, size_t outlen) {
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) {
        return -1;
    }
    size_t total = 0;
    while (total < outlen) {
        ssize_t n = read(fd, out + total, outlen - total);
        if (n <= 0) {
            close(fd);
            return -1;
        }
        total += (size_t)n;
    }
    close(fd);
    return 0;
}

