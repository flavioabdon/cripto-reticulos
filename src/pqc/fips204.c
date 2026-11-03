/**
 * @file fips204.c
 * @brief Implementación propia desde cero del estándar NIST FIPS 204 (ML-DSA-65).
 *
 * Proyecto de Grado - Universidad Mayor de San Andrés (UMSA)
 * Implementa fielmente los Algoritmos 1 al 49 de la especificación FIPS 204 sobre el anillo
 * ciclotómico R_q = Z_8380417[X]/(X^256 + 1) utilizando nuestra implementación propia de FIPS 202.
 */

#include "fips204.h"
#include "fips202.h"
#include <string.h>

/* Representación de un polinomio en R_q o T_q */
typedef struct {
    int32_t coeffs[FIPS204_N];
} fips204_poly;

/* Vectores de polinomios en R_q^l (l = 5) y R_q^k (k = 6) */
typedef struct {
    fips204_poly vec[FIPS204_L];
} fips204_polyvecl;

typedef struct {
    fips204_poly vec[FIPS204_K];
} fips204_polyveck;

/* Tabla de potencias de la raíz 512-ésima de la unidad zeta = 1753 mod 8380417 */
static int32_t ZETA_DSA_TABLE[FIPS204_N];
static int DSA_TABLES_INITIALIZED = 0;

/* Reducción modular canónica a [0, q - 1] */
static inline int32_t mod_q_dsa(int64_t x) {
    int64_t r = x % FIPS204_Q;
    return (int32_t)(r < 0 ? r + FIPS204_Q : r);
}

/* Reducción modular centrada mod^+- q en (-(q-1)/2, (q-1)/2] */
static inline int32_t mod_pm_q(int64_t x) {
    int32_t r = mod_q_dsa(x);
    if (r > (FIPS204_Q - 1) / 2) {
        r -= FIPS204_Q;
    }
    return r;
}

/* Exponenciación modular b^e mod 8380417 */
static int32_t mod_pow_dsa(int64_t base, int32_t exp) {
    int64_t result = 1;
    int64_t b = mod_q_dsa(base);
    while (exp > 0) {
        if (exp & 1) {
            result = (result * b) % FIPS204_Q;
        }
        b = (b * b) % FIPS204_Q;
        exp >>= 1;
    }
    return (int32_t)result;
}

/* Algoritmo 43 de FIPS 204: BitRev_8(x) - Inversión de 8 bits */
static int32_t bitrev8(int32_t x) {
    int32_t r = 0;
    for (int i = 0; i < 8; i++) {
        r = (r << 1) | (x & 1);
        x >>= 1;
    }
    return r;
}

static void ensure_dsa_tables(void) {
    if (DSA_TABLES_INITIALIZED) {
        return;
    }
    for (int m = 0; m < FIPS204_N; m++) {
        ZETA_DSA_TABLE[m] = mod_pow_dsa(1753, bitrev8(m));
    }
    DSA_TABLES_INITIALIZED = 1;
}

/* ============================================================
 * Transformada Teórica de Números (NTT / INTT) — Sección 7.5 de FIPS 204
 * ============================================================ */

/* Algoritmo 41 de FIPS 204: NTT(w) */
static void poly_ntt_dsa(fips204_poly *w) {
    ensure_dsa_tables();
    int m = 0;
    for (int len = 128; len >= 1; len >>= 1) {
        for (int start = 0; start < 256; start += 2 * len) {
            int64_t z = ZETA_DSA_TABLE[++m];
            for (int j = start; j < start + len; j++) {
                int32_t t = mod_q_dsa(z * w->coeffs[j + len]);
                w->coeffs[j + len] = mod_q_dsa((int64_t)w->coeffs[j] - t);
                w->coeffs[j]       = mod_q_dsa((int64_t)w->coeffs[j] + t);
            }
        }
    }
}

/* Algoritmo 42 de FIPS 204: NTT^-1(w_hat) */
static void poly_invntt_dsa(fips204_poly *w) {
    ensure_dsa_tables();
    int m = 256;
    for (int len = 1; len <= 128; len <<= 1) {
        for (int start = 0; start < 256; start += 2 * len) {
            int64_t z = FIPS204_Q - ZETA_DSA_TABLE[--m];
            for (int j = start; j < start + len; j++) {
                int32_t t = w->coeffs[j];
                w->coeffs[j]       = mod_q_dsa((int64_t)t + w->coeffs[j + len]);
                w->coeffs[j + len] = mod_q_dsa(z * ((int64_t)t - w->coeffs[j + len]));
            }
        }
    }
    /* Multiplicación por 256^-1 mod 8380417 = 8347681 */
    const int64_t inv_256 = 8347681;
    for (int j = 0; j < 256; j++) {
        w->coeffs[j] = mod_q_dsa(inv_256 * w->coeffs[j]);
    }
}

/* Algoritmo 45 de FIPS 204: MultiplyNTT(a_hat, b_hat) */
static void poly_pointwise_dsa(fips204_poly *c, const fips204_poly *a, const fips204_poly *b) {
    for (int i = 0; i < FIPS204_N; i++) {
        c->coeffs[i] = mod_q_dsa((int64_t)a->coeffs[i] * b->coeffs[i]);
    }
}

static void poly_add_dsa(fips204_poly *c, const fips204_poly *a, const fips204_poly *b) {
    for (int i = 0; i < FIPS204_N; i++) {
        c->coeffs[i] = mod_q_dsa((int64_t)a->coeffs[i] + b->coeffs[i]);
    }
}

static void poly_sub_dsa(fips204_poly *c, const fips204_poly *a, const fips204_poly *b) {
    for (int i = 0; i < FIPS204_N; i++) {
        c->coeffs[i] = mod_q_dsa((int64_t)a->coeffs[i] - b->coeffs[i]);
    }
}

/* ============================================================
 * Redondeo y Pistas (Hints) de Orden Superior/Inferior (Sección 7.4 de FIPS 204)
 * ============================================================ */

/* Algoritmo 35 de FIPS 204: Power2Round(r) con d = 13 */
static void power2round(int32_t r, int32_t *r1, int32_t *r0) {
    int32_t r_plus = mod_q_dsa(r);
    int32_t rem = r_plus & ((1 << FIPS204_D) - 1);
    if (rem > (1 << (FIPS204_D - 1))) {
        rem -= (1 << FIPS204_D);
    }
    *r0 = rem;
    *r1 = (r_plus - rem) >> FIPS204_D;
}

/* Algoritmo 36 de FIPS 204: Decompose(r) con gamma_2 = (q-1)/32 */
static void decompose(int32_t r, int32_t *r1, int32_t *r0) {
    int32_t r_plus = mod_q_dsa(r);
    const int32_t two_gamma2 = 2 * FIPS204_GAMMA2;
    int32_t rem = r_plus % two_gamma2;
    if (rem > FIPS204_GAMMA2) {
        rem -= two_gamma2;
    }
    if (r_plus - rem == FIPS204_Q - 1) {
        *r1 = 0;
        *r0 = rem - 1;
    } else {
        *r1 = (r_plus - rem) / two_gamma2;
        *r0 = rem;
    }
}

/* Algoritmo 37 de FIPS 204: HighBits(r) */
static int32_t high_bits(int32_t r) {
    int32_t r1, r0;
    decompose(r, &r1, &r0);
    return r1;
}

/* Algoritmo 38 de FIPS 204: LowBits(r) */
static int32_t low_bits(int32_t r) {
    int32_t r1, r0;
    decompose(r, &r1, &r0);
    return r0;
}

/* Algoritmo 39 de FIPS 204: MakeHint(z, r) */
static int32_t make_hint(int32_t z, int32_t r) {
    int32_t r1 = high_bits(r);
    int32_t v1 = high_bits(mod_q_dsa((int64_t)r + z));
    return (r1 != v1) ? 1 : 0;
}

/* Algoritmo 40 de FIPS 204: UseHint(h, r) */
static int32_t use_hint(int32_t h, int32_t r) {
    const int32_t m = (FIPS204_Q - 1) / (2 * FIPS204_GAMMA2); /* m = 16 */
    int32_t r1, r0;
    decompose(r, &r1, &r0);
    if (h == 1) {
        if (r0 > 0) {
            return (r1 + 1) % m;
        } else {
            return (r1 + m - 1) % m;
        }
    }
    return r1;
}

/* Verificación de norma infinito ||w||_inf < bound */
static int poly_check_norm(const fips204_poly *w, int32_t bound) {
    for (int i = 0; i < FIPS204_N; i++) {
        int32_t c = mod_pm_q(w->coeffs[i]);
        if (c < 0) {
            c = -c;
        }
        if (c >= bound) {
            return 1; /* Excede la cota */
        }
    }
    return 0;
}

/* ============================================================
 * Empaquetado y Desempaquetado de Bits (Sección 7.1 y 7.2 de FIPS 204)
 * ============================================================ */

/* Algoritmo 16 de FIPS 204: SimpleBitPack(w, b) con bitlen(b) = bits */
static void simple_bit_pack(uint8_t *out, const fips204_poly *w, int bits) {
    memset(out, 0, (size_t)(32 * bits));
    for (int i = 0; i < FIPS204_N; i++) {
        uint32_t val = (uint32_t)w->coeffs[i];
        for (int j = 0; j < bits; j++) {
            size_t bit_idx = (size_t)(i * bits + j);
            out[bit_idx >> 3] |= (uint8_t)(((val >> j) & 1U) << (bit_idx & 7U));
        }
    }
}

/* Algoritmo 18 de FIPS 204: SimpleBitUnpack(v, b) con bitlen(b) = bits */
static void simple_bit_unpack(fips204_poly *w, const uint8_t *in, int bits) {
    for (int i = 0; i < FIPS204_N; i++) {
        uint32_t val = 0;
        for (int j = 0; j < bits; j++) {
            size_t bit_idx = (size_t)(i * bits + j);
            uint32_t bit = (in[bit_idx >> 3] >> (bit_idx & 7U)) & 1U;
            val |= (bit << j);
        }
        w->coeffs[i] = (int32_t)val;
    }
}

/* Algoritmo 17 de FIPS 204: BitPack(w, a, b) codificando (b - w_i) en `bits` bits */
static void bit_pack(uint8_t *out, const fips204_poly *w, int32_t b_bound, int bits) {
    memset(out, 0, (size_t)(32 * bits));
    for (int i = 0; i < FIPS204_N; i++) {
        int32_t coeff = mod_pm_q(w->coeffs[i]);
        uint32_t val = (uint32_t)(b_bound - coeff);
        for (int j = 0; j < bits; j++) {
            size_t bit_idx = (size_t)(i * bits + j);
            out[bit_idx >> 3] |= (uint8_t)(((val >> j) & 1U) << (bit_idx & 7U));
        }
    }
}

/* Algoritmo 19 de FIPS 204: BitUnpack(v, a, b) decodificando w_i = b - u_i */
static void bit_unpack(fips204_poly *w, const uint8_t *in, int32_t b_bound, int bits) {
    for (int i = 0; i < FIPS204_N; i++) {
        uint32_t val = 0;
        for (int j = 0; j < bits; j++) {
            size_t bit_idx = (size_t)(i * bits + j);
            uint32_t bit = (in[bit_idx >> 3] >> (bit_idx & 7U)) & 1U;
            val |= (bit << j);
        }
        w->coeffs[i] = b_bound - (int32_t)val;
    }
}

/* Algoritmo 20 de FIPS 204: HintBitPack(h) */
static void hint_bit_pack(uint8_t y[FIPS204_OMEGA + FIPS204_K], const fips204_polyveck *h) {
    memset(y, 0, FIPS204_OMEGA + FIPS204_K);
    int index = 0;
    for (int i = 0; i < FIPS204_K; i++) {
        for (int j = 0; j < FIPS204_N; j++) {
            if (h->vec[i].coeffs[j] != 0) {
                y[index++] = (uint8_t)j;
            }
        }
        y[FIPS204_OMEGA + i] = (uint8_t)index;
    }
}

/* Algoritmo 21 de FIPS 204: HintBitUnpack(y) */
static int hint_bit_unpack(fips204_polyveck *h, const uint8_t y[FIPS204_OMEGA + FIPS204_K]) {
    memset(h, 0, sizeof(fips204_polyveck));
    int index = 0;
    for (int i = 0; i < FIPS204_K; i++) {
        if (y[FIPS204_OMEGA + i] < index || y[FIPS204_OMEGA + i] > FIPS204_OMEGA) {
            return -1;
        }
        int first = index;
        while (index < y[FIPS204_OMEGA + i]) {
            if (index > first && y[index - 1] >= y[index]) {
                return -1;
            }
            h->vec[i].coeffs[y[index]] = 1;
            index++;
        }
    }
    for (int i = index; i < FIPS204_OMEGA; i++) {
        if (y[i] != 0) {
            return -1;
        }
    }
    return 0;
}

/* Algoritmo 22 de FIPS 204: pkEncode(rho, t1) */
static void pk_encode(uint8_t pk[FIPS204_MLDSA65_PK_BYTES],
                      const uint8_t rho[32],
                      const fips204_polyveck *t1) {
    memcpy(pk, rho, 32);
    for (int i = 0; i < FIPS204_K; i++) {
        simple_bit_pack(pk + 32 + 320 * i, &t1->vec[i], 10);
    }
}

/* Algoritmo 23 de FIPS 204: pkDecode(pk) */
static void pk_decode(uint8_t rho[32],
                      fips204_polyveck *t1,
                      const uint8_t pk[FIPS204_MLDSA65_PK_BYTES]) {
    memcpy(rho, pk, 32);
    for (int i = 0; i < FIPS204_K; i++) {
        simple_bit_unpack(&t1->vec[i], pk + 32 + 320 * i, 10);
    }
}

/* Algoritmo 24 de FIPS 204: skEncode(rho, K, tr, s1, s2, t0) */
static void sk_encode(uint8_t sk[FIPS204_MLDSA65_SK_BYTES],
                      const uint8_t rho[32],
                      const uint8_t key[32],
                      const uint8_t tr[64],
                      const fips204_polyvecl *s1,
                      const fips204_polyveck *s2,
                      const fips204_polyveck *t0) {
    size_t offset = 0;
    memcpy(sk + offset, rho, 32); offset += 32;
    memcpy(sk + offset, key, 32); offset += 32;
    memcpy(sk + offset, tr, 64);  offset += 64;

    for (int i = 0; i < FIPS204_L; i++) {
        bit_pack(sk + offset, &s1->vec[i], FIPS204_ETA, 4);
        offset += 128;
    }
    for (int i = 0; i < FIPS204_K; i++) {
        bit_pack(sk + offset, &s2->vec[i], FIPS204_ETA, 4);
        offset += 128;
    }
    for (int i = 0; i < FIPS204_K; i++) {
        bit_pack(sk + offset, &t0->vec[i], 1 << (FIPS204_D - 1), 13);
        offset += 416;
    }
}

/* Algoritmo 25 de FIPS 204: skDecode(sk) */
static void sk_decode(uint8_t rho[32],
                      uint8_t key[32],
                      uint8_t tr[64],
                      fips204_polyvecl *s1,
                      fips204_polyveck *s2,
                      fips204_polyveck *t0,
                      const uint8_t sk[FIPS204_MLDSA65_SK_BYTES]) {
    size_t offset = 0;
    memcpy(rho, sk + offset, 32); offset += 32;
    memcpy(key, sk + offset, 32); offset += 32;
    memcpy(tr,  sk + offset, 64); offset += 64;

    for (int i = 0; i < FIPS204_L; i++) {
        bit_unpack(&s1->vec[i], sk + offset, FIPS204_ETA, 4);
        offset += 128;
    }
    for (int i = 0; i < FIPS204_K; i++) {
        bit_unpack(&s2->vec[i], sk + offset, FIPS204_ETA, 4);
        offset += 128;
    }
    for (int i = 0; i < FIPS204_K; i++) {
        bit_unpack(&t0->vec[i], sk + offset, 1 << (FIPS204_D - 1), 13);
        offset += 416;
    }
}

/* Algoritmo 26 de FIPS 204: sigEncode(c_tilde, z, h) */
static void sig_encode(uint8_t sig[FIPS204_MLDSA65_SIG_BYTES],
                       const uint8_t c_tilde[FIPS204_CTILDE],
                       const fips204_polyvecl *z,
                       const fips204_polyveck *h) {
    memcpy(sig, c_tilde, FIPS204_CTILDE);
    size_t offset = FIPS204_CTILDE;
    for (int i = 0; i < FIPS204_L; i++) {
        bit_pack(sig + offset, &z->vec[i], FIPS204_GAMMA1, 20);
        offset += 640;
    }
    hint_bit_pack(sig + offset, h);
}

/* Algoritmo 27 de FIPS 204: sigDecode(sig) */
static int sig_decode(uint8_t c_tilde[FIPS204_CTILDE],
                      fips204_polyvecl *z,
                      fips204_polyveck *h,
                      const uint8_t sig[FIPS204_MLDSA65_SIG_BYTES]) {
    memcpy(c_tilde, sig, FIPS204_CTILDE);
    size_t offset = FIPS204_CTILDE;
    for (int i = 0; i < FIPS204_L; i++) {
        bit_unpack(&z->vec[i], sig + offset, FIPS204_GAMMA1, 20);
        offset += 640;
    }
    return hint_bit_unpack(h, sig + offset);
}

/* Algoritmo 28 de FIPS 204: w1Encode(w1) (4 bits por coeficiente para ML-DSA-65) */
static void w1_encode(uint8_t out[128 * FIPS204_K], const fips204_polyveck *w1) {
    for (int i = 0; i < FIPS204_K; i++) {
        simple_bit_pack(out + 128 * i, &w1->vec[i], 4);
    }
}

/* ============================================================
 * Funciones de Muestreo Pseudoaleatorio (Sección 7.3 de FIPS 204)
 * ============================================================ */

/* Algoritmo 29 de FIPS 204: SampleInBall(c_tilde) con tau = 49 */
static void sample_in_ball(fips204_poly *c, const uint8_t c_tilde[FIPS204_CTILDE]) {
    memset(c, 0, sizeof(fips204_poly));
    fips202_shake256_ctx ctx;
    fips202_shake256_init(&ctx);
    fips202_shake256_absorb(&ctx, c_tilde, FIPS204_CTILDE);
    fips202_shake256_finalize(&ctx);

    uint8_t sign_bytes[8];
    fips202_shake256_squeeze(sign_bytes, 8, &ctx);
    uint64_t signs = 0;
    for (int i = 0; i < 8; i++) {
        signs |= ((uint64_t)sign_bytes[i]) << (8 * i);
    }

    for (int i = FIPS204_N - FIPS204_TAU; i < FIPS204_N; i++) {
        uint8_t j_byte;
        do {
            fips202_shake256_squeeze(&j_byte, 1, &ctx);
        } while ((int)j_byte > i);

        c->coeffs[i] = c->coeffs[j_byte];
        c->coeffs[j_byte] = (signs & 1ULL) ? (FIPS204_Q - 1) : 1;
        signs >>= 1;
    }
}

/* Algoritmo 30 y 32 de FIPS 204: RejNTTPoly y ExpandA(rho) */
static void expand_a(fips204_polyvecl A_hat[FIPS204_K], const uint8_t rho[32]) {
    for (int r = 0; r < FIPS204_K; r++) {
        for (int s = 0; s < FIPS204_L; s++) {
            uint8_t inbuf[34];
            memcpy(inbuf, rho, 32);
            inbuf[32] = (uint8_t)s;
            inbuf[33] = (uint8_t)r;

            fips202_shake128_ctx ctx;
            fips202_shake128_init(&ctx);
            fips202_shake128_absorb(&ctx, inbuf, 34);
            fips202_shake128_finalize(&ctx);

            int count = 0;
            uint8_t b[3];
            while (count < FIPS204_N) {
                fips202_shake128_squeeze(b, 3, &ctx);
                int32_t z = (int32_t)b[0] |
                            ((int32_t)b[1] << 8) |
                            (((int32_t)b[2] & 0x7F) << 16);
                if (z < FIPS204_Q) {
                    A_hat[r].vec[s].coeffs[count++] = z;
                }
            }
        }
    }
}

/* Algoritmo 31 de FIPS 204: RejBoundedPoly(rho', nonce) para eta = 4 */
static void rej_bounded_poly_eta4(fips204_poly *a, const uint8_t rhoprime[64], uint16_t nonce) {
    uint8_t inbuf[66];
    memcpy(inbuf, rhoprime, 64);
    inbuf[64] = (uint8_t)(nonce & 0xFFU);
    inbuf[65] = (uint8_t)((nonce >> 8) & 0xFFU);

    fips202_shake256_ctx ctx;
    fips202_shake256_init(&ctx);
    fips202_shake256_absorb(&ctx, inbuf, 66);
    fips202_shake256_finalize(&ctx);

    int count = 0;
    uint8_t z;
    while (count < FIPS204_N) {
        fips202_shake256_squeeze(&z, 1, &ctx);
        uint8_t z0 = z & 0x0FU;
        uint8_t z1 = z >> 4;
        if (z0 < 9U) {
            a->coeffs[count++] = (int32_t)FIPS204_ETA - (int32_t)z0;
        }
        if (z1 < 9U && count < FIPS204_N) {
            a->coeffs[count++] = (int32_t)FIPS204_ETA - (int32_t)z1;
        }
    }
}

/* Algoritmo 33 de FIPS 204: ExpandS(rho') */
static void expand_s(fips204_polyvecl *s1, fips204_polyveck *s2, const uint8_t rhoprime[64]) {
    for (int r = 0; r < FIPS204_L; r++) {
        rej_bounded_poly_eta4(&s1->vec[r], rhoprime, (uint16_t)r);
    }
    for (int r = 0; r < FIPS204_K; r++) {
        rej_bounded_poly_eta4(&s2->vec[r], rhoprime, (uint16_t)(FIPS204_L + r));
    }
}

/* Algoritmo 34 de FIPS 204: ExpandMask(rho'', kappa) para gamma_1 = 2^19 */
static void expand_mask(fips204_polyvecl *y, const uint8_t rhoprime[64], uint16_t kappa) {
    uint8_t inbuf[66];
    uint8_t buf[640];
    memcpy(inbuf, rhoprime, 64);

    for (int r = 0; r < FIPS204_L; r++) {
        uint16_t n = (uint16_t)(kappa + r);
        inbuf[64] = (uint8_t)(n & 0xFFU);
        inbuf[65] = (uint8_t)((n >> 8) & 0xFFU);
        fips202_shake256(buf, sizeof(buf), inbuf, sizeof(inbuf));
        bit_unpack(&y->vec[r], buf, FIPS204_GAMMA1, 20);
        for (int j = 0; j < FIPS204_N; j++) {
            y->vec[r].coeffs[j] = mod_q_dsa(y->vec[r].coeffs[j]);
        }
    }
}

/* Multiplicación matriz-vector en dominio NTT: w_hat = A_hat * u_hat */
static void matrix_vec_mul_ntt(fips204_polyveck *w,
                               const fips204_polyvecl A_hat[FIPS204_K],
                               const fips204_polyvecl *u_hat) {
    fips204_poly tmp;
    for (int i = 0; i < FIPS204_K; i++) {
        poly_pointwise_dsa(&w->vec[i], &A_hat[i].vec[0], &u_hat->vec[0]);
        for (int j = 1; j < FIPS204_L; j++) {
            poly_pointwise_dsa(&tmp, &A_hat[i].vec[j], &u_hat->vec[j]);
            poly_add_dsa(&w->vec[i], &w->vec[i], &tmp);
        }
    }
}

/* ============================================================
 * Algoritmos Principales de ML-DSA-65 (Sección 5 y 6 de FIPS 204)
 * ============================================================ */

int fips204_mldsa65_keygen_internal(uint8_t pk[FIPS204_MLDSA65_PK_BYTES],
                                    uint8_t sk[FIPS204_MLDSA65_SK_BYTES],
                                    const uint8_t xi[32]) {
    /* 1. Expandir semilla xi || k || l en (rho, rhoprime, K) de 128 bytes */
    uint8_t seed_in[34];
    uint8_t seed_out[128];
    memcpy(seed_in, xi, 32);
    seed_in[32] = FIPS204_K;
    seed_in[33] = FIPS204_L;
    fips202_shake256(seed_out, sizeof(seed_out), seed_in, sizeof(seed_in));

    const uint8_t *rho      = seed_out;
    const uint8_t *rhoprime = seed_out + 32;
    const uint8_t *key      = seed_out + 96;

    /* 2. Expandir matriz A_hat y vectores secretos s1, s2 */
    fips204_polyvecl A_hat[FIPS204_K], s1, s1_hat;
    fips204_polyveck s2, t, t1, t0;

    expand_a(A_hat, rho);
    expand_s(&s1, &s2, rhoprime);

    /* 3. t = NTT^-1(A_hat * NTT(s1)) + s2 */
    s1_hat = s1;
    for (int i = 0; i < FIPS204_L; i++) {
        for (int j = 0; j < FIPS204_N; j++) {
            s1_hat.vec[i].coeffs[j] = mod_q_dsa(s1_hat.vec[i].coeffs[j]);
        }
        poly_ntt_dsa(&s1_hat.vec[i]);
    }

    matrix_vec_mul_ntt(&t, A_hat, &s1_hat);
    for (int i = 0; i < FIPS204_K; i++) {
        poly_invntt_dsa(&t.vec[i]);
        poly_add_dsa(&t.vec[i], &t.vec[i], &s2.vec[i]);
    }

    /* 4. (t1, t0) = Power2Round(t) */
    for (int i = 0; i < FIPS204_K; i++) {
        for (int j = 0; j < FIPS204_N; j++) {
            power2round(t.vec[i].coeffs[j], &t1.vec[i].coeffs[j], &t0.vec[i].coeffs[j]);
        }
    }

    /* 5. Codificar pk y sk */
    pk_encode(pk, rho, &t1);
    uint8_t tr[64];
    fips202_shake256(tr, sizeof(tr), pk, FIPS204_MLDSA65_PK_BYTES);
    sk_encode(sk, rho, key, tr, &s1, &s2, &t0);

    return 0;
}

int fips204_mldsa65_sign_ctx(uint8_t sig[FIPS204_MLDSA65_SIG_BYTES],
                             size_t *siglen,
                             const uint8_t *m, size_t mlen,
                             const uint8_t *ctx, size_t ctxlen,
                             const uint8_t sk[FIPS204_MLDSA65_SK_BYTES],
                             const uint8_t rnd[32]) {
    if (ctxlen > 255) {
        return -1;
    }

    uint8_t rho[32], key[32], tr[64];
    fips204_polyvecl s1_hat, A_hat[FIPS204_K];
    fips204_polyveck s2_hat, t0_hat;

    sk_decode(rho, key, tr, &s1_hat, &s2_hat, &t0_hat, sk);

    /* 1. Calcular representante del mensaje mu = SHAKE256(tr || 0x00 || ctxlen || ctx || m, 64) */
    uint8_t dom[2] = { 0x00, (uint8_t)ctxlen };
    uint8_t mu[64];
    fips202_shake256_ctx hctx;
    fips202_shake256_init(&hctx);
    fips202_shake256_absorb(&hctx, tr, 64);
    fips202_shake256_absorb(&hctx, dom, 2);
    if (ctxlen > 0 && ctx != NULL) {
        fips202_shake256_absorb(&hctx, ctx, ctxlen);
    }
    if (mlen > 0 && m != NULL) {
        fips202_shake256_absorb(&hctx, m, mlen);
    }
    fips202_shake256_finalize(&hctx);
    fips202_shake256_squeeze(mu, 64, &hctx);

    /* 2. Calcular semilla de enmascaramiento rhoprime = SHAKE256(K || rnd || mu, 64) */
    uint8_t rho_in[128];
    uint8_t rhoprime[64];
    memcpy(rho_in, key, 32);
    memcpy(rho_in + 32, rnd, 32);
    memcpy(rho_in + 64, mu, 64);
    fips202_shake256(rhoprime, 64, rho_in, 128);

    /* 3. Expandir matriz A_hat y transformar s1, s2, t0 al dominio NTT */
    expand_a(A_hat, rho);
    for (int i = 0; i < FIPS204_L; i++) {
        for (int j = 0; j < FIPS204_N; j++) {
            s1_hat.vec[i].coeffs[j] = mod_q_dsa(s1_hat.vec[i].coeffs[j]);
        }
        poly_ntt_dsa(&s1_hat.vec[i]);
    }
    for (int i = 0; i < FIPS204_K; i++) {
        for (int j = 0; j < FIPS204_N; j++) {
            s2_hat.vec[i].coeffs[j] = mod_q_dsa(s2_hat.vec[i].coeffs[j]);
            t0_hat.vec[i].coeffs[j] = mod_q_dsa(t0_hat.vec[i].coeffs[j]);
        }
        poly_ntt_dsa(&s2_hat.vec[i]);
        poly_ntt_dsa(&t0_hat.vec[i]);
    }

    uint16_t kappa = 0;
    fips204_polyvecl y, y_hat, z;
    fips204_polyveck w, w1, cs2, ct0, h;
    fips204_poly c_hat;
    uint8_t w1_packed[128 * FIPS204_K];
    uint8_t c_tilde[FIPS204_CTILDE];

    /* 4. Bucle de muestreo con rechazo (Rejection Sampling Fiat-Shamir with Aborts) */
    while (1) {
        expand_mask(&y, rhoprime, kappa);
        kappa = (uint16_t)(kappa + FIPS204_L);

        /* w = NTT^-1(A_hat * NTT(y)) */
        y_hat = y;
        for (int i = 0; i < FIPS204_L; i++) {
            poly_ntt_dsa(&y_hat.vec[i]);
        }
        matrix_vec_mul_ntt(&w, A_hat, &y_hat);
        for (int i = 0; i < FIPS204_K; i++) {
            poly_invntt_dsa(&w.vec[i]);
            for (int j = 0; j < FIPS204_N; j++) {
                w1.vec[i].coeffs[j] = high_bits(w.vec[i].coeffs[j]);
            }
        }

        /* Hash de compromiso c_tilde = SHAKE256(mu || w1Encode(w1), 48) */
        w1_encode(w1_packed, &w1);
        fips202_shake256_init(&hctx);
        fips202_shake256_absorb(&hctx, mu, 64);
        fips202_shake256_absorb(&hctx, w1_packed, sizeof(w1_packed));
        fips202_shake256_finalize(&hctx);
        fips202_shake256_squeeze(c_tilde, FIPS204_CTILDE, &hctx);

        sample_in_ball(&c_hat, c_tilde);
        poly_ntt_dsa(&c_hat);

        /* z = y + NTT^-1(c_hat * s1_hat) */
        int reject = 0;
        for (int i = 0; i < FIPS204_L; i++) {
            poly_pointwise_dsa(&z.vec[i], &c_hat, &s1_hat.vec[i]);
            poly_invntt_dsa(&z.vec[i]);
            poly_add_dsa(&z.vec[i], &y.vec[i], &z.vec[i]);
            if (poly_check_norm(&z.vec[i], FIPS204_GAMMA1 - FIPS204_BETA)) {
                reject = 1;
                break;
            }
        }
        if (reject) {
            continue;
        }

        /* Verificar ||LowBits(w - c*s2)||_inf < gamma_2 - beta */
        for (int i = 0; i < FIPS204_K; i++) {
            poly_pointwise_dsa(&cs2.vec[i], &c_hat, &s2_hat.vec[i]);
            poly_invntt_dsa(&cs2.vec[i]);
            for (int j = 0; j < FIPS204_N; j++) {
                int32_t r0 = low_bits(mod_q_dsa((int64_t)w.vec[i].coeffs[j] - cs2.vec[i].coeffs[j]));
                int32_t abs_r0 = (r0 < 0) ? -r0 : r0;
                if (abs_r0 >= FIPS204_GAMMA2 - FIPS204_BETA) {
                    reject = 1;
                    break;
                }
            }
            if (reject) {
                break;
            }
        }
        if (reject) {
            continue;
        }

        /* Calcular vector de pistas h = MakeHint(-c*t0, w - c*s2 + c*t0) */
        int total_hints = 0;
        for (int i = 0; i < FIPS204_K; i++) {
            poly_pointwise_dsa(&ct0.vec[i], &c_hat, &t0_hat.vec[i]);
            poly_invntt_dsa(&ct0.vec[i]);
            if (poly_check_norm(&ct0.vec[i], FIPS204_GAMMA2)) {
                reject = 1;
                break;
            }
            for (int j = 0; j < FIPS204_N; j++) {
                int32_t neg_ct0 = mod_q_dsa(-ct0.vec[i].coeffs[j]);
                int32_t w_minus_cs2_plus_ct0 = mod_q_dsa(
                    (int64_t)w.vec[i].coeffs[j] - cs2.vec[i].coeffs[j] + ct0.vec[i].coeffs[j]
                );
                int32_t bit = make_hint(neg_ct0, w_minus_cs2_plus_ct0);
                h.vec[i].coeffs[j] = bit;
                total_hints += bit;
            }
        }
        if (reject || total_hints > FIPS204_OMEGA) {
            continue;
        }

        /* Firma válida encontrada */
        sig_encode(sig, c_tilde, &z, &h);
        if (siglen != NULL) {
            *siglen = FIPS204_MLDSA65_SIG_BYTES;
        }
        return 0;
    }
}

int fips204_mldsa65_verify_ctx(const uint8_t *sig, size_t siglen,
                               const uint8_t *m, size_t mlen,
                               const uint8_t *ctx, size_t ctxlen,
                               const uint8_t pk[FIPS204_MLDSA65_PK_BYTES]) {
    if (ctxlen > 255 || siglen != FIPS204_MLDSA65_SIG_BYTES) {
        return -1;
    }

    uint8_t rho[32], c_tilde[FIPS204_CTILDE];
    fips204_polyveck t1, h, w1;
    fips204_polyvecl z, A_hat[FIPS204_K];

    pk_decode(rho, &t1, pk);
    if (sig_decode(c_tilde, &z, &h, sig) != 0) {
        return -1;
    }

    /* 1. Verificar ||z||_inf < gamma_1 - beta */
    for (int i = 0; i < FIPS204_L; i++) {
        if (poly_check_norm(&z.vec[i], FIPS204_GAMMA1 - FIPS204_BETA)) {
            return -1;
        }
        for (int j = 0; j < FIPS204_N; j++) {
            z.vec[i].coeffs[j] = mod_q_dsa(z.vec[i].coeffs[j]);
        }
    }

    /* 2. Calcular tr = SHAKE256(pk, 64) y mu = SHAKE256(tr || 0x00 || ctxlen || ctx || m, 64) */
    uint8_t tr[64], mu[64];
    fips202_shake256(tr, 64, pk, FIPS204_MLDSA65_PK_BYTES);

    uint8_t dom[2] = { 0x00, (uint8_t)ctxlen };
    fips202_shake256_ctx hctx;
    fips202_shake256_init(&hctx);
    fips202_shake256_absorb(&hctx, tr, 64);
    fips202_shake256_absorb(&hctx, dom, 2);
    if (ctxlen > 0 && ctx != NULL) {
        fips202_shake256_absorb(&hctx, ctx, ctxlen);
    }
    if (mlen > 0 && m != NULL) {
        fips202_shake256_absorb(&hctx, m, mlen);
    }
    fips202_shake256_finalize(&hctx);
    fips202_shake256_squeeze(mu, 64, &hctx);

    /* 3. Reconstruir w'_approx = NTT^-1(A_hat * NTT(z) - NTT(c) * NTT(t1 * 2^d)) */
    fips204_poly c_hat;
    sample_in_ball(&c_hat, c_tilde);
    poly_ntt_dsa(&c_hat);

    expand_a(A_hat, rho);
    for (int i = 0; i < FIPS204_L; i++) {
        poly_ntt_dsa(&z.vec[i]);
    }
    matrix_vec_mul_ntt(&w1, A_hat, &z);

    for (int i = 0; i < FIPS204_K; i++) {
        for (int j = 0; j < FIPS204_N; j++) {
            t1.vec[i].coeffs[j] = mod_q_dsa((int64_t)t1.vec[i].coeffs[j] << FIPS204_D);
        }
        poly_ntt_dsa(&t1.vec[i]);
        poly_pointwise_dsa(&t1.vec[i], &c_hat, &t1.vec[i]);
        poly_sub_dsa(&w1.vec[i], &w1.vec[i], &t1.vec[i]);
        poly_invntt_dsa(&w1.vec[i]);

        /* 4. Aplicar UseHint(h, w'_approx) */
        for (int j = 0; j < FIPS204_N; j++) {
            w1.vec[i].coeffs[j] = use_hint(h.vec[i].coeffs[j], w1.vec[i].coeffs[j]);
        }
    }

    /* 5. Recalcular c_tilde' = SHAKE256(mu || w1Encode(w'_1), 48) y comparar */
    uint8_t w1_packed[128 * FIPS204_K];
    uint8_t c_tilde_prime[FIPS204_CTILDE];
    w1_encode(w1_packed, &w1);

    fips202_shake256_init(&hctx);
    fips202_shake256_absorb(&hctx, mu, 64);
    fips202_shake256_absorb(&hctx, w1_packed, sizeof(w1_packed));
    fips202_shake256_finalize(&hctx);
    fips202_shake256_squeeze(c_tilde_prime, FIPS204_CTILDE, &hctx);

    uint8_t diff = 0;
    for (int i = 0; i < FIPS204_CTILDE; i++) {
        diff |= c_tilde[i] ^ c_tilde_prime[i];
    }
    return (diff == 0) ? 0 : -1;
}

int fips204_mldsa65_keypair(uint8_t pk[FIPS204_MLDSA65_PK_BYTES],
                            uint8_t sk[FIPS204_MLDSA65_SK_BYTES]) {
    uint8_t xi[32];
    if (pqc_randombytes(xi, sizeof(xi)) != 0) {
        return -1;
    }
    return fips204_mldsa65_keygen_internal(pk, sk, xi);
}

int fips204_mldsa65_sign(uint8_t sig[FIPS204_MLDSA65_SIG_BYTES],
                         size_t *siglen,
                         const uint8_t *m, size_t mlen,
                         const uint8_t sk[FIPS204_MLDSA65_SK_BYTES]) {
    uint8_t rnd[32];
    if (pqc_randombytes(rnd, sizeof(rnd)) != 0) {
        return -1;
    }
    return fips204_mldsa65_sign_ctx(sig, siglen, m, mlen, NULL, 0, sk, rnd);
}

int fips204_mldsa65_verify(const uint8_t *sig, size_t siglen,
                           const uint8_t *m, size_t mlen,
                           const uint8_t pk[FIPS204_MLDSA65_PK_BYTES]) {
    return fips204_mldsa65_verify_ctx(sig, siglen, m, mlen, NULL, 0, pk);
}

