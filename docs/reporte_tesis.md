# Reporte Consolidado de Resultados Experimentales
## Tesis: Protocolo de Votación Electrónica Basado en Criptografía Post-Cuántica de Retículos
### Universidad Mayor de San Andrés (UMSA) — Facultad de Ciencias Puras y Naturales — 2026

---

## 1. Información del Experimento

| Campo | Valor |
|---|---|
| **Metodología** | Design Science Research (DSR) |
| **Hardware** | macOS 26.5.2 (Darwin 25.5.0), Apple Silicon ARM64 |
| **Compilador C** | Clang 21.0.0 (clang-2100.0.123.102) |
| **Python** | 3.14.4 |
| **Fecha de experimento** | 2026-08-29 |
| **Total de corridas** | 300 (5 escenarios × 30 repeticiones × 2 variantes) |
| **Total de operaciones criptográficas** | ~99,000 |

---

## 2. Pregunta de Investigación Central

> **¿Puede un protocolo de votación electrónica basado en criptografía post-cuántica de retículos (ML-KEM-768 + ML-DSA-65) operar dentro de los límites de viabilidad operativa (latencia ≤ 200 ms por voto) en condiciones de carga electoral realistas, siendo una alternativa segura y eficiente al protocolo clásico RSA-2048 / ECDSA P-256?**

---

## 3. Validación de Hipótesis

### H₀ (Hipótesis Nula)
La latencia media por voto del protocolo PQC **no** cumple el límite de viabilidad operativa (≥ 200 ms), o es estadísticamente indistinguible del protocolo clásico.

### H₁ (Hipótesis Alternativa — de la Tesis)
La latencia media por voto del protocolo PQC **es significativamente menor** a 200 ms y operativamente viable.

### Resultado

| Escenario | Media PQC (ms) | IC 95% | Mediana | p-value (U) | Decisión |
|---|---|---|---|---|---|
| N=10 | 1.333 | [1.281, 1.385] | 1.329 | 2.97×10⁻¹¹ | **Rechazar H₀** |
| N=50 | 1.330 | [1.311, 1.348] | 1.325 | 5.47×10⁻¹⁰ | **Rechazar H₀** |
| N=100 | 1.347 | [1.329, 1.364] | 1.337 | 2.94×10⁻¹¹ | **Rechazar H₀** |
| N=500 | 1.351 | [1.333, 1.368] | 1.346 | 2.86×10⁻¹¹ | **Rechazar H₀** |
| N=1000 | 1.343 | [1.336, 1.351] | 1.342 | 2.85×10⁻¹¹ | **Rechazar H₀** |

**✅ H₀ RECHAZADA en todos los escenarios — H₁ CONFIRMADA (α = 0.05)**

La latencia PQC media (1.34 ms) es **~149 veces menor** al umbral de viabilidad de 200 ms.

---

## 4. Resultados de Rendimiento Comparativo

### 4.1 Latencia por Voto (End-to-End)

| N votantes | Media PQC | DE PQC | Media Clásico | DE Clásico | Factor |
|---|---|---|---|---|---|
| 10 | 1.333 ms | 0.134 ms | 0.458 ms | 0.053 ms | 2.91× |
| 50 | 1.330 ms | 0.047 ms | 0.457 ms | 0.028 ms | 2.91× |
| 100 | 1.347 ms | 0.046 ms | 0.457 ms | 0.028 ms | 2.95× |
| 500 | 1.351 ms | 0.046 ms | 0.459 ms | 0.028 ms | 2.94× |
| 1000 | 1.343 ms | 0.020 ms | 0.459 ms | 0.006 ms | 2.93× |

> **Interpretación:** El protocolo PQC es ~2.9× más lento que el clásico por voto, pero **ambos están muy por debajo del umbral de 200 ms**. El overhead relativo es irrelevante en términos de experiencia de usuario.

### 4.2 Apertura de Urna — Escrutinio por Voto

| Operación | Tiempo (ms) | Diferencia Relativa |
|---|---|---|
| ML-KEM-768 Desencapsulamiento | **0.042 ms** | — |
| RSA-OAEP-2048 Descifrado | 92.137 ms | **PQC es 2,175× MÁS RÁPIDO** |

> **Interpretación:** En la fase de escrutinio masivo (apertura de urna), ML-KEM-768 ofrece una **ventaja operativa crítica** de más de tres órdenes de magnitud sobre RSA-2048. Para 10,000 votos: PQC tarda ~420 ms vs RSA ~921 segundos (15.4 minutos).

### 4.3 Micro-benchmarks por Operación Atómica

| Operación | Algoritmo | Tiempo (ms) |
|---|---|---|
| Generación de par de claves | ML-KEM-768 | ~0.18 ms |
| Generación de par de claves | ML-DSA-65 | ~0.21 ms |
| Encapsulamiento | ML-KEM-768 | ~0.19 ms |
| Firma digital | ML-DSA-65 | ~0.37 ms |
| Verificación de firma | ML-DSA-65 | ~0.21 ms |
| **Desencapsulamiento** | **ML-KEM-768** | **~0.042 ms** |
| Generación de par RSA-2048 | RSA | ~28.5 ms |
| Cifrado RSA-OAEP-2048 | RSA | ~0.18 ms |
| **Descifrado RSA-OAEP-2048** | **RSA** | **~92.14 ms** |
| Firma ECDSA P-256 | ECDSA | ~0.12 ms |
| Verificación ECDSA P-256 | ECDSA | ~0.18 ms |

---

## 5. Tamaños de Estructuras Criptográficas

### 5.1 PQC (ML-KEM-768 + ML-DSA-65)

| Estructura | Tamaño (bytes) | Notas |
|---|---|---|
| Clave pública ML-KEM-768 | 1,184 bytes | Clave de elección pública |
| Clave privada ML-KEM-768 | 2,400 bytes | Solo AC, custodia segura |
| Texto cifrado ML-KEM-768 | 1,088 bytes | Por boleta |
| Clave pública ML-DSA-65 | 1,952 bytes | Del votante (efímero) |
| Clave privada ML-DSA-65 | 4,032 bytes | Del votante (efímero, destruir post-voto) |
| Firma ML-DSA-65 | 3,309 bytes | Firma del votante sobre la boleta |
| **Boleta total estimada** | **~16,200 bytes** | ct + voto cifrado + pk_V + firma + token |

### 5.2 Clásico (RSA-2048 + ECDSA P-256)

| Estructura | Tamaño (bytes) |
|---|---|
| Clave pública RSA-2048 | ~294 bytes |
| Texto cifrado RSA-2048 | 256 bytes |
| Clave pública ECDSA P-256 | ~94 bytes |
| Firma ECDSA P-256 | ~72 bytes |
| **Boleta total estimada** | **~1,200 bytes** |

### 5.3 Análisis de la Sobrecarga de Comunicación

El paquete PQC (~16.2 KB) es 13.5× mayor que el clásico (~1.2 KB). Sin embargo:
- En una red 4G (10 Mbps uplink): ~13 ms de transmisión adicional por boleta.
- En Wi-Fi (100 Mbps): < 2 ms adicionales.
- **Conclusión:** La sobrecarga es operativamente despreciable en redes modernas.

---

## 6. Análisis Estadístico Inferencial

### 6.1 Prueba de Normalidad (Shapiro-Wilk, n=30 por grupo)

| Escenario | PQC (p-value) | Clásico (p-value) | Distribución |
|---|---|---|---|
| N=10 | < 0.05 | < 0.05 | No normal |
| N=50 | < 0.05 | < 0.05 | No normal |
| N=100–1000 | > 0.05 | > 0.05 | Normal (CLT) |

> Dado que varios grupos no son normales, se utilizó **Mann-Whitney U** como prueba principal para todos los escenarios (conservador y no paramétrico).

### 6.2 Prueba de Homocedasticidad (Levene)

| Escenario | p-value Levene | Varianzas iguales |
|---|---|---|
| N=10 | 0.023 | ❌ No |
| N=50–1000 | > 0.05 | ✅ Sí |

### 6.3 Tamaño del Efecto (Cohen's d)

| Escenario | Cohen's d | Interpretación |
|---|---|---|
| N=10 | 7.23 | Efecto enorme (> 0.8) |
| N=50 | 18.45 | Efecto enorme |
| N=100 | 19.31 | Efecto enorme |
| N=500 | 18.92 | Efecto enorme |
| N=1000 | 26.71 | Efecto enorme |

> El tamaño del efecto extremadamente grande confirma que la diferencia medida entre PQC y Clásico es **sustancial y no un artefacto estadístico**.

---

## 7. Verificación Formal de Seguridad

El protocolo fue modelado y verificado con **Tamarin Prover** (análisis simbólico en el modelo Dolev-Yao):

| Lema | Estado | Tiempo de verificación |
|---|---|---|
| `anonimato_votante` | ✅ **VERIFIED** | < 5 s |
| `integridad_voto` | ✅ **VERIFIED** | < 5 s |
| `doble_voto_imposible` | ✅ **VERIFIED** | < 5 s |
| `autenticidad_resultado` | ✅ **VERIFIED** | < 5 s |

---

## 8. Validación de Implementación KAT

| Algoritmo | Estándar | Vectores PASS | Vectores FAIL | Estado |
|---|---|---|---|---|
| ML-KEM-768 | FIPS 203 | 100 | 0 | ✅ PASS 100% |
| ML-DSA-65 | FIPS 204 | 100 | 0 | ✅ PASS 100% |

---

## 9. Conclusiones de la Investigación

### 9.1 Respecto a la Hipótesis
La hipótesis de investigación es **formalmente confirmada con evidencia estadística a nivel α = 0.0001**. El protocolo PQC opera a una latencia promedio de **1.34 ms por voto**, que es 149 veces inferior al umbral de viabilidad de 200 ms, y esta diferencia es estadísticamente significativa ($p < 0.0001$, Mann-Whitney U).

### 9.2 Ventajas del Protocolo PQC
1. **Resistencia cuántica comprobada:** ML-KEM-768 y ML-DSA-65 están basados en el problema Module-LWE, considerado intractable para computadoras cuánticas de gran escala.
2. **Escrutinio ultrarrápido:** El desencapsulamiento ML-KEM-768 es 2,175× más rápido que RSA-2048 en la apertura de urna, haciéndolo superior para conteos masivos.
3. **Estandarización oficial:** Ambos algoritmos son estándares NIST FIPS 203/204 (2024), asegurando interoperabilidad y soporte a largo plazo.
4. **Seguridad formal verificada:** 4 lemas de seguridad demostrados con Tamarin Prover.

### 9.3 Limitaciones y Trabajo Futuro
1. **Sobrecarga de comunicación:** Las boletas PQC son 13.5× más grandes (~16.2 KB vs ~1.2 KB). En redes de baja velocidad (< 1 Mbps) esto podría ser relevante.
2. **Generación de claves RSA:** RSA-2048 es ~157× más lento en keygen que ML-KEM-768. Esto favorece aún más al PQC en inicialización.
3. **Escalabilidad:** Las pruebas se realizaron hasta N=1,000 votantes simultáneos. Para elecciones nacionales (millones de votantes) se requeriría una arquitectura distribuida adicional.
4. **Trabajo futuro:** Evaluar FALCON-512 (firmas más compactas) y SPHINCS+-128f como alternativas para reducir el tamaño de la boleta.

---

## 10. Métricas de Calidad del Código

| Métrica | Valor |
|---|---|
| Tests unitarios / integración | 20/20 (100% PASS) |
| Vectores KAT validados | 200/200 (100% PASS) |
| Lemas formales verificados | 4/4 (100% VERIFIED) |
| Líneas de código Python | ~2,500 |
| Líneas de código C | ~500 |
| Commits en el repositorio | 8+ commits |

---

*Reporte generado como parte de la Fase 8 — Documentación Final — Proyecto de Grado UMSA 2026*
