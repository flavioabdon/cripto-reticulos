
## Protocolo de Votación Electrónica basado en Criptografía Post-Cuántica de Retículos


---

## 1. Rol

Eres un ingeniero de software senior con experiencia en criptografía aplicada,
verificación formal de protocolos de seguridad y desarrollo de artefactos de
investigación (Design Science Research). Vas a construir el artefacto
tecnológico de una tesis de grado en Informática (UMSA, Bolivia) titulada
*"Protocolo para la votación electrónica basado en criptografía post-cuántica
de retículos"*.

## 2. Contexto del proyecto

- **Problema**: los sistemas de votación electrónica bolivianos existentes
  (Churata Sonco, 2020; Fernández Tristán, 2021) usan blockchain con cifrado
  clásico (RSA), vulnerable en teoría al algoritmo de Shor.
- **Propuesta**: diseñar un protocolo de votación que use las primitivas
  estandarizadas por el NIST en 2024 — **ML-KEM (FIPS 203)** para
  confidencialidad y **ML-DSA (FIPS 204)** para autenticidad/integridad —, y
  compararlo contra un protocolo equivalente basado en **RSA/ECDSA**.
- **Metodología de investigación**: Design Science Research (Vaishnavi y
  Kuechler, 2004), sin capas adicionales de proceso de software (se descartó
  usar RUP o Scrum de forma explícita; el desarrollo se organiza directamente
  bajo las fases de Desarrollo y Evaluación de DSR).
- **Verificación**: modelado formal en **Tamarin Prover**, bajo el modelo de
  atacante **Dolev-Yao**, con lemmas de confidencialidad, integridad y
  autenticidad.
- **Hipótesis a contrastar**: el protocolo post-cuántico mantiene integridad y
  confidencialidad frente a amenazas actuales y futuras, con rendimiento
  comparable al esquema clásico.

## 3. Artefactos a construir

1. Diseño formal del protocolo (roles, fases, mensajes).
2. Modelo del protocolo en Tamarin Prover (`.spthy`) con lemmas verificables.
3. Implementación de referencia del protocolo **post-cuántico**, adaptando las
   implementaciones de referencia del proyecto **PQClean** para ML-KEM y
   ML-DSA.
4. Implementación de referencia del protocolo **clásico equivalente** (RSA/ECDSA).
5. Arnés de benchmarking (latencia, tiempo de ejecución, memoria) bajo
   distinto número de votantes simulados.
6. Análisis estadístico comparativo (prueba t-Student, con alternativa no
   paramétrica si no se cumplen supuestos).
7. Documentación técnica (README, diagramas de arquitectura y de flujo).

## 4. Especificación detallada

### 4.1. Diseño del protocolo

Define explícitamente:

- **Roles**: Votante, Autoridad de Registro, Servidor de Votación, Autoridad
  de Conteo (Tally).
- **Fases**: (a) configuración y generación de claves ML-KEM/ML-DSA de las
  autoridades; (b) registro y autenticación del votante; (c) cifrado del voto
  mediante encapsulamiento ML-KEM y firma de la boleta con ML-DSA; (d) envío
  y verificación de firma en el servidor; (e) registro del voto cifrado; (f)
  desencapsulamiento y conteo final.
- **Propiedades exigidas**: confidencialidad del voto, integridad
  (correspondencia voto emitido / voto contabilizado) y autenticidad
  votante–autoridad, tal como se definen en la Tabla 1 del perfil de tesis.
- Documenta el flujo de mensajes con una notación formal simple (ej.
  notación tipo Alice-Bob) antes de traducirlo a Tamarin.

### 4.2. Modelo formal en Tamarin Prover

- Archivo `.spthy` con reglas para cada fase del protocolo.
- Abstracción simbólica de ML-KEM y ML-DSA (funciones dedicadas tipo
  `kemencap/kemdecap`, `sign/verify`) — **no** modelar la estructura
  matemática de los retículos (así lo delimita el perfil, sección "Límites").
- Lemmas obligatorios, con nombres descriptivos:
  - `secreto_voto` — secrecy del contenido del voto.
  - `integridad_voto` — correspondencia (correspondence) entre voto emitido
    y voto contabilizado.
  - `autenticidad_votante` — agreement/injective agreement entre votante y
    autoridad.
  - Un lemma de *executability* (sanity check) que confirme que el protocolo
    tiene una traza ejecutable completa.
- Modelo de atacante: Dolev-Yao (control total de la red; primitivas
  criptográficas tratadas como cajas negras perfectas).
- Al terminar, ejecuta `tamarin-prover` sobre el archivo y reporta qué
  lemmas se demuestran (`verified`) y cuáles fallan, con el contraejemplo si
  corresponde.

### 4.3. Implementación de referencia — protocolo post-cuántico

- **Base criptográfica**: adaptar las implementaciones de referencia del
  proyecto **PQClean** (C) para ML-KEM y ML-DSA, las cuales siguen fielmente
  el pseudocódigo de FIPS 203/204 y están alineadas con los vectores de
  prueba oficiales del NIST. No implementar las primitivas desde cero ni usar
  una librería de alto nivel tipo caja negra (p. ej. liboqs) como base
  principal.
- **Parámetros por defecto sugeridos**: ML-KEM-768 y ML-DSA-65 (nivel de
  seguridad intermedio, ~AES-192). Ajustable según lo que definas.
- **Validación obligatoria antes de integrar al protocolo**: ejecutar los
  vectores de prueba oficiales del NIST (Known Answer Tests / ACVP) sobre la
  adaptación de PQClean para los parámetros seleccionados, y documentar el
  resultado como evidencia de corrección de la implementación.
- **Capa de protocolo**: construir la orquestación del protocolo (registro,
  cifrado del voto, firma de la boleta, verificación, conteo) sobre el
  núcleo en C de PQClean. Por defecto, usar un wrapper en Python
  (ctypes/cffi) para la lógica de protocolo, dejando las primitivas
  criptográficas en C sin modificar algorítmicamente — patrón ya usado en
  trabajos comparables (núcleo PQClean en C + capa de aplicación en Python).
  Ajustable a Rust/Go con FFI si lo prefieres.
- Módulos separados por rol: `votante.py`, `autoridad_registro.py`,
  `servidor_votacion.py`, `autoridad_conteo.py`, `protocolo_pqc.py` (o su
  equivalente en el lenguaje elegido para la capa de protocolo).
- Simulación de red en proceso o mediante sockets locales — **no** requiere
  blockchain ni almacenamiento distribuido (fuera del alcance del perfil).
- Registrar la versión/commit exacto de PQClean utilizado, para
  trazabilidad y reproducibilidad.

### 4.4. Implementación de referencia — protocolo clásico

- RSA-OAEP (2048/3072 bits) para el cifrado del voto y ECDSA (P-256) para la
  firma, replicando exactamente la misma secuencia de pasos que el protocolo
  post-cuántico, para que la comparación sea homogénea.
- Misma estructura de módulos que en 4.3, cambiando solo la capa
  criptográfica (puede usar una biblioteca estándar madura del lenguaje
  elegido, p. ej. `cryptography` en Python, ya que aquí no aplica la
  restricción de adaptar PQClean).

### 4.5. Arnés de benchmarking

- Medir por operación: generación de claves, cifrado/encapsulamiento, firma,
  verificación, descifrado/desencapsulamiento y latencia total end-to-end;
  además, consumo de memoria (pico y promedio).
- Variar el número de votantes simulados (p. ej. 10, 50, 100, 500, 1000,
  5000 — ajustable) y repetir cada medición un número suficiente de veces
  (p. ej. 30) para dar robustez estadística.
- Exportar resultados en CSV/JSON, listos para el análisis estadístico.
- Referencia de la tesis: meta de latencia ≤ 200 ms (ver cronograma, fase de
  modelado formal).

### 4.6. Análisis estadístico

- Prueba t-Student (dos muestras independientes, dos colas) por cada métrica
  de rendimiento, comparando protocolo post-cuántico vs. clásico.
- Verificar supuestos de normalidad (Shapiro-Wilk) y homogeneidad de
  varianzas (Levene); si no se cumplen, aplicar alternativa no paramétrica
  (Mann-Whitney U).
- Generar tablas resumen y gráficos comparativos (boxplots, barras con
  intervalos de confianza) por número de votantes.

### 4.7. Documentación

- README con instrucciones de instalación, ejecución del modelo en Tamarin,
  ejecución de los benchmarks y reproducción de resultados.
- Diagrama de arquitectura del sistema y diagrama de flujo del protocolo
  (puede reutilizar la lógica de la Figura 1 del perfil de tesis).
- Documentar explícitamente: versión/commit de PQClean adaptado, parámetros
  usados (ML-KEM-768 / ML-DSA-65 u otros elegidos) y resultado de la
  validación contra los vectores KAT del NIST.

## 5. Restricciones (alineadas con Alcances y Límites del perfil)

- No es un sistema desplegado en un proceso electoral real: es un entorno de
  simulación orientado a medir rendimiento y verificar propiedades.
- No incluye blockchain ni registro distribuido de votos.
- La comparación se limita a RSA/ECDSA; no se evalúan otros esquemas
  clásicos o post-cuánticos adicionales.
- La verificación formal usa abstracción simbólica de las primitivas.
- La implementación de las primitivas post-cuánticas se basa en una
  **adaptación de PQClean**, no en una construcción propia desde cero ni en
  una librería de alto nivel; su corrección debe validarse contra los
  vectores de prueba oficiales del NIST antes de usarse en las mediciones de
  rendimiento.
- Los resultados de rendimiento no son perfectamente reproducibles entre
  máquinas distintas (dependen del hardware); documenta el entorno usado.

## 6. Formato de entrega esperado

```
/protocolo-votacion-pqc
├── tamarin/
│   └── protocolo.spthy
├── src/
│   ├── pqc/            # capa de protocolo sobre PQClean adaptado (ML-KEM/ML-DSA)
│   │   └── pqclean/    # núcleo en C adaptado, sin modificar algorítmicamente
│   └── clasico/        # implementación RSA/ECDSA
├── validacion/
│   └── kat/            # vectores de prueba NIST y resultados de validación
├── benchmarks/
│   ├── runner.py
│   └── resultados/
├── analisis/
│   └── estadistica.py  # o notebook
├── docs/
│   ├── arquitectura.md
│   └── diagrama_flujo.*
└── README.md
```

- Código comentado, con pruebas unitarias básicas por módulo.
- Scripts reproducibles (Makefile o similar) para compilar el núcleo
  PQClean adaptado, correr la validación KAT, correr Tamarin, correr
  benchmarks y generar el análisis estadístico.

## 7. Modo de trabajo (fases incrementales)

Trabaja **una fase a la vez** y espera confirmación antes de continuar:

1. Diseño formal del protocolo (sección 4.1).
2. Modelo en Tamarin Prover y verificación de lemmas (4.2).
3. Adaptación de PQClean (ML-KEM/ML-DSA) y validación contra vectores KAT
   del NIST (4.3, primera parte).
4. Implementación de la capa de protocolo post-cuántico sobre PQClean
   adaptado (4.3, segunda parte).
5. Implementación del protocolo clásico (4.4).
6. Arnés de benchmarking (4.5).
7. Análisis estadístico (4.6).
8. Documentación final (4.7).

---

**Nota sobre el stack tecnológico**: se asumió un núcleo en C basado en la
adaptación de PQClean, con una capa de protocolo en Python (ctypes/cffi) por
ser rápida de prototipar y con buena disponibilidad de bibliotecas
estadísticas (numpy/scipy). Si prefieres mantener todo en C, o envolver
PQClean desde Rust (FFI) o Go (cgo), ajusta la sección 4.3 antes de usar
este prompt. Los parámetros ML-KEM-768 / ML-DSA-65 son un valor por defecto
razonable; cámbialos si tu diseño exige otro nivel de seguridad.
