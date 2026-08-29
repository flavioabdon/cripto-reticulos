#include "pqc_core.h"
#include "pqclean/crypto_kem/ml-kem-768/clean/api.h"
#include "pqclean/crypto_sign/ml-dsa-65/clean/api.h"

int ml_kem_768_keypair(uint8_t *pk, uint8_t *sk) {
    return PQCLEAN_MLKEM768_CLEAN_crypto_kem_keypair(pk, sk);
}

int ml_kem_768_encaps(uint8_t *ct, uint8_t *ss, const uint8_t *pk) {
    return PQCLEAN_MLKEM768_CLEAN_crypto_kem_enc(ct, ss, pk);
}

int ml_kem_768_decaps(uint8_t *ss, const uint8_t *ct, const uint8_t *sk) {
    return PQCLEAN_MLKEM768_CLEAN_crypto_kem_dec(ss, ct, sk);
}

int ml_dsa_65_keypair(uint8_t *pk, uint8_t *sk) {
    return PQCLEAN_MLDSA65_CLEAN_crypto_sign_keypair(pk, sk);
}

int ml_dsa_65_sign(uint8_t *sig, size_t *siglen,
                   const uint8_t *m, size_t mlen,
                   const uint8_t *sk) {
    return PQCLEAN_MLDSA65_CLEAN_crypto_sign_signature(sig, siglen, m, mlen, sk);
}

int ml_dsa_65_verify(const uint8_t *sig, size_t siglen,
                     const uint8_t *m, size_t mlen,
                     const uint8_t *pk) {
    return PQCLEAN_MLDSA65_CLEAN_crypto_sign_verify(sig, siglen, m, mlen, pk);
}
