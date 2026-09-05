"""
Orquestador Principal del Protocolo de Votación Clásico (RSA-OAEP + ECDSA).
Ejecuta el flujo idéntico de 6 fases para comparación homogénea con el protocolo PQC:
  (a) Configuración / Setup (AR, SV, AC)
  (b) Registro y emisión de credenciales (AR -> Votantes)
  (c) Cifrado RSA-OAEP y firma ECDSA (Votantes)
  (d) Envío y verificación de firmas ECDSA (Votantes -> SV)
  (e) Registro en la ánfora digital y emisión de recibos ECDSA (SV)
  (f) Descifrado RSA-OAEP y escrutinio final (AC)
"""

import os
import sys
import time
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.clasico.autoridad_registro_clasico import AutoridadRegistroClasico, CredencialVotanteClasico
from src.clasico.servidor_votacion_clasico import ServidorVotacionClasico, ReciboVotacionClasico
from src.clasico.votante_clasico import VotanteClasico, PaqueteVotoClasico
from src.clasico.autoridad_conteo_clasico import AutoridadConteoClasico, ResultadoEscrutinioClasico


class ProtocoloVotacionClasico:
    """Orquestador del protocolo de votación electrónica clásico."""

    def __init__(self, nombre_eleccion: str = "Elecciones Clásicas RSA/ECDSA 2026", rsa_key_size: int = 2048):
        self.nombre_eleccion = nombre_eleccion
        self.rsa_key_size = rsa_key_size
        self.ar: Optional[AutoridadRegistroClasico] = None
        self.sv: Optional[ServidorVotacionClasico] = None
        self.ac: Optional[AutoridadConteoClasico] = None
        self.votantes: Dict[str, VotanteClasico] = {}
        self.recibos: Dict[str, ReciboVotacionClasico] = {}
        self.resultado: Optional[ResultadoEscrutinioClasico] = None

    def fase_setup(self):
        """Fase (a): Configuración y generación de claves de las autoridades."""
        # 1. Autoridad de Registro genera par ECDSA P-256
        self.ar = AutoridadRegistroClasico(nombre=f"{self.nombre_eleccion} - AR")

        # 2. Servidor de Votación genera par RSA (2048 bits) y par ECDSA P-256
        self.sv = ServidorVotacionClasico(pk_ar_ecdsa=self.ar.pk_ar, autoridad_registro=self.ar, rsa_key_size=self.rsa_key_size)

        # 3. Autoridad de Conteo recibe sk_sv_rsa fuera de banda
        sk_sv_rsa = self.sv.obtener_sk_rsa_para_conteo()
        self.ac = AutoridadConteoClasico(sk_servidor_rsa=sk_sv_rsa, pk_ar_ecdsa=self.ar.pk_ar)

    def fase_registro(self, id_votante: str, nombre: str = "") -> VotanteClasico:
        """Fase (b): Registro del votante y emisión de credencial firmada con ECDSA."""
        if not self.ar:
            raise RuntimeError("Debe ejecutar la fase_setup antes de registrar votantes.")

        sk_v, credencial = self.ar.registrar_votante(id_votante, nombre_completo=nombre)
        votante = VotanteClasico(id_votante=id_votante, sk_votante_ecdsa=sk_v, credencial=credencial)
        self.votantes[id_votante] = votante
        return votante

    def fase_emision_y_recepcion(self, id_votante: str, opcion_candidato: str) -> Tuple[bool, str, Optional[ReciboVotacionClasico]]:
        """Fases (c) + (d) + (e): Emisión de voto con RSA-OAEP + ECDSA, verificación en SV y recibo."""
        if id_votante not in self.votantes:
            raise ValueError(f"Votante {id_votante} no registrado.")

        votante = self.votantes[id_votante]

        # Fase (c): Cifrado RSA-OAEP + AES-256-GCM y firma ECDSA
        paquete = votante.emitir_voto(opcion_candidato, self.sv.pk_sv_rsa)

        # Fases (d) + (e): Recepción, verificación de firmas ECDSA, registro y recibo
        exito, msg, recibo = self.sv.recepcionar_voto(paquete)
        if exito and recibo:
            votante.recibo_emitido = recibo
            self.recibos[id_votante] = recibo

        return exito, msg, recibo

    def fase_conteo(self) -> ResultadoEscrutinioClasico:
        """Fase (f): Cierre de urna, descifrado RSA-OAEP y escrutinio final."""
        if not self.sv or not self.ac:
            raise RuntimeError("Autoridades no inicializadas.")

        urna = self.sv.cerrar_jornada()
        self.resultado = self.ac.realizar_escrutinio(urna)
        return self.resultado


def demo_simulacion_clasica():
    """Ejecuta una simulación completa de demostración del protocolo Clásico."""
    print("=" * 70)
    print("  SIMULACIÓN END-TO-END DEL PROTOCOLO DE VOTACIÓN CLÁSICO")
    print("  Primitivas: RSA-OAEP-2048 + ECDSA (P-256)")
    print("=" * 70)

    proto = ProtocoloVotacionClasico()

    # 1. Setup
    print("[1] Fase (a): Generando claves de AR, SV y AC...")
    t0 = time.time()
    proto.fase_setup()
    t_setup = (time.time() - t0) * 1000
    print(f"    ✓ Claves generadas en {t_setup:.2f} ms")
    print(f"    - PK AR (ECDSA P-256): {len(proto.ar.pk_ar)} bytes")
    print(f"    - PK SV (RSA-2048): {len(proto.sv.pk_sv_rsa)} bytes")

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
    print("\n[3] Fases (c, d, e): Emisión de votos cifrados con RSA-OAEP + ECDSA...")
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
    assert not dup_exito

    # 5. Cierre y escrutinio
    print("\n[5] Fase (f): Cierre de jornada y escrutinio final por AC...")
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
    print("  SIMULACIÓN CLÁSICA COMPLETADA EXITOSAMENTE (100% CORRECTO)")
    print("=" * 70)


if __name__ == "__main__":
    demo_simulacion_clasica()
