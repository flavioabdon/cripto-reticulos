# Protocolos Criptográficos y Arquitectura Post-Cuántica (PQC)
**Proyecto de Grado — Criptografía Basada en Retículos para Votación Electrónica**  
*Universidad Mayor de San Andrés (UMSA) — Facultad de Ciencias Puras y Naturales*

---

## 1. Justificación Técnica: ¿Por qué SHA3-256 y no FIPS 203 / FIPS 204 para el Hash de la Boleta?

Una duda fundamental al diseñar o auditar un sistema criptográfico post-cuántico es:  
*¿Por qué no usar únicamente los estándares post-cuánticos FIPS 203 o FIPS 204 para todo el protocolo, incluyendo el cálculo del comprobante de la boleta?*

La respuesta radica en que **las primitivas criptográficas son herramientas con propiedades matemáticas y propósitos ortogonales**. Un algoritmo de encapsulamiento (FIPS 203) o de firma digital (FIPS 204) no puede sustituir a una función hash criptográfica (FIPS 202 / SHA3-256), del mismo modo que un candado no puede utilizarse para obtener una huella digital determinista.

### 1.1 Comparativa de Primitivas Criptográficas en el Sistema

| Primitiva | Estándar NIST | Familia / Base Matemática | Tipo de Primitiva | Salida | Propósito en el Protocolo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ML-KEM-768** | **FIPS 203** | Retículos (*Module Learning With Errors - M-LWE*) | KEM (Mecanismo de Encapsulamiento de Clave) | `ciphertext` (1088 bytes), `shared_secret` (32 bytes) | **Confidencialidad:** Cifra/encapsula la clave simétrica que protege el contenido del voto. |
| **ML-DSA-65** | **FIPS 204** | Retículos (*Module Short Integer Solution - M-SIS*) | DSA (Algoritmo de Firma Digital) | `signature` (3293 bytes), `public_key` (1952 bytes) | **Autenticidad y No Repudio:** Firma la credencial de elector y la boleta emitida. |
| **AES-256-GCM** | **NIST SP 800-38D** | Bloque simétrico + Galois Counter Mode | DEM (Mecanismo de Encapsulamiento de Datos) | `ciphertext` (variable), `tag` (16 bytes) | **Cifrado Simétrico Autenticado:** Cifra la selección del candidato a velocidad nativa. |
| **SHA3-256** | **FIPS 202** | Esponja Keccak ($r=1088, c=512$) | Función Hash Criptográfica | `digest` determinista (32 bytes / 256 bits) | **Integridad y Recibo de Auditoría:** Identificador único, público e inmutable de la boleta. |

---

## 2. Incompatibilidad de Roles: ¿Por qué FIPS 203 o 204 no pueden calcular el Hash?

### 2.1 Por qué FIPS 203 (ML-KEM) no es apto para un identificador de boleta
1. **Es un mecanismo asimétrico y probabilístico:** Cada ejecución de encapsulamiento (`crypto_kem_enc`) genera números aleatorios nuevos. Si se encapsula la misma boleta dos veces, se obtendrán dos ciphertexts completamente distintos. Un identificador de auditoría o recibo debe ser **100% determinista**.
2. **Dependencia de claves:** Para desencapsular y verificar se requiere una clave privada (`dk`). Un comprobante de voto debe poder ser auditado universalmente por cualquier ciudadano u observador sin necesidad de poseer claves secretas.
3. **Sobrecarga de tamaño:** Un ciphertext de ML-KEM-768 ocupa 1088 bytes, mientras que el hash SHA3-256 ocupa exactamente 32 bytes (64 caracteres hexadecimales), ideal para códigos QR, papeletas impresas o cadenas de bloques.

### 2.2 Por qué FIPS 204 (ML-DSA) no sustituye a la función hash
1. **Propósito de autenticación, no de resumen universal:** ML-DSA genera una firma digital vinculada a un par de claves específico ($sk, pk$). La firma certifica *quién* generó el dato, no cuál es la *identidad matemática intrínseca* del dato.
2. **Determinismo y tamaño:** La firma ML-DSA-65 mide **3293 bytes**. Presentar un recibo o verificar la integridad de un ánfora con firmas en lugar de hashes generaría un consumo excesivo de almacenamiento y ancho de banda.
3. **Internamente ya utiliza Keccak (FIPS 202):** Tanto ML-KEM como ML-DSA emplean internamente SHAKE128, SHAKE256 y SHA3 para su muestreo de matrices y oráculos aleatorios. Utilizar SHA3-256 en la capa de aplicación mantiene coherencia matemática estricta con el ecosistema Keccak.

---

## 3. Resistencia Cuántica: SHA3-256 frente a Algoritmos de Grover y Shor

Existe la creencia errónea de que toda la criptografía clásica queda obsoleta ante un computador cuántico. Sin embargo, el impacto depende del tipo de problema matemático:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │              AMENAZA CUÁNTICA POR TIPO                  │
                  └─────────────────────────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│  ALGORITMO DE SHOR (1994)    │              │  ALGORITMO DE GROVER (1996)  │
├──────────────────────────────┤              ├──────────────────────────────┤
│ Resuelve en tiempo POLINOMIAL│              │ Aceleración CUADRÁTICA sobre │
│ factorización entera y log   │              │ búsquedas en espacio desor-  │
│ discreto (RSA, ECC, Diffie-  │              │ denado (cifrado simétrico    │
│ Hellman, ElGamal).           │              │ y funciones hash).           │
│                              │              │                              │
│ ¡DESTRUYE COMPLETAMENTE LA   │              │ IMPACTO MODERADO:            │
│ CRIPTOGRAFÍA ASIMÉTRICA      │              │ Fuerza bruta O(2^n) pasa a   │
│ CLÁSICA!                     │              │ O(2^(n/2)).                  │
└──────────────────────────────┘              └──────────────────────────────┘
            │                                                     │
            ▼                                                     ▼
  Solución: Reemplazar por                      Solución: Duplicar tamaño de
  retículos (FIPS 203 / 204).                   clave/salida (256 bits).
```

### Seguridad de SHA3-256 ante Grover:
* **Preimagen (Inversión):** La complejidad clásica de $2^{256}$ pasa a $2^{128}$ operaciones cuánticas bajo Grover. Un nivel de $2^{128}$ operaciones cuánticas supera con creces el límite computacional del universo observable y cumple el **Nivel de Seguridad 5 del NIST**.
* **Colisiones:** Para encontrar $H(m_1) = H(m_2)$, los algoritmos cuánticos (como BHT) requieren $O(2^{n/3}) \approx 2^{85}$ operaciones, pero exigen una memoria cuántica de acceso aleatorio (QRAM) astronómicamente inviable. Por tanto, SHA3-256 es considerado **post-cuánticamente seguro**.

---

## 4. Flujo de Construcción de la Boleta y Roles en el Código

En el presente proyecto ([`src/pqc/`](file:///Users/flavioabdon/UMSA/PROYECTO%20DE%20GRADO/CRIPTOGRAFIA%20RETICULOS/src/pqc)), las primitivas colaboran en una arquitectura por capas (*KEM-DEM + Firma + Hash*):

```
                                  VOTANTE
                                     │
                 [ Opción de Candidato: "ALIANZA FUTURO" ]
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           │ 1. KEM (FIPS 203 - ML-KEM-768):                   │
           │    (ct_kem, ss) = MLKEM768.encaps(ek_sv)          │
           │                                                   │
           │ 2. DEM (AES-256-GCM):                             │
           │    voto_cifrado = AES_GCM_Encrypt(ss, candidato)  │
           └─────────────────────────┬─────────────────────────┘
                                     │
                                     ▼
                      [ Estructura BoletaSufragio ]
                    - ciphertext_kem (1088 B)
                    - voto_cifrado + nonce
                    - credencial (firmada por AR con ML-DSA-65)
                    - timestamp_emision
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           │ 3. FIRMA (FIPS 204 - ML-DSA-65):                  │
           │    payload = canonical_json(BoletaSufragio)       │
           │    firma_votante = MLDSA65.sign(payload, sk_v)    │
           └─────────────────────────┬─────────────────────────┘
                                     │
                                     ▼
                [ PaqueteVoto: Boleta + Firma Votante ]
                                     │
                                     ▼  (Envío a Servidor de Votación)
                        SERVIDOR DE VOTACIÓN (SV)
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           │ 4. VERIFICACIÓN Y REGISTRO:                       │
           │    - MLDSA65.verify(credencial, firma_ar, pk_ar)  │
           │    - MLDSA65.verify(payload, firma_votante, pk_v) │
           │    - Inserción en Ánfora Digital                  │
           │                                                   │
           │ 5. GENERACIÓN DEL RECIBO (FIPS 202 - SHA3-256):   │
           │    hash_boleta = sha3_256(payload)                │
           │    recibo = ReciboVotacion(hash_boleta, ts)       │
           │    firma_sv = MLDSA65.sign(recibo, sk_sv)         │
           └─────────────────────────┬─────────────────────────┘
                                     │
                                     ▼
                    [ Recibo Entregado al Votante ]
                 Hash SHA3-256: 32 bytes (64 hex chars)
                 Firma ML-DSA-65 del Servidor
```

---

## 5. Mapeo a la Implementación del Repositorio

| Concepto Criptográfico | Módulo en el Proyecto | Función / Clase |
| :--- | :--- | :--- |
| **Encapsulamiento KEM** | [`src/pqc/votante.py`](file:///Users/flavioabdon/UMSA/PROYECTO%20DE%20GRADO/CRIPTOGRAFIA%20RETICULOS/src/pqc/votante.py#L70-L100) | `MLKEM768.encaps(ek_sv)` |
| **Cifrado Simétrico del Voto** | [`src/pqc/crypto_utils.py`](file:///Users/flavioabdon/UMSA/PROYECTO%20DE%20GRADO/CRIPTOGRAFIA%20RETICULOS/src/pqc/crypto_utils.py#L30-L50) | `aes_gcm_encrypt(key, plaintext)` |
| **Firma Digital del Elector** | [`src/pqc/votante.py`](file:///Users/flavioabdon/UMSA/PROYECTO%20DE%20GRADO/CRIPTOGRAFIA%20RETICULOS/src/pqc/votante.py#L110-L125) | `MLDSA65.sign(payload, sk_votante)` |
| **Verificación de Firmas** | [`src/pqc/servidor_votacion.py`](file:///Users/flavioabdon/UMSA/PROYECTO%20DE%20GRADO/CRIPTOGRAFIA%20RETICULOS/src/pqc/servidor_votacion.py#L103-L112) | `MLDSA65.verify(...)` |
| **Generación de Hash Boleta** | [`src/pqc/servidor_votacion.py`](file:///Users/flavioabdon/UMSA/PROYECTO%20DE%20GRADO/CRIPTOGRAFIA%20RETICULOS/src/pqc/servidor_votacion.py#L121) | `hash_b = sha3_256(payload_boleta)` |
| **Verificación de Ánfora** | [`src/pqc/autoridad_conteo.py`](file:///Users/flavioabdon/UMSA/PROYECTO%20DE%20GRADO/CRIPTOGRAFIA%20RETICULOS/src/pqc/autoridad_conteo.py#L75-L80) | `sha3_256(payload_boleta).hex()` |
| **Desencapsulamiento y Conteo**| [`src/pqc/autoridad_conteo.py`](file:///Users/flavioabdon/UMSA/PROYECTO%20DE%20GRADO/CRIPTOGRAFIA%20RETICULOS/src/pqc/autoridad_conteo.py#L82-L95) | `MLKEM768.decaps(ct, dk_sv)` + `aes_gcm_decrypt` |

---

## 6. Resumen Ejecutivo para Tesis / Documentación

1. **FIPS 203 (ML-KEM-768)** resuelve la **confidencialidad**: solo la Autoridad de Conteo puede abrir el voto al finalizar los comicios.
2. **FIPS 204 (ML-DSA-65)** resuelve la **autenticidad y no repudio**: garantiza que el votante esté habilitado por el padrón y que el servidor no pueda repudiar el recibo entregado.
3. **FIPS 202 (SHA3-256)** resuelve la **integridad, auditabilidad y compacidad**: genera un identificador público único de 256 bits inmune a preimágenes cuánticas, permitiendo al ciudadano verificar que su boleta está incluida en el ánfora sin exponer su voto.
