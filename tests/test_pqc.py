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
    FIPS202,
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
from src.pqc import fips202, fips203, fips204
from src.pqc.autoridad_registro import AutoridadRegistro, CredencialVotante
from src.pqc.servidor_votacion import ServidorVotacion
from src.pqc.votante import Votante, BoletaSufragio, PaqueteVoto
from src.pqc.autoridad_conteo import AutoridadConteo
from src.pqc.protocolo_pqc import ProtocoloVotacionPQC


class TestPQCPrimitives(unittest.TestCase):
    """Pruebas de nuestras implementaciones propias de FIPS 202, FIPS 203 y FIPS 204."""

    def test_fips202_vectors(self):
        # Vector oficial NIST FIPS 202 para SHA3-256("")
        expected_empty = "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"
        self.assertEqual(fips202.sha3_256(b"").hex(), expected_empty)

        # Verificar equivalencia entre motor C propio (fips202.c) y esponja Python pura (KeccakSponge)
        msg = b"Protocolo de votacion electronica UMSA - FIPS 202"
        sponge_py = fips202.KeccakSponge(rate=136, domain_sep=0x06).absorb(msg).squeeze(32)
        self.assertEqual(fips202.sha3_256(msg), sponge_py)

        # SHAKE128 y SHAKE256
        s128_c = fips202.shake128(msg, 64)
        s128_py = fips202.KeccakSponge(rate=168, domain_sep=0x1F).absorb(msg).squeeze(64)
        self.assertEqual(s128_c, s128_py)

        s256_c = fips202.shake256(msg, 64)
        s256_py = fips202.KeccakSponge(rate=136, domain_sep=0x1F).absorb(msg).squeeze(64)
        self.assertEqual(s256_c, s256_py)

    def test_ml_kem_768_roundtrip(self):
        pk, sk = fips203.keygen()
        self.assertEqual(len(pk), MLKEM768_PUBLIC_KEY_BYTES)
        self.assertEqual(len(sk), MLKEM768_SECRET_KEY_BYTES)

        ct, ss1 = fips203.encaps(pk)
        self.assertEqual(len(ct), MLKEM768_CIPHERTEXT_BYTES)
        self.assertEqual(len(ss1), MLKEM768_SHARED_SECRET_BYTES)

        ss2 = fips203.decaps(ct, sk)
        self.assertEqual(ss1, ss2)

        # Prueba determinista (Algoritmos 16 y 17 de FIPS 203)
        d = bytes(range(32))
        z = bytes(range(32, 64))
        m = bytes(range(64, 96))
        ek1, dk1 = fips203.keygen_internal(d, z)
        ek2, dk2 = fips203.keygen_internal(d, z)
        self.assertEqual(ek1, ek2)
        self.assertEqual(dk1, dk2)
        ct_det, k_det = fips203.encaps_internal(ek1, m)
        self.assertEqual(fips203.decaps(ct_det, dk1), k_det)

    def test_ml_dsa_65_roundtrip(self):
        pk, sk = fips204.keygen()
        self.assertEqual(len(pk), MLDSA65_PUBLIC_KEY_BYTES)
        self.assertEqual(len(sk), MLDSA65_SECRET_KEY_BYTES)

        msg = b"Mensaje de prueba para firma digital post-cuantica"
        sig = fips204.sign(msg, sk)
        self.assertEqual(len(sig), MLDSA65_SIGNATURE_BYTES)

        self.assertTrue(fips204.verify(msg, sig, pk))
        self.assertFalse(fips204.verify(b"Mensaje alterado", sig, pk))

        # Prueba determinista de generacion de claves (Algoritmo 6 de FIPS 204)
        xi = bytes(range(32))
        pk1, sk1 = fips204.keygen_internal(xi)
        pk2, sk2 = fips204.keygen_internal(xi)
        self.assertEqual(pk1, pk2)
        self.assertEqual(sk1, sk2)


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
