#ifndef PQC_CORE_H
#define PQC_CORE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================
 * Constantes de tamaño para ML-KEM-768 (FIPS 203)
 * ============================================================ */
#define MLKEM768_PUBLICKEYBYTES  1184
#define MLKEM768_SECRETKEYBYTES  2400
#define MLKEM768_CIPHERTEXTBYTES 1088
#define MLKEM768_SHAREDKEYBYTES  32

/* ============================================================
 * Constantes de tamaño para ML-DSA-65 (FIPS 204)
 * ============================================================ */
#define MLDSA65_PUBLICKEYBYTES 1952
#define MLDSA65_SECRETKEYBYTES 4032
#define MLDSA65_SIGNATUREBYTES 3309

/* ============================================================
 * API para ML-KEM-768 (Key Encapsulation Mechanism)
 * ============================================================ */
int ml_kem_768_keypair(uint8_t *pk, uint8_t *sk);
int ml_kem_768_encaps(uint8_t *ct, uint8_t *ss, const uint8_t *pk);
int ml_kem_768_decaps(uint8_t *ss, const uint8_t *ct, const uint8_t *sk);

/* ============================================================
 * API para ML-DSA-65 (Digital Signature Algorithm)
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
