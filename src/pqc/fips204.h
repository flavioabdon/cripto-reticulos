/**
 * @file fips204.h
 * @brief Implementación propia del estándar NIST FIPS 204 (ML-DSA-65).
 *
 * Proyecto de Grado - Universidad Mayor de San Andrés (UMSA)
 * Criptografía Post-Cuántica Basada en Retículos (Module-LWE / Module-SIS).
 *
 * Parámetros de ML-DSA-65 (Categoría de Seguridad 3 de NIST, Tabla 1 de FIPS 204):
 *   - n = 256, q = 8380417 (2^23 - 2^13 + 1)
 *   - d = 13, tau = 49, lambda = 192 (c_tilde = 48 bytes)
 *   - gamma_1 = 2^19 = 524288, gamma_2 = (q - 1) / 32 = 261888
 *   - (k, l) = (6, 5), eta = 4, beta = tau * eta = 196, omega = 55
 */

#ifndef PQC_FIPS204_H
#define PQC_FIPS204_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Parámetros matemáticos de ML-DSA-65 (Tabla 1 de FIPS 204) */
#define FIPS204_N       256
#define FIPS204_Q       8380417
#define FIPS204_D       13
#define FIPS204_TAU     49
#define FIPS204_CTILDE  48
#define FIPS204_GAMMA1  (1 << 19)
#define FIPS204_GAMMA2  ((FIPS204_Q - 1) / 32)
#define FIPS204_K       6
#define FIPS204_L       5
#define FIPS204_ETA     4
#define FIPS204_BETA    196
#define FIPS204_OMEGA   55

/* Tamaños en bytes de claves y firmas (Tabla 2 de FIPS 204) */
#define FIPS204_MLDSA65_PK_BYTES  1952
#define FIPS204_MLDSA65_SK_BYTES  4032
#define FIPS204_MLDSA65_SIG_BYTES 3309

/* ============================================================
 * Algoritmos Internos Deterministas (Sección 6 de FIPS 204)
 * ============================================================ */

/**
 * Algoritmo 6 de FIPS 204: ML-DSA.KeyGen_internal(xi)
 * Genera (pk, sk) de manera determinista a partir de la semilla xi (32 B).
 */
int fips204_mldsa65_keygen_internal(uint8_t pk[FIPS204_MLDSA65_PK_BYTES],
                                    uint8_t sk[FIPS204_MLDSA65_SK_BYTES],
                                    const uint8_t xi[32]);

/**
 * Algoritmo 7 de FIPS 204: ML-DSA.Sign_internal(sk, M', rnd)
 * Firma el mensaje con separación de dominio sobre M = (0x00 || ctxlen || ctx || msg).
 */
int fips204_mldsa65_sign_ctx(uint8_t sig[FIPS204_MLDSA65_SIG_BYTES],
                             size_t *siglen,
                             const uint8_t *m, size_t mlen,
                             const uint8_t *ctx, size_t ctxlen,
                             const uint8_t sk[FIPS204_MLDSA65_SK_BYTES],
                             const uint8_t rnd[32]);

/**
 * Algoritmo 8 de FIPS 204: ML-DSA.Verify_internal(pk, M', sig)
 * Verifica la firma sig sobre el mensaje m con contexto ctx.
 */
int fips204_mldsa65_verify_ctx(const uint8_t *sig, size_t siglen,
                               const uint8_t *m, size_t mlen,
                               const uint8_t *ctx, size_t ctxlen,
                               const uint8_t pk[FIPS204_MLDSA65_PK_BYTES]);

/* ============================================================
 * API Pública de Alto Nivel (Sección 5 de FIPS 204)
 * ============================================================ */

/**
 * Algoritmo 1 de FIPS 204: ML-DSA.KeyGen()
 */
int fips204_mldsa65_keypair(uint8_t pk[FIPS204_MLDSA65_PK_BYTES],
                            uint8_t sk[FIPS204_MLDSA65_SK_BYTES]);

/**
 * Algoritmo 2 de FIPS 204: ML-DSA.Sign(sk, M, ctx="")
 */
int fips204_mldsa65_sign(uint8_t sig[FIPS204_MLDSA65_SIG_BYTES],
                         size_t *siglen,
                         const uint8_t *m, size_t mlen,
                         const uint8_t sk[FIPS204_MLDSA65_SK_BYTES]);

/**
 * Algoritmo 3 de FIPS 204: ML-DSA.Verify(pk, M, sig, ctx="")
 */
int fips204_mldsa65_verify(const uint8_t *sig, size_t siglen,
                           const uint8_t *m, size_t mlen,
                           const uint8_t pk[FIPS204_MLDSA65_PK_BYTES]);

#ifdef __cplusplus
}
#endif

#endif /* PQC_FIPS204_H */

