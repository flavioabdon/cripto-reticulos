"""
Backend Web y API REST para el Dashboard y Sistema de Demostración del Protocolo de Votación.
Tesis de Grado: "Protocolo para la votación electrónica basado en criptografía post-cuántica de retículos"
UMSA - Informática
"""

import os
import sys
import time
from typing import Dict, List, Any

# Agregar raíz al sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for

# Importar motores criptográficos
from src.pqc.pqc_wrapper import MLKEM768, MLDSA65
from src.pqc.autoridad_registro import AutoridadRegistro, CredencialVotante
from src.pqc.servidor_votacion import ServidorVotacion, ReciboVotacion
from src.pqc.votante import Votante, PaqueteVoto
from src.pqc.autoridad_conteo import AutoridadConteo, ResultadoEscrutinio

from src.clasico.crypto_clasico import RSACipher, ECDSASigner
from src.clasico.autoridad_registro_clasico import AutoridadRegistroClasico, CredencialVotanteClasico
from src.clasico.servidor_votacion_clasico import ServidorVotacionClasico, ReciboVotacionClasico
from src.clasico.votante_clasico import VotanteClasico, PaqueteVotoClasico
from src.clasico.autoridad_conteo_clasico import AutoridadConteoClasico, ResultadoEscrutinioClasico
from src.pqc.crypto_utils import sha3_256, sha256

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pqc_electoral_umsa_secret_key_2026")

# Credenciales preconfiguradas para jurados y administradores
CREDENTIALS_JURADO = {
    "jurado": "jurado",
    "mesa1": "1234",
}
CREDENTIALS_ADMIN = {
    "admin": "admin",
    "tribunal": "admin2026",
}

# ============================================================
# ESTADO GLOBAL DE LA ELECCIÓN
# ============================================================
class EstadoEleccion:
    def __init__(self):
        self.nombre = "Elecciones Universitarias UMSA 2026"
        self.motor = "pqc"  # 'pqc' o 'clasico'
        self.fase_electoral = "VOTACION_ABIERTA"  # 'CONFIGURACION', 'VOTACION_ABIERTA', 'ESCRUTINIO_FINALIZADO'
        
        # Candidatos registrados
        self.candidatos = [
            {
                "id": "CAND-01",
                "nombre": "Dra. Valeria Ramos",
                "partido": "Frente Renovación Universitaria (FRU)",
                "sigla": "FRU",
                "color": "#6366f1",
                "icono": "graduation-cap",
                "propuestas": "Digitalización académica, laboratorios cuánticos e IA.",
            },
            {
                "id": "CAND-02",
                "nombre": "MSc. Rodrigo Morales",
                "partido": "Unidad y Progreso Estudiantil (UPE)",
                "sigla": "UPE",
                "color": "#ec4899",
                "icono": "rocket",
                "propuestas": "Becas de investigación, convenios internacionales y campus verde.",
            },
            {
                "id": "CAND-03",
                "nombre": "Lic. Sofia Mendoza",
                "partido": "Alianza Innovación & Transparencia (AIT)",
                "sigla": "AIT",
                "color": "#10b981",
                "icono": "shield-check",
                "propuestas": "Transparencia con criptografía post-cuántica y acreditación internacional.",
            },
            {
                "id": "BLANCO",
                "nombre": "Voto Blanco",
                "partido": "Opción Institucional",
                "sigla": "VOTO BLANCO",
                "color": "#64748b",
                "icono": "file",
                "propuestas": "Voto en blanco conforme a normativa electoral.",
            },
        ]
        
        self.inicializar_motores()

    def inicializar_motores(self):
        # 1. Motor Post-Cuántica (PQC)
        self.ar_pqc = AutoridadRegistro(nombre=f"{self.nombre} - AR (ML-DSA-65)")
        self.sv_pqc = ServidorVotacion(pk_ar=self.ar_pqc.pk_ar, autoridad_registro=self.ar_pqc)
        dk_sv_pqc = self.sv_pqc.obtener_dk_para_conteo()
        self.ac_pqc = AutoridadConteo(dk_servidor=dk_sv_pqc, pk_ar=self.ar_pqc.pk_ar)
        self.votantes_pqc: Dict[str, Votante] = {}

        # 2. Motor Clásico (RSA + ECDSA)
        self.ar_clasico = AutoridadRegistroClasico(nombre=f"{self.nombre} - AR (ECDSA P-256)")
        self.sv_clasico = ServidorVotacionClasico(pk_ar_ecdsa=self.ar_clasico.pk_ar, autoridad_registro=self.ar_clasico)
        sk_sv_rsa = self.sv_clasico.obtener_sk_rsa_para_conteo()
        self.ac_clasico = AutoridadConteoClasico(sk_servidor_rsa=sk_sv_rsa, pk_ar_ecdsa=self.ar_clasico.pk_ar)
        self.votantes_clasico: Dict[str, VotanteClasico] = {}

        # Registros de votantes pre-cargados
        self.padron_info: List[dict] = []
        self.historial_votos: List[dict] = []
        self.escrutinio_resultado = None

        # Pre-cargar votantes muestra
        self._cargar_votantes_muestra()

    def _cargar_votantes_muestra(self):
        muestra = [
            ("CI-8432190", "Alejandro Quispe Gutierrez", "Facultad de Ciencias Puras"),
            ("CI-7392014", "Beatriz Mamani Conde", "Carrera de Informática"),
            ("CI-9182304", "Carlos Eduardo Torrez", "Ingeniería de Sistemas"),
            ("CI-6523901", "Daniela Vargas Rojas", "Facultad de Tecnología"),
            ("CI-5182930", "Ernesto Silva Flores", "Carrera de Informática"),
            ("CI-4019283", "Fabiana Morales Choque", "Facultad de Ciencias Puras"),
            ("CI-3918204", "Gonzalo Aruquipa Luna", "Carrera de Informática"),
            ("CI-8823901", "Helena Ticona Quisbert", "Ingeniería Electrónica"),
        ]
        for ci, nom, fac in muestra:
            self.registrar_ciudadano(ci, nom, fac)

    def registrar_ciudadano(self, id_votante: str, nombre: str, facultad: str = "") -> dict:
        # Registrar en motor PQC
        sk_pqc, cred_pqc = self.ar_pqc.registrar_votante(id_votante, nombre)
        votante_pqc = Votante(id_votante, sk_pqc, cred_pqc)
        self.votantes_pqc[id_votante] = votante_pqc

        # Registrar en motor clásico
        sk_clasico, cred_clasico = self.ar_clasico.registrar_votante(id_votante, nombre)
        votante_clasico = VotanteClasico(id_votante, sk_clasico, cred_clasico)
        self.votantes_clasico[id_votante] = votante_clasico

        info = {
            "id_votante": id_votante,
            "nombre": nombre,
            "facultad": facultad,
            "estado": "HABILITADO",
            "timestamp": time.time(),
            "pqc": {
                "algoritmo": "ML-DSA-65 (FIPS 204)",
                "estandar": "FIPS 204 / NIST SP 800-208",
                "base_matematica": "Retículos Euclidianos (M-SIS)",
                "seguridad": "Nivel 3 NIST (Post-Cuántico)",
                "pk_votante_hex": cred_pqc.pk_votante.hex()[:48] + "...",
                "pk_votante_full": cred_pqc.pk_votante.hex(),
                "firma_ar_hex": cred_pqc.firma_ar.hex()[:48] + "...",
                "firma_ar_full": cred_pqc.firma_ar.hex(),
                "pk_bytes": len(cred_pqc.pk_votante),
                "sk_bytes": len(sk_pqc),
                "sig_bytes": len(cred_pqc.firma_ar),
                "ar_pk_hex": self.ar_pqc.pk_ar.hex()[:32] + "...",
            },
            "clasico": {
                "algoritmo": "ECDSA (NIST P-256)",
                "estandar": "FIPS 186-4 / SECG SEC2",
                "base_matematica": "Curvas Elípticas (ECDLP)",
                "seguridad": "128 bits clásico / Vulnerable a Shor",
                "pk_votante_hex": cred_clasico.pk_votante.hex()[:48] + "...",
                "pk_votante_full": cred_clasico.pk_votante.hex(),
                "firma_ar_hex": cred_clasico.firma_ar.hex()[:48] + "...",
                "firma_ar_full": cred_clasico.firma_ar.hex(),
                "pk_bytes": len(cred_clasico.pk_votante),
                "sk_bytes": len(sk_clasico),
                "sig_bytes": len(cred_clasico.firma_ar),
                "ar_pk_hex": self.ar_clasico.pk_ar.hex()[:32] + "...",
            }
        }
        self.padron_info.append(info)
        return info


eleccion = EstadoEleccion()


# ============================================================
# RUTAS HTML Y CONTROL DE VISTAS POR ROL
# ============================================================
@app.route("/")
def index():
    """Redirige según el rol en sesión; si no hay sesión, va al login."""
    u = session.get("user")
    if not u:
        return redirect(url_for("login"))
    rol = u.get("role")
    if rol == "ciudadano":
        return redirect(url_for("vista_ciudadano"))
    elif rol == "jurado":
        return redirect(url_for("vista_jurado"))
    elif rol == "admin":
        return redirect(url_for("vista_admin"))
    return redirect(url_for("login"))


@app.route("/login")
def login():
    """Pantalla unificada de autenticación para Ciudadano, Jurado y Tribunal."""
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Cierra la sesión y redirige al login."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/ciudadano")
def vista_ciudadano():
    """Vista de cabina de votación exclusiva para el elector autenticado."""
    u = session.get("user")
    if not u or u.get("role") != "ciudadano":
        return redirect(url_for("login"))
    return render_template("ciudadano.html", user=u)


@app.route("/jurado")
def vista_jurado():
    """Vista de control de mesa y padrón electoral para el Jurado de Mesa."""
    u = session.get("user")
    if not u or u.get("role") not in ["jurado", "admin"]:
        return redirect(url_for("login"))
    return render_template("jurado.html", user=u)


@app.route("/admin")
def vista_admin():
    """Vista del Tribunal Electoral / Autoridad de Conteo (AC) para escrutinio y ánfora."""
    u = session.get("user")
    if not u or u.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin.html", user=u)


@app.route("/demo")
def vista_demo():
    """Vista de demostración global consolidada (todas las pestañas)."""
    return render_template("index.html")


# ============================================================
# API DE AUTENTICACIÓN
# ============================================================
@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    """
    Autentica al usuario según su rol:
      - 'ciudadano': mediante su CI (id_votante)
      - 'jurado': usuario y contraseña de mesa
      - 'admin': usuario y contraseña de autoridad electoral
    """
    data = request.get_json() or {}
    role = data.get("role", "").lower().strip()

    if role == "ciudadano":
        id_v = data.get("id_votante", "").strip()
        if not id_v:
            return jsonify({"success": False, "error": "Debe ingresar su Cédula de Identidad (CI)."}), 400
        
        votante_info = next((v for v in eleccion.padron_info if v["id_votante"] == id_v), None)
        if not votante_info:
            return jsonify({"success": False, "error": f"El CI '{id_v}' no se encuentra habilitado en el padrón electoral."}), 404

        # Buscar si ya emitió voto para recuperar su recibo
        recibo_existente = next((h["recibo"] for h in eleccion.historial_votos if h["id_votante"] == id_v), None)

        user_data = {
            "role": "ciudadano",
            "id_votante": id_v,
            "nombre": votante_info["nombre"],
            "facultad": votante_info["facultad"],
            "estado": votante_info["estado"],
            "recibo": recibo_existente,
            "pqc_pk_preview": votante_info["pqc"]["pk_votante_hex"],
        }
        session["user"] = user_data
        return jsonify({"success": True, "user": user_data, "redirect": url_for("vista_ciudadano")})

    elif role == "jurado":
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        if CREDENTIALS_JURADO.get(username) == password:
            user_data = {
                "role": "jurado",
                "username": username,
                "nombre": "Jurado Electoral de Mesa",
                "mesa": "Mesa N° 01 — Facultad de Ciencias Puras y Naturales",
                "recinto": "Campus Universitario Cota Cota — Edificio Carrera de Informática",
            }
            session["user"] = user_data
            return jsonify({"success": True, "user": user_data, "redirect": url_for("vista_jurado")})
        return jsonify({"success": False, "error": "Credenciales de Jurado de Mesa incorrectas."}), 401

    elif role == "admin":
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        if CREDENTIALS_ADMIN.get(username) == password:
            user_data = {
                "role": "admin",
                "username": username,
                "nombre": "Tribunal Electoral / Autoridad de Conteo",
                "cargo": "Custodio Criptográfico del Ánfora Digital",
            }
            session["user"] = user_data
            return jsonify({"success": True, "user": user_data, "redirect": url_for("vista_admin")})
        return jsonify({"success": False, "error": "Credenciales de Administrador / Tribunal incorrectas."}), 401

    return jsonify({"success": False, "error": "Rol no reconocido."}), 400


@app.route("/api/auth/logout", methods=["POST", "GET"])
def auth_logout():
    """Limpia la sesión activa."""
    session.clear()
    return jsonify({"success": True, "message": "Sesión cerrada correctamente."})


@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    """Retorna información del usuario en sesión activa."""
    user = session.get("user")
    if not user:
        return jsonify({"authenticated": False})
    
    # Si es ciudadano, actualizar estado desde padrón
    if user.get("role") == "ciudadano":
        id_v = user.get("id_votante")
        v = next((item for item in eleccion.padron_info if item["id_votante"] == id_v), None)
        if v:
            user["estado"] = v["estado"]
            user["recibo"] = next((h["recibo"] for h in eleccion.historial_votos if h["id_votante"] == id_v), None)
            session["user"] = user

    return jsonify({"authenticated": True, "user": user})


@app.route("/api/jury/authorize", methods=["POST"])
def jury_authorize_voter():
    """Acción del jurado: verifica la credencial física y habilita al elector en cabina."""
    data = request.get_json() or {}
    id_v = data.get("id_votante", "").strip()
    v = next((item for item in eleccion.padron_info if item["id_votante"] == id_v), None)
    if not v:
        return jsonify({"success": False, "error": "Votante no encontrado."}), 404
    if v["estado"] == "YA_VOTO":
        return jsonify({"success": False, "error": "El votante ya emitió su sufragio."}), 400
    
    v["estado"] = "HABILITADO_EN_MESA"
    return jsonify({
        "success": True,
        "message": f"Votante '{v['nombre']}' ({id_v}) habilitado para ingresar a cabina.",
        "votante": v
    })


# ============================================================
# ENDPOINTS REST API
# ============================================================
@app.route("/api/status", methods=["GET"])
def get_status():
    """Retorna el estado general del sistema."""
    urna_actual = eleccion.sv_pqc.urna if eleccion.motor == "pqc" else eleccion.sv_clasico.urna
    votantes_total = len(eleccion.padron_info)
    votos_emitidos = len(urna_actual)
    
    return jsonify({
        "nombre_eleccion": eleccion.nombre,
        "motor": eleccion.motor,
        "fase_electoral": eleccion.fase_electoral,
        "total_padron": votantes_total,
        "votos_anfora": votos_emitidos,
        "participacion_pct": round((votos_emitidos / max(1, votantes_total)) * 100, 1),
        "total_candidatos": len(eleccion.candidatos),
        "info_cripto": {
            "pqc": {
                "kem": "ML-KEM-768 (FIPS 203)",
                "dsa": "ML-DSA-65 (FIPS 204)",
                "seguridad": "Nivel 3 NIST (~AES-192) - Post-Cuántica",
                "pk_ar_len": len(eleccion.ar_pqc.pk_ar),
                "ek_sv_len": len(eleccion.sv_pqc.ek_sv),
            },
            "clasico": {
                "kem": "RSA-OAEP-2048",
                "dsa": "ECDSA (NIST P-256)",
                "seguridad": "112-128 bits Clásica (Vulnerable a Shor)",
                "pk_ar_len": len(eleccion.ar_clasico.pk_ar),
                "ek_sv_len": len(eleccion.sv_clasico.pk_sv_rsa),
            }
        }
    })


@app.route("/api/engine/mode", methods=["POST"])
def set_engine_mode():
    """Cambia el motor criptográfico activo: 'pqc' vs 'clasico'."""
    data = request.get_json() or {}
    mode = data.get("mode", "pqc").lower()
    if mode not in ["pqc", "clasico"]:
        return jsonify({"error": "Modo inválido. Use 'pqc' o 'clasico'."}), 400
    eleccion.motor = mode
    return jsonify({"success": True, "motor": eleccion.motor})


@app.route("/api/election/phase", methods=["POST"])
def set_election_phase():
    """Actualiza la fase de la elección: 'CONFIGURACION', 'VOTACION_ABIERTA', 'ESCRUTINIO_FINALIZADO'."""
    data = request.get_json() or {}
    fase = data.get("phase", "VOTACION_ABIERTA")
    eleccion.fase_electoral = fase
    if fase == "VOTACION_ABIERTA":
        eleccion.sv_pqc.jornada_abierta = True
        eleccion.sv_clasico.jornada_abierta = True
    elif fase == "ESCRUTINIO_FINALIZADO":
        eleccion.sv_pqc.jornada_abierta = False
        eleccion.sv_clasico.jornada_abierta = False
    return jsonify({"success": True, "fase_electoral": eleccion.fase_electoral})


@app.route("/api/election/reset", methods=["POST"])
def reset_election():
    """Reinicia la elección al estado inicial."""
    global eleccion
    eleccion = EstadoEleccion()
    return jsonify({"success": True, "message": "Elección reiniciada exitosamente."})


@app.route("/api/candidates", methods=["GET"])
def get_candidates():
    """Lista todos los candidatos registrados."""
    return jsonify({"candidatos": eleccion.candidatos})


@app.route("/api/candidates", methods=["POST"])
def add_candidate():
    """Agrega un nuevo candidato."""
    data = request.get_json() or {}
    cid = f"CAND-{len(eleccion.candidatos) + 1:02d}"
    nuevo = {
        "id": cid,
        "nombre": data.get("nombre", "Nuevo Candidato"),
        "partido": data.get("partido", "Partido Independiente"),
        "sigla": data.get("sigla", "IND"),
        "color": data.get("color", "#8b5cf6"),
        "icono": data.get("icono", "user"),
        "propuestas": data.get("propuestas", "Sin propuestas registradas."),
    }
    # Insertar antes de voto blanco
    eleccion.candidatos.insert(-1, nuevo)
    return jsonify({"success": True, "candidato": nuevo})


@app.route("/api/voters", methods=["GET"])
def get_voters():
    """Lista el padrón de votantes con su estado."""
    return jsonify({"padron": eleccion.padron_info})


@app.route("/api/voters/register", methods=["POST"])
def register_voter():
    """Registra un nuevo votante y emite sus credenciales en ambos motores."""
    data = request.get_json() or {}
    id_v = data.get("id_votante", "").strip()
    nombre = data.get("nombre", "").strip()
    facultad = data.get("facultad", "Universidad Mayor de San Andrés")

    if not id_v or not nombre:
        return jsonify({"error": "Debe proporcionar ID y Nombre del votante."}), 400

    if any(v["id_votante"] == id_v for v in eleccion.padron_info):
        return jsonify({"error": f"El votante '{id_v}' ya está registrado."}), 400

    info = eleccion.registrar_ciudadano(id_v, nombre, facultad)
    return jsonify({"success": True, "votante": info})


@app.route("/api/vote/cast", methods=["POST"])
def cast_vote():
    """
    Ejecuta el flujo de votación desde la mesa de votación con desglose criptográfico pedagógico.
    """
    data = request.get_json() or {}
    id_v = data.get("id_votante", "").strip()
    candidato_id = data.get("candidato_id", "").strip()

    candidato_obj = next((c for c in eleccion.candidatos if c["id"] == candidato_id), None)
    if not candidato_obj:
        return jsonify({"error": "Candidato seleccionado no válido."}), 400

    opcion_str = f"{candidato_obj['id']}: {candidato_obj['nombre']} ({candidato_obj['sigla']})"

    t0 = time.perf_counter()

    if eleccion.motor == "pqc":
        # MOTOR POST-CUÁNTICA
        if id_v not in eleccion.votantes_pqc:
            return jsonify({"error": f"Votante {id_v} no encontrado en el padrón PQC."}), 404

        votante = eleccion.votantes_pqc[id_v]

        # 1. Encapsulamiento y Cifrado
        t_enc0 = time.perf_counter()
        ct_kem, shared_secret = MLKEM768.enc(eleccion.sv_pqc.ek_sv)
        t_enc = (time.perf_counter() - t_enc0) * 1000

        # Cifrado simétrico AES-256-GCM
        from src.pqc.crypto_utils import aes_gcm_encrypt
        voto_cifrado, nonce = aes_gcm_encrypt(shared_secret, opcion_str.encode("utf-8"))

        # 2. Firma de la boleta
        from src.pqc.votante import BoletaSufragio, PaqueteVoto
        ts_v = time.time()
        boleta = BoletaSufragio(ct_kem, voto_cifrado, nonce, votante.credencial, ts_v)
        
        t_sig0 = time.perf_counter()
        firma_v = MLDSA65.sign(boleta.payload_bytes(), votante._sk_votante)
        t_sig = (time.perf_counter() - t_sig0) * 1000

        paquete = PaqueteVoto(boleta, firma_v)

        # 3. Verificación en el Servidor
        t_serv0 = time.perf_counter()
        exito, msg, recibo = eleccion.sv_pqc.recepcionar_voto(paquete)
        t_serv = (time.perf_counter() - t_serv0) * 1000

        t_total = (time.perf_counter() - t0) * 1000

        # Actualizar estado en padrón
        if exito:
            for v in eleccion.padron_info:
                if v["id_votante"] == id_v:
                    v["estado"] = "YA_VOTO"
                    break

        crypto_breakdown = {
            "motor": "ML-KEM-768 + ML-DSA-65 (Post-Cuántica)",
            "encaps_time_ms": round(t_enc, 3),
            "sign_time_ms": round(t_sig, 3),
            "server_verify_time_ms": round(t_serv, 3),
            "total_time_ms": round(t_total, 3),
            "ct_kem_bytes": len(ct_kem),
            "ct_kem_preview": ct_kem.hex()[:48] + "...",
            "shared_secret_preview": shared_secret.hex()[:32] + "...",
            "voto_cifrado_hex": voto_cifrado.hex(),
            "nonce_hex": nonce.hex(),
            "firma_votante_bytes": len(firma_v),
            "firma_votante_preview": firma_v.hex()[:48] + "...",
            "recibo": recibo.to_dict() if recibo else None,
        }

    else:
        # MOTOR CLÁSICO (RSA + ECDSA)
        if id_v not in eleccion.votantes_clasico:
            return jsonify({"error": f"Votante {id_v} no encontrado en el padrón Clásico."}), 404

        votante = eleccion.votantes_clasico[id_v]

        t_enc0 = time.perf_counter()
        k_efimera = os.urandom(32)
        clave_cifrada_rsa = RSACipher.encrypt(eleccion.sv_clasico.pk_sv_rsa, k_efimera)
        t_enc = (time.perf_counter() - t_enc0) * 1000

        from src.clasico.crypto_clasico import aes_gcm_encrypt as aes_gcm_enc_c
        voto_cifrado, nonce = aes_gcm_enc_c(k_efimera, opcion_str.encode("utf-8"))

        from src.clasico.votante_clasico import BoletaSufragioClasico, PaqueteVotoClasico
        ts_v = time.time()
        boleta = BoletaSufragioClasico(clave_cifrada_rsa, voto_cifrado, nonce, votante.credencial, ts_v)

        t_sig0 = time.perf_counter()
        firma_v = ECDSASigner.sign(boleta.payload_bytes(), votante._sk_votante)
        t_sig = (time.perf_counter() - t_sig0) * 1000

        paquete = PaqueteVotoClasico(boleta, firma_v)

        t_serv0 = time.perf_counter()
        exito, msg, recibo = eleccion.sv_clasico.recepcionar_voto(paquete)
        t_serv = (time.perf_counter() - t_serv0) * 1000

        t_total = (time.perf_counter() - t0) * 1000

        if exito:
            for v in eleccion.padron_info:
                if v["id_votante"] == id_v:
                    v["estado"] = "YA_VOTO"
                    break

        crypto_breakdown = {
            "motor": "RSA-OAEP-2048 + ECDSA P-256 (Clásica)",
            "encaps_time_ms": round(t_enc, 3),
            "sign_time_ms": round(t_sig, 3),
            "server_verify_time_ms": round(t_serv, 3),
            "total_time_ms": round(t_total, 3),
            "ct_kem_bytes": len(clave_cifrada_rsa),
            "ct_kem_preview": clave_cifrada_rsa.hex()[:48] + "...",
            "shared_secret_preview": k_efimera.hex()[:32] + "...",
            "voto_cifrado_hex": voto_cifrado.hex(),
            "nonce_hex": nonce.hex(),
            "firma_votante_bytes": len(firma_v),
            "firma_votante_preview": firma_v.hex()[:48] + "...",
            "recibo": recibo.to_dict() if recibo else None,
        }

    if exito and crypto_breakdown.get("recibo"):
        eleccion.historial_votos.append({
            "id_votante": id_v,
            "recibo": crypto_breakdown["recibo"],
            "motor": eleccion.motor,
            "candidato": candidato_obj,
            "timestamp": time.time(),
        })
        if session.get("user") and session["user"].get("id_votante") == id_v:
            session["user"]["estado"] = "YA_VOTO"
            session["user"]["recibo"] = crypto_breakdown["recibo"]

    return jsonify({
        "success": exito,
        "message": msg,
        "crypto_breakdown": crypto_breakdown,
        "candidato_seleccionado": candidato_obj,
    })


@app.route("/api/urn", methods=["GET"])
def get_urn():
    """Retorna los votos cifrados presentes en la urna digital actual."""
    if eleccion.motor == "pqc":
        urna_data = []
        for idx, p in enumerate(eleccion.sv_pqc.urna):
            urna_data.append({
                "posicion": idx + 1,
                "id_votante": p.boleta.credencial.id_votante,
                "ciphertext_preview": p.boleta.ciphertext_kem.hex()[:32] + "...",
                "voto_cifrado_hex": p.boleta.voto_cifrado.hex(),
                "nonce_hex": p.boleta.nonce_aead.hex(),
                "firma_preview": p.firma_votante.hex()[:32] + "...",
                "timestamp": p.boleta.timestamp_emision,
                "hash_boleta": sha3_256(p.boleta.payload_bytes()).hex(),
            })
    else:
        urna_data = []
        for idx, p in enumerate(eleccion.sv_clasico.urna):
            urna_data.append({
                "posicion": idx + 1,
                "id_votante": p.boleta.credencial.id_votante,
                "ciphertext_preview": p.boleta.clave_cifrada_rsa.hex()[:32] + "...",
                "voto_cifrado_hex": p.boleta.voto_cifrado.hex(),
                "nonce_hex": p.boleta.nonce_aead.hex(),
                "firma_preview": p.firma_votante.hex()[:32] + "...",
                "timestamp": p.boleta.timestamp_emision,
                "hash_boleta": sha256(p.boleta.payload_bytes()).hex(),
            })

    return jsonify({
        "total": len(urna_data),
        "motor": eleccion.motor,
        "anfora": urna_data, "urna": urna_data,
    })


@app.route("/api/tally", methods=["POST"])
def perform_tally():
    """
    Ejecuta el proceso de escrutinio oficial:
      Apertura de ánfora, desencapsulamiento seguro y cómputo de resultados.
    """
    t0 = time.perf_counter()

    if eleccion.motor == "pqc":
        urna = eleccion.sv_pqc.cerrar_jornada()
        resultado = eleccion.ac_pqc.realizar_escrutinio(urna)
    else:
        urna = eleccion.sv_clasico.cerrar_jornada()
        resultado = eleccion.ac_clasico.realizar_escrutinio(urna)

    t_tally = (time.perf_counter() - t0) * 1000
    eleccion.fase_electoral = "ESCRUTINIO_FINALIZADO"
    eleccion.escrutinio_resultado = resultado.to_dict()

    # Formatear votos por candidato con información de colores
    resultados_detallados = []
    for cand in eleccion.candidatos:
        # Buscar en conteo por id o nombre
        votos_cand = 0
        for k, v in resultado.conteo.items():
            if k.startswith(cand["id"]):
                votos_cand += v
        
        pct = round((votos_cand / max(1, resultado.votos_validos)) * 100, 2)
        resultados_detallados.append({
            "candidato": cand,
            "votos": votos_cand,
            "porcentaje": pct,
        })

    resultados_detallados.sort(key=lambda x: -x["votos"])

    return jsonify({
        "success": True,
        "motor": eleccion.motor,
        "tiempo_escrutinio_ms": round(t_tally, 2),
        "total_anfora": resultado.total_votos,
        "votos_validos": resultado.votos_validos,
        "votos_invalidos": resultado.votos_invalidos,
        "resultados": resultados_detallados,
        "hashes_auditoria": resultado.hashes_auditoria,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
