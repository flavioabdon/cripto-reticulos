/**
 * @file fips203.h
 * @brief Implementación propia del estándar NIST FIPS 203 (ML-KEM-768).
 *
 * Proyecto de Grado - Universidad Mayor de San Andrés (UMSA)
 * Criptografía Post-Cuántica Basada en Retículos (Module-LWE).
 *
 * Parámetros de ML-KEM-768 (Categoría de Seguridad 3 de NIST):
 *   - n = 256, q = 3329, k = 3
 *   - eta_1 = 2, eta_2 = 2
 *   - d_u = 10, d_v = 4
 */

#ifndef PQC_FIPS203_H
#define PQC_FIPS203_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Parámetros matemáticos de ML-KEM-768 (Tabla 2 de FIPS 203) */
#define FIPS203_N    256
#define FIPS203_Q    3329
#define FIPS203_K    3
#define FIPS203_ETA1 2
#define FIPS203_ETA2 2
#define FIPS203_DU   10
#define FIPS203_DV   4

/* Longitudes en bytes de claves, texto cifrado y secreto compartido */
#define FIPS203_MLKEM768_EK_BYTES 1184
#define FIPS203_MLKEM768_DK_BYTES 2400
#define FIPS203_MLKEM768_CT_BYTES 1088
#define FIPS203_MLKEM768_SS_BYTES 32

/* ============================================================
 * Algoritmos Internos Deterministas (Sección 6 de FIPS 203)
 * ============================================================ */

/**
 * Algoritmo 16 de FIPS 203: ML-KEM.KeyGen_internal(d, z)
 * Genera (ek, dk) de manera determinista a partir de las semillas d (32 B) y z (32 B).
 */
int fips203_mlkem768_keygen_internal(uint8_t ek[FIPS203_MLKEM768_EK_BYTES],
                                     uint8_t dk[FIPS203_MLKEM768_DK_BYTES],
                                     const uint8_t d[32],
                                     const uint8_t z[32]);

/**
 * Algoritmo 17 de FIPS 203: ML-KEM.Encaps_internal(ek, m)
 * Encapsula de manera determinista un secreto compartido K (32 B) y texto cifrado c (1088 B)
 * a partir de la clave de encapsulamiento ek y la entropía m (32 B).
 */
int fips203_mlkem768_encaps_internal(uint8_t ct[FIPS203_MLKEM768_CT_BYTES],
                                     uint8_t ss[FIPS203_MLKEM768_SS_BYTES],
                                     const uint8_t ek[FIPS203_MLKEM768_EK_BYTES],
                                     const uint8_t m[32]);

/**
 * Algoritmo 18 de FIPS 203: ML-KEM.Decaps_internal(dk, c)
 * Desencapsula el texto cifrado c (1088 B) usando la clave de desencapsulamiento dk (2400 B)
 * con rechazo implícito Fujisaki-Okamoto en tiempo constante.
 */
int fips203_mlkem768_decaps_internal(uint8_t ss[FIPS203_MLKEM768_SS_BYTES],
                                     const uint8_t ct[FIPS203_MLKEM768_CT_BYTES],
                                     const uint8_t dk[FIPS203_MLKEM768_DK_BYTES]);

/* ============================================================
 * API Pública de Alto Nivel (Sección 7 de FIPS 203)
 * ============================================================ */

/**
 * Algoritmo 19 de FIPS 203: ML-KEM.KeyGen()
 */
int fips203_mlkem768_keypair(uint8_t ek[FIPS203_MLKEM768_EK_BYTES],
                             uint8_t dk[FIPS203_MLKEM768_DK_BYTES]);

/**
 * Algoritmo 20 de FIPS 203: ML-KEM.Encaps(ek)
 */
int fips203_mlkem768_encaps(uint8_t ct[FIPS203_MLKEM768_CT_BYTES],
                            uint8_t ss[FIPS203_MLKEM768_SS_BYTES],
                            const uint8_t ek[FIPS203_MLKEM768_EK_BYTES]);

/**
 * Algoritmo 21 de FIPS 203: ML-KEM.Decaps(dk, c)
 */
int fips203_mlkem768_decaps(uint8_t ss[FIPS203_MLKEM768_SS_BYTES],
                            const uint8_t ct[FIPS203_MLKEM768_CT_BYTES],
                            const uint8_t dk[FIPS203_MLKEM768_DK_BYTES]);

#ifdef __cplusplus
}
#endif

#endif /* PQC_FIPS203_H */

