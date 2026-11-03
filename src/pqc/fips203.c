/**
 * @file fips203.c
 * @brief Implementación propia desde cero del estándar NIST FIPS 203 (ML-KEM-768).
 *
 * Proyecto de Grado - Universidad Mayor de San Andrés (UMSA)
 * Implementa fielmente los Algoritmos 5 al 21 de la especificación FIPS 203 sobre el anillo
 * ciclotómico R_q = Z_3329[X]/(X^256 + 1) utilizando nuestra implementación propia de FIPS 202.
 */

#include "fips203.h"
#include "fips202.h"
#include <string.h>

/* Representación de un polinomio en R_q o T_q con coeficientes en [0, 3328] */
typedef struct {
    int16_t coeffs[FIPS203_N];
} fips203_poly;

/* Vector de k = 3 polinomios en R_q^k */
typedef struct {
    fips203_poly vec[FIPS203_K];
} fips203_polyvec;

/* Tablas matemáticas para NTT e INTT derivadas de la raíz primitiva 256-ésima zeta = 17 mod 3329 */
static int16_t ZETA_TABLE[128];
static int16_t GAMMA_TABLE[128];
static int TABLES_INITIALIZED = 0;

/* Reducción modular canónica a [0, q - 1] */
static inline int16_t mod_q(int32_t x) {
    int32_t r = x % FIPS203_Q;
    return (int16_t)(r < 0 ? r + FIPS203_Q : r);
}

/* Exponenciación modular b^e mod 3329 */
static int16_t mod_pow_q(int32_t base, int32_t exp) {
    int32_t result = 1;
    int32_t b = mod_q(base);
    while (exp > 0) {
        if (exp & 1) {
            result = (result * b) % FIPS203_Q;
        }
        b = (b * b) % FIPS203_Q;
        exp >>= 1;
    }
    return (int16_t)result;
}

/* Algoritmo 3 de FIPS 203: BitRev_7(x) - Inversión de 7 bits */
static int32_t bitrev7(int32_t x) {
    int32_t r = 0;
    for (int i = 0; i < 7; i++) {
        r = (r << 1) | (x & 1);
        x >>= 1;
    }
    return r;
}

/* Inicialización determinista de las potencias de zeta = 17 mod 3329 (Sección 4.3 de FIPS 203) */
static void ensure_ntt_tables(void) {
    if (TABLES_INITIALIZED) {
        return;
    }
    for (int i = 0; i < 128; i++) {
        int32_t br = bitrev7(i);
        ZETA_TABLE[i] = mod_pow_q(17, br);
        GAMMA_TABLE[i] = mod_pow_q(17, 2 * br + 1);
    }
    TABLES_INITIALIZED = 1;
}

/* ============================================================
 * Compresión, Descompresión y Codificación (Sección 4.2.1 de FIPS 203)
 * ============================================================ */

/* Compress_d(x) = round((2^d / q) * x) mod 2^d */
static inline uint16_t compress_d(int16_t x, int d) {
    uint32_t ux = (uint32_t)mod_q(x);
    uint32_t num = (ux << d) + (FIPS203_Q / 2);
    return (uint16_t)((num / FIPS203_Q) & ((1U << d) - 1U));
}

/* Decompress_d(y) = round((q / 2^d) * y) */
static inline int16_t decompress_d(uint16_t y, int d) {
    uint32_t num = ((uint32_t)y * FIPS203_Q) + (1U << (d - 1));
    return (int16_t)(num >> d);
}

/* Algoritmo 5 de FIPS 203: ByteEncode_d(F) */
static void byte_encode(uint8_t *B, const fips203_poly *F, int d) {
    memset(B, 0, (size_t)(32 * d));
    for (int i = 0; i < FIPS203_N; i++) {
        uint16_t a = (uint16_t)mod_q(F->coeffs[i]);
        for (int j = 0; j < d; j++) {
            size_t bit_idx = (size_t)(i * d + j);
            B[bit_idx >> 3] |= (uint8_t)(((a >> j) & 1U) << (bit_idx & 7U));
        }
    }
}

/* Algoritmo 6 de FIPS 203: ByteDecode_d(B) */
static void byte_decode(fips203_poly *F, const uint8_t *B, int d) {
    for (int i = 0; i < FIPS203_N; i++) {
        uint16_t val = 0;
        for (int j = 0; j < d; j++) {
            size_t bit_idx = (size_t)(i * d + j);
            uint8_t bit = (B[bit_idx >> 3] >> (bit_idx & 7U)) & 1U;
            val |= (uint16_t)(bit << j);
        }
        if (d == 12) {
            F->coeffs[i] = (int16_t)(val % FIPS203_Q);
        } else {
            F->coeffs[i] = (int16_t)val;
        }
    }
}

/* ============================================================
 * Muestreo Uniforme (SampleNTT) y Binomial Centrado (SamplePolyCBD)
 * ============================================================ */

/* Algoritmo 7 de FIPS 203: SampleNTT(B) usando SHAKE128 sobre (rho || j || i) */
static void sample_ntt(fips203_poly *a_hat, const uint8_t rho[32], uint8_t j_idx, uint8_t i_idx) {
    uint8_t inbuf[34];
    memcpy(inbuf, rho, 32);
    inbuf[32] = j_idx;
    inbuf[33] = i_idx;

    fips202_shake128_ctx ctx;
    fips202_shake128_init(&ctx);
    fips202_shake128_absorb(&ctx, inbuf, 34);
    fips202_shake128_finalize(&ctx);

    int count = 0;
    uint8_t c[3];
    while (count < FIPS203_N) {
        fips202_shake128_squeeze(c, 3, &ctx);
        uint16_t d1 = (uint16_t)c[0] + 256U * ((uint16_t)c[1] & 0x0FU);
        uint16_t d2 = ((uint16_t)c[1] >> 4) + 16U * (uint16_t)c[2];
        if (d1 < FIPS203_Q) {
            a_hat->coeffs[count++] = (int16_t)d1;
        }
        if (d2 < FIPS203_Q && count < FIPS203_N) {
            a_hat->coeffs[count++] = (int16_t)d2;
        }
    }
}

/* Algoritmo 8 de FIPS 203: SamplePolyCBD_eta(PRF_eta(sigma, N)) para eta = 2 */
static void sample_poly_cbd_eta2(fips203_poly *f, const uint8_t sigma[32], uint8_t nonce) {
    uint8_t prf_in[33];
    uint8_t buf[64 * 2]; /* 128 bytes para eta = 2 */
    memcpy(prf_in, sigma, 32);
    prf_in[32] = nonce;

    fips202_shake256(buf, sizeof(buf), prf_in, sizeof(prf_in));

    for (int i = 0; i < 128; i++) {
        uint8_t b = buf[i];
        int16_t x0 = (int16_t)((b & 1U) + ((b >> 1) & 1U));
        int16_t y0 = (int16_t)(((b >> 2) & 1U) + ((b >> 3) & 1U));
        int16_t x1 = (int16_t)(((b >> 4) & 1U) + ((b >> 5) & 1U));
        int16_t y1 = (int16_t)(((b >> 6) & 1U) + ((b >> 7) & 1U));

        f->coeffs[2 * i]     = mod_q(x0 - y0);
        f->coeffs[2 * i + 1] = mod_q(x1 - y1);
    }
}

/* ============================================================
 * Transformada Teórica de Números (NTT / INTT) — Sección 4.3 de FIPS 203
 * ============================================================ */

/* Algoritmo 9 de FIPS 203: NTT(f) */
static void poly_ntt(fips203_poly *f) {
    ensure_ntt_tables();
    int k = 1;
    for (int len = 128; len >= 2; len >>= 1) {
        for (int start = 0; start < 256; start += 2 * len) {
            int32_t zeta = ZETA_TABLE[k++];
            for (int j = start; j < start + len; j++) {
                int16_t t = mod_q(zeta * f->coeffs[j + len]);
                f->coeffs[j + len] = mod_q(f->coeffs[j] - t);
                f->coeffs[j]       = mod_q(f->coeffs[j] + t);
            }
        }
    }
}

/* Algoritmo 10 de FIPS 203: NTT^-1(f_hat) */
static void poly_invntt(fips203_poly *f) {
    ensure_ntt_tables();
    int k = 127;
    for (int len = 2; len <= 128; len <<= 1) {
        for (int start = 0; start < 256; start += 2 * len) {
            int32_t zeta = ZETA_TABLE[k--];
            for (int j = start; j < start + len; j++) {
                int16_t t = f->coeffs[j];
                f->coeffs[j]       = mod_q(t + f->coeffs[j + len]);
                f->coeffs[j + len] = mod_q(zeta * (f->coeffs[j + len] - t));
            }
        }
    }
    /* Multiplicación por 128^-1 mod 3329 = 3303 */
    for (int j = 0; j < 256; j++) {
        f->coeffs[j] = mod_q((int32_t)f->coeffs[j] * 3303);
    }
}

/* Algoritmo 11 y 12 de FIPS 203: MultiplyNTTs y BaseCaseMultiply en T_q */
static void poly_multiply_ntt(fips203_poly *h, const fips203_poly *f, const fips203_poly *g) {
    ensure_ntt_tables();
    for (int i = 0; i < 128; i++) {
        int32_t a0 = f->coeffs[2 * i];
        int32_t a1 = f->coeffs[2 * i + 1];
        int32_t b0 = g->coeffs[2 * i];
        int32_t b1 = g->coeffs[2 * i + 1];
        int32_t gamma = GAMMA_TABLE[i];

        int32_t a1b1_gamma = mod_q(mod_q(a1 * b1) * gamma);
        h->coeffs[2 * i]     = mod_q(a0 * b0 + a1b1_gamma);
        h->coeffs[2 * i + 1] = mod_q(a0 * b1 + a1 * b0);
    }
}

static void poly_add(fips203_poly *r, const fips203_poly *a, const fips203_poly *b) {
    for (int i = 0; i < FIPS203_N; i++) {
        r->coeffs[i] = mod_q(a->coeffs[i] + b->coeffs[i]);
    }
}

static void poly_sub(fips203_poly *r, const fips203_poly *a, const fips203_poly *b) {
    for (int i = 0; i < FIPS203_N; i++) {
        r->coeffs[i] = mod_q(a->coeffs[i] - b->coeffs[i]);
    }
}

/* Producto punto de dos vectores de polinomios en el dominio NTT */
static void polyvec_dot_ntt(fips203_poly *res, const fips203_polyvec *u, const fips203_polyvec *v) {
    fips203_poly tmp;
    poly_multiply_ntt(res, &u->vec[0], &v->vec[0]);
    for (int j = 1; j < FIPS203_K; j++) {
        poly_multiply_ntt(&tmp, &u->vec[j], &v->vec[j]);
        poly_add(res, res, &tmp);
    }
}

/* ============================================================
 * Esquema de Cifrado de Clave Pública Subyacente K-PKE (Sección 5 de FIPS 203)
 * ============================================================ */

/* Algoritmo 13 de FIPS 203: K-PKE.KeyGen(d) */
static void kpke_keygen(uint8_t ek_pke[FIPS203_MLKEM768_EK_BYTES],
                        uint8_t dk_pke[384 * FIPS203_K],
                        const uint8_t d[32]) {
    uint8_t g_in[33];
    uint8_t g_out[64];
    memcpy(g_in, d, 32);
    g_in[32] = FIPS203_K;
    fips202_sha3_512(g_out, g_in, 33);

    const uint8_t *rho   = g_out;
    const uint8_t *sigma = g_out + 32;

    /* 1. Generar matriz A_hat[i][j] en dominio NTT */
    fips203_polyvec A_hat[FIPS203_K];
    for (int i = 0; i < FIPS203_K; i++) {
        for (int j = 0; j < FIPS203_K; j++) {
            sample_ntt(&A_hat[i].vec[j], rho, (uint8_t)j, (uint8_t)i);
        }
    }

    /* 2. Muestrear vectores secretos s y de error e desde CBD_eta1 */
    uint8_t nonce = 0;
    fips203_polyvec s, e, t_hat;
    for (int i = 0; i < FIPS203_K; i++) {
        sample_poly_cbd_eta2(&s.vec[i], sigma, nonce++);
    }
    for (int i = 0; i < FIPS203_K; i++) {
        sample_poly_cbd_eta2(&e.vec[i], sigma, nonce++);
    }

    /* 3. Transformar s y e al dominio NTT */
    for (int i = 0; i < FIPS203_K; i++) {
        poly_ntt(&s.vec[i]);
        poly_ntt(&e.vec[i]);
    }

    /* 4. Calcular t_hat = A_hat * s_hat + e_hat */
    for (int i = 0; i < FIPS203_K; i++) {
        polyvec_dot_ntt(&t_hat.vec[i], &A_hat[i], &s);
        poly_add(&t_hat.vec[i], &t_hat.vec[i], &e.vec[i]);
    }

    /* 5. Codificar ek_pke = ByteEncode_12(t_hat) || rho y dk_pke = ByteEncode_12(s_hat) */
    for (int i = 0; i < FIPS203_K; i++) {
        byte_encode(ek_pke + 384 * i, &t_hat.vec[i], 12);
        byte_encode(dk_pke + 384 * i, &s.vec[i], 12);
    }
    memcpy(ek_pke + 384 * FIPS203_K, rho, 32);
}

/* Algoritmo 14 de FIPS 203: K-PKE.Encrypt(ek_pke, m, r) */
static void kpke_encrypt(uint8_t c[FIPS203_MLKEM768_CT_BYTES],
                         const uint8_t ek_pke[FIPS203_MLKEM768_EK_BYTES],
                         const uint8_t m[32],
                         const uint8_t r[32]) {
    fips203_polyvec t_hat;
    for (int i = 0; i < FIPS203_K; i++) {
        byte_decode(&t_hat.vec[i], ek_pke + 384 * i, 12);
    }
    const uint8_t *rho = ek_pke + 384 * FIPS203_K;

    /* 1. Regenerar matriz transpuesta A_hat^T: entrada (i, j) usa SampleNTT(rho, i, j) */
    fips203_polyvec AT_hat[FIPS203_K];
    for (int i = 0; i < FIPS203_K; i++) {
        for (int j = 0; j < FIPS203_K; j++) {
            sample_ntt(&AT_hat[i].vec[j], rho, (uint8_t)i, (uint8_t)j);
        }
    }

    /* 2. Muestrear r_vec (y), e1 y e2 */
    uint8_t nonce = 0;
    fips203_polyvec y, e1, u;
    fips203_poly e2, v, mu;
    for (int i = 0; i < FIPS203_K; i++) {
        sample_poly_cbd_eta2(&y.vec[i], r, nonce++);
    }
    for (int i = 0; i < FIPS203_K; i++) {
        sample_poly_cbd_eta2(&e1.vec[i], r, nonce++);
    }
    sample_poly_cbd_eta2(&e2, r, nonce++);

    /* 3. NTT(y) */
    for (int i = 0; i < FIPS203_K; i++) {
        poly_ntt(&y.vec[i]);
    }

    /* 4. u = NTT^-1(A_hat^T * y_hat) + e1 */
    for (int i = 0; i < FIPS203_K; i++) {
        polyvec_dot_ntt(&u.vec[i], &AT_hat[i], &y);
        poly_invntt(&u.vec[i]);
        poly_add(&u.vec[i], &u.vec[i], &e1.vec[i]);
    }

    /* 5. Decodificar mensaje m en polinomio mu = Decompress_1(ByteDecode_1(m)) */
    byte_decode(&mu, m, 1);
    for (int i = 0; i < FIPS203_N; i++) {
        mu.coeffs[i] = decompress_d((uint16_t)mu.coeffs[i], 1);
    }

    /* 6. v = NTT^-1(t_hat^T * y_hat) + e2 + mu */
    polyvec_dot_ntt(&v, &t_hat, &y);
    poly_invntt(&v);
    poly_add(&v, &v, &e2);
    poly_add(&v, &v, &mu);

    /* 7. Comprimir y codificar c = c1 || c2 */
    fips203_poly tmp;
    for (int i = 0; i < FIPS203_K; i++) {
        for (int j = 0; j < FIPS203_N; j++) {
            tmp.coeffs[j] = (int16_t)compress_d(u.vec[i].coeffs[j], FIPS203_DU);
        }
        byte_encode(c + 32 * FIPS203_DU * i, &tmp, FIPS203_DU);
    }
    for (int j = 0; j < FIPS203_N; j++) {
        tmp.coeffs[j] = (int16_t)compress_d(v.coeffs[j], FIPS203_DV);
    }
    byte_encode(c + 32 * FIPS203_DU * FIPS203_K, &tmp, FIPS203_DV);
}

/* Algoritmo 15 de FIPS 203: K-PKE.Decrypt(dk_pke, c) */
static void kpke_decrypt(uint8_t m[32],
                         const uint8_t dk_pke[384 * FIPS203_K],
                         const uint8_t c[FIPS203_MLKEM768_CT_BYTES]) {
    fips203_polyvec u, s_hat;
    fips203_poly v, w;

    /* 1. Decodificar y descomprimir u' y v' */
    for (int i = 0; i < FIPS203_K; i++) {
        byte_decode(&u.vec[i], c + 32 * FIPS203_DU * i, FIPS203_DU);
        for (int j = 0; j < FIPS203_N; j++) {
            u.vec[i].coeffs[j] = decompress_d((uint16_t)u.vec[i].coeffs[j], FIPS203_DU);
        }
    }
    byte_decode(&v, c + 32 * FIPS203_DU * FIPS203_K, FIPS203_DV);
    for (int j = 0; j < FIPS203_N; j++) {
        v.coeffs[j] = decompress_d((uint16_t)v.coeffs[j], FIPS203_DV);
    }

    /* 2. Decodificar clave secreta s_hat */
    for (int i = 0; i < FIPS203_K; i++) {
        byte_decode(&s_hat.vec[i], dk_pke + 384 * i, 12);
    }

    /* 3. w = v' - NTT^-1(s_hat^T * NTT(u')) */
    for (int i = 0; i < FIPS203_K; i++) {
        poly_ntt(&u.vec[i]);
    }
    polyvec_dot_ntt(&w, &s_hat, &u);
    poly_invntt(&w);
    poly_sub(&w, &v, &w);

    /* 4. m = ByteEncode_1(Compress_1(w)) */
    for (int j = 0; j < FIPS203_N; j++) {
        w.coeffs[j] = (int16_t)compress_d(w.coeffs[j], 1);
    }
    byte_encode(m, &w, 1);
}

/* ============================================================
 * Esquema Completo ML-KEM-768 (Sección 6 y 7 de FIPS 203)
 * ============================================================ */

int fips203_mlkem768_keygen_internal(uint8_t ek[FIPS203_MLKEM768_EK_BYTES],
                                     uint8_t dk[FIPS203_MLKEM768_DK_BYTES],
                                     const uint8_t d[32],
                                     const uint8_t z[32]) {
    kpke_keygen(ek, dk, d);
    /* dk = dk_pke (1152 B) || ek (1184 B) || H(ek) (32 B) || z (32 B) */
    memcpy(dk + 384 * FIPS203_K, ek, FIPS203_MLKEM768_EK_BYTES);
    fips202_sha3_256(dk + 384 * FIPS203_K + FIPS203_MLKEM768_EK_BYTES,
                     ek, FIPS203_MLKEM768_EK_BYTES);
    memcpy(dk + 384 * FIPS203_K + FIPS203_MLKEM768_EK_BYTES + 32, z, 32);
    return 0;
}

int fips203_mlkem768_encaps_internal(uint8_t ct[FIPS203_MLKEM768_CT_BYTES],
                                     uint8_t ss[FIPS203_MLKEM768_SS_BYTES],
                                     const uint8_t ek[FIPS203_MLKEM768_EK_BYTES],
                                     const uint8_t m[32]) {
    uint8_t g_in[64];
    uint8_t kr[64];

    memcpy(g_in, m, 32);
    fips202_sha3_256(g_in + 32, ek, FIPS203_MLKEM768_EK_BYTES);
    fips202_sha3_512(kr, g_in, 64);

    kpke_encrypt(ct, ek, m, kr + 32);
    memcpy(ss, kr, 32);
    return 0;
}

int fips203_mlkem768_decaps_internal(uint8_t ss[FIPS203_MLKEM768_SS_BYTES],
                                     const uint8_t ct[FIPS203_MLKEM768_CT_BYTES],
                                     const uint8_t dk[FIPS203_MLKEM768_DK_BYTES]) {
    const uint8_t *dk_pke = dk;
    const uint8_t *ek_pke = dk + 384 * FIPS203_K;
    const uint8_t *h      = dk + 384 * FIPS203_K + FIPS203_MLKEM768_EK_BYTES;
    const uint8_t *z      = dk + 384 * FIPS203_K + FIPS203_MLKEM768_EK_BYTES + 32;

    uint8_t m_prime[32];
    kpke_decrypt(m_prime, dk_pke, ct);

    /* (K', r') = G(m' || h) */
    uint8_t g_in[64];
    uint8_t kr[64];
    memcpy(g_in, m_prime, 32);
    memcpy(g_in + 32, h, 32);
    fips202_sha3_512(kr, g_in, 64);

    /* K_bar = J(z || c) = SHAKE256(z || c, 32) para rechazo implícito */
    uint8_t k_bar[32];
    fips202_shake256_ctx j_ctx;
    fips202_shake256_init(&j_ctx);
    fips202_shake256_absorb(&j_ctx, z, 32);
    fips202_shake256_absorb(&j_ctx, ct, FIPS203_MLKEM768_CT_BYTES);
    fips202_shake256_finalize(&j_ctx);
    fips202_shake256_squeeze(k_bar, 32, &j_ctx);

    /* Re-cifrado c' = K-PKE.Encrypt(ek_pke, m', r') */
    uint8_t ct_prime[FIPS203_MLKEM768_CT_BYTES];
    kpke_encrypt(ct_prime, ek_pke, m_prime, kr + 32);

    /* Comparación de ct y ct_prime en tiempo constante */
    uint8_t diff = 0;
    for (size_t i = 0; i < FIPS203_MLKEM768_CT_BYTES; i++) {
        diff |= ct[i] ^ ct_prime[i];
    }
    /* mask = 0x00 si ct == ct_prime, 0xFF si son distintos */
    uint8_t mask = (uint8_t)((-(int16_t)(uint16_t)diff) >> 8);
    for (int i = 0; i < 32; i++) {
        ss[i] = (uint8_t)((kr[i] & ~mask) | (k_bar[i] & mask));
    }
    return 0;
}

int fips203_mlkem768_keypair(uint8_t ek[FIPS203_MLKEM768_EK_BYTES],
                             uint8_t dk[FIPS203_MLKEM768_DK_BYTES]) {
    uint8_t coins[64];
    if (pqc_randombytes(coins, sizeof(coins)) != 0) {
        return -1;
    }
    return fips203_mlkem768_keygen_internal(ek, dk, coins, coins + 32);
}

int fips203_mlkem768_encaps(uint8_t ct[FIPS203_MLKEM768_CT_BYTES],
                            uint8_t ss[FIPS203_MLKEM768_SS_BYTES],
                            const uint8_t ek[FIPS203_MLKEM768_EK_BYTES]) {
    uint8_t m[32];
    if (pqc_randombytes(m, sizeof(m)) != 0) {
        return -1;
    }
    return fips203_mlkem768_encaps_internal(ct, ss, ek, m);
}

int fips203_mlkem768_decaps(uint8_t ss[FIPS203_MLKEM768_SS_BYTES],
                            const uint8_t ct[FIPS203_MLKEM768_CT_BYTES],
                            const uint8_t dk[FIPS203_MLKEM768_DK_BYTES]) {
    return fips203_mlkem768_decaps_internal(ss, ct, dk);
}

