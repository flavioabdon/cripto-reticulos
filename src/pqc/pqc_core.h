/**
 * @file pqc_core.h
 * @brief Interfaz C unificada de nuestras implementaciones propias de:
 *   - FIPS 202 (SHA3-256, SHA3-512, SHAKE128, SHAKE256)
 *   - FIPS 203 (ML-KEM-768)
 *   - FIPS 204 (ML-DSA-65)
 */

#ifndef PQC_CORE_H
#define PQC_CORE_H

#include <stddef.h>
#include <stdint.h>
#include "fips202.h"
#include "fips203.h"
#include "fips204.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================
 * Constantes de tamaño para ML-KEM-768 (FIPS 203)
 * ============================================================ */
#define MLKEM768_PUBLICKEYBYTES  FIPS203_MLKEM768_EK_BYTES
#define MLKEM768_SECRETKEYBYTES  FIPS203_MLKEM768_DK_BYTES
#define MLKEM768_CIPHERTEXTBYTES FIPS203_MLKEM768_CT_BYTES
#define MLKEM768_SHAREDKEYBYTES  FIPS203_MLKEM768_SS_BYTES

/* ============================================================
 * Constantes de tamaño para ML-DSA-65 (FIPS 204)
 * ============================================================ */
#define MLDSA65_PUBLICKEYBYTES FIPS204_MLDSA65_PK_BYTES
#define MLDSA65_SECRETKEYBYTES FIPS204_MLDSA65_SK_BYTES
#define MLDSA65_SIGNATUREBYTES FIPS204_MLDSA65_SIG_BYTES

/* ============================================================
 * API para FIPS 202 (Keccak / SHA-3 / SHAKE)
 * ============================================================ */
void pqc_sha3_256(uint8_t out[32], const uint8_t *in, size_t inlen);
void pqc_sha3_512(uint8_t out[64], const uint8_t *in, size_t inlen);
void pqc_shake128(uint8_t *out, size_t outlen, const uint8_t *in, size_t inlen);
void pqc_shake256(uint8_t *out, size_t outlen, const uint8_t *in, size_t inlen);

/* ============================================================
 * API para ML-KEM-768 (FIPS 203 - Key Encapsulation Mechanism)
 * ============================================================ */
int ml_kem_768_keypair(uint8_t *pk, uint8_t *sk);
int ml_kem_768_encaps(uint8_t *ct, uint8_t *ss, const uint8_t *pk);
int ml_kem_768_decaps(uint8_t *ss, const uint8_t *ct, const uint8_t *sk);

/* ============================================================
 * API para ML-DSA-65 (FIPS 204 - Digital Signature Algorithm)
 * ============================================================ */
int ml_dsa_65_keypair(uint8_t *pk, uint8_t *sk);
int ml_dsa_65_sign(uint8_t *sig, size_t *siglen,
                   const uint8_t *m, size_t mlen,
                   const uint8_t *sk);
int ml_dsa_65_verify(const uint8_t *sig, size_t siglen,
                     const uint8_t *m, size_t mlen,
                     const uint8_t *pk);

#ifdef __cplusplus
}
#endif

#endif /* PQC_CORE_H */
