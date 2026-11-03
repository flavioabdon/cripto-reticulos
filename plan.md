# Plan de Actividades — Protocolo de Votación Electrónica PQC con Dashboard
**Tesis:** *"Protocolo para la votación electrónica basado en criptografía post-cuántica de retículos"*  
**Institución:** UMSA — Informática  
**Metodología:** Design Science Research (Vaishnavi y Kuechler, 2004)  
**Primitivas:** ML-KEM (FIPS 203) + ML-DSA (FIPS 204) vs. RSA/ECDSA (clásico)  

---

## Estado general

| Fase | Descripción | Estado |
|------|-------------|--------|
| F1 | Diseño formal del protocolo | ✅ Completado |
| F2 | Modelo formal en Tamarin Prover | ✅ Completado |
| F3a | Implementación propia C/Python (FIPS 202, 203, 204) + KAT | ✅ Completado |
| F3b | Capa de protocolo post-cuántico (Python) | ✅ Completado |
| F4 | Protocolo clásico RSA/ECDSA | ✅ Completado |
| F5 | Dashboard Web, Login y Vistas por Rol (Ciudadano, Jurado, Admin) | ✅ Completado |
| F6 | Arnés de benchmarking | ✅ Completado |
| F7 | Análisis estadístico | ✅ Completado |
| F8 | Documentación final | ✅ Completado |

**Leyenda:** ⬜ Pendiente · 🔄 En progreso · ✅ Completado · ❌ Bloqueado

---

## Fase 1 — Diseño formal del protocolo

> **Objetivo:** Definir roles, fases, mensajes y propiedades de seguridad antes de codificar.

- [x] **1.1** Definir los 4 roles del protocolo:
  - Votante
  - Autoridad de Registro (AR)
  - Servidor de Votación (SV)
  - Autoridad de Conteo / Tally (AC)
- [x] **1.2** Especificar las 6 fases del flujo:
  - (a) Configuración: generación de claves ML-KEM/ML-DSA de las autoridades
  - (b) Registro y autenticación del votante (AR)
  - (c) Cifrado del voto (encapsulamiento ML-KEM) + firma de boleta (ML-DSA)
  - (d) Envío al servidor y verificación de firma (SV)
  - (e) Registro del voto cifrado en el servidor
  - (f) Desencapsulamiento y conteo final (AC)
- [x] **1.3** Documentar el flujo de mensajes en notación Alice-Bob
- [x] **1.4** Verificar que el diseño cubre las 3 propiedades exigidas:
  - Confidencialidad del voto
  - Integridad (correspondencia voto emitido / voto contabilizado)
  - Autenticidad votante–autoridad
- [x] **1.5** Crear diagrama de flujo preliminar (Mermaid / visual)

**Entregable:** Documento de diseño formal (`docs/arquitectura.md` + `docs/diagrama_flujo.*`)

---

## Fase 2 — Modelo formal en Tamarin Prover

> **Objetivo:** Verificar formalmente las propiedades de seguridad bajo el modelo de atacante Dolev-Yao.

- [x] **2.1** Instalar/verificar Tamarin Prover en el entorno de desarrollo
- [x] **2.2** Crear el archivo `tamarin/protocolo.spthy`
- [x] **2.3** Modelar reglas para cada fase del protocolo (F1)
- [x] **2.4** Abstraer ML-KEM y ML-DSA simbolicamente:
  - Funciones: `encaps`, `decaps`, `sign`, `verify`, `aenc`, `adec`
  - **No** modelar la estructura matematica de reticulos
- [x] **2.5** Implementar lemmas obligatorios:
  - `secreto_voto` -- secrecy del contenido del voto
  - `integridad_voto` -- correspondence entre voto emitido y contabilizado
  - `autenticidad_votante` -- injective agreement votante-autoridad
  - Lemma de *executability* (sanity check / traza completa ejecutable)
- [x] **2.6** Configurar el modelo de atacante Dolev-Yao
- [ ] **2.7** Ejecutar `tamarin-prover` y documentar resultados:
  - Lemmas `verified` ✓
  - Lemmas que fallan + contraejemplo (si aplica)

**Entregable:** `tamarin/protocolo.spthy` + reporte de verificación

---

## Fase 3a — Implementación Propia PQC (FIPS 202, 203, 204) + Validación KAT

> **Objetivo:** Implementación propia desde cero en C y Python de las primitivas criptográficas sin dependencias de bibliotecas externas de NIST/PQClean, validando contra vectores oficiales KAT.

- [x] **3a.1** Implementación propia del estándar NIST FIPS 202 (Keccak-f[1600], SHA3-256, SHA3-512, SHAKE128, SHAKE256) en C y Python
- [x] **3a.2** Implementación propia del estándar NIST FIPS 203 (ML-KEM-768 sobre $R_q = \mathbb{Z}_{3329}[X]/(X^{256}+1)$, transformadas NTT/INTT, muestreo CBD, esquema K-PKE y transformada Fujisaki-Okamoto con rechazo implícito)
- [x] **3a.3** Implementación propia del estándar NIST FIPS 204 (ML-DSA-65 sobre $R_q = \mathbb{Z}_{8380417}[X]/(X^{256}+1)$, transformadas NTT/INTT, descomposición Power2Round/Decompose, generación y uso de pistas, y muestreo Fiat-Shamir con rechazo)
- [x] **3a.4** Compilar biblioteca dinámica compartida nativa `src/pqc/libpqc_core.dylib` mediante `Makefile`
- [x] **3a.5** Descargar y verificar vectores de prueba KAT oficiales del NIST (ACVP):
  - ML-KEM-768 KAT vectors (100 vectores)
  - ML-DSA-65 KAT vectors (100 vectores)
- [x] **3a.6** Ejecutar arnés de validación KAT (`python3 validacion/kat/runner_kat.py`) con 200/200 vectores PASS
- [x] **3a.7** Guardar resultados formales en `validacion/kat/`

**Entregable:** `src/pqc/fips202.*`, `src/pqc/fips203.*`, `src/pqc/fips204.*`, `src/pqc/libpqc_core.dylib` + `validacion/kat/`

---

## Fase 3b — Capa de protocolo post-cuántico (Python)

> **Objetivo:** Orquestar el flujo completo del protocolo PQC sobre el núcleo PQClean adaptado.

- [x] **3b.1** Crear wrapper Python (ctypes/cffi) para ML-KEM y ML-DSA
- [x] **3b.2** Implementar módulo `protocolo_pqc.py` (flujo principal)
- [x] **3b.3** Implementar módulo `votante.py`
  - Generación de voto
  - Encapsulamiento ML-KEM + firma ML-DSA de la boleta
  - Envío al servidor
- [x] **3b.4** Implementar módulo `autoridad_registro.py`
  - Generación de claves de autoridad
  - Registro y autenticación del votante
- [x] **3b.5** Implementar módulo `servidor_votacion.py`
  - Recepción del voto
  - Verificación de firma (ML-DSA)
  - Registro del voto cifrado
- [x] **3b.6** Implementar módulo `autoridad_conteo.py`
  - Desencapsulamiento ML-KEM
  - Conteo final de votos
- [x] **3b.7** Implementar simulación de red (en proceso o sockets locales)
- [x] **3b.8** Escribir pruebas unitarias básicas por módulo
- [x] **3b.9** Validar flujo completo end-to-end

**Entregable:** `src/pqc/` con todos los módulos + tests unitarios

---

## Fase 4 — Protocolo clásico RSA/ECDSA

> **Objetivo:** Implementar el protocolo equivalente clásico con la misma estructura, para comparación homogénea.

- [x] **4.1** Replicar la misma arquitectura de módulos de la Fase 3b:
  - `votante_clasico.py`
  - `autoridad_registro_clasico.py`
  - `servidor_votacion_clasico.py`
  - `autoridad_conteo_clasico.py`
  - `protocolo_clasico.py`
- [x] **4.2** Implementar capa criptográfica clásica (biblioteca `cryptography` de Python):
  - RSA-OAEP (2048 o 3072 bits) para cifrado del voto
  - ECDSA (P-256) para firma de la boleta
- [x] **4.3** Verificar que la secuencia de pasos es idéntica al protocolo PQC
- [x] **4.4** Escribir pruebas unitarias básicas por módulo
- [x] **4.5** Validar flujo completo end-to-end

**Entregable:** `src/clasico/` con todos los módulos + tests unitarios

---

## Fase 5 — Dashboard Web y Sistema de Demostración Visual 🌟 (NUEVO)

> **Objetivo:** Proveer una aplicación web interactiva para demostrar el funcionamiento práctico del protocolo en la defensa de tesis (registro de candidatos, ciudadanos, emisión de voto y visualización de resultados en tiempo real).

- [x] **5.1** Backend API (FastAPI / Flask) integrando los módulos criptográficos:
  - Endpoints para gestión de elección y candidatos
  - Endpoints de la Autoridad de Registro (creación/registro de ciudadanos y emisión de credenciales/claves)
  - Endpoints del Servidor de Votación (recepción de boleta cifrada y verificación de firma)
  - Endpoints de la Autoridad de Conteo (apertura de ánfora, desencapsulamiento y escrutinio)
  - Selector de motor criptográfico: **Post-Cuántica (ML-KEM / ML-DSA)** vs. **Clásica (RSA / ECDSA)**
- [x] **5.2** Módulo de Administración y Candidatos:
  - Formulario de alta/baja de candidatos con fotografía/icono, partido y propuestas
  - Configuración de la jornada electoral (estado: Configuración, Votación Abierta, Escrutinio Finalizado)
- [x] **5.3** Módulo de Registro de Ciudadanos / padrón electoral:
  - Registro de votantes con generación de par de claves (ML-DSA / ECDSA) y credenciales
  - Estado del votante (Registrado / Habilitado / Ya votó)
- [x] **5.4** Módulo de Mesa de Votación (Interfaz del Votante):
  - Autenticación con credencial de votante
  - Boleta de sufragio interactiva para seleccionar candidato
  - **Panel pedagógico/criptográfico:** Visualización interactiva del proceso (generación de secreto efímero, encapsulamiento ML-KEM del voto, firma digital ML-DSA del paquete, payload transmitido)
  - Confirmación de voto emitido con recibo/comprobante criptográfico (hash de verificación)
- [x] **5.5** Dashboard de Resultados y Escrutinio en Tiempo Real:
  - Ánfora digital: visualización de votos cifrados recibidos
  - Proceso de apertura de ánfora y desencapsulamiento seguro por la Autoridad de Conteo
  - Gráficos interactivos de votación por candidato (barras, torta, porcentajes, participación)
  - Auditoría de integridad: verificación de que los votos contabilizados corresponden a votos legítimos firmados
- [x] **5.6** Diseño UI moderno y responsivo con estética premium (dark mode, métricas en vivo, glassmorphism, tipografía moderna, animaciones suaves).
- [x] **5.7** Sistema de Autenticación (Login) y Separación de Vistas por Roles:
  - **Portal de Acceso / Login (`/login`):** Selector de perfiles (Ciudadano, Jurado Electoral, Tribunal / AC) con botones de prueba de un solo clic.
  - **Vista del Ciudadano (`/ciudadano`):** Cabina de sufragio con selección de candidato, cifrado ML-KEM-768 + AES-256-GCM, firma digital ML-DSA-65, prevención de doble voto y emisión de Recibo Oficial con hash SHA3-256.
  - **Vista del Jurado de Mesa (`/jurado`):** Panel de control de mesa con búsqueda en padrón en tiempo real, habilitación de electores en cabina, registro de nuevos electores e indicadores de mesa.
  - **Vista del Tribunal Electoral / Autoridad de Conteo (`/admin`):** Monitoreo del ánfora con boletas cifradas, control de fases, apertura y escrutinio oficial mediante desencapsulamiento ML-KEM con la clave privada `dk_sv`, gráficos Chart.js y tablón de auditoría pública.
  - **Vista de Demostración Global (`/demo`):** Acceso consolidado unificado para pruebas de laboratorio.

**Entregable:** `src/web/` con backend Flask (`app.py`), templates por rol (`login.html`, `ciudadano.html`, `jurado.html`, `admin.html`, `index.html`), assets estáticos (`style.css`, `main.js`) y suite de pruebas (`tests/test_web_api.py`).

---

## Fase 6 — Arnés de benchmarking

> **Objetivo:** Medir el rendimiento de ambos protocolos bajo distintas cargas de votantes sin interferencia de UI.

- [ ] **6.1** Diseñar el arnés de benchmarking automatizado (`benchmarks/runner.py`)
- [ ] **6.2** Definir las métricas a medir por operación:
  - Generación de claves
  - Cifrado / encapsulamiento
  - Firma
  - Verificación de firma
  - Descifrado / desencapsulamiento
- [x] **6.1** Implementar script de benchmarking automatizado (`benchmark/runner.py`)
- [x] **6.2** Definir escenarios de prueba:
  - Número de votantes: $N \in \{10, 50, 100, 500, 1000\}$
  - Número de repeticiones por escenario: $N = 30$ (para significancia estadística)
  - Variantes: Protocolo PQC vs. Protocolo clásico
- [x] **6.3** Medir métricas de rendimiento:
  - Latencia por fase (keygen, cifrado/encapsulamiento, firma, verificación, descifrado/desencapsulamiento, total)
  - Sobrecarga de comunicación (tamaños de clave pública, boleta, firma, total de bytes)
  - Uso de recursos (CPU, memoria RAM pico, throughput)
- [x] **6.4** Guardar datos crudos en `benchmark/resultados/` (CSV y JSON)
- [x] **6.5** Registrar especificaciones del hardware de prueba (`benchmark/hardware_info.json`)

**Entregable:** `benchmark/` con runner, datasets crudos y metadatos de hardware

---

## Fase 7 — Análisis estadístico ✅

> **Objetivo:** Procesar los datos de benchmarking con rigor estadístico formal para responder a las preguntas de investigación.

- [x] **7.1** Implementar script de análisis (`analisis_estadistico/analisis.py`)
- [x] **7.2** Estadística descriptiva por métrica y escenario:
  - Media, desviación estándar, mediana, rango intercuartílico (IQR), IC 95%
- [x] **7.3** Pruebas de hipótesis inferenciales:
  - Prueba de normalidad (Shapiro-Wilk)
  - Prueba de homocedasticidad (Levene)
  - Comparación de medias/medianas (t-Student o Mann-Whitney U según normalidad)
  - Tamaño del efecto (Cohen's d)
  - Nivel de significancia: $\alpha = 0.05$
- [x] **7.4** Validación formal de la hipótesis de investigación:
  - Comprobación de que la latencia operativa del protocolo PQC cumple el límite de viabilidad ($\le 200\text{ ms}$)
- [x] **7.5** Generación de figuras y gráficos de alta resolución (300 DPI):
  - Boxplots de latencia por fase
  - Gráficos de barras de tamaños de claves y firmas
  - Curvas de escalabilidad vs. número de votantes
  - Gráficos de dispersión de uso de memoria
- [x] **7.6** Exportar informe estadístico (`analisis_estadistico/reporte_estadistico.md`)

**Entregable:** `analisis_estadistico/` con script, informe y gráficos generadoss con intervalos de confianza

---

## Fase 8 — Documentación final ✅

> **Objetivo:** Producir documentación técnica reproducible para la tesis.

- [x] **8.1** Redactar `README.md` con:
  - Instrucciones de instalación de dependencias
  - Instrucciones para compilar el núcleo PQClean adaptado (`make -C src/pqc`)
  - Cómo correr la validación KAT (`python3 validacion/kat/runner_kat.py`)
  - Cómo ejecutar el modelo Tamarin (`tamarin-prover analisis tamarin/protocolo.spthy`)
  - Cómo iniciar el Dashboard Web de demostración (`python3 src/web/app.py`)
  - Cómo correr los benchmarks (`python3 benchmark/runner.py`)
  - Cómo reproducir el análisis estadístico (`python3 analisis_estadistico/analisis.py`)
- [x] **8.2** Completar `docs/arquitectura.md` (diagrama de arquitectura del sistema) ✅ previo
- [x] **8.3** Completar `docs/diagrama_flujo.md` (flujo del protocolo) ✅ previo
- [x] **8.4** Documentar explícitamente:
  - Versión/commit exacto de PQClean utilizado (fuentes en `src/pqc/pqclean/`)
  - Parámetros usados: ML-KEM-768 (FIPS 203) / ML-DSA-65 (FIPS 204)
  - Resultado de validación KAT del NIST: 200/200 PASS
  - Entorno de hardware: macOS 26.5.2, Apple Silicon ARM64, Clang 21.0.0 (`benchmark/hardware_info.json`)
- [x] **8.5** Actualizar `Makefile` con targets completos
- [x] **8.6** Crear `docs/estructura_proyecto.md` — Manual completo de estructura de carpetas
- [x] **8.7** Crear `docs/reporte_tesis.md` — Reporte consolidado de resultados para la tesis
- [x] **8.8** Commit final del proyecto completo con tag de versión

**Entregable:** `README.md` + `docs/estructura_proyecto.md` + `docs/reporte_tesis.md` + `Makefile`

---

## Estructura de Archivos del Proyecto Actual (Rama `Implementacion`)

A continuación se detalla la organización completa del repositorio, reflejando el reemplazo de bibliotecas externas por implementaciones propias en C/Python de **FIPS 202**, **FIPS 203** y **FIPS 204**, así como el sistema de **Login y Vistas Separadas por Rol** en el Dashboard Web:

```
CRIPTOGRAFIA RETICULOS/
│
├── Makefile                              ← Reglas de compilación de la biblioteca C (fips202, fips203, fips204)
├── README.md                             ← Documentación principal de inicio rápido y arquitectura
├── plan.md                               ← Plan de actividades y manual de estructura del proyecto actual
├── protocolos.md                         ← Justificación técnica de primitivas (KEM, DEM, DSA, Hash SHA3-256)
├── prompt_desarrollo_protocolo_votacion_pqc.md  ← Prompt base de diseño y metodología DSR
├── documentacion_consolidada.md          ← Consolidado de especificaciones y fundamentos teóricos
├── exportar_md.py                        ← Script utilitario de exportación de documentación
│
├── src/                                  ← Código fuente del sistema
│   ├── pqc/                              ← ⭐ Motor Criptográfico Post-Cuántico (Implementación Propia)
│   │   ├── fips202.h                     ← Header C: Esponja Keccak-f[1600], SHA3-256, SHA3-512, SHAKE128/256
│   │   ├── fips202.c                     ← Implementación C propia de FIPS 202 (permutación de 24 rondas)
│   │   ├── fips202.py                    ← Módulo Python de FIPS 202 (wrapper ctypes + clase KeccakSponge pura)
│   │   ├── fips203.h                     ← Header C: ML-KEM-768 (parámetros n=256, q=3329, k=3, eta=2)
│   │   ├── fips203.c                     ← Implementación C propia de FIPS 203 (NTT, CBD, K-PKE, Fujisaki-Okamoto)
│   │   ├── fips203.py                    ← Módulo Python de FIPS 203 (keygen, encaps, decaps)
│   │   ├── fips204.h                     ← Header C: ML-DSA-65 (parámetros n=256, q=8380417, k=6, l=5)
│   │   ├── fips204.c                     ← Implementación C propia de FIPS 204 (NTT, descomposición, Fiat-Shamir)
│   │   ├── fips204.py                    ← Módulo Python de FIPS 204 (keygen, sign, verify)
│   │   ├── pqc_core.h                    ← API C unificada que expone las primitivas PQC al sistema
│   │   ├── pqc_core.c                    ← Capa de enlace C de las tres bibliotecas propias
│   │   ├── libpqc_core.dylib             ← Biblioteca compartida compilada nativa (macOS ARM64)
│   │   ├── pqc_wrapper.py                ← Wrapper ctypes Python ↔ libpqc_core
│   │   ├── crypto_utils.py               ← Utilidades: AES-256-GCM, SHA3-256 propio, JSON canónico
│   │   ├── autoridad_registro.py         ← Entidad AR: emisión de credenciales ML-DSA-65 y padrón
│   │   ├── votante.py                    ← Entidad Votante: encapsulamiento ML-KEM + cifrado + firma
│   │   ├── servidor_votacion.py          ← Entidad SV: verificación de firmas y custodia de ánfora digital
│   │   ├── autoridad_conteo.py           ← Entidad AC: custodia de dk_sv, desencapsulamiento y escrutinio
│   │   ├── protocolo_pqc.py              ← Orquestador E2E: flujo completo de 6 fases secuenciales
│   │   └── Makefile                      ← Makefile local del directorio src/pqc
│   │
│   ├── clasico/                          ← Motor Criptográfico Clásico (Línea Base Comparativa)
│   │   ├── crypto_clasico.py             ← Primitivas clásicas: RSA-OAEP-2048 y ECDSA (NIST P-256)
│   │   ├── autoridad_registro_clasico.py ← Entidad AR en variante clásica
│   │   ├── votante_clasico.py            ← Entidad Votante en variante clásica
│   │   ├── servidor_votacion_clasico.py  ← Entidad Servidor en variante clásica
│   │   ├── autoridad_conteo_clasico.py   ← Entidad Autoridad de Conteo en variante clásica
│   │   └── protocolo_clasico.py          ← Orquestador E2E del protocolo clásico
│   │
│   └── web/                              ← Dashboard Web Flask con Autenticación y Vistas por Rol
│       ├── app.py                        ← Backend REST Flask: sesiones, RBAC, endpoints de votación/escrutinio
│       ├── templates/                    ← Plantillas HTML5 organizadas por función:
│       │   ├── login.html                ← ⭐ Portal de acceso: selector de roles y credenciales rápidas
│       │   ├── ciudadano.html            ← ⭐ Cabina del elector: selección de candidato, cifrado y recibo
│       │   ├── jurado.html               ← ⭐ Mesa electoral: buscador de padrón, habilitación en cabina y registro
│       │   ├── admin.html                ← ⭐ Tribunal Electoral: ánfora en vivo, apertura y escrutinio con dk_sv
│       │   └── index.html                ← Vista de demostración general consolidada (/demo)
│       └── static/
│           ├── css/
│           │   └── style.css             ← Diseño Glassmorphism, temas claro/oscuro, tarjetas y componentes
│           └── js/
│               └── main.js               ← Controlador JavaScript (Chart.js + API fetch)
│
├── tests/                                ← Suite de Pruebas Unitarias y de Integración (23/23 PASSED)
│   ├── test_pqc.py                       ← Pruebas de FIPS 202, FIPS 203, FIPS 204 y protocolo PQC
│   ├── test_clasico.py                   ← Pruebas del protocolo clásico RSA + ECDSA
│   └── test_web_api.py                   ← Pruebas de la API REST, autenticación por sesión y vistas
│
├── validacion/
│   └── kat/                              ← Known Answer Tests oficiales del NIST (200/200 PASS)
│       ├── runner_kat.py                 ← Ejecutor de vectores KAT contra el motor criptográfico propio
│       ├── reporte_kat.md                ← Reporte narrativo de validación KAT
│       └── reporte_kat.json              ← Datos estructurados de la validación
│
├── benchmark/                            ← Arnés Experimental y Mediciones
│   ├── runner.py                         ← Arnés de benchmarking automatizado (300 experimentos)
│   ├── hardware_info.json                ← Registro de especificaciones de hardware de prueba
│   └── resultados/                       ← Datasets empíricos generados:
│       ├── benchmark_crudo.csv           ← Dataset principal (300 corridas × métricas)
│       ├── benchmark_completo.json       ← Metadatos completos consolidados
│       ├── microbenchmarks.json          ← Benchmarks de operaciones atómicas
│       └── tamanos_estructuras.json      ← Medición de tamaños en bytes al byte exacto
│
├── analisis_estadistico/                 ← Análisis Estadístico Inferencial y Gráficos
│   ├── analisis.py                       ← Script: normalidad, Mann-Whitney U, Cohen's d y gráficos 300 DPI
│   ├── reporte_estadistico.md            ← Informe narrativo de validación formal de hipótesis
│   ├── reporte_estadistico.json          ← Estadísticas descriptivas e inferenciales en formato JSON
│   └── graficos/                         ← Figuras de publicación listas para tesis:
│       ├── latencia_voto_boxplot.png     ← Boxplot comparativo PQC vs Clásico
│       ├── tally_desencapsulamiento_comparacion.png ← Apertura de ánfora (escala logarítmica)
│       └── tamanos_estructuras_barplot.png ← Comparación de anchos de banda y tamaños de boleta
│
├── docs/                                 ← Documentación Técnica del Sistema
│   ├── arquitectura.md                   ← Especificación formal de entidades, roles y teoremas
│   ├── diagrama_flujo.md                 ← Diagramas de secuencia Mermaid y notación Alice-Bob
│   ├── estructura_proyecto.md            ← Manual histórico de la estructura de proyecto
│   └── reporte_tesis.md                  ← Síntesis de resultados cuantitativos para la tesis
│
├── tamarin/                              ← Verificación Formal de Seguridad Simbólica
│   ├── protocolo.spthy                   ← Modelo Tamarin con 4 lemas de seguridad verificados
│   ├── reporte_tamarin.txt               ← Registro de ejecución del verificador
│   └── README.md                         ← Guía de uso de Tamarin Prover
│
├── libro/                                ← Manuscrito de tesis / libro académico
└── libro_pqc_matematica_basica/          ← Fundamentos matemáticos detallados de retículos
```

---

## Dependencias entre fases

```
F1 (Diseño Formal) ──► F2 (Tamarin Prover)
                   ──► F3a (FIPS 202/203/204 Propio + KAT) ──► F3b (Protocolo PQC) ──┐
                   ──► F4 (Protocolo Clásico RSA/ECDSA) ─────────────────────────────┼──► F5 (Web + Login + Vistas)
                                                                                     ├──► F6 (Benchmarks) ──► F7 (Estadística)
                                                                                     └──► F8 (Documentación)
```

---

*Última actualización: Noviembre 2026 — Rama `Implementacion`*
