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
    const tabButtons = document.querySelectorAll(".tab-btn");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
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

    btnPqc.addEventListener("click", () => switchEngine("pqc"));
    btnClassic.addEventListener("click", () => switchEngine("clasico"));
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
        btnClassic.className = "engine-btn";
        if (badgeEngine) {
            badgeEngine.innerHTML = `<i class="fa-solid fa-atom"></i> Motor Post-Cuántica (ML-KEM-768 + ML-DSA-65)`;
            badgeEngine.className = "badge badge-info";
        }
    } else {
        btnPqc.className = "engine-btn";
        btnClassic.className = "engine-btn active-classic";
        if (badgeEngine) {
            badgeEngine.innerHTML = `<i class="fa-solid fa-lock"></i> Motor Clásico (RSA-2048 + ECDSA P-256)`;
            badgeEngine.className = "badge badge-warning";
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

        currentEngine = data.motor;
        updateEngineUI();

        document.getElementById("metric-padron-count").innerText = data.total_padron;
        document.getElementById("metric-urn-count").innerText = data.votos_urna;
        document.getElementById("metric-participacion").innerText = `${data.participacion_pct}%`;
        document.getElementById("metric-fase").innerText = data.fase_electoral;

        const infoCripto = data.info_cripto[data.motor];
        document.getElementById("metric-cripto-info").innerText = `${infoCripto.kem} + ${infoCripto.dsa}`;
        document.getElementById("metric-cripto-sub").innerText = infoCripto.seguridad;
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
        card.className = `candidate-card-option ${selectedCandidateId === cand.id ? 'selected' : ''}`;
        card.setAttribute("data-id", cand.id);
        card.onclick = () => selectCandidate(cand.id);

        card.innerHTML = `
            <div class="cand-avatar" style="background: ${cand.color}">
                <i class="fa-solid fa-${cand.icono}"></i>
            </div>
            <div class="cand-info">
                <div class="cand-name">${cand.nombre}</div>
                <div class="cand-party"><span class="badge badge-info">${cand.sigla}</span> ${cand.partido}</div>
                <div class="cand-propuestas">${cand.propuestas}</div>
            </div>
        `;
        container.appendChild(card);
    });
}

function selectCandidate(candId) {
    selectedCandidateId = candId;
    document.querySelectorAll(".candidate-card-option").forEach(card => {
        if (card.getAttribute("data-id") === candId) {
            card.classList.add("selected");
        } else {
            card.classList.remove("selected");
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
        const badgeClass = isVotado ? "badge-success" : "badge-info";
        const badgeIcon = isVotado ? "check-double" : "user-check";

        tr.innerHTML = `
            <td><strong>#${idx + 1}</strong></td>
            <td><code>${v.id_votante}</code></td>
            <td><strong>${v.nombre}</strong></td>
            <td>${v.facultad || 'N/A'}</td>
            <td><span class="badge ${badgeClass}"><i class="fa-solid fa-${badgeIcon}"></i> ${v.estado}</span></td>
            <td><code class="text-xs" title="Clave Pública">${v[currentEngine]?.pk_votante_hex || 'N/A'}</code></td>
            <td>
                <button class="btn btn-secondary text-xs" onclick="quickSelectVoter('${v.id_votante}')" ${isVotado ? 'disabled' : ''}>
                    <i class="fa-solid fa-booth-curtain"></i> Votar
                </button>
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
    document.querySelector('.tab-btn[data-tab="tab-cabin"]').click();
    setTimeout(() => {
        const select = document.getElementById("select-voter-cabin");
        if (select) {
            select.value = idVotante;
        }
    }, 100);
}

// Registro de nuevo votante
async function handleRegisterVoterForm(e) {
    e.preventDefault();
    const id_votante = document.getElementById("input-reg-ci").value.trim();
    const nombre = document.getElementById("input-reg-nombre").value.trim();
    const facultad = document.getElementById("input-reg-facultad").value.trim();

    if (!id_votante || !nombre) {
        showNotification("Debe ingresar CI y Nombre completo.", "danger");
        return;
    }

    try {
        const res = await fetch("/api/voters/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_votante, nombre, facultad })
        });
        const data = await res.json();
        if (data.success) {
            showNotification(`Votante ${nombre} registrado con claves ${currentEngine.toUpperCase()} y credencial firmada.`, "success");
            document.getElementById("form-register-voter").reset();
            loadVoters();
            loadSystemStatus();
        } else {
            showNotification(data.error || "Error al registrar votante", "danger");
        }
    } catch (err) {
        console.error(err);
        showNotification("Error en la solicitud de registro.", "danger");
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
    btnEmitir.setAttribute("disabled", "true");
    btnEmitir.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Cifrando y Firmando...`;

    try {
        const res = await fetch("/api/vote/cast", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                id_votante: id_votante,
                candidato_id: selectedCandidateId
            })
        });
        const data = await res.json();

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
        btnEmitir.innerHTML = `<i class="fa-solid fa-fingerprint"></i> Cifrar Voto y Emitir Sufragio`;
    }
}

function renderCryptoInspection(breakdown, candidato, idVotante) {
    const container = document.getElementById("crypto-inspection-container");
    if (!container) return;

    const isPqc = currentEngine === "pqc";

    container.innerHTML = `
        <div class="glass-card" style="border-color: rgba(16, 185, 129, 0.4); animation: fadeIn 0.4s ease-out;">
            <div class="card-title-row">
                <div class="card-title text-success">
                    <i class="fa-solid fa-shield-check"></i> Voto Criptográficamente Emitido y Registrado
                </div>
                <span class="badge badge-success"><i class="fa-solid fa-check"></i> 100% Verificado</span>
            </div>

            <div class="crypto-inspector">
                <div class="crypto-step">
                    <div class="step-num">1</div>
                    <div class="step-content">
                        <div class="step-title">Generación de Secreto Compartido & Encapsulamiento (${isPqc ? 'ML-KEM-768 FIPS 203' : 'RSA-OAEP-2048'})</div>
                        <div class="text-sub">Tiempo de ejecución: <strong>${breakdown.encaps_time_ms} ms</strong> | Longitud Ciphertext: <strong>${breakdown.ct_kem_bytes} bytes</strong></div>
                        <div class="step-code">Ciphertext KEM: ${breakdown.ct_kem_preview}</div>
                        <div class="step-code">Shared Secret K: ${breakdown.shared_secret_preview}</div>
                    </div>
                </div>

                <div class="crypto-step">
                    <div class="step-num">2</div>
                    <div class="step-content">
                        <div class="step-title">Cifrado Simétrico del Voto (AES-256-GCM)</div>
                        <div class="text-sub">Candidato cifrado: <code>${candidato.nombre} (${candidato.sigla})</code></div>
                        <div class="step-code">Payload Cifrado: ${breakdown.voto_cifrado_hex}</div>
                        <div class="step-code">Nonce AEAD: ${breakdown.nonce_hex}</div>
                    </div>
                </div>

                <div class="crypto-step">
                    <div class="step-num">3</div>
                    <div class="step-content">
                        <div class="step-title">Firma Digital de la Boleta (${isPqc ? 'ML-DSA-65 FIPS 204' : 'ECDSA NIST P-256'})</div>
                        <div class="text-sub">Tiempo de firma: <strong>${breakdown.sign_time_ms} ms</strong> | Longitud Firma: <strong>${breakdown.firma_votante_bytes} bytes</strong></div>
                        <div class="step-code">Firma Digital Votante: ${breakdown.firma_votante_preview}</div>
                    </div>
                </div>

                <div class="crypto-step">
                    <div class="step-num">4</div>
                    <div class="step-content">
                        <div class="step-title">Verificación en Servidor de Votación & Emisión de Recibo</div>
                        <div class="text-sub">Verificación de firma AR + Votante: <strong>${breakdown.server_verify_time_ms} ms</strong> | Latencia End-to-End: <strong>${breakdown.total_time_ms} ms</strong></div>
                    </div>
                </div>
            </div>

            <!-- Recibo Digital -->
            <div class="receipt-box">
                <div class="receipt-header">
                    <i class="fa-solid fa-receipt text-cyan text-xl"></i>
                    <div>
                        <strong>RECIBO OFICIAL DE VOTACIÓN DIGITAL</strong>
                        <div class="text-sub text-xs">Comprobante inmutable de sufragio emitido</div>
                    </div>
                </div>
                <div class="receipt-row">
                    <span class="label">ID Votante:</span>
                    <span class="val">${idVotante}</span>
                </div>
                <div class="receipt-row">
                    <span class="label">Hash Boleta (SHA3-256):</span>
                    <span class="val">${breakdown.recibo?.hash_boleta_hex || 'N/A'}</span>
                </div>
                <div class="receipt-row">
                    <span class="label">Firma Servidor:</span>
                    <span class="val">${breakdown.recibo?.firma_servidor_hex?.substring(0, 36) + '...' || 'N/A'}</span>
                </div>
                <div class="receipt-row">
                    <span class="label">Timestamp:</span>
                    <span class="val">${new Date((breakdown.recibo?.timestamp_recibo || Date.now() / 1000) * 1000).toLocaleString()}</span>
                </div>
            </div>
        </div>
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
                <td><span class="badge badge-success"><i class="fa-solid fa-lock"></i> Cifrado & Firmado</span></td>
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
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Desencapsulando y Contabilizando...`;

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
        btn.innerHTML = `<i class="fa-solid fa-unlock-keyhole"></i> Aperturar Ánfora y Ejecutar Escrutinio`;
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
    document.getElementById("res-total-urna").innerText = data.total_urna;
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
            <td><span class="badge badge-info">${cand.sigla}</span> ${cand.partido}</td>
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
function showNotification(msg, type = "info") {
    const toast = document.getElementById("toast-notification");
    if (!toast) return;

    toast.innerText = msg;
    toast.className = `toast-box show toast-${type}`;
    setTimeout(() => {
        toast.className = "toast-box";
    }, 4000);
}
