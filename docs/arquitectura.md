# Arquitectura del Protocolo de Votación Electrónica PQC
**Tesis:** *"Protocolo para la votación electrónica basado en criptografía post-cuántica de retículos"*  
**Institución:** UMSA — Carrera de Informática  
**Metodología:** Design Science Research (Vaishnavi y Kuechler, 2004)  
**Versión del documento:** 1.0 — Fase 1 (Diseño formal)  
**Fecha:** 2026-08-26  

---

## 1. Visión general

El protocolo propone una arquitectura de votación electrónica en la que la confidencialidad del voto se garantiza mediante **ML-KEM** (FIPS 203 — Key Encapsulation Mechanism basado en módulo-LWE) y la autenticidad/integridad se garantiza mediante **ML-DSA** (FIPS 204 — Digital Signature Algorithm basado en módulo-LWE). Ambos esquemas fueron estandarizados por el NIST en 2024 y son resistentes al algoritmo de Shor ejecutado en una computadora cuántica universal.

La hipótesis de la tesis es:

> El protocolo post-cuántico (ML-KEM + ML-DSA) **mantiene** las propiedades de confidencialidad, integridad y autenticidad frente a amenazas actuales y futuras, con **rendimiento comparable** al protocolo clásico (RSA-OAEP + ECDSA).

---

## 2. Roles del protocolo (tarea 1.1)

El protocolo define cuatro entidades (roles) con responsabilidades claramente delimitadas:

| ID  | Rol | Descripción |
|-----|-----|-------------|
| **V** | **Votante** | Ciudadano habilitado para emitir un voto. Posee un par de claves ML-DSA `(sk_V, pk_V)` generado durante el registro. Cifra su voto con la clave pública del Servidor de Votación y firma la boleta con su clave privada. |
| **AR** | **Autoridad de Registro** | Entidad de confianza responsable de verificar la identidad del Votante, emitir sus credenciales/claves y registrarlo en el padrón electoral. Posee un par de claves ML-DSA `(sk_AR, pk_AR)` para firmar credenciales. |
| **SV** | **Servidor de Votación** | Entidad receptora de las boletas cifradas. Posee un par de claves ML-KEM `(ek_SV, dk_SV)` para la recepción de votos. Verifica la firma ML-DSA de cada boleta recibida, y registra los votos cifrados. |
| **AC** | **Autoridad de Conteo (Tally)** | Entidad responsable del escrutinio final. Custodia la clave de desencapsulamiento `dk_SV`. Desencapsula cada voto y realiza el conteo. |

### Separación de responsabilidades

La arquitectura separa deliberadamente el **cifrado** (SV solo almacena, nunca descifra) del **desencapsulamiento** (AC descifra en la fase de conteo). Esto impide que el SV conozca el contenido de los votos durante la jornada electoral, satisfaciendo la propiedad de confidencialidad.

---

## 3. Parámetros criptográficos

| Primitiva | Estándar | Parámetros | Nivel de seguridad | Uso en el protocolo |
|-----------|----------|------------|--------------------|---------------------|
| ML-KEM | FIPS 203 | **ML-KEM-768** | ~AES-192 (Categoría 3) | Cifrado / encapsulamiento del voto |
| ML-DSA | FIPS 204 | **ML-DSA-65** | ~AES-192 (Categoría 3) | Firma de boleta, credenciales |
| AES-256-GCM | NIST SP 800-38D | 256-bit key | 256-bit security | Cifrado simétrico autenticado del voto |
| SHA3-256 | FIPS 202 | — | 128-bit collision | Hash para recibos y auditoría |

Ambos parámetros ML-KEM/ML-DSA operan al mismo nivel de seguridad para homogeneidad. Pueden ajustarse sin cambiar la estructura del protocolo.

---

## 4. Fases del protocolo (tarea 1.2)

El protocolo se divide en **seis fases** secuenciales:

### Fase (a) — Configuración y generación de claves

**Actores:** AR, SV, AC  
**Pre-condición:** Ninguna.  

1. La **Autoridad de Registro** genera su par de claves ML-DSA:  
   `(sk_AR, pk_AR) ← ML-DSA.KeyGen()`
2. El **Servidor de Votación** genera su par de claves ML-KEM:  
   `(ek_SV, dk_SV) ← ML-KEM.KeyGen()`  
   donde `ek_SV` es la clave de encapsulamiento (pública) y `dk_SV` la de desencapsulamiento (privada).
3. El **Servidor de Votación** también genera un par ML-DSA para firmar recibos:  
   `(sk_SV, pk_SV) ← ML-DSA.KeyGen()`
4. La **Autoridad de Conteo** recibe `dk_SV` por canal seguro fuera de banda.
5. Las claves públicas `pk_AR`, `ek_SV`, `pk_SV` se publican en un directorio de confianza.

**Post-condición:** Todas las entidades tienen sus claves; las claves públicas son conocidas por todos.

---

### Fase (b) — Registro y autenticación del Votante

**Actores:** V, AR  
**Pre-condición:** Fase (a) completada.  

1. El Votante **V** se presenta ante la AR con su identidad `ID_V`.
2. La AR verifica la identidad de V contra el padrón electoral.
3. Si V es válido y no ha sido registrado antes, la AR:
   - Genera par de claves ML-DSA para el votante:  
     `(sk_V, pk_V) ← ML-DSA.KeyGen()`
   - Emite credencial firmada:  
     `cred_V = (ID_V || pk_V || ts)`  
     `σ_AR = ML-DSA.Sign(sk_AR, cred_V)`  
     `Credencial = (cred_V, σ_AR)`
   - Registra `(ID_V, pk_V, estado="Registrado")` en el padrón electoral.
   - Entrega `(sk_V, Credencial)` al votante.

**Post-condición:** V posee `(sk_V, Credencial)` válida; AR registra `pk_V` asociada a `ID_V`.

---

### Fase (c) — Cifrado del voto y firma de la boleta

**Actores:** V  
**Pre-condición:** V autenticado con `(sk_V, Credencial)` válida; conoce `ek_SV`.  

1. V selecciona candidato: `voto ∈ {c₁, c₂, ..., cₙ}`, codificado como `m = encode(voto)`.
2. V encapsula para obtener secreto compartido efímero:  
   `(K, ct) ← ML-KEM.Encaps(ek_SV)`
3. V cifra el voto con K usando AES-256-GCM:  
   `voto_cifrado = AEAD.Encrypt(K, m, nonce)`
4. V construye la boleta:  
   `boleta = (ct || voto_cifrado || nonce || Credencial || ts_boleta)`
5. V firma la boleta:  
   `σ_V = ML-DSA.Sign(sk_V, boleta)`
6. V construye el paquete:  
   `paquete = (boleta, σ_V)`

**Post-condición:** `paquete` listo para envío. El contenido `m` es confidencial.

---

### Fase (d) — Envío al Servidor y verificación de firma

**Actores:** V, SV  
**Pre-condición:** V tiene `paquete`; SV conoce `pk_AR`.  

1. V envía `paquete = (boleta, σ_V)` al SV.
2. SV verifica credencial interna en `boleta`:  
   `ML-DSA.Verify(pk_AR, cred_V, σ_AR) == true`
3. SV verifica firma del votante sobre la boleta:  
   `ML-DSA.Verify(pk_V, boleta, σ_V) == true`
4. SV verifica que `ID_V` no ha votado antes (control de duplicados).
5. Si todo pasa → aceptar. Si alguna falla → rechazar.

**Post-condición:** SV ha verificado autenticidad e integridad de la boleta.

---

### Fase (e) — Registro del voto cifrado

**Actores:** SV  
**Pre-condición:** Fase (d) exitosa.  

1. SV registra `(ID_V, boleta)` en la ánfora digital; marca votante como "Ya votó".
2. SV **no desencapsula** el voto (no accede a `K` ni al contenido `m`).
3. SV emite recibo al votante:  
   `recibo = SHA3-256(boleta || ts_recibo)`  
   `σ_recibo = ML-DSA.Sign(sk_SV, recibo)`

**Post-condición:** Voto cifrado registrado; SV no conoce el contenido.

---

### Fase (f) — Desencapsulamiento y conteo final

**Actores:** AC, SV  
**Pre-condición:** Jornada cerrada; AC posee `dk_SV`.  

1. AC obtiene lista de boletas `{boleta_i}` del SV.
2. Para cada boleta `boleta_i`:
   - `K_i ← ML-KEM.Decaps(dk_SV, ct_i)`
   - `m_i = AEAD.Decrypt(K_i, voto_cifrado_i, nonce_i)`
   - Re-verifica `σ_V_i` para confirmar correspondencia voto emitido / contabilizado.
3. AC acumula conteo por candidato.
4. AC publica resultado + `{hash(boleta_i)}` para auditoría.

**Post-condición:** Resultados publicados; auditores pueden verificar integridad.

---

## 5. Propiedades de seguridad (tarea 1.4)

### 5.1 Confidencialidad del voto

**Definición:** Un adversario polinomial no puede determinar el contenido del voto a partir del paquete transmitido y del registro de la ánfora.

**Mecanismo:** La seguridad IND-CCA2 de ML-KEM garantiza que `K` es computacionalmente indistinguible de un valor aleatorio sin `dk_SV`. `dk_SV` es custodiado exclusivamente por AC.

**Lemma Tamarin:** `secreto_voto` — el contenido `m` no puede ser aprendido por el atacante Dolev-Yao mientras `dk_SV` permanece secreto.

---

### 5.2 Integridad del voto

**Definición:** Todo voto contabilizado corresponde exactamente a un voto emitido por un votante legítimo. Ningún voto puede ser modificado sin detección.

**Mecanismo:** La propiedad EUF-CMA de ML-DSA garantiza que ningún adversario puede forjar una firma válida sin `sk_V`. AC re-verifica cada firma antes de contabilizar.

**Lemma Tamarin:** `integridad_voto` — correspondence entre `VotoEmitido(V, m)` y `VotoContabilizado(AC, m)`.

---

### 5.3 Autenticidad votante–autoridad

**Definición:** Cualquier boleta aceptada por el SV proviene de un votante registrado por la AR.

**Mecanismo:** La credencial vincula `pk_V` a `ID_V` mediante la firma de AR (EUF-CMA de ML-DSA). El SV verifica ambas firmas en la fase (d).

**Lemma Tamarin:** `autenticidad_votante` — injective agreement entre V y AR/SV.

---

## 6. Invariantes adicionales

| Invariante | Descripción |
|-----------|-------------|
| Unicidad del voto | Cada `ID_V` emite a lo sumo un voto aceptado. |
| Separación de funciones | SV nunca posee `dk_SV`; AC no participa en verificación de identidad. |
| Freshness | `ts_boleta` + nonce previenen ataques de replay. |
| Auditoría | Hashes publicados permiten verificación externa. |

---

## 7. Estructuras de datos

### Credencial de votante
```
Credencial := {
    cred_V   : { ID_V: string, pk_V: bytes[ML-DSA-65], ts: timestamp },
    σ_AR     : bytes   -- firma de AR sobre cred_V (ML-DSA-65)
}
```

### Boleta de sufragio
```
Boleta := {
    ct           : bytes[ML-KEM-768 ciphertext],
    voto_cifrado : bytes,         -- AEAD.Encrypt(K, m, nonce)
    nonce        : bytes[12],     -- nonce AES-256-GCM
    Credencial   : Credencial,
    ts_boleta    : timestamp
}
```

### Paquete de voto
```
Paquete := {
    boleta : Boleta,
    σ_V    : bytes   -- firma de V sobre boleta (ML-DSA-65)
}
```

### Recibo del servidor
```
Recibo := {
    hash_boleta : bytes[32],     -- SHA3-256(boleta || ts_recibo)
    ts_recibo   : timestamp,
    σ_SV        : bytes          -- firma del SV (ML-DSA-65)
}
```

---

## 8. Supuestos del modelo de seguridad

1. **Hardness MLWE:** El problema Module Learning With Errors es difícil ante adversarios cuánticos.
2. **Canal fuera de banda:** Entrega de `sk_V` al votante y de `dk_SV` a la AC son canales seguros fuera del modelo.
3. **Directorio de confianza:** Publicación de claves públicas a través de canal auténtico (supuesto de la infraestructura).
4. **Seguridad del dispositivo:** El dispositivo del votante donde reside `sk_V` no está comprometido.
5. **Modelo Dolev-Yao:** Atacante controla la red pero no puede romper las primitivas criptográficas.

---

## 9. Referencias

| Referencia | Descripción |
|-----------|-------------|
| FIPS 203 (2024) | NIST, *Module-Lattice-Based Key-Encapsulation Mechanism Standard* |
| FIPS 204 (2024) | NIST, *Module-Lattice-Based Digital Signature Standard* |
| Dolev & Yao (1983) | *On the security of public key protocols* |
| Vaishnavi & Kuechler (2004) | *Design Science Research in Information Systems* |
| PQClean | Repositorio de implementaciones de referencia de algoritmos PQC |
| Tamarin Prover | Herramienta de verificación formal simbólica |

---

*Entregable de la Fase 1. Ver también: [`diagrama_flujo.md`](./diagrama_flujo.md)*
