"""
Arnés de Benchmarking Automatizado para la Tesis de Grado:
"Protocolo para la votación electrónica basado en criptografía post-cuántica de retículos"

Compara rigurosamente:
  - Protocolo Post-Cuántica: ML-KEM-768 (FIPS 203) + ML-DSA-65 (FIPS 204)
  - Protocolo Clásico: RSA-OAEP-2048 + ECDSA (NIST P-256)

Mide:
  1. Latencia granular por fase (ms)
  2. Sobrecarga de comunicación y tamaños de estructuras (bytes)
  3. Uso de CPU y memoria pico (RAM)
  4. Throughput del servidor (votos/segundo)
"""

import csv
import json
import os
import platform
import sys
import time
import tracemalloc
from typing import Dict, List, Any

# Agregar directorio raíz al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pqc.pqc_wrapper import MLKEM768, MLDSA65
from src.pqc.autoridad_registro import AutoridadRegistro
from src.pqc.servidor_votacion import ServidorVotacion
from src.pqc.votante import Votante
from src.pqc.autoridad_conteo import AutoridadConteo
from src.pqc.protocolo_pqc import ProtocoloVotacionPQC

from src.clasico.crypto_clasico import RSACipher, ECDSASigner
from src.clasico.autoridad_registro_clasico import AutoridadRegistroClasico
from src.clasico.servidor_votacion_clasico import ServidorVotacionClasico
from src.clasico.votante_clasico import VotanteClasico
from src.clasico.autoridad_conteo_clasico import AutoridadConteoClasico
from src.clasico.protocolo_clasico import ProtocoloVotacionClasico


def medir_tamanos_estructuras() -> Dict[str, Dict[str, int]]:
    """Mide con precisión en bytes todas las estructuras criptográficas de ambos protocolos."""
    # 1. PQC
    ar_pqc = AutoridadRegistro()
    sv_pqc = ServidorVotacion(pk_ar=ar_pqc.pk_ar)
    sk_v_pqc, cred_pqc = ar_pqc.registrar_votante("V-001", "Votante Test")
    votante_pqc = Votante("V-001", sk_v_pqc, cred_pqc)
    paquete_pqc = votante_pqc.emitir_voto("Candidato 1", sv_pqc.ek_sv)
    _, _, recibo_pqc = sv_pqc.recepcionar_voto(paquete_pqc)

    sizes_pqc = {
        "pk_ar_bytes": len(ar_pqc.pk_ar),
        "ek_sv_bytes": len(sv_pqc.ek_sv),
        "pk_votante_bytes": len(cred_pqc.pk_votante),
        "credencial_payload_bytes": len(cred_pqc.payload_bytes()),
        "firma_credencial_bytes": len(cred_pqc.firma_ar),
        "ciphertext_kem_bytes": len(paquete_pqc.boleta.ciphertext_kem),
        "voto_cifrado_bytes": len(paquete_pqc.boleta.voto_cifrado),
        "nonce_bytes": len(paquete_pqc.boleta.nonce_aead),
        "boleta_payload_bytes": len(paquete_pqc.boleta.payload_bytes()),
        "firma_boleta_bytes": len(paquete_pqc.firma_votante),
        "paquete_voto_total_bytes": len(paquete_pqc.boleta.payload_bytes()) + len(paquete_pqc.firma_votante),
        "recibo_bytes": len(recibo_pqc.payload_bytes()) + len(recibo_pqc.firma_servidor) if recibo_pqc else 0,
    }

    # 2. Clásico
    ar_c = AutoridadRegistroClasico()
    sv_c = ServidorVotacionClasico(pk_ar_ecdsa=ar_c.pk_ar)
    sk_v_c, cred_c = ar_c.registrar_votante("V-001", "Votante Test")
    votante_c = VotanteClasico("V-001", sk_v_c, cred_c)
    paquete_c = votante_c.emitir_voto("Candidato 1", sv_c.pk_sv_rsa)
    _, _, recibo_c = sv_c.recepcionar_voto(paquete_c)

    sizes_c = {
        "pk_ar_bytes": len(ar_c.pk_ar),
        "ek_sv_bytes": len(sv_c.pk_sv_rsa),
        "pk_votante_bytes": len(cred_c.pk_votante),
        "credencial_payload_bytes": len(cred_c.payload_bytes()),
        "firma_credencial_bytes": len(cred_c.firma_ar),
        "ciphertext_kem_bytes": len(paquete_c.boleta.clave_cifrada_rsa),
        "voto_cifrado_bytes": len(paquete_c.boleta.voto_cifrado),
        "nonce_bytes": len(paquete_c.boleta.nonce_aead),
        "boleta_payload_bytes": len(paquete_c.boleta.payload_bytes()),
        "firma_boleta_bytes": len(paquete_c.firma_votante),
        "paquete_voto_total_bytes": len(paquete_c.boleta.payload_bytes()) + len(paquete_c.firma_votante),
        "recibo_bytes": len(recibo_c.payload_bytes()) + len(recibo_c.firma_servidor) if recibo_c else 0,
    }

    return {"pqc": sizes_pqc, "clasico": sizes_c}


def ejecutar_benchmark_fases_individuales(num_repeticiones: int = 100) -> Dict[str, Any]:
    """Ejecuta micro-benchmarks detallados de cada operación criptográfica individual."""
    print(f"\n[*] Ejecutando micro-benchmarks de operaciones individuales ({num_repeticiones} repeticiones)...")
    
    resultados = {"pqc": {}, "clasico": {}}

    # ----------------------------------------------------
    # 1. PQC: Micro-benchmarks
    # ----------------------------------------------------
    # KeyGen AR (ML-DSA-65)
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        MLDSA65.keypair()
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["pqc"]["keygen_ar_ms"] = tiempos

    # KeyGen SV (ML-KEM-768)
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        MLKEM768.keypair()
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["pqc"]["keygen_sv_kem_ms"] = tiempos

    # Encapsulamiento ML-KEM-768
    pk_kem, sk_kem = MLKEM768.keypair()
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        MLKEM768.enc(pk_kem)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["pqc"]["encaps_kem_ms"] = tiempos

    # Desencapsulamiento ML-KEM-768
    ct_kem, ss_kem = MLKEM768.enc(pk_kem)
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        MLKEM768.dec(ct_kem, sk_kem)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["pqc"]["decaps_kem_ms"] = tiempos

    # Firma ML-DSA-65
    pk_dsa, sk_dsa = MLDSA65.keypair()
    msg = b"Boleta de sufragio electoral UMSA 2026 hash payload"
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        MLDSA65.sign(msg, sk_dsa)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["pqc"]["sign_dsa_ms"] = tiempos

    # Verificación ML-DSA-65
    sig_dsa = MLDSA65.sign(msg, sk_dsa)
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        MLDSA65.verify(msg, sig_dsa, pk_dsa)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["pqc"]["verify_dsa_ms"] = tiempos

    # ----------------------------------------------------
    # 2. Clásico: Micro-benchmarks
    # ----------------------------------------------------
    # KeyGen AR (ECDSA P-256)
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        ECDSASigner.generate_keypair()
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["clasico"]["keygen_ar_ms"] = tiempos

    # KeyGen SV (RSA-2048)
    tiempos = []
    for _ in range(max(10, num_repeticiones // 5)):  # RSA KeyGen es más costoso
        t0 = time.perf_counter_ns()
        RSACipher.generate_keypair(2048)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["clasico"]["keygen_sv_rsa_ms"] = tiempos

    # Cifrado RSA-OAEP
    pk_rsa, sk_rsa = RSACipher.generate_keypair(2048)
    secret_bytes = os.urandom(32)
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        RSACipher.encrypt(pk_rsa, secret_bytes)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["clasico"]["encrypt_rsa_ms"] = tiempos

    # Descifrado RSA-OAEP
    ct_rsa = RSACipher.encrypt(pk_rsa, secret_bytes)
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        RSACipher.decrypt(sk_rsa, ct_rsa)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["clasico"]["decrypt_rsa_ms"] = tiempos

    # Firma ECDSA P-256
    pk_ecdsa, sk_ecdsa = ECDSASigner.generate_keypair()
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        ECDSASigner.sign(msg, sk_ecdsa)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["clasico"]["sign_ecdsa_ms"] = tiempos

    # Verificación ECDSA P-256
    sig_ecdsa = ECDSASigner.sign(msg, sk_ecdsa)
    tiempos = []
    for _ in range(num_repeticiones):
        t0 = time.perf_counter_ns()
        ECDSASigner.verify(msg, sig_ecdsa, pk_ecdsa)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
    resultados["clasico"]["verify_ecdsa_ms"] = tiempos

    return resultados


def ejecutar_escenario_electoral(motor_tipo: str, num_votantes: int, repeticion: int) -> Dict[str, Any]:
    """Ejecuta una corrida completa del protocolo para N votantes midiendo todas las métricas."""
    tracemalloc.start()
    t_cpu_start = time.process_time()
    t_wall_start = time.perf_counter_ns()

    if motor_tipo == "pqc":
        proto = ProtocoloVotacionPQC(f"Benchmark PQC N={num_votantes} R={repeticion}")
    else:
        proto = ProtocoloVotacionClasico(f"Benchmark Clásico N={num_votantes} R={repeticion}")

    # 1. Setup
    t0 = time.perf_counter_ns()
    proto.fase_setup()
    t_setup_ms = (time.perf_counter_ns() - t0) / 1e6

    # 2. Registro
    t_reg_total = 0
    candidatos = ["Candidato A", "Candidato B", "Candidato C", "Voto Blanco"]
    votos_plan = [candidatos[i % len(candidatos)] for i in range(num_votantes)]

    for i in range(num_votantes):
        t0 = time.perf_counter_ns()
        proto.fase_registro(f"CI-{i+1:06d}", f"Votante {i+1}")
        t_reg_total += (time.perf_counter_ns() - t0) / 1e6

    # 3. Emisión & Recepción
    t_voto_total = 0
    for i in range(num_votantes):
        id_v = f"CI-{i+1:06d}"
        opcion = votos_plan[i]
        t0 = time.perf_counter_ns()
        exito, _, _ = proto.fase_emision_y_recepcion(id_v, opcion)
        assert exito, f"Fallo en voto de {id_v}"
        t_voto_total += (time.perf_counter_ns() - t0) / 1e6

    # 4. Escrutinio / Tally
    t0 = time.perf_counter_ns()
    resultado = proto.fase_conteo()
    t_tally_ms = (time.perf_counter_ns() - t0) / 1e6
    assert resultado.votos_validos == num_votantes, "Discrepancia en escrutinio"

    t_wall_total_ms = (time.perf_counter_ns() - t_wall_start) / 1e6
    t_cpu_total_ms = (time.process_time() - t_cpu_start) * 1000
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    throughput_votos_sec = num_votantes / (t_voto_total / 1000) if t_voto_total > 0 else 0

    return {
        "motor": motor_tipo,
        "num_votantes": num_votantes,
        "repeticion": repeticion,
        "t_setup_ms": round(t_setup_ms, 3),
        "t_registro_total_ms": round(t_reg_total, 3),
        "t_registro_promedio_ms": round(t_reg_total / num_votantes, 3),
        "t_emision_recepcion_total_ms": round(t_voto_total, 3),
        "t_voto_promedio_ms": round(t_voto_total / num_votantes, 3),
        "t_tally_total_ms": round(t_tally_ms, 3),
        "t_tally_por_voto_ms": round(t_tally_ms / num_votantes, 4),
        "t_wall_total_ms": round(t_wall_total_ms, 3),
        "t_cpu_total_ms": round(t_cpu_total_ms, 3),
        "memoria_pico_kb": round(peak_mem / 1024, 2),
        "throughput_votos_sec": round(throughput_votos_sec, 2),
    }


def main():
    print("=" * 75)
    print("  ARNÉS DE BENCHMARKING RIGUROSO — PROTOCOLO PQC vs CLÁSICO")
    print("  Tesis de Grado UMSA — Criptografía de Retículos")
    print("=" * 75)

    # 1. Medir tamaños de estructuras
    print("\n[1/3] Midiendo tamaños de estructuras en bytes...")
    tamanos = medir_tamanos_estructuras()
    tamanos_path = os.path.join(os.path.dirname(__file__), "resultados", "tamanos_estructuras.json")
    with open(tamanos_path, "w", encoding="utf-8") as f:
        json.dump(tamanos, f, indent=2)
    print(f"    ✓ Guardado en {tamanos_path}")

    # 2. Micro-benchmarks de operaciones
    print("\n[2/3] Ejecutando micro-benchmarks individuales (100 repeticiones)...")
    micro = ejecutar_benchmark_fases_individuales(num_repeticiones=100)
    micro_path = os.path.join(os.path.dirname(__file__), "resultados", "microbenchmarks.json")
    with open(micro_path, "w", encoding="utf-8") as f:
        json.dump(micro, f, indent=2)
    print(f"    ✓ Guardado en {micro_path}")

    # 3. Escenarios de prueba con N votantes y R=30 repeticiones
    escenarios_n = [10, 50, 100, 500, 1000]
    num_repeticiones = 30

    print(f"\n[3/3] Ejecutando escenarios electorales: N in {escenarios_n} (R = {num_repeticiones} repeticiones)...")

    todas_filas = []

    for n in escenarios_n:
        print(f"\n  >>> Escenario N = {n} votantes (30 repeticiones PQC + 30 Clásico) <<<")
        
        # PQC
        print(f"    - Ejecutando PQC (ML-KEM-768 + ML-DSA-65)...", end="", flush=True)
        for r in range(1, num_repeticiones + 1):
            fila = ejecutar_escenario_electoral("pqc", n, r)
            todas_filas.append(fila)
        print(" Listo ✓")

        # Clásico
        print(f"    - Ejecutando Clásico (RSA-2048 + ECDSA P-256)...", end="", flush=True)
        for r in range(1, num_repeticiones + 1):
            fila = ejecutar_escenario_electoral("clasico", n, r)
            todas_filas.append(fila)
        print(" Listo ✓")

    # Guardar CSV Crudo
    csv_path = os.path.join(os.path.dirname(__file__), "resultados", "benchmark_crudo.csv")
    if todas_filas:
        keys = todas_filas[0].keys()
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(todas_filas)
        print(f"\n✓ Dataset crudo guardado: {csv_path} ({len(todas_filas)} registros)")

    # Guardar JSON Completo
    json_full_path = os.path.join(os.path.dirname(__file__), "resultados", "benchmark_completo.json")
    with open(json_full_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "hardware": platform.uname()._asdict(),
            "tamanos_estructuras": tamanos,
            "microbenchmarks": micro,
            "corridas_electorales": todas_filas
        }, f, indent=2)
    print(f"✓ Dataset completo JSON guardado: {json_full_path}")

    print("\n" + "=" * 75)
    print("  BENCHMARKING COMPLETADO CON ÉXITO")
    print("=" * 75)


if __name__ == "__main__":
    main()
