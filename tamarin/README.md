# Verificación Formal del Protocolo de Votación Electrónica PQC con Tamarin Prover

Este directorio contiene el modelo formal y los artefactos de verificación del protocolo de votación electrónica basado en retículos (ML-KEM y ML-DSA).

## Archivos

- `protocolo.spthy`: Especificación formal en lenguaje de reescritura de multiconjuntos de Tamarin Prover.
- `reporte_tamarin.txt`: Salida y evidencia de la verificación automática de los lemmas de seguridad.

## Modelo de Seguridad

- **Modelo de Atacante**: Dolev-Yao (control total del canal de red; interceptación, inyección, modificación y repetición de paquetes).
- **Abstracción Criptográfica**: Cajas negras perfectas simbólicas para:
  - **ML-KEM (FIPS 203)**: funciones `encaps/2`, `decaps/2`, `ek_from_dk/1` con ecuación de corrección:
    $$\text{decaps}(dk, \text{encaps}(\text{ek\_from\_dk}(dk), r)) = r$$
  - **ML-DSA (FIPS 204)**: funciones `sign/2`, `verify/3`, `pk/1` con ecuación de verificación:
    $$\text{verify}(\text{sign}(m, sk), m, \text{pk}(sk)) = \text{true}$$
  - **Cifrado Simétrico AEAD**: funciones `senc/2`, `sdec/2` con ecuación de descifrado:
    $$\text{sdec}(\text{senc}(m, k), k) = m$$

## Propiedades y Lemmas de Seguridad

| Lemma | Tipo | Propiedad Evaluada |
|---|---|---|
| `executability` | `exists-trace` | Sanity check: existe al menos una traza válida donde el voto es emitido, aceptado y contabilizado en orden temporal estricto. |
| `secreto_voto` | `all-traces` | Confidencialidad: el adversario Dolev-Yao nunca aprende el contenido del voto $m$ durante la jornada electoral. |
| `integridad_voto` | `all-traces` | Correspondencia: todo voto contabilizado por la Autoridad de Conteo fue legítimamente emitido por el votante registrado. |
| `autenticidad_votante` | `all-traces` | Injective Agreement: por cada boleta aceptada por el servidor, existe exactamente un envío previo legítimo, previniendo ataques de replay. |

## Instrucciones de Ejecución

Para reproducir la verificación formal:

```bash
# Verificar todos los lemmas automáticamente
tamarin-prover --prove tamarin/protocolo.spthy

# Modo interactivo web (GUI)
tamarin-prover interactive tamarin/protocolo.spthy
```
