/**
 * @file fips202.h
 * @brief Implementación propia del estándar NIST FIPS 202 (SHA-3 y funciones XOF SHAKE).
 *
 * Proyecto de Grado - Universidad Mayor de San Andrés (UMSA)
 * Criptografía Post-Cuántica Basada en Retículos para Votación Electrónica.
 *
 * Implementa desde cero la construcción esponja Keccak-f[1600] y las funciones:
 *   - SHA3-256  (r = 136 bytes, c = 64 bytes, sufijo 0x06, salida 32 bytes)
 *   - SHA3-512  (r = 72 bytes,  c = 128 bytes, sufijo 0x06, salida 64 bytes)
 *   - SHAKE128  (r = 168 bytes, c = 32 bytes, sufijo 0x1F, salida de longitud arbitraria)
 *   - SHAKE256  (r = 136 bytes, c = 64 bytes, sufijo 0x1F, salida de longitud arbitraria)
 */

#ifndef PQC_FIPS202_H
#define PQC_FIPS202_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Tasas de absorción/extracción (rate en bytes) según FIPS 202 */
#define FIPS202_SHAKE128_RATE 168
#define FIPS202_SHAKE256_RATE 136
#define FIPS202_SHA3_256_RATE 136
#define FIPS202_SHA3_512_RATE 72

/* Sufijos de separación de dominio de FIPS 202 */
#define FIPS202_DOMAIN_SHA3  0x06
#define FIPS202_DOMAIN_SHAKE 0x1F

/**
 * Estado de la esponja Keccak-f[1600] (1600 bits = 25 palabras de 64 bits).
 * Almacenado en pila sin asignaciones dinámicas de memoria.
 */
typedef struct {
    uint64_t state[25];  /* Arreglo de estado A[5][5] aplanado como state[x + 5*y] */
    size_t rate;         /* Tasa r en bytes */
    size_t pos;          /* Posición actual dentro del bloque de tasa [0, rate) */
    int finalized;       /* Indicador de si ya se aplicó el padding final */
} fips202_sponge_ctx;

typedef fips202_sponge_ctx fips202_shake128_ctx;
typedef fips202_sponge_ctx fips202_shake256_ctx;
typedef fips202_sponge_ctx fips202_sha3_256_ctx;
typedef fips202_sponge_ctx fips202_sha3_512_ctx;

/* ============================================================
 * API Incremental de Esponja Genérica (FIPS 202)
 * ============================================================ */
void fips202_sponge_init(fips202_sponge_ctx *ctx, size_t rate);
void fips202_sponge_absorb(fips202_sponge_ctx *ctx, const uint8_t *in, size_t inlen);
void fips202_sponge_finalize(fips202_sponge_ctx *ctx, uint8_t domain_sep);
void fips202_sponge_squeeze(fips202_sponge_ctx *ctx, uint8_t *out, size_t outlen);

/* ============================================================
 * API SHAKE128 (XOF con seguridad de 128 bits)
 * ============================================================ */
void fips202_shake128_init(fips202_shake128_ctx *ctx);
void fips202_shake128_absorb(fips202_shake128_ctx *ctx, const uint8_t *in, size_t inlen);
void fips202_shake128_finalize(fips202_shake128_ctx *ctx);
void fips202_shake128_squeeze(uint8_t *out, size_t outlen, fips202_shake128_ctx *ctx);
void fips202_shake128(uint8_t *out, size_t outlen, const uint8_t *in, size_t inlen);

/* ============================================================
 * API SHAKE256 (XOF con seguridad de 256 bits)
 * ============================================================ */
void fips202_shake256_init(fips202_shake256_ctx *ctx);
void fips202_shake256_absorb(fips202_shake256_ctx *ctx, const uint8_t *in, size_t inlen);
void fips202_shake256_finalize(fips202_shake256_ctx *ctx);
void fips202_shake256_squeeze(uint8_t *out, size_t outlen, fips202_shake256_ctx *ctx);
void fips202_shake256(uint8_t *out, size_t outlen, const uint8_t *in, size_t inlen);

/* ============================================================
 * API SHA3-256 y SHA3-512 (Funciones Hash Criptográficas)
 * ============================================================ */
void fips202_sha3_256(uint8_t out[32], const uint8_t *in, size_t inlen);
void fips202_sha3_512(uint8_t out[64], const uint8_t *in, size_t inlen);

/* ============================================================
 * Generador de Entropía del Sistema Operativo (CSPRNG)
 * ============================================================ */
int pqc_randombytes(uint8_t *out, size_t outlen);

#ifdef __cplusplus
}
#endif

#endif /* PQC_FIPS202_H */

