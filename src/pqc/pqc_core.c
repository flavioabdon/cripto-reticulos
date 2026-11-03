/**
 * @file pqc_core.c
 * @brief Capa de enlace de nuestras implementaciones propias de FIPS 202, FIPS 203 y FIPS 204.
 *
 * No utiliza ninguna librería externa de NIST ni PQClean.
 */

#include "pqc_core.h"

void pqc_sha3_256(uint8_t out[32], const uint8_t *in, size_t inlen) {
    fips202_sha3_256(out, in, inlen);
}

void pqc_sha3_512(uint8_t out[64], const uint8_t *in, size_t inlen) {
    fips202_sha3_512(out, in, inlen);
}

void pqc_shake128(uint8_t *out, size_t outlen, const uint8_t *in, size_t inlen) {
    fips202_shake128(out, outlen, in, inlen);
}

void pqc_shake256(uint8_t *out, size_t outlen, const uint8_t *in, size_t inlen) {
    fips202_shake256(out, outlen, in, inlen);
}

int ml_kem_768_keypair(uint8_t *pk, uint8_t *sk) {
    return fips203_mlkem768_keypair(pk, sk);
}

int ml_kem_768_encaps(uint8_t *ct, uint8_t *ss, const uint8_t *pk) {
    return fips203_mlkem768_encaps(ct, ss, pk);
}

int ml_kem_768_decaps(uint8_t *ss, const uint8_t *ct, const uint8_t *sk) {
    return fips203_mlkem768_decaps(ss, ct, sk);
}

int ml_dsa_65_keypair(uint8_t *pk, uint8_t *sk) {
    return fips204_mldsa65_keypair(pk, sk);
}

int ml_dsa_65_sign(uint8_t *sig, size_t *siglen,
                   const uint8_t *m, size_t mlen,
                   const uint8_t *sk) {
    return fips204_mldsa65_sign(sig, siglen, m, mlen, sk);
}

int ml_dsa_65_verify(const uint8_t *sig, size_t siglen,
                     const uint8_t *m, size_t mlen,
                     const uint8_t *pk) {
    return fips204_mldsa65_verify(sig, siglen, m, mlen, pk);
}
