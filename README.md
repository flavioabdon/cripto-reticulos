# Protocolo de Votación Electrónica Basado en Criptografía Post-Cuántica de Retículos

> **Proyecto de Grado — Universidad Mayor de San Andrés (UMSA)**
> Carrera de Informática — Facultad de Ciencias Puras y Naturales
>
> **Metodología:** Design Science Research (DSR) | **Año:** 2026

---

## Resumen Ejecutivo

Este repositorio contiene el artefacto computacional completo de la tesis de grado, cuyo objetivo central es **diseñar, implementar y evaluar empíricamente un protocolo de votación electrónica resistente a la amenaza cuántica**, utilizando los estándares post-cuánticos del NIST:

- **ML-KEM-768** (Module Lattice-based Key Encapsulation Mechanism, FIPS 203) — encapsulamiento de claves de sesión con seguridad de nivel 3 (192 bits clásico-equivalente).
- **ML-DSA-65** (Module Lattice-based Digital Signature Algorithm, FIPS 204) — autenticación e integridad de mensajes mediante firmas digitales de nivel 3.

El protocolo fue evaluado empíricamente bajo **300 experimentos independientes** (5 escenarios × 30 repeticiones por variante), comparando el rendimiento operativo frente al protocolo clásico RSA-2048 / ECDSA P-256.

---

##  Hipótesis de Investigación y Resultado

> *"El protocolo de votación electrónica post-cuántico basado en retículos puede operar dentro de los límites de viabilidad operativa (latencia por voto ≤ 200 ms) en condiciones de carga electoral realistas."*

| Métrica | PQC (ML-KEM-768 + ML-DSA-65) | Clásico (RSA-2048 + ECDSA) | Límite |
|---|---|---|---|
| **Latencia media por voto** | **1.34 ms ± 0.05 ms** | 0.46 ms ± 0.01 ms | ≤ 200 ms |
| **Apertura de urna (1 voto)** | **0.042 ms** | 92.137 ms | — |
| **p-value (Mann-Whitney U)** | **< 0.0001** | — | α = 0.05 |
| **Cohen's d** | **> 3.5** | — | — |

**Hipótesis CONFIRMADA** — La latencia PQC es ~150 veces menor al umbral de 200 ms.

---

## Arquitectura del Protocolo

### Entidades Formales

| Entidad | Código | Rol |
|---|---|---|
| Autoridad de Registro | `AR` | Emite credenciales de votante y firma el padrón electoral |
| Autoridad de Conteo | `AC` | Genera par de claves de elección y descifra la urna al cierre |
| Servidor de Votación | `SV` | Recibe, valida y almacena boletas cifradas |
| Votante | `V` | Genera, cifra y firma su voto con anonimato garantizado |

### Fases Secuenciales

```
F1: Inicialización → F2: Registro → F3: Votación
F4: Cierre         → F5: Escrutinio → F6: Publicación
```

1. **Inicialización** — `AC` genera `(pk_eleccion, sk_eleccion)` ML-KEM-768; `AR` genera `(pk_AR, sk_AR)` ML-DSA-65.
2. **Registro** — `AR` emite token `τ = Sign(sk_AR, ID_V)`.
3. **Votación** — Votante encapsula `(ct, K) = KEM.Enc(pk_eleccion)`, cifra `c = AES-256-GCM(KDF(K), voto)`, construye boleta `B = (ct, c, pk_V, τ, Sig_V)`.
4. **Cierre** — `SV` sella la urna.
5. **Escrutinio** — `AC` desencapsula `K` de cada boleta y recupera votos.
6. **Publicación** — Resultado firmado y tablón de auditoría publicados.

>   Documentación técnica completa: [`docs/arquitectura.md`](docs/arquitectura.md) y [`docs/diagrama_flujo.md`](docs/diagrama_flujo.md)

---

##  Requisitos del Sistema

| Componente | Versión Mínima | Verificación |
|---|---|---|
| **Python** | 3.11+ | `python3 --version` |
| **Clang / GCC** | 12+ | `clang --version` |
| **Make** | 3.81+ | `make --version` |

> **Entorno de desarrollo:** macOS 26.5.2 (Darwin 25.5.0), Apple Silicon ARM64, Clang 21.0.0, Python 3.14.4.

---

##  Instalación

### 1. Clonar el repositorio

```bash
git clone <URL-del-repositorio>
cd "CRIPTOGRAFIA RETICULOS"
```

### 2. Crear entorno virtual Python

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install flask cryptography scipy numpy matplotlib seaborn pandas
```

### 4. Compilar la biblioteca criptográfica C

```bash
make -C src/pqc
```

> macOS Apple Silicon requiere Xcode Command Line Tools: `xcode-select --install`
> La biblioteca resultante es `src/pqc/libpqc_core.dylib`.

---

##  Verificación y Pruebas

### Validación KAT (Known Answer Tests — NIST FIPS 203/204)

```bash
source venv/bin/activate
python3 validacion/kat/runner_kat.py
```

**Resultado esperado:**
```
[ML-KEM-768] KAT:  PASS (100/100 vectores)
[ML-DSA-65]  KAT:  PASS (100/100 vectores)
```

### Suite completa de tests (20/20)

```bash
python3 -m pytest tests/ -v
```

---

##  Dashboard Web de Demostración

```bash
source venv/bin/activate
python3 src/web/app.py
# → http://127.0.0.1:5050
```

| Pestaña | Descripción |
|---|---|
|  Cabina de Votación | Flujo completo con inspector criptográfico |
|  Urna Digital | Boletas cifradas en tiempo real |
|  Escrutinio | Apertura de urna con gráfico Chart.js |
|  Padrón Electoral | Registro de votantes habilitados |
|  Administración | Modo PQC / Clásico configurable |

---

##  Reproducir los Benchmarks

```bash
# Ejecutar el arnés completo (~15-30 min)
python3 benchmark/runner.py

# Generar análisis estadístico y gráficos 300 DPI
python3 analisis_estadistico/analisis.py
```

**Gráficos generados en `analisis_estadistico/graficos/`:**
- `latencia_voto_boxplot.png`
- `tally_desencapsulamiento_comparacion.png`
- `tamanos_estructuras_barplot.png`

---

##  Verificación Formal — Tamarin Prover

```bash
tamarin-prover analisis tamarin/protocolo.spthy
```

**4 lemas formalmente verificados:**
1. `anonimato_votante` — El servidor no puede vincular votos con identidades.
2. `integridad_voto` — Votos no pueden ser modificados sin detección.
3. `doble_voto_imposible` — Cada votante solo puede sufragar una vez.
4. `autenticidad_resultado` — El resultado publicado es auténtico y verificable.

---

##  Estructura del Proyecto

> Manual completo: [`docs/estructura_proyecto.md`](docs/estructura_proyecto.md)

```
CRIPTOGRAFIA RETICULOS/
├── src/pqc/          # Motor PQC (C + Python)
├── src/clasico/      # Motor clásico RSA/ECDSA
├── src/web/          # Dashboard Flask
├── benchmark/        # Benchmarking y resultados
├── analisis_estadistico/ # Análisis inferencial
├── tests/            # Suite de pruebas
├── docs/             # Documentación técnica
├── tamarin/          # Modelo formal Tamarin
└── validacion/kat/   # Vectores KAT NIST
```

---

##  Resultados Principales

### Latencia por voto

| N votantes | PQC Media | Clásico Media |
|---|---|---|
| 10 | 1.33 ms | 0.46 ms |
| 100 | 1.35 ms | 0.46 ms |
| 1000 | 1.34 ms | 0.46 ms |

### Apertura de urna (escrutinio)

| Algoritmo | Tiempo |
|---|---|
| ML-KEM-768 (desencapsular) | **0.042 ms** |
| RSA-OAEP-2048 (descifrar) | 92.137 ms — **2,175× más lento** |

### Sobrecarga de comunicación

| Estructura | PQC | Clásico |
|---|---|---|
| Clave pública de elección | ~1,184 bytes | ~294 bytes |
| Firma digital | ~3,309 bytes | ~72 bytes |
| **Paquete de voto total** | **~16,200 bytes** | **~1,200 bytes** |

---

##  Fundamentos Teóricos

### Module-LWE (base de seguridad)

Dado $R_q = \mathbb{Z}_q[x]/(x^n+1)$ con $n=256$, $q=3329$, $k=3$ (ML-KEM-768):

$$\mathbf{A} \in R_q^{k \times k},\; \mathbf{s}, \mathbf{e} \in R_q^k \quad \Rightarrow \quad \mathbf{b} = \mathbf{As} + \mathbf{e}$$

Distinguir $(\mathbf{A}, \mathbf{b})$ de uniforme es intractable incluso para computadoras cuánticas.

### Estándares NIST implementados

| Estándar | Algoritmo | Nivel de Seguridad | Uso |
|---|---|---|---|
| FIPS 203 | ML-KEM-768 | 3 (192 bits equiv.) | Encapsulamiento de clave |
| FIPS 204 | ML-DSA-65 | 3 (192 bits equiv.) | Firmas digitales |

---

##  Referencias

1. NIST. *FIPS 203 — Module-Lattice-Based Key-Encapsulation Mechanism Standard*. 2024.
2. NIST. *FIPS 204 — Module-Lattice-Based Digital Signature Standard*. 2024.
3. Bernstein, D.J.; Lange, T. *Post-quantum cryptography*. Nature, 2017.
4. PQClean Project. https://github.com/PQClean/PQClean
5. Schmidt, B. et al. *The TAMARIN Prover for the Symbolic Analysis of Security Protocols*. CAV 2012.

---

*Proyecto de Grado UMSA — Facultad de Ciencias Puras y Naturales — 2026*
