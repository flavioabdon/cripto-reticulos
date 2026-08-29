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
| F2 | Modelo formal en Tamarin Prover | 🔄 En progreso |
| F3a | Adaptación de PQClean + validación KAT | ⬜ Pendiente |
| F3b | Capa de protocolo post-cuántico (Python) | ⬜ Pendiente |
| F4 | Protocolo clásico RSA/ECDSA | ⬜ Pendiente |
| F5 | Dashboard Web y Sistema de Demostración Visual | ⬜ Pendiente |
| F6 | Arnés de benchmarking | ⬜ Pendiente |
| F7 | Análisis estadístico | ⬜ Pendiente |
| F8 | Documentación final | ⬜ Pendiente |

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

- [ ] **3a.1** Clonar el repositorio PQClean y registrar el commit exacto
- [ ] **3a.2** Seleccionar e identificar los módulos de interés:
  - `ml-kem-768` (FIPS 203 / ML-KEM, nivel ~AES-192)
  - `ml-dsa-65` (FIPS 204 / ML-DSA, nivel ~AES-192)
- [ ] **3a.3** Adaptar el código C sin modificar los algoritmos:
  - Ajustar la API de encapsulamiento/desencapsulamiento para el protocolo
  - Ajustar la API de firma/verificación para el protocolo
- [ ] **3a.4** Compilar el núcleo C adaptado (Makefile)
- [ ] **3a.5** Descargar los vectores de prueba KAT oficiales del NIST (ACVP):
  - ML-KEM-768 KAT vectors
  - ML-DSA-65 KAT vectors
- [ ] **3a.6** Ejecutar los KAT tests sobre la adaptación y documentar:
  - Número de vectores probados
  - Resultado (pass/fail)
  - Evidencia de corrección antes de usar en benchmarks
- [ ] **3a.7** Guardar resultados en `validacion/kat/`

**Entregable:** `src/pqc/pqclean/` + `validacion/kat/` + registro de commit PQClean

---

## Fase 3b — Capa de protocolo post-cuántico (Python)

> **Objetivo:** Orquestar el flujo completo del protocolo PQC sobre el núcleo PQClean adaptado.

- [ ] **3b.1** Crear wrapper Python (ctypes/cffi) para ML-KEM y ML-DSA
- [ ] **3b.2** Implementar módulo `protocolo_pqc.py` (flujo principal)
- [ ] **3b.3** Implementar módulo `votante.py`
  - Generación de voto
  - Encapsulamiento ML-KEM + firma ML-DSA de la boleta
  - Envío al servidor
- [ ] **3b.4** Implementar módulo `autoridad_registro.py`
  - Generación de claves de autoridad
  - Registro y autenticación del votante
- [ ] **3b.5** Implementar módulo `servidor_votacion.py`
  - Recepción del voto
  - Verificación de firma (ML-DSA)
  - Registro del voto cifrado
- [ ] **3b.6** Implementar módulo `autoridad_conteo.py`
  - Desencapsulamiento ML-KEM
  - Conteo final de votos
- [ ] **3b.7** Implementar simulación de red (en proceso o sockets locales)
- [ ] **3b.8** Escribir pruebas unitarias básicas por módulo
- [ ] **3b.9** Validar flujo completo end-to-end

**Entregable:** `src/pqc/` con todos los módulos + tests unitarios

---

## Fase 4 — Protocolo clásico RSA/ECDSA

> **Objetivo:** Implementar el protocolo equivalente clásico con la misma estructura, para comparación homogénea.

- [ ] **4.1** Replicar la misma arquitectura de módulos de la Fase 3b:
  - `votante_clasico.py`
  - `autoridad_registro_clasico.py`
  - `servidor_votacion_clasico.py`
  - `autoridad_conteo_clasico.py`
  - `protocolo_clasico.py`
- [ ] **4.2** Implementar capa criptográfica clásica (biblioteca `cryptography` de Python):
  - RSA-OAEP (2048 o 3072 bits) para cifrado del voto
  - ECDSA (P-256) para firma de la boleta
- [ ] **4.3** Verificar que la secuencia de pasos es idéntica al protocolo PQC
- [ ] **4.4** Escribir pruebas unitarias básicas por módulo
- [ ] **4.5** Validar flujo completo end-to-end

**Entregable:** `src/clasico/` con todos los módulos + tests unitarios

---

## Fase 5 — Dashboard Web y Sistema de Demostración Visual 🌟 (NUEVO)

> **Objetivo:** Proveer una aplicación web interactiva para demostrar el funcionamiento práctico del protocolo en la defensa de tesis (registro de candidatos, ciudadanos, emisión de voto y visualización de resultados en tiempo real).

- [ ] **5.1** Backend API (FastAPI / Flask) integrando los módulos criptográficos:
  - Endpoints para gestión de elección y candidatos
  - Endpoints de la Autoridad de Registro (creación/registro de ciudadanos y emisión de credenciales/claves)
  - Endpoints del Servidor de Votación (recepción de boleta cifrada y verificación de firma)
  - Endpoints de la Autoridad de Conteo (apertura de urna, desencapsulamiento y escrutinio)
  - Selector de motor criptográfico: **Post-Cuántica (ML-KEM / ML-DSA)** vs. **Clásica (RSA / ECDSA)**
- [ ] **5.2** Módulo de Administración y Candidatos:
  - Formulario de alta/baja de candidatos con fotografía/icono, partido y propuestas
  - Configuración de la jornada electoral (estado: Configuración, Votación Abierta, Escrutinio Finalizado)
- [ ] **5.3** Módulo de Registro de Ciudadanos / Padrón:
  - Registro de votantes con generación de par de claves (ML-DSA / ECDSA) y credenciales
  - Estado del votante (Registrado / Habilitado / Ya votó)
- [ ] **5.4** Módulo de Cabina de Votación (Interfaz del Votante):
  - Autenticación con credencial de votante
  - Boleta de sufragio interactiva para seleccionar candidato
  - **Panel pedagógico/criptográfico:** Visualización interactiva del proceso (generación de secreto efímero, encapsulamiento ML-KEM del voto, firma digital ML-DSA del paquete, payload transmitido)
  - Confirmación de voto emitido con recibo/comprobante criptográfico (hash de verificación)
- [ ] **5.5** Dashboard de Resultados y Escrutinio en Tiempo Real:
  - Urna digital: visualización de votos cifrados recibidos
  - Proceso de apertura de urna y desencapsulamiento seguro por la Autoridad de Conteo
  - Gráficos interactivos de votación por candidato (barras, torta, porcentajes, participación)
  - Auditoría de integridad: verificación de que los votos contabilizados corresponden a votos legítimos firmados
- [ ] **5.6** Diseño UI moderno y responsivo con estética premium (dark mode/light mode, métricas en vivo)

**Entregable:** `src/web/` (Backend API + Frontend Dashboard)

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
  - Latencia total end-to-end
  - Consumo de memoria (pico y promedio)
- [ ] **6.3** Configurar los escenarios de carga (votantes simulados):
  - 10, 50, 100, 500, 1000, 5000 votantes (ajustable)
- [ ] **6.4** Repetir cada medición N=30 veces para robustez estadística
- [ ] **6.5** Exportar resultados en CSV/JSON a `benchmarks/resultados/`
- [ ] **6.6** Documentar el entorno de hardware (CPU, RAM, OS)
- [ ] **6.7** Verificar meta de latencia ≤ 200 ms (objetivo de la tesis)

**Entregable:** `benchmarks/runner.py` + `benchmarks/resultados/` (CSV/JSON)

---

## Fase 7 — Análisis estadístico

> **Objetivo:** Comparar estadísticamente el rendimiento PQC vs. clásico y generar evidencia para la hipótesis.

- [ ] **7.1** Implementar script/notebook de análisis (`analisis/estadistica.py` o `.ipynb`)
- [ ] **7.2** Verificar supuestos para cada métrica:
  - Normalidad: prueba Shapiro-Wilk
  - Homogeneidad de varianzas: prueba de Levene
- [ ] **7.3** Aplicar prueba estadística según supuestos:
  - Si se cumplen → t-Student (dos muestras independientes, dos colas)
  - Si **no** se cumplen → Mann-Whitney U (alternativa no paramétrica)
- [ ] **7.4** Generar tablas resumen por métrica y por número de votantes
- [ ] **7.5** Generar gráficos comparativos:
  - Boxplots (PQC vs. clásico por métrica)
  - Barras con intervalos de confianza
  - Curvas de escalabilidad por número de votantes
- [ ] **7.6** Interpretar resultados en relación a la hipótesis de la tesis

**Entregable:** `analisis/estadistica.py` + gráficos + tablas de resultados

---

## Fase 8 — Documentación final

> **Objetivo:** Producir documentación técnica reproducible para la tesis.

- [ ] **8.1** Redactar `README.md` con:
  - Instrucciones de instalación de dependencias
  - Instrucciones para compilar el núcleo PQClean adaptado
  - Cómo correr la validación KAT
  - Cómo ejecutar el modelo Tamarin
  - Cómo iniciar el Dashboard Web de demostración
  - Cómo correr los benchmarks
  - Cómo reproducir el análisis estadístico
- [ ] **8.2** Completar `docs/arquitectura.md` (diagrama de arquitectura del sistema)
- [ ] **8.3** Completar `docs/diagrama_flujo.*` (flujo del protocolo)
- [ ] **8.4** Documentar explícitamente:
  - Versión/commit exacto de PQClean utilizado
  - Parámetros usados: ML-KEM-768 / ML-DSA-65
  - Resultado de validación KAT del NIST
  - Entorno de hardware para benchmarks
- [ ] **8.5** Crear/verificar `Makefile` con targets:
  - `make build` — compilar núcleo PQClean
  - `make kat` — correr validación KAT
  - `make tamarin` — correr Tamarin Prover
  - `make app` — levantar el Dashboard Web
  - `make benchmark` — correr arnés de benchmarks
  - `make analisis` — correr análisis estadístico

**Entregable:** `README.md` + `docs/` + `Makefile`

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
│       └── templates/        # Vistas: Admin, Registro, Cabina Voto, Dashboard
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
