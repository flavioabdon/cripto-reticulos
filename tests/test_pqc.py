"""
Pruebas Unitarias y de Integración para el Protocolo de Votación PQC.
Cubre todas las fases y propiedades de seguridad:
  - Primitivas ML-KEM-768 y ML-DSA-65
  - Autoridad de Registro
  - Votante
  - Servidor de Votación (anti-duplicados, verificación de firmas)
  - Autoridad de Conteo (desencapsulamiento y escrutinio)
  - Flujo end-to-end
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pqc.pqc_wrapper import (
    MLKEM768,
    MLDSA65,
    MLKEM768_PUBLIC_KEY_BYTES,
    MLKEM768_SECRET_KEY_BYTES,
    MLKEM768_CIPHERTEXT_BYTES,
    MLKEM768_SHARED_SECRET_BYTES,
    MLDSA65_PUBLIC_KEY_BYTES,
    MLDSA65_SECRET_KEY_BYTES,
    MLDSA65_SIGNATURE_BYTES,
)
from src.pqc.autoridad_registro import AutoridadRegistro, CredencialVotante
from src.pqc.servidor_votacion import ServidorVotacion
from src.pqc.votante import Votante, BoletaSufragio, PaqueteVoto
from src.pqc.autoridad_conteo import AutoridadConteo
from src.pqc.protocolo_pqc import ProtocoloVotacionPQC


class TestPQCPrimitives(unittest.TestCase):
    """Pruebas de las primitivas criptográficas básicas (PQClean)."""

    def test_ml_kem_768_roundtrip(self):
        pk, sk = MLKEM768.keypair()
        self.assertEqual(len(pk), MLKEM768_PUBLIC_KEY_BYTES)
        self.assertEqual(len(sk), MLKEM768_SECRET_KEY_BYTES)

        ct, ss1 = MLKEM768.enc(pk)
        self.assertEqual(len(ct), MLKEM768_CIPHERTEXT_BYTES)
        self.assertEqual(len(ss1), MLKEM768_SHARED_SECRET_BYTES)

        ss2 = MLKEM768.dec(ct, sk)
        self.assertEqual(ss1, ss2)

    def test_ml_dsa_65_roundtrip(self):
        pk, sk = MLDSA65.keypair()
        self.assertEqual(len(pk), MLDSA65_PUBLIC_KEY_BYTES)
        self.assertEqual(len(sk), MLDSA65_SECRET_KEY_BYTES)

        msg = b"Mensaje de prueba para firma digital post-cuantica"
        sig = MLDSA65.sign(msg, sk)
        self.assertEqual(len(sig), MLDSA65_SIGNATURE_BYTES)

        self.assertTrue(MLDSA65.verify(msg, sig, pk))
        self.assertFalse(MLDSA65.verify(b"Mensaje alterado", sig, pk))


class TestAutoridadRegistro(unittest.TestCase):
    """Pruebas del módulo de Autoridad de Registro (AR)."""

    def setUp(self):
        self.ar = AutoridadRegistro("Tribunal Electoral Test")

    def test_registro_votante_exitoso(self):
        sk_v, cred = self.ar.registrar_votante("CI-100", "Juan Perez")
        self.assertEqual(cred.id_votante, "CI-100")
        self.assertEqual(len(sk_v), MLDSA65_SECRET_KEY_BYTES)
        self.assertTrue(self.ar.verificar_credencial(cred))
        self.assertTrue(self.ar.esta_habilitado("CI-100"))

    def test_registro_duplicado_falla(self):
        self.ar.registrar_votante("CI-100", "Juan Perez")
        with self.assertRaises(ValueError):
            self.ar.registrar_votante("CI-100", "Juan Perez Duplicado")


class TestServidorVotacion(unittest.TestCase):
    """Pruebas del Servidor de Votación (SV)."""

    def setUp(self):
        self.ar = AutoridadRegistro()
        self.sv = ServidorVotacion(self.ar.pk_ar, self.ar)
        self.sk_v, self.cred = self.ar.registrar_votante("CI-200", "Maria Gomez")
        self.votante = Votante("CI-200", self.sk_v, self.cred)

    def test_recepcion_voto_valido(self):
        paquete = self.votante.emitir_voto("Candidato 1", self.sv.ek_sv)
        exito, msg, recibo = self.sv.recepcionar_voto(paquete)
        self.assertTrue(exito)
        self.assertIsNotNone(recibo)
        self.assertEqual(len(self.sv.urna), 1)

    def test_rechazo_voto_duplicado(self):
        paquete1 = self.votante.emitir_voto("Candidato 1", self.sv.ek_sv)
        exito1, _, _ = self.sv.recepcionar_voto(paquete1)
        self.assertTrue(exito1)

        # Segundo intento del mismo votante
        paquete2 = self.votante.emitir_voto("Candidato 2", self.sv.ek_sv)
        exito2, msg2, _ = self.sv.recepcionar_voto(paquete2)
        self.assertFalse(exito2)
        self.assertIn("ya ha emitido su voto", msg2)
        self.assertEqual(len(self.sv.urna), 1)

    def test_rechazo_firma_ar_falsificada(self):
        paquete = self.votante.emitir_voto("Candidato 1", self.sv.ek_sv)
        # Falsificar firma de AR alterando el primer byte
        corrupted_firma_ar = bytearray(paquete.boleta.credencial.firma_ar)
        corrupted_firma_ar[0] ^= 0xFF
        paquete.boleta.credencial.firma_ar = bytes(corrupted_firma_ar)

        exito, msg, _ = self.sv.recepcionar_voto(paquete)
        self.assertFalse(exito)
        self.assertIn("firma de la Autoridad de Registro INVÁLIDA", msg)

    def test_rechazo_firma_votante_falsificada(self):
        paquete = self.votante.emitir_voto("Candidato 1", self.sv.ek_sv)
        # Falsificar firma del votante
        corrupted_sig = bytearray(paquete.firma_votante)
        corrupted_sig[0] ^= 0xFF
        paquete.firma_votante = bytes(corrupted_sig)

        exito, msg, _ = self.sv.recepcionar_voto(paquete)
        self.assertFalse(exito)
        self.assertIn("firma digital del votante INVÁLIDA", msg)


class TestAutoridadConteo(unittest.TestCase):
    """Pruebas de la Autoridad de Conteo (AC) y Escrutinio."""

    def test_escrutinio_completo(self):
        proto = ProtocoloVotacionPQC("Eleccion Test")
        proto.fase_setup()

        # Registrar 3 votantes
        proto.fase_registro("CI-1", "Votante 1")
        proto.fase_registro("CI-2", "Votante 2")
        proto.fase_registro("CI-3", "Votante 3")

        # Emitir votos
        proto.fase_emision_y_recepcion("CI-1", "Opcion A")
        proto.fase_emision_y_recepcion("CI-2", "Opcion B")
        proto.fase_emision_y_recepcion("CI-3", "Opcion A")

        # Conteo
        res = proto.fase_conteo()
        self.assertEqual(res.total_votos, 3)
        self.assertEqual(res.votos_validos, 3)
        self.assertEqual(res.votos_invalidos, 0)
        self.assertEqual(res.conteo["Opcion A"], 2)
        self.assertEqual(res.conteo["Opcion B"], 1)


if __name__ == "__main__":
    unittest.main()
