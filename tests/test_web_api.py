"""
Pruebas de la API REST del Dashboard Web (Flask).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.web.app import app


class TestWebAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.post("/api/election/reset")

    def test_status_endpoint(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("motor", data)
        self.assertIn("info_cripto", data)
        self.assertEqual(data["motor"], "pqc")

    def test_switch_engine(self):
        res = self.client.post("/api/engine/mode", json={"mode": "clasico"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["motor"], "clasico")

        res = self.client.post("/api/engine/mode", json={"mode": "pqc"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["motor"], "pqc")

    def test_candidates_endpoint(self):
        res = self.client.get("/api/candidates")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(len(data["candidatos"]), 3)

    def test_voters_endpoint(self):
        res = self.client.get("/api/voters")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(len(data["padron"]), 1)

    def test_cast_vote_and_tally_pqc(self):
        # 1. Emitir voto
        res = self.client.post("/api/vote/cast", json={
            "id_votante": "CI-8432190",
            "candidato_id": "CAND-01"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("crypto_breakdown", data)

        # 2. Intento de voto duplicado (debe fallar)
        res_dup = self.client.post("/api/vote/cast", json={
            "id_votante": "CI-8432190",
            "candidato_id": "CAND-02"
        })
        data_dup = res_dup.get_json()
        self.assertFalse(data_dup["success"])

        # 3. Urna
        res_urn = self.client.get("/api/urn")
        self.assertEqual(res_urn.status_code, 200)
        data_urn = res_urn.get_json()
        self.assertEqual(data_urn["total"], 1)

        # 4. Escrutinio
        res_tally = self.client.post("/api/tally")
        self.assertEqual(res_tally.status_code, 200)
        data_tally = res_tally.get_json()
        self.assertTrue(data_tally["success"])
        self.assertEqual(data_tally["votos_validos"], 1)


if __name__ == "__main__":
    unittest.main()
