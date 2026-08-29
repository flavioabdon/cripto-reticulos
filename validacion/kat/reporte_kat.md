# Reporte de Validación KAT — Núcleo Criptográfico PQC (PQClean)

**Fecha:** 2026-08-29 10:09:19  
**Plataforma:** `macOS-26.5.2-arm64-arm-64bit-Mach-O` (`arm`)  
**Commit PQClean:** `0586a824fc0d49df0b6b6e9179d8d15d06d0974f`  
**Resultado Global:** `✅ PASS`

## 1. Resumen de Pruebas

| Primitiva | Estándar NIST | Nivel | Vectores Probados | Aprobados | Fallidos | Resistencia Alteración | Resultado |
|---|---|---|---|---|---|---|---|
| **ML-KEM-768** | FIPS 203 | Cat. 3 (~AES-192) | 100 | 100 | 0 | 100/100 | `✅ PASS` |
| **ML-DSA-65** | FIPS 204 | Cat. 3 (~AES-192) | 100 | 100 | 0 | 100/100 | `✅ PASS` |

## 2. Tamaños de Parámetros Verificados

### ML-KEM-768 (FIPS 203)
- Clave pública (`pk`): **1184 bytes**
- Clave privada (`sk`): **2400 bytes**
- Ciphertext (`ct`): **1088 bytes**
- Secreto compartido (`ss`): **32 bytes**

### ML-DSA-65 (FIPS 204)
- Clave pública (`pk`): **1952 bytes**
- Clave privada (`sk`): **4032 bytes**
- Firma digital (`sig`): **3309 bytes**

## 3. Conclusión de Corrección

La adaptación del núcleo C de PQClean cumple estrictamente con las especificaciones de FIPS 203 y FIPS 204. El 100% de los vectores de prueba de encapsulamiento/desencapsulamiento y firma/verificación fueron validados con éxito antes de su integración en el protocolo de votación electrónica.
