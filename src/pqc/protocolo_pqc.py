"""
Orquestador Principal del Protocolo de Votación Post-Cuántica (PQC).
Ejecuta el flujo completo de las 6 fases:
  (a) Configuración / Setup (AR, SV, AC)
  (b) Registro y emisión de credenciales (AR -> Votantes)
  (c) Cifrado ML-KEM y firma ML-DSA (Votantes)
  (d) Envío y verificación de firmas (Votantes -> SV)
  (e) Registro en la ánfora digital y emisión de recibos (SV)
  (f) Desencapsulamiento y escrutinio final (AC)
"""

import os
import sys
import time
from typing import Dict, List, Optional, Tuple

# Garantizar que el directorio raíz esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.pqc.autoridad_registro import AutoridadRegistro, CredencialVotante
from src.pqc.servidor_votacion import ServidorVotacion, ReciboVotacion
from src.pqc.votante import Votante, PaqueteVoto
from src.pqc.autoridad_conteo import AutoridadConteo, ResultadoEscrutinio


class ProtocoloVotacionPQC:
    """Orquestador del protocolo de votación electrónica post-cuántica."""

    def __init__(self, nombre_eleccion: str = "Elecciones Generales UMSA 2026"):
        self.nombre_eleccion = nombre_eleccion
        self.ar: Optional[AutoridadRegistro] = None
        self.sv: Optional[ServidorVotacion] = None
        self.ac: Optional[AutoridadConteo] = None
        self.votantes: Dict[str, Votante] = {}
        self.recibos: Dict[str, ReciboVotacion] = {}
        self.resultado: Optional[ResultadoEscrutinio] = None

    def fase_setup(self):
        """Fase (a): Configuración y generación de claves de las autoridades."""
        # 1. Autoridad de Registro genera par ML-DSA-65
        self.ar = AutoridadRegistro(nombre=f"{self.nombre_eleccion} - AR")

        # 2. Servidor de Votación genera par ML-KEM-768 y par ML-DSA-65
        self.sv = ServidorVotacion(pk_ar=self.ar.pk_ar, autoridad_registro=self.ar)

        # 3. Autoridad de Conteo recibe dk_sv fuera de banda
        dk_sv = self.sv.obtener_dk_para_conteo()
        self.ac = AutoridadConteo(dk_servidor=dk_sv, pk_ar=self.ar.pk_ar)

    def fase_registro(self, id_votante: str, nombre: str = "") -> Votante:
        """Fase (b): Registro del votante y emisión de credencial firmada."""
        if not self.ar:
            raise RuntimeError("Debe ejecutar la fase_setup antes de registrar votantes.")

        sk_v, credencial = self.ar.registrar_votante(id_votante, nombre_completo=nombre)
        votante = Votante(id_votante=id_votante, sk_votante=sk_v, credencial=credencial)
        self.votantes[id_votante] = votante
        return votante

    def fase_emision_y_recepcion(self, id_votante: str, opcion_candidato: str) -> Tuple[bool, str, Optional[ReciboVotacion]]:
        """Fases (c) + (d) + (e): Emisión del voto, verificación en SV y emisión de recibo."""
        if id_votante not in self.votantes:
            raise ValueError(f"Votante {id_votante} no registrado.")

        votante = self.votantes[id_votante]

        # Fase (c): Cifrado ML-KEM-768 + AES-256-GCM y firma ML-DSA-65
        paquete = votante.emitir_voto(opcion_candidato, self.sv.ek_sv)

        # Fases (d) + (e): Recepción, verificación de firmas, registro y recibo
        exito, msg, recibo = self.sv.recepcionar_voto(paquete)
        if exito and recibo:
            votante.recibo_emitido = recibo
            self.recibos[id_votante] = recibo

        return exito, msg, recibo

    def fase_conteo(self) -> ResultadoEscrutinio:
        """Fase (f): Cierre de jornada, apertura de ánfora, desencapsulamiento y escrutinio."""
        if not self.sv or not self.ac:
            raise RuntimeError("Autoridades no inicializadas.")

        # Cierre de urna
        urna = self.sv.cerrar_jornada()

        # Escrutinio por la Autoridad de Conteo
        self.resultado = self.ac.realizar_escrutinio(urna)
        return self.resultado


def demo_simulacion():
    """Ejecuta una simulación completa de demostración del protocolo PQC."""
    print("=" * 70)
    print("  SIMULACIÓN END-TO-END DEL PROTOCOLO DE VOTACIÓN PQC")
    print("  Primitivas: ML-KEM-768 (FIPS 203) + ML-DSA-65 (FIPS 204)")
    print("=" * 70)

    proto = ProtocoloVotacionPQC()

    # 1. Setup
    print("[1] Fase (a): Generando claves de AR, SV y AC...")
    t0 = time.time()
    proto.fase_setup()
    t_setup = (time.time() - t0) * 1000
    print(f"    ✓ Claves generadas en {t_setup:.2f} ms")
    print(f"    - PK AR (ML-DSA-65): {len(proto.ar.pk_ar)} bytes")
    print(f"    - EK SV (ML-KEM-768): {len(proto.sv.ek_sv)} bytes")

    # 2. Registro de votantes
    print("\n[2] Fase (b): Registrando votantes y emitiendo credenciales firmadas...")
    votantes_datos = [
        ("CI-1001", "Ana Gomez", "Candidato A (Renovación)"),
        ("CI-1002", "Carlos Mamani", "Candidato B (Progreso)"),
        ("CI-1003", "Elena Quispe", "Candidato A (Renovación)"),
        ("CI-1004", "David Morales", "Candidato C (Unidad)"),
        ("CI-1005", "Lucia Flores", "Candidato A (Renovación)"),
    ]

    for id_v, nom, _ in votantes_datos:
        proto.fase_registro(id_v, nom)
    print(f"    ✓ {len(votantes_datos)} votantes registrados en el padrón electoral.")

    # 3. Emisión y recepción de votos
    print("\n[3] Fases (c, d, e): Emisión de votos cifrados, verificación y recepción...")
    for id_v, nom, opcion in votantes_datos:
        t_voto0 = time.time()
        exito, msg, recibo = proto.fase_emision_y_recepcion(id_v, opcion)
        t_voto = (time.time() - t_voto0) * 1000
        print(f"    - Votante {id_v} ({nom}): {opcion[:25]}... -> {msg} ({t_voto:.2f} ms)")
        assert exito, f"Fallo al emitir voto para {id_v}"

    # 4. Intento de voto duplicado (debe ser rechazado)
    print("\n[4] Prueba de seguridad: Intento de voto duplicado...")
    dup_exito, dup_msg, _ = proto.fase_emision_y_recepcion("CI-1001", "Candidato B (Progreso)")
    print(f"    - Reintento CI-1001: {'ACEPTADO (ERROR)' if dup_exito else 'RECHAZADO CORRECTAMENTE ✓'}")
    print(f"      Motivo: {dup_msg}")
    assert not dup_exito, "El servidor debió rechazar el voto duplicado"

    # 5. Cierre y escrutinio
    print("\n[5] Fase (f): Cierre de jornada electoral y escrutinio final por AC...")
    t_tally0 = time.time()
    resultado = proto.fase_conteo()
    t_tally = (time.time() - t_tally0) * 1000

    print(f"    ✓ Escrutinio finalizado en {t_tally:.2f} ms")
    print(f"    Total votos en urna: {resultado.total_votos}")
    print(f"    Votos válidos contabilizados: {resultado.votos_validos}")
    print(f"    Votos inválidos: {resultado.votos_invalidos}")
    print("\n  RESULTADOS OFICIALES:")
    for cand, votos in sorted(resultado.conteo.items(), key=lambda x: -x[1]):
        pct = (votos / resultado.votos_validos) * 100
        print(f"    • {cand}: {votos} votos ({pct:.1f}%)")

    print("\n" + "=" * 70)
    print("  SIMULACIÓN COMPLETADA EXITOSAMENTE (100% CORRECTO)")
    print("=" * 70)


if __name__ == "__main__":
    demo_simulacion()
