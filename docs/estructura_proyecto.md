# 📁 Manual de Estructura del Proyecto

> **Protocolo de Votación Electrónica Post-Cuántica — UMSA 2026**
> Referencia completa de la organización del repositorio para futuras modificaciones, auditorías y extensiones.

---

## Vista General del Árbol de Directorios

```
CRIPTOGRAFIA RETICULOS/               ← Raíz del proyecto
│
├── README.md                         ← Guía de inicio rápido e introducción
├── plan.md                           ← Plan de desarrollo DSR con estado de fases
├── prompt_desarrollo_protocolo_votacion_pqc.md  ← Prompt original de diseño
├── Makefile                          ← Reglas de compilación para la biblioteca C
│
├── docs/                             ← 📚 Documentación técnica
│   ├── arquitectura.md               ← Especificación formal del protocolo (entidades, fases)
│   ├── diagrama_flujo.md             ← Diagramas Mermaid del flujo de mensajes
│   └── estructura_proyecto.md        ← Este archivo — manual de estructura de carpetas
│
├── src/                              ← 💻 Código fuente principal
│   ├── pqc/                          ← Motor criptográfico post-cuántico
│   │   ├── pqclean/                  ← Fuentes C de PQClean (subárbol)
│   │   │   ├── common/               ← Código compartido entre algoritmos
│   │   │   ├── crypto_kem/           ← Implementación ML-KEM-768 (FIPS 203)
│   │   │   └── crypto_sign/          ← Implementación ML-DSA-65 (FIPS 204)
│   │   ├── pqc_core.h                ← Header C de la API unificada
│   │   ├── pqc_core.c                ← Implementación C de la capa de interfaz
│   │   ├── pqc_core.o                ← Objeto compilado (artefacto de build)
│   │   ├── libpqc_core.dylib         ← ⭐ Biblioteca dinámica compilada (macOS ARM64)
│   │   ├── pqc_wrapper.py            ← Wrapper ctypes Python ↔ C
│   │   ├── crypto_utils.py           ← Utilidades: AES-256-GCM, SHA3-256, KDF
│   │   ├── autoridad_registro.py     ← Lógica de la Autoridad de Registro (PQC)
│   │   ├── votante.py                ← Lógica del Votante (PQC)
│   │   ├── servidor_votacion.py      ← Lógica del Servidor de Votación (PQC)
│   │   ├── autoridad_conteo.py       ← Lógica de la Autoridad de Conteo (PQC)
│   │   └── protocolo_pqc.py          ← Orquestador: flujo completo E2E (PQC)
│   │
│   ├── clasico/                      ← Motor criptográfico clásico (referencia comparativa)
│   │   ├── crypto_clasico.py         ← Primitivas: RSA-OAEP-2048, ECDSA P-256, AES-256-GCM
│   │   ├── autoridad_registro_clasico.py  ← Autoridad de Registro (clásico)
│   │   ├── votante_clasico.py        ← Votante (clásico)
│   │   ├── servidor_votacion_clasico.py   ← Servidor de Votación (clásico)
│   │   ├── autoridad_conteo_clasico.py    ← Autoridad de Conteo (clásico)
│   │   └── protocolo_clasico.py      ← Orquestador E2E (clásico)
│   │
│   └── web/                          ← Dashboard Flask de demostración visual
│       ├── app.py                    ← ⭐ Backend Flask: API REST + rutas HTML
│       ├── templates/
│       │   └── index.html            ← Template maestro con 5 pestañas interactivas
│       └── static/
│           ├── css/
│           │   └── style.css         ← Estilos Glassmorphism / Cyber-Sleek
│           └── js/
│               └── main.js           ← Controlador JavaScript (Chart.js + fetch API)
│
├── benchmark/                        ← 📊 Arnés de benchmarking y resultados empíricos
│   ├── runner.py                     ← ⭐ Script principal de benchmarking automatizado
│   ├── hardware_info.json            ← Especificaciones del hardware de prueba
│   └── resultados/                   ← Datos generados (no modificar manualmente)
│       ├── benchmark_crudo.csv       ← Dataset principal: 300 registros × métricas
│       ├── benchmark_completo.json   ← Consolidado con metadatos completos
│       ├── microbenchmarks.json      ← 100 repeticiones por operación atómica
│       └── tamanos_estructuras.json  ← Tamaños exactos al byte de claves y firmas
│
├── analisis_estadistico/             ← 📈 Análisis estadístico inferencial
│   ├── analisis.py                   ← ⭐ Script: estadística descriptiva + pruebas + gráficos
│   ├── reporte_estadistico.md        ← Informe narrativo con resultados y validación de hipótesis
│   ├── reporte_estadistico.json      ← Datos estructurados del informe (para automatización)
│   └── graficos/                     ← Figuras de publicación (300 DPI, PNG)
│       ├── latencia_voto_boxplot.png           ← Boxplot PQC vs Clásico por escenario
│       ├── tally_desencapsulamiento_comparacion.png  ← Comparación apertura de urna (log-scale)
│       └── tamanos_estructuras_barplot.png     ← Tamaños de estructuras en bytes
│
├── tests/                            ← 🧪 Suite de pruebas (20/20 aprobados)
│   ├── test_pqc.py                   ← Tests unitarios del protocolo PQC
│   ├── test_clasico.py               ← Tests unitarios del protocolo clásico
│   └── test_web_api.py               ← Tests de integración del API web Flask
│
├── tamarin/                          ← 🔬 Verificación formal de seguridad
│   └── protocolo.spthy               ← Modelo Tamarin con 4 lemas verificados
│
├── validacion/                       ← ✅ Vectores de validación NIST
│   └── kat/                          ← Known Answer Tests (FIPS 203 / FIPS 204)
│       ├── runner_kat.py             ← Script de validación KAT
│       ├── reporte_kat.md            ← Informe de resultados KAT
│       └── reporte_kat.json          ← Datos KAT estructurados
│
└── venv/                             ← 🐍 Entorno virtual Python (NO versionar)
```

---

## Descripción Detallada por Módulo

### `src/pqc/` — Motor Criptográfico Post-Cuántico

El núcleo computacional del protocolo. Implementa ML-KEM-768 (FIPS 203) y ML-DSA-65 (FIPS 204) mediante una arquitectura de dos capas:

**Capa C (PQClean):**
- `pqclean/` contiene las implementaciones C de referencia portables y auditadas del proyecto PQClean.
- `pqc_core.h` / `pqc_core.c` definen una API C unificada que expone las primitivas de ambos algoritmos.
- `libpqc_core.dylib` es la biblioteca dinámica compilada para macOS ARM64 (Apple Silicon). En Linux se generaría `libpqc_core.so`.

**Capa Python (wrapper + protocolo):**
- `pqc_wrapper.py` usa `ctypes` para invocar las funciones C desde Python, con gestión automática de buffers y tipos.
- `crypto_utils.py` implementa AES-256-GCM, SHA3-256 y KDF en Python puro usando la librería `cryptography`.
- Cada entidad tiene su propio módulo (`autoridad_registro.py`, `votante.py`, etc.) que encapsula su estado y operaciones.
- `protocolo_pqc.py` es el orquestador de alto nivel que ejecuta el flujo completo de 6 fases.

**Cómo compilar en macOS:**
```bash
make -C src/pqc
# → genera src/pqc/libpqc_core.dylib
```

**Cómo compilar en Linux:**
```bash
cd src/pqc
clang -shared -fPIC -O2 -o libpqc_core.so pqc_core.c pqclean/...
```

---

### `src/clasico/` — Motor Criptográfico Clásico

Implementación del protocolo equivalente usando algoritmos pre-cuánticos:
- **RSA-OAEP-2048** para cifrado de boletas (equivalente funcional de ML-KEM-768).
- **ECDSA P-256** para firmas digitales (equivalente funcional de ML-DSA-65).
- **AES-256-GCM** para cifrado simétrico (compartido con PQC).

Utiliza exclusivamente la librería Python `cryptography` (PyCa). No requiere compilación C.

Propósito: **línea base comparativa** para el análisis estadístico y la validación de la hipótesis.

---

### `src/web/` — Dashboard de Demostración Visual

Aplicación web Flask que permite visualizar el protocolo en acción:

- `app.py`: Define las rutas REST (`/api/vote`, `/api/tally`, `/api/register`, etc.) y sirve el frontend HTML. Soporta modo PQC y Clásico en tiempo real mediante un parámetro de configuración.
- `templates/index.html`: UI de 5 pestañas construida con HTML5 semántico, sin frameworks CSS externos.
- `static/css/style.css`: Diseño Glassmorphism con variables CSS, paleta Cyber-Sleek (púrpura/cian oscuro), animaciones y efectos de hover.
- `static/js/main.js`: Controlador SPA-like que gestiona las 5 pestañas, el inspector criptográfico, el gráfico Chart.js de escrutinio y las llamadas `fetch` al backend.

**Iniciar el servidor:**
```bash
python3 src/web/app.py
# → http://127.0.0.1:5050
```

---

### `benchmark/` — Arnés de Benchmarking

- `runner.py`: Ejecuta experimentos sistemáticos con $N \in \{10, 50, 100, 500, 1000\}$ votantes y $R=30$ repeticiones por variante (PQC y Clásico). Mide: latencia keygen, encapsulamiento, firma, verificación, descifrado, total; tamaños de estructuras; uso de CPU y RAM. Exporta a CSV y JSON.
- `hardware_info.json`: Snapshot de las especificaciones del hardware donde se realizaron los benchmarks.
- `resultados/benchmark_crudo.csv`: **Dataset principal** con 300 registros — es la fuente de datos para el análisis estadístico. No modificar manualmente.

**Regenerar resultados:**
```bash
python3 benchmark/runner.py
```

---

### `analisis_estadistico/` — Análisis Inferencial

- `analisis.py`: Lee `benchmark/resultados/benchmark_crudo.csv`, calcula estadísticas descriptivas (media, DE, mediana, IQR, IC95%), ejecuta pruebas de normalidad (Shapiro-Wilk), homocedasticidad (Levene), comparación de grupos (Mann-Whitney U / t-Student), calcula el tamaño del efecto (Cohen's d), y genera los 3 gráficos de publicación a 300 DPI.
- `reporte_estadistico.md`: Informe narrativo de los resultados con la validación formal de la hipótesis.
- `graficos/`: Figuras PNG listas para insertar en la tesis (resolución 300 DPI, fondo blanco, etiquetas completas).

**Regenerar análisis y gráficos:**
```bash
python3 analisis_estadistico/analisis.py
```

---

### `tests/` — Suite de Pruebas

| Archivo | Cobertura | Tests |
|---|---|---|
| `test_pqc.py` | Protocolo PQC completo | ~8 tests |
| `test_clasico.py` | Protocolo clásico completo | ~7 tests |
| `test_web_api.py` | Endpoints Flask | 5 tests |
| **Total** | | **20/20 PASSED** |

**Ejecutar todos los tests:**
```bash
python3 -m pytest tests/ -v
```

---

### `tamarin/` — Verificación Formal

`protocolo.spthy` especifica el protocolo en el lenguaje de Tamarin Prover y verifica 4 propiedades de seguridad:
1. **Anonimato del votante** — Unlinkability entre identidad y voto.
2. **Integridad del voto** — Ningún adversario puede modificar un voto sin ser detectado.
3. **Imposibilidad de doble voto** — Cada credencial solo puede emitir una boleta válida.
4. **Autenticidad del resultado** — El resultado publicado proviene de la AC legítima.

---

### `validacion/kat/` — Known Answer Tests NIST

Los KAT son vectores de prueba oficiales del NIST para verificar que una implementación produce exactamente la misma salida que la implementación de referencia:

- `runner_kat.py`: Carga los vectores KAT embebidos del NIST, los ejecuta contra `libpqc_core.dylib` y verifica byte a byte.
- Resultado esperado: `100/100 vectores PASS` para ML-KEM-768 y `100/100 vectores PASS` para ML-DSA-65.

---

## Flujo de Dependencias

```
validacion/kat/ ──────────────────────────────────────┐
                                                       ↓
src/pqc/pqclean/ → src/pqc/pqc_core.c → libpqc_core.dylib
                                                ↓
src/pqc/pqc_wrapper.py ← ctypes ──────────────┘
         ↓
src/pqc/{protocolo_pqc.py, votante.py, ...}
         ↓
src/web/app.py → Dashboard HTTP :5050
         ↓
tests/test_web_api.py

src/clasico/{protocolo_clasico.py, ...} ←── benchmark/runner.py ──→ benchmark/resultados/
                                                                              ↓
                                                              analisis_estadistico/analisis.py
                                                                              ↓
                                                              analisis_estadistico/graficos/
```

---

## Convenciones de Nomenclatura

| Patrón | Significado |
|---|---|
| `*_pqc.py` | Módulo del motor post-cuántico (ML-KEM + ML-DSA) |
| `*_clasico.py` | Módulo del motor clásico (RSA + ECDSA) |
| `test_*.py` | Archivo de pruebas (pytest) |
| `runner_*.py` | Script ejecutable de procesamiento en lote |
| `reporte_*.md` | Informe de resultados legible por humanos |
| `reporte_*.json` | Datos estructurados para procesamiento automático |
| `*.dylib` | Biblioteca dinámica compilada (macOS) |
| `*.so` | Biblioteca dinámica compilada (Linux) |

---

## Archivos Importantes de No Modificar

| Archivo | Razón |
|---|---|
| `benchmark/resultados/benchmark_crudo.csv` | Dataset de investigación — fuente de los resultados de la tesis |
| `benchmark/hardware_info.json` | Registro del entorno experimental — necesario para reproducibilidad |
| `validacion/kat/reporte_kat.json` | Evidencia de la validación KAT NIST |
| `src/pqc/libpqc_core.dylib` | Binario compilado — regenerar con `make -C src/pqc` |

---

## Extensión y Mantenimiento Futuro

### Para agregar un nuevo algoritmo PQC (ej. SPHINCS+, FALCON)

1. Añadir las fuentes C en `src/pqc/pqclean/` (nueva subcarpeta).
2. Extender `src/pqc/pqc_core.h` y `pqc_core.c` con las nuevas funciones.
3. Recompilar con `make -C src/pqc`.
4. Extender `src/pqc/pqc_wrapper.py` con los nuevos bindings ctypes.
5. Agregar módulo `src/pqc/protocolo_<algoritmo>.py`.
6. Añadir tests en `tests/test_<algoritmo>.py`.
7. Extender `benchmark/runner.py` con el nuevo escenario.

### Para portar a Linux / Windows

- Linux: Modificar `Makefile` para generar `.so` en lugar de `.dylib`. Ajustar `DYLIB_EXT` en `pqc_wrapper.py`.
- Windows: Usar MinGW o MSVC para compilar `.dll`. Ajustar la lógica `ctypes.cdll.LoadLibrary()` en `pqc_wrapper.py`.

### Para escalar el sistema a producción

- El backend Flask (`src/web/app.py`) puede desplegarse detrás de Gunicorn/uWSGI.
- Las operaciones criptográficas son thread-safe (sin estado global compartido).
- Se recomienda usar una base de datos (PostgreSQL/SQLite) en lugar de estructuras en memoria para la urna y el padrón.

---

*Manual generado como parte de la Fase 8 — Documentación Final — Proyecto de Grado UMSA 2026*
