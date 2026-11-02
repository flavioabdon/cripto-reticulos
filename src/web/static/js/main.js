/**
 * Dashboard & Sistema de Demostración del Protocolo de Votación PQC
 * Frontend Controller (Vanilla JavaScript + Chart.js)
 */

let currentEngine = "pqc";
let selectedCandidateId = null;
let currentVoters = [];
let currentCandidates = [];
let barChart = null;
let donutChart = null;

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initEngineToggle();
    loadSystemStatus();
    loadCandidates();
    loadVoters();
    loadUrn();
});

// ============================================================
// TAB NAVIGATION
// ============================================================
function initTabs() {
    const tabButtons = document.querySelectorAll(".nav-tab[data-tab]");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => {
                b.classList.remove("active");
                b.removeAttribute("aria-current");
            });
            document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            btn.setAttribute("aria-current", "page");
            const targetId = btn.getAttribute("data-tab");
            const targetPanel = document.getElementById(targetId);
            if (targetPanel) {
                targetPanel.classList.add("active");
            }

            // Refrescar datos específicos según pestaña
            if (targetId === "tab-cabin") {
                loadVoterSelector();
                loadCandidateCards();
            } else if (targetId === "tab-urn") {
                loadUrn();
            } else if (targetId === "tab-results") {
                loadResultsView();
            } else if (targetId === "tab-padron") {
                loadVoters();
            }
        });
    });
}

// ============================================================
// ENGINE TOGGLE (PQC vs Clásico)
// ============================================================
function initEngineToggle() {
    const btnPqc = document.getElementById("btn-engine-pqc");
    const btnClassic = document.getElementById("btn-engine-classic");

    // Los eventos ya se manejan en el HTML (inline), aquí solo registramos si no están
    if (!btnPqc._engineListenerAdded) {
        btnPqc.addEventListener("click", () => switchEngine("pqc"));
        btnClassic.addEventListener("click", () => switchEngine("clasico"));
        btnPqc._engineListenerAdded = true;
    }
}

async function switchEngine(mode) {
    try {
        const res = await fetch("/api/engine/mode", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: mode })
        });
        const data = await res.json();
        if (data.success) {
            currentEngine = data.motor;
            updateEngineUI();
            loadSystemStatus();
            loadUrn();
            showNotification(`Motor cambiado a: ${currentEngine === 'pqc' ? 'ML-KEM-768 / ML-DSA-65 (Post-Cuántica)' : 'RSA-2048 / ECDSA (Clásica)'}`, "info");
        }
    } catch (err) {
        console.error("Error al cambiar motor:", err);
    }
}

function updateEngineUI() {
    const btnPqc = document.getElementById("btn-engine-pqc");
    const btnClassic = document.getElementById("btn-engine-classic");
    const badgeEngine = document.getElementById("badge-current-engine");

    if (currentEngine === "pqc") {
        btnPqc.className = "engine-btn active-pqc";
        btnPqc.setAttribute("aria-pressed", "true");
        btnClassic.className = "engine-btn";
        btnClassic.setAttribute("aria-pressed", "false");
        if (badgeEngine) {
            badgeEngine.innerHTML = `<i class="bi bi-cpu" aria-hidden="true"></i> Motor Post-Cuántica`;
            badgeEngine.className = "badge badge-engine badge-engine-pqc";
        }
    } else {
        btnPqc.className = "engine-btn";
        btnPqc.setAttribute("aria-pressed", "false");
        btnClassic.className = "engine-btn active-classic";
        btnClassic.setAttribute("aria-pressed", "true");
        if (badgeEngine) {
            badgeEngine.innerHTML = `<i class="bi bi-lock" aria-hidden="true"></i> Motor Clásico`;
            badgeEngine.className = "badge badge-engine badge-engine-classic";
        }
    }
}

// ============================================================
// STATUS & METRICS
// ============================================================
async function loadSystemStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();

        currentEngine = data.motor || currentEngine;
        updateEngineUI();

        // Actualización segura de métricas (con guards ante elementos ausentes o datos undefined)
        const setEl = (id, val) => {
            const el = document.getElementById(id);
            if (el && val !== undefined && val !== null) el.innerText = val;
        };

        setEl("metric-padron-count", data.total_padron ?? 0);
        setEl("metric-urn-count",    data.votos_urna   ?? data.total_urna ?? 0);
        setEl("metric-participacion", `${data.participacion_pct ?? 0}%`);
        // metric-fase fue eliminado del nuevo diseño — no se actualiza
        setEl("metric-fase", data.fase_electoral); // no-op si el elemento no existe

        const infoCripto = data.info_cripto?.[currentEngine];
        if (infoCripto) {
            setEl("metric-cripto-info", `${infoCripto.kem} + ${infoCripto.dsa}`);
            setEl("metric-cripto-sub",  infoCripto.seguridad);
        }
    } catch (err) {
        console.error("Error cargando estado:", err);
    }
}

// ============================================================
// CANDIDATES
// ============================================================
async function loadCandidates() {
    try {
        const res = await fetch("/api/candidates");
        const data = await res.json();
        currentCandidates = data.candidatos || [];
        loadCandidateCards();
        renderAdminCandidatesTable();
    } catch (err) {
        console.error("Error cargando candidatos:", err);
    }
}

function loadCandidateCards() {
    const container = document.getElementById("ballot-candidates-list");
    if (!container) return;

    container.innerHTML = "";
    currentCandidates.forEach(cand => {
        const card = document.createElement("div");
        card.className = `candidate-option ${selectedCandidateId === cand.id ? 'selected' : ''}`;
        card.setAttribute("data-id", cand.id);
        card.setAttribute("role", "radio");
        card.setAttribute("aria-checked", selectedCandidateId === cand.id ? "true" : "false");
        card.setAttribute("tabindex", "0");
        card.onclick = () => selectCandidate(cand.id);
        card.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') selectCandidate(cand.id); };

        // Usar la inicial del nombre como avatar si no hay icono
        const inicial = cand.nombre ? cand.nombre.charAt(0).toUpperCase() : '?';
        card.innerHTML = `
            <div class="cand-avatar" style="background: ${cand.color}" aria-hidden="true">
                ${inicial}
            </div>
            <div class="cand-info">
                <span class="cand-name">${cand.nombre}</span>
                <span class="cand-party"><span class="badge badge-soft-secondary">${cand.sigla}</span> ${cand.partido}</span>
            </div>
        `;
        container.appendChild(card);
    });
}

function selectCandidate(candId) {
    selectedCandidateId = candId;
    document.querySelectorAll(".candidate-option").forEach(card => {
        if (card.getAttribute("data-id") === candId) {
            card.classList.add("selected");
            card.setAttribute("aria-checked", "true");
        } else {
            card.classList.remove("selected");
            card.setAttribute("aria-checked", "false");
        }
    });

    const btnEmitir = document.getElementById("btn-emitir-voto");
    if (btnEmitir) {
        btnEmitir.removeAttribute("disabled");
    }
}

// ============================================================
// VOTERS & REGISTRATION
// ============================================================
async function loadVoters() {
    try {
        const res = await fetch("/api/voters");
        const data = await res.json();
        currentVoters = data.padron || [];
        renderVotersTable();
        loadVoterSelector();
    } catch (err) {
        console.error("Error cargando votantes:", err);
    }
}

function renderVotersTable() {
    const tbody = document.getElementById("padron-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";
    currentVoters.forEach((v, idx) => {
        const tr = document.createElement("tr");
        const isVotado = v.estado === "YA_VOTO";
        const badgeClass = isVotado ? "badge-success" : "badge-soft-primary";
        const badgeIcon = isVotado ? "bi-check2-all" : "bi-person-check";
        const engineData = v[currentEngine] || {};

        tr.innerHTML = `
            <td><strong>#${idx + 1}</strong></td>
            <td><code>${v.id_votante}</code></td>
            <td><strong>${v.nombre}</strong></td>
            <td>${v.facultad || 'N/A'}</td>
            <td><span class="badge ${badgeClass}"><i class="bi ${badgeIcon}" aria-hidden="true"></i> ${v.estado}</span></td>
            <td>
                <div style="display:flex;align-items:center;gap:6px">
                    <span class="didactic-tag ${currentEngine === 'pqc' ? 'tag-pqc' : 'tag-classical'}">
                        ${currentEngine === 'pqc' ? 'ML-DSA-65' : 'ECDSA'}
                    </span>
                    <code class="text-xs" title="Clave Pública">${engineData.pk_votante_hex?.substring(0, 16) + '...' || 'N/A'}</code>
                </div>
            </td>
            <td>
                <div style="display:flex;gap:4px;flex-wrap:nowrap">
                    <button class="btn btn-outline-primary btn-sm" onclick="showVoterCredentialModal('${v.id_votante}')" title="Inspeccionar credencial y par de claves">
                        <i class="bi bi-key-fill" aria-hidden="true"></i> Claves
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="quickSelectVoter('${v.id_votante}')" ${isVotado ? 'disabled aria-disabled="true"' : ''} title="${isVotado ? 'El ciudadano ya votó' : 'Habilitar para votar'}">
                        <i class="bi bi-check-circle" aria-hidden="true"></i> Votar
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function loadVoterSelector() {
    const select = document.getElementById("select-voter-cabin");
    if (!select) return;

    select.innerHTML = `<option value="">-- Seleccione un Votante Habilitado --</option>`;
    currentVoters.forEach(v => {
        const isVotado = v.estado === "YA_VOTO";
        select.innerHTML += `
            <option value="${v.id_votante}" ${isVotado ? 'disabled' : ''}>
                ${v.id_votante} - ${v.nombre} ${isVotado ? '(YA VOTÓ ✓)' : '(HABILITADO)'}
            </option>
        `;
    });
}

function quickSelectVoter(idVotante) {
    // Cambiar a pestaña de mesa de votación
    document.querySelector('.nav-tab[data-tab="tab-cabin"]').click();
    setTimeout(() => {
        const select = document.getElementById("select-voter-cabin");
        if (select) {
            select.value = idVotante;
        }
    }, 100);
}

// ============================================================
// MODAL DIDÁCTICO: INSPECCIÓN DE CLAVES DEL VOTANTE
// ============================================================
function showVoterCredentialModal(idVotante) {
    const voter = currentVoters.find(v => v.id_votante === idVotante);
    if (!voter) return;

    const modal = document.getElementById("modal-voter-credential");
    const container = document.getElementById("modal-cred-content");
    if (!modal || !container) return;

    const pqc = voter.pqc || {};
    const clasico = voter.clasico || {};
    const isPqc = currentEngine === "pqc";
    const activeData = isPqc ? pqc : clasico;

    container.innerHTML = `
        <div style="margin-bottom:var(--space-2)">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
                <div>
                    <h3 style="font-size:18px;margin:0"><strong>${voter.nombre}</strong></h3>
                    <span style="font-size:13px;color:var(--color-text-muted)">Cédula de Identidad: <code>${voter.id_votante}</code> · ${voter.facultad || 'UMSA'}</span>
                </div>
                <span class="badge ${voter.estado === 'YA_VOTO' ? 'badge-success' : 'badge-soft-primary'}">
                    ${voter.estado === 'YA_VOTO' ? 'YA EMITIÓ SUFRAGIO' : 'HABILITADO EN PADRÓN'}
                </span>
            </div>
        </div>

        <!-- Flujo Didáctico de Emisión -->
        <div class="didactic-box pqc">
            <div class="didactic-title">
                <i class="bi bi-diagram-3-fill text-primary" aria-hidden="true"></i>
                Fases de Generación de Claves (Autoridad de Registro - AR)
            </div>
            <div style="font-size:12px;color:var(--color-text-body);margin-top:4px;line-height:1.45">
                La AR actúa como autoridad certificadora electoral: genera el par asimétrico para el elector y avala su credencial con su clave institucional.
            </div>
        </div>

        <div class="crypto-pipeline" style="margin-top:var(--space-2)">
            <!-- Paso 1 -->
            <div class="pipeline-step completed">
                <div class="pipeline-icon"><i class="bi bi-key-fill" aria-hidden="true"></i></div>
                <div class="pipeline-content">
                    <div class="pipeline-header">
                        <span class="pipeline-title">1. Muestreo de Par de Claves del Elector</span>
                        <span class="didactic-tag ${isPqc ? 'tag-pqc' : 'tag-classical'}">${activeData.algoritmo || (isPqc ? 'ML-DSA-65' : 'ECDSA')}</span>
                    </div>
                    <p class="pipeline-desc">
                        ${isPqc 
                            ? 'Muestreo de vectores en retículos euclidianos (problema M-SIS). Genera una clave privada <code>sk_v</code> (4032 bytes) custodiada por el votante, y una clave pública <code>pk_v</code> (1952 bytes) registrada públicamente.' 
                            : 'Generación de par asimétrico sobre curva elíptica NIST P-256. Clave pública de 64 bytes.'}
                    </p>
                    <div class="pipeline-detail">
                        <strong>Clave Pública (pk_v):</strong> [${activeData.pk_bytes || (isPqc ? 1952 : 64)} bytes]
                        <br><code>${activeData.pk_votante_full || activeData.pk_votante_hex || 'N/A'}</code>
                    </div>
                </div>
            </div>

            <!-- Paso 2 -->
            <div class="pipeline-step completed">
                <div class="pipeline-icon"><i class="bi bi-file-earmark-text-fill" aria-hidden="true"></i></div>
                <div class="pipeline-content">
                    <div class="pipeline-header">
                        <span class="pipeline-title">2. Construcción Canónica de la Credencial</span>
                        <span class="badge badge-info">JSON Canónico</span>
                    </div>
                    <p class="pipeline-desc">
                        Se vincula la identidad cívica con la clave pública generada: <code>{ id_votante: "${voter.id_votante}", pk_votante_hex, timestamp }</code>.
                    </p>
                </div>
            </div>

            <!-- Paso 3 -->
            <div class="pipeline-step completed">
                <div class="pipeline-icon"><i class="bi bi-pen-fill" aria-hidden="true"></i></div>
                <div class="pipeline-content">
                    <div class="pipeline-header">
                        <span class="pipeline-title">3. Firma Institucional de la Autoridad de Registro (AR)</span>
                        <span class="badge badge-soft-success">Firma Válida</span>
                    </div>
                    <p class="pipeline-desc">
                        La AR sella la credencial con su clave privada institucional (<code>sk_AR</code>). Esta firma garantiza al Servidor de Votación que este ciudadano tiene derecho oficial de sufragio.
                    </p>
                    <div class="pipeline-detail">
                        <strong>Firma AR (sig_AR):</strong> [${activeData.sig_bytes || (isPqc ? 3293 : 71)} bytes]
                        <br><code>${activeData.firma_ar_full || activeData.firma_ar_hex || 'N/A'}</code>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tabla Didáctica Comparativa -->
        <article class="card" style="margin-top:var(--space-2);background:var(--gray-100)">
            <div class="card-header" style="padding:10px 14px">
                <h4 style="font-size:13px;margin:0"><strong>Comparativa Criptográfica: Post-Cuántica vs Clásica</strong></h4>
            </div>
            <div class="table-wrapper" style="padding:0">
                <table class="data-table" style="font-size:12px">
                    <thead>
                        <tr>
                            <th>Propiedad</th>
                            <th>Post-Cuántica (FIPS 204)</th>
                            <th>Clásica (NIST P-256)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Algoritmo</strong></td>
                            <td><span class="didactic-tag tag-pqc">ML-DSA-65</span></td>
                            <td><span class="didactic-tag tag-classical">ECDSA P-256</span></td>
                        </tr>
                        <tr>
                            <td><strong>Base Matemática</strong></td>
                            <td>Retículos Euclidianos (M-SIS)</td>
                            <td>Curvas Elípticas (ECDLP)</td>
                        </tr>
                        <tr>
                            <td><strong>Longitud Clave Pública</strong></td>
                            <td><strong>1,952 bytes</strong> (polinomios en R_q)</td>
                            <td><strong>64 bytes</strong> (punto afín)</td>
                        </tr>
                        <tr>
                            <td><strong>Longitud Firma</strong></td>
                            <td><strong>3,293 bytes</strong></td>
                            <td><strong>~71 bytes</strong></td>
                        </tr>
                        <tr>
                            <td><strong>Seguridad Cuántica</strong></td>
                            <td><span class="badge badge-success">Inmune a Shor</span></td>
                            <td><span class="badge badge-danger">Vulnerable a Shor</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </article>
    `;

    modal.classList.remove("d-none");
}

function closeVoterCredentialModal() {
    const modal = document.getElementById("modal-voter-credential");
    if (modal) modal.classList.add("d-none");
}

// Cerrar modal con ESC o clic en el backdrop
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeVoterCredentialModal();
});
document.addEventListener("click", (e) => {
    const modal = document.getElementById("modal-voter-credential");
    if (modal && e.target === modal) closeVoterCredentialModal();
});

// Registro de nuevo votante con flujo didáctico en vivo
async function handleRegisterVoterForm(e) {
    e.preventDefault();
    const id_votante = document.getElementById("input-reg-ci").value.trim();
    const nombre = document.getElementById("input-reg-nombre").value.trim();
    const facultad = document.getElementById("input-reg-facultad").value.trim();

    if (!id_votante || !nombre) {
        showNotification("Debe ingresar CI y Nombre completo.", "danger");
        return;
    }

    const btnSubmit = document.getElementById("btn-submit-register");
    const stepperContainer = document.getElementById("reg-stepper-live");
    const isPqc = currentEngine === "pqc";

    if (btnSubmit) {
        btnSubmit.setAttribute("disabled", "true");
        btnSubmit.innerHTML = `<i class="bi bi-hourglass-split" aria-hidden="true"></i> Generando Claves Criptográficas...`;
    }

    // Renderizar stepper didáctico en progreso
    if (stepperContainer) {
        stepperContainer.innerHTML = `
            <div class="crypto-pipeline" style="margin-top:10px">
                <div class="pipeline-step active" id="p-step-keygen">
                    <div class="pipeline-icon"><i class="bi bi-arrow-repeat" aria-hidden="true"></i></div>
                    <div class="pipeline-content">
                        <div class="pipeline-header">
                            <span class="pipeline-title">Fase 1: Muestreo de Claves ${isPqc ? 'ML-DSA-65 (FIPS 204)' : 'ECDSA P-256'}</span>
                            <span class="badge badge-soft-primary">En proceso...</span>
                        </div>
                        <p class="pipeline-desc">Generando par asimétrico del elector: clave privada <code>sk_v</code> y clave pública <code>pk_v</code>.</p>
                    </div>
                </div>

                <div class="pipeline-step pending" id="p-step-pack">
                    <div class="pipeline-icon"><i class="bi bi-file-earmark-text" aria-hidden="true"></i></div>
                    <div class="pipeline-content">
                        <div class="pipeline-header">
                            <span class="pipeline-title">Fase 2: Serialización Canónica de la Credencial</span>
                            <span class="badge badge-secondary">En espera</span>
                        </div>
                        <p class="pipeline-desc">Empaquetando identificador <code>${id_votante}</code> con la clave pública en formato canónico.</p>
                    </div>
                </div>

                <div class="pipeline-step pending" id="p-step-sign">
                    <div class="pipeline-icon"><i class="bi bi-pen" aria-hidden="true"></i></div>
                    <div class="pipeline-content">
                        <div class="pipeline-header">
                            <span class="pipeline-title">Fase 3: Firma de la Autoridad de Registro (AR)</span>
                            <span class="badge badge-secondary">En espera</span>
                        </div>
                        <p class="pipeline-desc">La AR sella la credencial con su clave privada para habilitar formalmente al elector.</p>
                    </div>
                </div>
            </div>
        `;
    }

    // Pequeño retardo pedagógico para que el usuario perciba la generación
    await new Promise(r => setTimeout(r, 300));

    try {
        const res = await fetch("/api/voters/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_votante, nombre, facultad })
        });
        const data = await res.json();

        if (data.success) {
            const v = data.votante;
            const engineInfo = v[currentEngine] || {};

            // Actualizar stepper a completado
            if (stepperContainer) {
                stepperContainer.innerHTML = `
                    <div class="didactic-box success" style="animation:fadeSlideIn 0.3s ease">
                        <div class="didactic-title">
                            <i class="bi bi-check-circle-fill text-success" aria-hidden="true"></i>
                            ¡Credencial Emitida con Éxito para ${v.nombre}!
                        </div>
                        <p style="margin:4px 0 8px;font-size:12px;color:var(--color-text-body)">
                            Se generó el par de claves <strong>${engineInfo.algoritmo || 'ML-DSA-65'}</strong>. 
                            Clave pública: <strong>${engineInfo.pk_bytes || 1952} bytes</strong> · 
                            Firma de la AR: <strong>${engineInfo.sig_bytes || 3293} bytes</strong>.
                        </p>
                        <div style="display:flex;gap:8px">
                            <button type="button" class="btn btn-outline-primary btn-sm" onclick="showVoterCredentialModal('${v.id_votante}')">
                                <i class="bi bi-key-fill" aria-hidden="true"></i> Ver Credencial Completa
                            </button>
                            <button type="button" class="btn btn-primary btn-sm" onclick="quickSelectVoter('${v.id_votante}')">
                                <i class="bi bi-check2-circle" aria-hidden="true"></i> Ir a Votar
                            </button>
                        </div>
                    </div>
                `;
            }

            showNotification(`Votante ${nombre} registrado con claves ${currentEngine.toUpperCase()} y credencial firmada.`, "success");
            document.getElementById("form-register-voter").reset();
            loadVoters();
            loadSystemStatus();
        } else {
            if (stepperContainer) stepperContainer.innerHTML = "";
            showNotification(data.error || "Error al registrar votante", "danger");
        }
    } catch (err) {
        console.error(err);
        if (stepperContainer) stepperContainer.innerHTML = "";
        showNotification("Error en la solicitud de registro.", "danger");
    } finally {
        if (btnSubmit) {
            btnSubmit.removeAttribute("disabled");
            btnSubmit.innerHTML = `<i class="bi bi-key-fill" aria-hidden="true"></i> Generar Claves y Emitir Credencial`;
        }
    }
}

// ============================================================
// VOTING DESK PROCESSOR (MESA DE VOTACIÓN) (Interactive Cryptographic Breakdown)
// ============================================================
async function handleEmitirVoto() {
    const voterSelect = document.getElementById("select-voter-cabin");
    const id_votante = voterSelect ? voterSelect.value : null;

    if (!id_votante) {
        showNotification("Seleccione un votante habilitado.", "warning");
        return;
    }

    if (!selectedCandidateId) {
        showNotification("Seleccione un candidato en la boleta.", "warning");
        return;
    }

    const btnEmitir = document.getElementById("btn-emitir-voto");
    const container = document.getElementById("crypto-inspection-container");
    const isPqc = currentEngine === "pqc";

    btnEmitir.setAttribute("disabled", "true");
    btnEmitir.innerHTML = `<i class="bi bi-hourglass-split" aria-hidden="true"></i> Cifrando y Firmando...`;

    // Renderizar Pipeline Dinámico en Vivo (Flujo pedagógico interactivo)
    if (container) {
        container.innerHTML = `
            <article class="card" style="border-color: var(--color-primary-main); animation: fadeSlideIn 0.3s ease;">
                <div class="card-header">
                    <h2 class="card-title text-primary">
                        <i class="bi bi-cpu-fill" aria-hidden="true"></i>
                        Procesamiento Criptográfico en Vivo
                    </h2>
                    <span class="badge badge-soft-primary">
                        ${isPqc ? 'ML-KEM-768 + ML-DSA-65 (FIPS 203/204)' : 'RSA-2048 + ECDSA P-256'}
                    </span>
                </div>

                <div class="crypto-pipeline" id="live-crypto-pipeline">
                    <!-- Paso 1 -->
                    <div class="pipeline-step active" id="pipe-step-1">
                        <div class="pipeline-icon"><i class="bi bi-key-fill"></i></div>
                        <div class="pipeline-content">
                            <div class="pipeline-header">
                                <span class="pipeline-title">1. Encapsulamiento KEM (${isPqc ? 'ML-KEM-768 / FIPS 203' : 'RSA-OAEP-2048'})</span>
                                <span class="badge badge-soft-primary" id="badge-p1">Ejecutando...</span>
                            </div>
                            <p class="pipeline-desc">
                                ${isPqc 
                                    ? 'Encapsulando secreto simétrico efímero de 256 bits contra la clave pública del Servidor (<code>ek_sv</code>) mediante retículos M-LWE.' 
                                    : 'Cifrando clave simétrica efímera con la clave pública RSA-2048 del Servidor.'}
                            </p>
                        </div>
                    </div>

                    <!-- Paso 2 -->
                    <div class="pipeline-step pending" id="pipe-step-2">
                        <div class="pipeline-icon"><i class="bi bi-lock-fill"></i></div>
                        <div class="pipeline-content">
                            <div class="pipeline-header">
                                <span class="pipeline-title">2. Cifrado Simétrico del Voto (AES-256-GCM)</span>
                                <span class="badge badge-secondary" id="badge-p2">En espera</span>
                            </div>
                            <p class="pipeline-desc">Cifrando la opción del candidato seleccionado con el secreto derivado y un nonce único de 96 bits.</p>
                        </div>
                    </div>

                    <!-- Paso 3 -->
                    <div class="pipeline-step pending" id="pipe-step-3">
                        <div class="pipeline-icon"><i class="bi bi-pen-fill"></i></div>
                        <div class="pipeline-content">
                            <div class="pipeline-header">
                                <span class="pipeline-title">3. Firma Digital de la Boleta (${isPqc ? 'ML-DSA-65 / FIPS 204' : 'ECDSA P-256'})</span>
                                <span class="badge badge-secondary" id="badge-p3">En espera</span>
                            </div>
                            <p class="pipeline-desc">El elector firma digitalmente el paquete de la boleta con su clave privada única (<code>sk_v</code>). Garantiza no repudio.</p>
                        </div>
                    </div>

                    <!-- Paso 4 -->
                    <div class="pipeline-step pending" id="pipe-step-4">
                        <div class="pipeline-icon"><i class="bi bi-shield-check"></i></div>
                        <div class="pipeline-content">
                            <div class="pipeline-header">
                                <span class="pipeline-title">4. Verificación en Servidor de Votación</span>
                                <span class="badge badge-secondary" id="badge-p4">En espera</span>
                            </div>
                            <p class="pipeline-desc">El Servidor verifica dos firmas criptográficas: la de la AR (credencial legítima) y la del elector (boleta inalterada).</p>
                        </div>
                    </div>

                    <!-- Paso 5 -->
                    <div class="pipeline-step pending" id="pipe-step-5">
                        <div class="pipeline-icon"><i class="bi bi-receipt"></i></div>
                        <div class="pipeline-content">
                            <div class="pipeline-header">
                                <span class="pipeline-title">5. Registro en Ánfora y Recibo (SHA3-256 / FIPS 202)</span>
                                <span class="badge badge-secondary" id="badge-p5">En espera</span>
                            </div>
                            <p class="pipeline-desc">Cálculo del hash SHA3-256 (32 bytes), depósito en urna digital y firma institucional del recibo oficial.</p>
                        </div>
                    </div>
                </div>
            </article>
        `;
    }

    // Progresión pedagógica visible
    const advanceStep = async (stepNum, nextStepNum, badgeText) => {
        const cur = document.getElementById(`pipe-step-${stepNum}`);
        const badgeCur = document.getElementById(`badge-p${stepNum}`);
        if (cur) {
            cur.className = "pipeline-step completed";
            cur.querySelector(".pipeline-icon").innerHTML = `<i class="bi bi-check-lg"></i>`;
        }
        if (badgeCur) {
            badgeCur.className = "badge badge-success";
            badgeCur.innerText = badgeText || "Completado";
        }
        if (nextStepNum) {
            const next = document.getElementById(`pipe-step-${nextStepNum}`);
            const badgeNext = document.getElementById(`badge-p${nextStepNum}`);
            if (next) {
                next.className = "pipeline-step active";
                next.querySelector(".pipeline-icon").innerHTML = `<i class="bi bi-arrow-repeat"></i>`;
            }
            if (badgeNext) {
                badgeNext.className = "badge badge-soft-primary";
                badgeNext.innerText = "Ejecutando...";
            }
        }
    };

    try {
        // Iniciar petición y animación paralela pedagógica
        const startTime = Date.now();
        const requestPromise = fetch("/api/vote/cast", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                id_votante: id_votante,
                candidato_id: selectedCandidateId
            })
        });

        // Transición didáctica paso 1 -> 2
        await new Promise(r => setTimeout(r, 220));
        await advanceStep(1, 2, "KEM Listo");

        // Transición paso 2 -> 3
        await new Promise(r => setTimeout(r, 220));
        await advanceStep(2, 3, "AES-GCM Cifrado");

        // Transición paso 3 -> 4
        await new Promise(r => setTimeout(r, 240));
        await advanceStep(3, 4, "Firma Estampada");

        // Transición paso 4 -> 5
        await new Promise(r => setTimeout(r, 220));
        await advanceStep(4, 5, "Verificado en Servidor");

        const res = await requestPromise;
        const data = await res.json();

        await new Promise(r => setTimeout(r, 200));
        await advanceStep(5, null, "Recibo Generado");

        if (data.success) {
            renderCryptoInspection(data.crypto_breakdown, data.candidato_seleccionado, id_votante);
            showNotification("¡Voto cifrado, firmado y registrado en el ánfora con éxito!", "success");
            loadSystemStatus();
            loadVoters();
            loadUrn();
        } else {
            showNotification(data.error || data.message || "Error al emitir el voto", "danger");
        }
    } catch (err) {
        console.error(err);
        showNotification("Error de red al emitir voto.", "danger");
    } finally {
        btnEmitir.removeAttribute("disabled");
        btnEmitir.innerHTML = `<i class="bi bi-fingerprint" aria-hidden="true"></i> Cifrar Voto y Emitir Sufragio`;
    }
}

function renderCryptoInspection(breakdown, candidato, idVotante) {
    const container = document.getElementById("crypto-inspection-container");
    if (!container) return;

    const isPqc = currentEngine === "pqc";

    container.innerHTML = `
        <article class="card" style="border-color: var(--color-success); animation: fadeSlideIn 0.4s ease;">
            <div class="card-header">
                <div>
                    <h2 class="card-title text-success">
                        <i class="bi bi-shield-check-fill" aria-hidden="true"></i>
                        Voto Criptográficamente Emitido y Registrado
                    </h2>
                    <p class="card-subtitle">Desglose técnico de la boleta depositada en el ánfora digital</p>
                </div>
                <span class="badge badge-soft-success">
                    <i class="bi bi-check-circle-fill" aria-hidden="true"></i> 100% Verificado
                </span>
            </div>

            <!-- Caja didáctica explicativa -->
            <div class="didactic-box ${isPqc ? 'pqc' : 'info'}">
                <div class="didactic-title">
                    <i class="bi bi-mortarboard-fill ${isPqc ? 'text-primary' : 'text-info'}" aria-hidden="true"></i>
                    Didáctica: ¿Por qué este sufragio es seguro?
                </div>
                <div style="font-size:12px;color:var(--color-text-body);line-height:1.45">
                    ${isPqc
                        ? 'Este voto fue blindado mediante una arquitectura híbrida <strong>KEM-DEM + Firma + Hash</strong>. <strong>ML-KEM-768 (FIPS 203)</strong> garantiza confidencialidad ante computadoras cuánticas (Module-LWE); <strong>ML-DSA-65 (FIPS 204)</strong> previene suplantación de identidad (Module-SIS); y <strong>SHA3-256 (FIPS 202)</strong> genera el recibo público sin revelar la opción elegida.'
                        : 'Este voto fue blindado mediante criptografía clásica <strong>RSA-2048 + ECDSA P-256</strong>. Es seguro hoy en día, pero vulnerable ante un computador cuántico que ejecute el algoritmo de Shor.'}
                </div>
            </div>

            <!-- Pipeline Desglosado con métricas -->
            <div class="crypto-inspector" role="log" aria-label="Inspector criptográfico">
                <!-- Paso 1 -->
                <div class="crypto-step">
                    <div class="step-num" aria-hidden="true">1</div>
                    <div class="step-content">
                        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">
                            <span class="step-title">Acuerdo de Clave &amp; Encapsulamiento (${isPqc ? 'ML-KEM-768 FIPS 203' : 'RSA-OAEP-2048'})</span>
                            <span class="badge badge-soft-primary">${breakdown.encaps_time_ms} ms</span>
                        </div>
                        <span style="font-size:12px;color:var(--color-text-muted)">
                            Longitud Ciphertext: <strong>${breakdown.ct_kem_bytes} bytes</strong> · Secreto Compartido: <strong>32 bytes (256 bits)</strong>
                        </span>
                        <code class="step-code">Ciphertext KEM: ${breakdown.ct_kem_preview}</code>
                        <code class="step-code">Shared Secret: ${breakdown.shared_secret_preview}</code>
                    </div>
                </div>

                <!-- Paso 2 -->
                <div class="crypto-step">
                    <div class="step-num" aria-hidden="true">2</div>
                    <div class="step-content">
                        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">
                            <span class="step-title">Cifrado Simétrico del Voto (AES-256-GCM / NIST SP 800-38D)</span>
                            <span class="badge badge-soft-primary">Cifrado Autenticado</span>
                        </div>
                        <span style="font-size:12px;color:var(--color-text-muted)">
                            Opción elegida: <strong>${candidato.nombre} (${candidato.sigla})</strong>
                        </span>
                        <code class="step-code">Voto Cifrado (hex): ${breakdown.voto_cifrado_hex}</code>
                        <code class="step-code">Nonce AEAD (12 bytes): ${breakdown.nonce_hex}</code>
                    </div>
                </div>

                <!-- Paso 3 -->
                <div class="crypto-step">
                    <div class="step-num" aria-hidden="true">3</div>
                    <div class="step-content">
                        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">
                            <span class="step-title">Firma Digital del Elector (${isPqc ? 'ML-DSA-65 FIPS 204' : 'ECDSA NIST P-256'})</span>
                            <span class="badge badge-soft-primary">${breakdown.sign_time_ms} ms</span>
                        </div>
                        <span style="font-size:12px;color:var(--color-text-muted)">
                            Longitud de Firma: <strong>${breakdown.firma_votante_bytes} bytes</strong> · Garantiza No Repudio e Integridad
                        </span>
                        <code class="step-code">Firma Elector: ${breakdown.firma_votante_preview}</code>
                    </div>
                </div>

                <!-- Paso 4 -->
                <div class="crypto-step">
                    <div class="step-num" aria-hidden="true">4</div>
                    <div class="step-content">
                        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">
                            <span class="step-title">Verificación en Servidor de Votación</span>
                            <span class="badge badge-soft-primary">${breakdown.server_verify_time_ms} ms</span>
                        </div>
                        <span style="font-size:12px;color:var(--color-text-muted)">
                            Doble validación: Firma de AR en credencial + Firma de votante en boleta. Latencia Total E2E: <strong>${breakdown.total_time_ms} ms</strong>.
                        </span>
                    </div>
                </div>
            </div>

            <!-- Recibo Oficial de Sufragio -->
            <div class="receipt-box" role="region" aria-label="Recibo oficial de votación">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-1);flex-wrap:wrap;gap:8px">
                    <div style="display:flex;align-items:center;gap:8px">
                        <i class="bi bi-receipt-cutoff text-primary" style="font-size:22px" aria-hidden="true"></i>
                        <div>
                            <strong>RECIBO OFICIAL DE VOTACIÓN DIGITAL</strong>
                            <div style="font-size:11px;color:var(--color-text-muted)">Comprobante inmutable entregado al elector</div>
                        </div>
                    </div>
                    <span class="badge badge-soft-success">
                        <i class="bi bi-shield-lock" aria-hidden="true"></i> Auditoría Universal
                    </span>
                </div>

                <div class="receipt-row">
                    <span class="receipt-label">ID Votante:</span>
                    <span class="receipt-val">${idVotante}</span>
                </div>
                <div class="receipt-row">
                    <span class="receipt-label">Hash Boleta (SHA3-256):</span>
                    <span class="receipt-val" style="color:var(--color-primary-main);font-weight:700">${breakdown.recibo?.hash_boleta_hex || 'N/A'}</span>
                </div>
                <div class="receipt-row">
                    <span class="receipt-label">Firma Servidor (${isPqc ? 'ML-DSA-65' : 'ECDSA'}):</span>
                    <span class="receipt-val">${breakdown.recibo?.firma_servidor_hex?.substring(0, 36) + '...' || 'N/A'}</span>
                </div>
                <div class="receipt-row">
                    <span class="receipt-label">Fecha y Hora de Emisión:</span>
                    <span class="receipt-val">${new Date((breakdown.recibo?.timestamp_recibo || Date.now() / 1000) * 1000).toLocaleString()}</span>
                </div>
            </div>
        </article>
    `;
}

// ============================================================
// DIGITAL URN (Votos Cifrados en Custodia)
// ============================================================
async function loadUrn() {
    try {
        const res = await fetch("/api/urn");
        const data = await res.json();
        const tbody = document.getElementById("urn-table-body");
        if (!tbody) return;

        tbody.innerHTML = "";
        const urnVotes = data.urna || [];

        if (urnVotes.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted" style="padding: 2rem;">El ánfora digital se encuentra vacía. Emita un voto desde la mesa de votación para visualizarlo.</td></tr>`;
            return;
        }

        urnVotes.forEach(v => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>#${v.posicion}</strong></td>
                <td><code>${v.id_votante}</code></td>
                <td><code class="text-xs" title="${v.ciphertext_preview}">${v.ciphertext_preview}</code></td>
                <td><code class="text-xs">${v.voto_cifrado_hex.substring(0, 24)}...</code></td>
                <td><code class="text-xs" title="${v.firma_preview}">${v.firma_preview}</code></td>
                <td><span class="badge badge-soft-success"><i class="bi bi-lock-fill" aria-hidden="true"></i> Cifrado &amp; Firmado</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error cargando urna:", err);
    }
}

// ============================================================
// TALLY & ESCRUTINIO EN TIEMPO REAL
// ============================================================
async function handleRealizarEscrutinio() {
    const btn = document.getElementById("btn-ejecutar-escrutinio");
    btn.setAttribute("disabled", "true");
    btn.innerHTML = `<i class="bi bi-hourglass-split" aria-hidden="true"></i> Desencapsulando y Contabilizando...`;

    try {
        const res = await fetch("/api/tally", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await res.json();

        if (data.success) {
            renderResults(data);
            showNotification(`Escrutinio finalizado en ${data.tiempo_escrutinio_ms} ms. ${data.votos_validos} votos contabilizados.`, "success");
            loadSystemStatus();
        } else {
            showNotification(data.error || "Error al realizar escrutinio.", "danger");
        }
    } catch (err) {
        console.error(err);
        showNotification("Error de red al ejecutar escrutinio.", "danger");
    } finally {
        btn.removeAttribute("disabled");
        btn.innerHTML = `<i class="bi bi-unlock-fill" aria-hidden="true"></i> Aperturar Ánfora y Ejecutar Escrutinio`;
    }
}

function loadResultsView() {
    // Si ya hay escrutinio previo, refrescar gráficos
    const btn = document.getElementById("btn-ejecutar-escrutinio");
    if (btn) {
        // Listo para escrutinio
    }
}

function renderResults(data) {
    const container = document.getElementById("results-content-area");
    if (!container) return;

    container.style.display = "block";

    // Actualizar badges
    const totalEl = document.getElementById("res-total-ánfora") || document.getElementById("res-total-urna");
    if (totalEl) totalEl.innerText = data.total_urna;
    document.getElementById("res-validos").innerText = data.votos_validos;
    document.getElementById("res-invalidos").innerText = data.votos_invalidos;
    document.getElementById("res-tiempo-tally").innerText = `${data.tiempo_escrutinio_ms} ms`;

    // Renderizar tabla de candidatos
    const tbody = document.getElementById("results-table-body");
    tbody.innerHTML = "";

    const labels = [];
    const voteCounts = [];
    const colors = [];

    data.resultados.forEach(item => {
        const cand = item.candidato;
        labels.push(`${cand.sigla}`);
        voteCounts.push(item.votos);
        colors.push(cand.color || '#6366f1');

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="width: 14px; height: 14px; border-radius: 3px; background: ${cand.color};"></div>
                    <strong>${cand.nombre}</strong>
                </div>
            </td>
            <td><span class="badge badge-soft-primary">${cand.sigla}</span> ${cand.partido}</td>
            <td><strong>${item.votos}</strong></td>
            <td>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div style="flex-grow: 1; background: rgba(255,255,255,0.08); height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="width: ${item.porcentaje}%; height: 100%; background: ${cand.color};"></div>
                    </div>
                    <span style="font-weight: 700; min-width: 45px;">${item.porcentaje}%</span>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Renderizar Gráficos Chart.js
    renderCharts(labels, voteCounts, colors);

    // Renderizar Hashes de Auditoría
    renderAuditLogs(data.hashes_auditoria);
}

function renderCharts(labels, data, colors) {
    // 1. Bar Chart
    const ctxBar = document.getElementById("chart-bar-results");
    if (ctxBar) {
        if (barChart) barChart.destroy();
        barChart = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Votos Obtenidos',
                    data: data,
                    backgroundColor: colors,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } }
                }
            }
        });
    }

    // 2. Donut Chart
    const ctxDonut = document.getElementById("chart-donut-results");
    if (ctxDonut) {
        if (donutChart) donutChart.destroy();
        donutChart = new Chart(ctxDonut, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#94a3b8' } }
                }
            }
        });
    }
}

function renderAuditLogs(logs) {
    const tbody = document.getElementById("audit-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";
    (logs || []).forEach(log => {
        const tr = document.createElement("tr");
        const isValid = log.estado.startsWith("VALIDO");
        tr.innerHTML = `
            <td>#${log.posicion + 1}</td>
            <td><code>${log.id_votante}</code></td>
            <td><code class="text-xs">${log.hash_boleta}</code></td>
            <td><span class="badge ${isValid ? 'badge-success' : 'badge-danger'}">${log.estado}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// ============================================================
// ADMIN & ELECTIONS SETUP
// ============================================================
function renderAdminCandidatesTable() {
    const tbody = document.getElementById("admin-candidates-body");
    if (!tbody) return;

    tbody.innerHTML = "";
    currentCandidates.forEach(cand => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><code>${cand.id}</code></td>
            <td><strong>${cand.nombre}</strong></td>
            <td>${cand.partido}</td>
            <td><span class="badge badge-info">${cand.sigla}</span></td>
            <td><div style="width: 20px; height: 20px; border-radius: 4px; background: ${cand.color};"></div></td>
        `;
        tbody.appendChild(tr);
    });
}

async function handleResetElection() {
    if (!confirm("¿Está seguro de reiniciar la elección? Se borrarán todos los votos y el padrón electoral volverá al estado inicial.")) {
        return;
    }

    try {
        const res = await fetch("/api/election/reset", { method: "POST" });
        const data = await res.json();
        if (data.success) {
            showNotification("Elección reiniciada.", "info");
            location.reload();
        }
    } catch (err) {
        console.error(err);
    }
}

// ============================================================
// NOTIFICATIONS / TOAST
// ============================================================
// showNotification está definida en el HTML y usa el sistema AGETIC de toasts.
// Este stub solo existe por compatibilidad por si se llama antes de que el DOM cargue.
if (typeof showNotification === 'undefined') {
    function showNotification(msg, type = "info") {
        console.warn('[PQC-VOTE] Toast:', type, msg);
    }
}
