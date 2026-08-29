"""
Pruebas Unitarias y de Integración para el Protocolo de Votación Clásico (RSA + ECDSA).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.clasico.crypto_clasico import RSACipher, ECDSASigner
from src.clasico.autoridad_registro_clasico import AutoridadRegistroClasico
from src.clasico.servidor_votacion_clasico import ServidorVotacionClasico
from src.clasico.votante_clasico import VotanteClasico
from src.clasico.autoridad_conteo_clasico import AutoridadConteoClasico
from src.clasico.protocolo_clasico import ProtocoloVotacionClasico


class TestClassicalPrimitives(unittest.TestCase):
    """Pruebas de RSA-OAEP y ECDSA P-256."""

    def test_rsa_roundtrip(self):
        pk, sk = RSACipher.generate_keypair(2048)
        secret = os.urandom(32)
        ct = RSACipher.encrypt(pk, secret)
        recovered = RSACipher.decrypt(sk, ct)
        self.assertEqual(secret, recovered)

    def test_ecdsa_roundtrip(self):
        pk, sk = ECDSASigner.generate_keypair()
        msg = b"Mensaje clasico para firma ECDSA"
        sig = ECDSASigner.sign(msg, sk)
        self.assertTrue(ECDSASigner.verify(msg, sig, pk))
        self.assertFalse(ECDSASigner.verify(b"Mensaje alterado", sig, pk))


class TestServidorVotacionClasico(unittest.TestCase):
    """Pruebas del Servidor de Votación Clásico."""

    def setUp(self):
        self.ar = AutoridadRegistroClasico()
        self.sv = ServidorVotacionClasico(self.ar.pk_ar, self.ar)
        self.sk_v, self.cred = self.ar.registrar_votante("CI-500", "Carlos Perez")
        self.votante = VotanteClasico("CI-500", self.sk_v, self.cred)

    def test_recepcion_voto_valido(self):
        paquete = self.votante.emitir_voto("Opcion 1", self.sv.pk_sv_rsa)
        exito, msg, recibo = self.sv.recepcionar_voto(paquete)
        self.assertTrue(exito)
        self.assertIsNotNone(recibo)
        self.assertEqual(len(self.sv.urna), 1)

    def test_rechazo_voto_duplicado(self):
        paquete1 = self.votante.emitir_voto("Opcion 1", self.sv.pk_sv_rsa)
        exito1, _, _ = self.sv.recepcionar_voto(paquete1)
        self.assertTrue(exito1)

        paquete2 = self.votante.emitir_voto("Opcion 2", self.sv.pk_sv_rsa)
        exito2, msg2, _ = self.sv.recepcionar_voto(paquete2)
        self.assertFalse(exito2)
        self.assertIn("ya ha emitido su voto", msg2)

    def test_rechazo_firma_ar_falsificada(self):
        paquete = self.votante.emitir_voto("Opcion 1", self.sv.pk_sv_rsa)
        corrupted = bytearray(paquete.boleta.credencial.firma_ar)
        corrupted[0] ^= 0xFF
        paquete.boleta.credencial.firma_ar = bytes(corrupted)

        exito, msg, _ = self.sv.recepcionar_voto(paquete)
        self.assertFalse(exito)
        self.assertIn("firma de la AR INVÁLIDA", msg)


class TestProtocoloClasicoEndToEnd(unittest.TestCase):
    """Prueba completa end-to-end del protocolo clásico."""

    def test_flujo_completo(self):
        proto = ProtocoloVotacionClasico("Test Eleccion")
        proto.fase_setup()

        proto.fase_registro("V-1", "Votante 1")
        proto.fase_registro("V-2", "Votante 2")

        proto.fase_emision_y_recepcion("V-1", "Candidato X")
        proto.fase_emision_y_recepcion("V-2", "Candidato Y")

        resultado = proto.fase_conteo()
        self.assertEqual(resultado.total_votos, 2)
        self.assertEqual(resultado.votos_validos, 2)
        self.assertEqual(resultado.conteo["Candidato X"], 1)
        self.assertEqual(resultado.conteo["Candidato Y"], 1)


if __name__ == "__main__":
    unittest.main()
