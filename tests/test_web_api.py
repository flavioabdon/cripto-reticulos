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

    def test_auth_ciudadano_flow(self):
        # 1. Acceso a /ciudadano sin sesión debe redirigir a /login
        res_anon = self.client.get("/ciudadano")
        self.assertEqual(res_anon.status_code, 302)
        self.assertIn("/login", res_anon.headers["Location"])

        # 2. Login con CI inválido falla
        res_err = self.client.post("/api/auth/login", json={
            "role": "ciudadano",
            "id_votante": "CI-INEXISTENTE"
        })
        self.assertEqual(res_err.status_code, 404)

        # 3. Login con CI válido
        res_login = self.client.post("/api/auth/login", json={
            "role": "ciudadano",
            "id_votante": "CI-8432190"
        })
        self.assertEqual(res_login.status_code, 200)
        login_data = res_login.get_json()
        self.assertTrue(login_data["success"])
        self.assertEqual(login_data["user"]["id_votante"], "CI-8432190")

        # 4. Verificar sesión con /api/auth/me
        res_me = self.client.get("/api/auth/me")
        self.assertEqual(res_me.status_code, 200)
        self.assertTrue(res_me.get_json()["authenticated"])

        # 5. Con sesión de ciudadano, /ciudadano carga 200
        res_view = self.client.get("/ciudadano")
        self.assertEqual(res_view.status_code, 200)

        # 6. Logout
        res_logout = self.client.get("/logout")
        self.assertEqual(res_logout.status_code, 302)

    def test_auth_jurado_and_admin_flow(self):
        # Jurado sin login es redirigido
        res_jurado_anon = self.client.get("/jurado")
        self.assertEqual(res_jurado_anon.status_code, 302)

        # Login jurado
        res_jurado = self.client.post("/api/auth/login", json={
            "role": "jurado",
            "username": "jurado",
            "password": "jurado"
        })
        self.assertEqual(res_jurado.status_code, 200)
        self.assertTrue(res_jurado.get_json()["success"])

        res_jurado_view = self.client.get("/jurado")
        self.assertEqual(res_jurado_view.status_code, 200)

        # Jurado autoriza a votante en mesa
        res_auth_voter = self.client.post("/api/jury/authorize", json={"id_votante": "CI-7392014"})
        self.assertEqual(res_auth_voter.status_code, 200)
        self.assertTrue(res_auth_voter.get_json()["success"])

        # Logout jurado
        self.client.get("/logout")

        # Admin login
        res_admin = self.client.post("/api/auth/login", json={
            "role": "admin",
            "username": "admin",
            "password": "admin"
        })
        self.assertEqual(res_admin.status_code, 200)

        res_admin_view = self.client.get("/admin")
        self.assertEqual(res_admin_view.status_code, 200)



if __name__ == "__main__":
    unittest.main()
