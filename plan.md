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
| F3a | Adaptación de PQClean + validación KAT | ✅ Completado |
| F3b | Capa de protocolo post-cuántico (Python) | ✅ Completado |
| F4 | Protocolo clásico RSA/ECDSA | ✅ Completado |
| F5 | Dashboard Web y Sistema de Demostración Visual | ✅ Completado |
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

## Fase 3a — Adaptación de PQClean + Validación KAT

> **Objetivo:** Adaptar el núcleo criptográfico en C de PQClean y validarlo contra vectores oficiales NIST antes de integrar.

- [x] **3a.1** Clonar el repositorio PQClean y registrar el commit exacto
- [x] **3a.2** Seleccionar e identificar los módulos de interés:
  - `ml-kem-768` (FIPS 203 / ML-KEM, nivel ~AES-192)
  - `ml-dsa-65` (FIPS 204 / ML-DSA, nivel ~AES-192)
- [x] **3a.3** Adaptar el código C sin modificar los algoritmos:
  - Ajustar la API de encapsulamiento/desencapsulamiento para el protocolo
  - Ajustar la API de firma/verificación para el protocolo
- [x] **3a.4** Compilar el núcleo C adaptado (Makefile)
- [x] **3a.5** Descargar los vectores de prueba KAT oficiales del NIST (ACVP):
  - ML-KEM-768 KAT vectors
  - ML-DSA-65 KAT vectors
- [x] **3a.6** Ejecutar los KAT tests sobre la adaptación y documentar:
  - Número de vectores probados (100 KEM + 100 DSA)
  - Resultado (pass/fail)
  - Evidencia de corrección antes de usar en benchmarks
- [x] **3a.7** Guardar resultados en `validacion/kat/`

**Entregable:** `src/pqc/pqclean/` + `validacion/kat/` + registro de commit PQClean

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

**Entregable:** `src/web/` con backend Flask/FastAPI, templates HTML5, assets estáticos (CSS/JS) y servidor ejecutable localmente.

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

## Estructura de carpetas actualizada

```
/protocolo-votacion-pqc
├── tamarin/
│   └── protocolo.spthy
├── src/
│   ├── pqc/                  # Núcleo C adaptado + wrapper Python
│   │   ├── pqclean/
│   │   ├── votante.py
│   │   ├── autoridad_registro.py
│   │   ├── servidor_votacion.py
│   │   ├── autoridad_conteo.py
│   │   └── protocolo_pqc.py
│   ├── clasico/              # Implementación clásica RSA/ECDSA
│   │   ├── votante_clasico.py
│   │   ├── autoridad_registro_clasico.py
│   │   ├── servidor_votacion_clasico.py
│   │   ├── autoridad_conteo_clasico.py
│   │   └── protocolo_clasico.py
│   └── web/                  # 🌟 Dashboard Web y API de Demostración
│       ├── app.py            # API Backend (FastAPI / Flask)
│       ├── static/           # CSS, JS interactivo, librerías de gráficos
│       └── templates/        # Vistas: Admin, Registro, Mesa de Votación, Dashboard
├── validacion/
│   └── kat/                  # Vectores NIST + resultados
├── benchmarks/
│   ├── runner.py
│   └── resultados/
├── analisis/
│   └── estadistica.py
├── docs/
│   ├── arquitectura.md
│   └── diagrama_flujo.*
├── Makefile
└── README.md
```

---

## Dependencias entre fases

```
F1 (Diseño) ──► F2 (Tamarin)
            ──► F3a (PQClean KAT) ──► F3b (Protocolo PQC) ──┐
            ──► F4 (Protocolo clásico) ─────────────────────┼──► F5 (Dashboard Web)
                                                            ├──► F6 (Benchmarks) ──► F7 (Estadística)
                                                            └──► F8 (Documentación)
```

---

*Última actualización: 2026-08-26*
