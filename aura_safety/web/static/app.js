/**
 * AURA AI Safety Red Team Agent - Advanced Interactive Application Logic
 */

let currentRunData = null;
let historicalRuns = [];
let registeredStrategies = [];
let strategyChartInstance = null;
let outcomeChartInstance = null;

let activeStatusFilter = "ALL";

document.addEventListener("DOMContentLoaded", async () => {
  // Initialize Lucide Icons
  lucide.createIcons();

  // Setup Navigation Tabs
  setupNavigation();

  // Setup Event Listeners
  setupEventListeners();

  // Setup Presets & Filters
  setupPresetsAndFilters();

  // Load Strategies & Historical Runs
  await Promise.all([
    loadStrategies(),
    loadHistoricalRuns()
  ]);
});

// Toast Notification System
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconName = type === "safe" ? "check-circle" : (type === "unsafe" ? "alert-triangle" : "info");
  toast.innerHTML = `<i data-lucide="${iconName}"></i> <span>${message}</span>`;
  
  container.appendChild(toast);
  lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Setup Navigation Tabs
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const pageTitle = document.getElementById("page-title");
  const pageSubtitle = document.getElementById("page-subtitle");
  const headerBreadcrumb = document.getElementById("header-breadcrumb");

  const titles = {
    overview: { title: "Executive Safety Overview", sub: "Automated policy boundary verification, latent drift analysis & regression tracking", bread: "OVERVIEW" },
    runner: { title: "Live Red Team Evaluation Runner", sub: "Dispatch safety probes and observe real-time model responses", bread: "TEST RUNNER" },
    trajectories: { title: "Probe Trajectory & Outcome Explorer", sub: "Deep inspection of conversational turns, latent leakage & judge reasoning", bread: "TRAJECTORIES" },
    regression: { title: "Safety Regression Matrix", sub: "Comparative benchmark diffing between baseline and candidate models", bread: "REGRESSION" },
    strategies: { title: "Defensive Strategy Matrix", sub: "Taxonomies, threat modeling rationale, and synthetic probe inventories", bread: "STRATEGIES" }
  };

  navItems.forEach(btn => {
    btn.addEventListener("click", () => {
      const tabKey = btn.getAttribute("data-tab");

      navItems.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = document.getElementById(`tab-${tabKey}`);
      if (targetPane) targetPane.classList.add("active");

      if (titles[tabKey]) {
        pageTitle.textContent = titles[tabKey].title;
        pageSubtitle.textContent = titles[tabKey].sub;
        headerBreadcrumb.textContent = titles[tabKey].bread;
      }
    });
  });

  document.getElementById("btn-open-runner").addEventListener("click", () => {
    const runnerNav = document.querySelector('.nav-item[data-tab="runner"]');
    if (runnerNav) runnerNav.click();
  });
}

// Setup Presets and Quick Filter Chips
function setupPresetsAndFilters() {
  // Preset Chips
  const presets = {
    "preset-all": ["direct_policy_probe", "role_instruction_pressure", "multi_turn_persistence", "obfuscated_instruction_phrasing", "sensitive_info_handling"],
    "preset-boundary": ["direct_policy_probe", "role_instruction_pressure"],
    "preset-multiturn": ["multi_turn_persistence"],
    "preset-canary": ["sensitive_info_handling", "obfuscated_instruction_phrasing"],
  };

  Object.keys(presets).forEach(presetId => {
    const btn = document.getElementById(presetId);
    if (!btn) return;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".preset-chip").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");

      const targets = presets[presetId];
      const checkboxes = document.querySelectorAll('input[name="strategy"]');
      let count = 0;
      checkboxes.forEach(cb => {
        cb.checked = targets.includes(cb.value);
        if (cb.checked) count++;
      });
      document.getElementById("selected-strat-count").textContent = `${count} selected`;
      showToast(`Applied preset: ${btn.textContent}`, "info");
    });
  });

  // Quick Status Filter Pills in Trajectories Tab
  const statusPills = document.querySelectorAll(".status-pill-chip");
  statusPills.forEach(pill => {
    pill.addEventListener("click", () => {
      statusPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeStatusFilter = pill.getAttribute("data-filter");
      document.getElementById("filter-outcome").value = activeStatusFilter;
      filterProbesTable();
    });
  });
}

// Setup Event Listeners
function setupEventListeners() {
  // Run Selector Change
  const runSelect = document.getElementById("run-select");
  runSelect.addEventListener("change", async (e) => {
    const runId = e.target.value;
    if (runId) {
      await fetchAndDisplayRun(runId);
      showToast(`Loaded evaluation run: ${runId}`, "info");
    }
  });

  // Export Buttons
  document.getElementById("btn-export-csv").addEventListener("click", () => {
    if (currentRunData) {
      window.location.href = `/api/export/${currentRunData.run_id}/csv`;
      showToast("Downloading CSV Report...", "safe");
    }
  });

  document.getElementById("btn-export-json").addEventListener("click", () => {
    if (currentRunData) {
      window.location.href = `/api/export/${currentRunData.run_id}/json`;
      showToast("Downloading JSON Artifact...", "safe");
    }
  });

  // Live Test Runner Form
  const runForm = document.getElementById("run-form");
  runForm.addEventListener("submit", handleLiveRunSubmit);

  // Target select changes mock-mode visibility
  document.getElementById("run-target").addEventListener("change", (e) => {
    const isMock = e.target.value === "mock";
    document.getElementById("mock-mode-group").style.display = isMock ? "flex" : "none";
  });

  // Probe Filters
  document.getElementById("probe-search").addEventListener("input", filterProbesTable);
  document.getElementById("filter-category").addEventListener("change", filterProbesTable);
  document.getElementById("filter-outcome").addEventListener("change", (e) => {
    activeStatusFilter = e.target.value;
    document.querySelectorAll(".status-pill-chip").forEach(p => {
      p.classList.toggle("active", p.getAttribute("data-filter") === activeStatusFilter);
    });
    filterProbesTable();
  });

  // Regression Button
  document.getElementById("btn-run-regression").addEventListener("click", handleRegressionCompute);

  // Modal Close
  document.getElementById("btn-close-modal").addEventListener("click", () => {
    document.getElementById("trajectory-modal").classList.remove("active");
  });

  document.getElementById("trajectory-modal").addEventListener("click", (e) => {
    if (e.target.id === "trajectory-modal") {
      document.getElementById("trajectory-modal").classList.remove("active");
    }
  });

  // Copy Trajectory Full Log
  document.getElementById("btn-copy-trajectory").addEventListener("click", () => {
    const modalProbeId = document.getElementById("modal-probe-id").textContent;
    const turnsText = Array.from(document.querySelectorAll("#modal-turns .turn-box")).map(box => {
      const turnTitle = box.querySelector(".turn-header").textContent.trim();
      const prompt = box.querySelector(".prompt-block .code-snippet").textContent.trim();
      const response = box.querySelector(".response-block .code-snippet").textContent.trim();
      return `[${turnTitle}]\nUSER: ${prompt}\nMODEL: ${response}`;
    }).join("\n\n---\n\n");

    navigator.clipboard.writeText(`PROBE: ${modalProbeId}\n\n${turnsText}`);
    showToast("Copied full conversational trajectory to clipboard!", "safe");
  });

  // Keyboard shortcut Esc to close modal
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.getElementById("trajectory-modal").classList.remove("active");
    }
  });
}

// Fetch Strategies
async function loadStrategies() {
  try {
    const res = await fetch("/api/strategies");
    const data = await res.json();
    registeredStrategies = data.strategies || [];

    // Populate Checkboxes in Runner
    const checkboxContainer = document.getElementById("strategy-checkboxes");
    checkboxContainer.innerHTML = registeredStrategies.map(s => `
      <label class="checkbox-label">
        <input type="checkbox" name="strategy" value="${s.name}" checked>
        <span><strong>${s.name}</strong> (${s.probes_count} probes)</span>
      </label>
    `).join("");

    // Dynamic strategy checkbox count updater
    checkboxContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.addEventListener("change", () => {
        const count = checkboxContainer.querySelectorAll('input[type="checkbox"]:checked').length;
        document.getElementById("selected-strat-count").textContent = `${count} selected`;
      });
    });

    // Populate Catalog Grid
    const catalogGrid = document.getElementById("strategies-catalog-grid");
    catalogGrid.innerHTML = registeredStrategies.map(s => `
      <div class="strategy-catalog-card">
        <div class="strat-card-header">
          <h4>${s.name}</h4>
          <span class="badge badge-info">${s.category}</span>
        </div>
        <p class="strat-desc">${s.description}</p>
        <div class="strat-footer">
          <span><strong>${s.probes_count}</strong> synthetic probes</span>
          <span>Defensive Evaluation</span>
        </div>
      </div>
    `).join("");

  } catch (err) {
    console.error("Failed to load strategies:", err);
  }
}

// Fetch Historical Runs
async function loadHistoricalRuns() {
  try {
    const res = await fetch("/api/runs");
    const data = await res.json();
    historicalRuns = data.runs || [];

    const runSelect = document.getElementById("run-select");
    const baseSelect = document.getElementById("reg-baseline-select");
    const candSelect = document.getElementById("reg-candidate-select");

    if (historicalRuns.length === 0) {
      runSelect.innerHTML = `<option value="">No historical runs found. Execute a run first.</option>`;
      return;
    }

    const optionsHtml = historicalRuns.map(r => 
      `<option value="${r.run_id}">[${r.target_model}] ${r.run_id} — ${r.safety_score}%</option>`
    ).join("");

    runSelect.innerHTML = optionsHtml;
    baseSelect.innerHTML = optionsHtml;
    candSelect.innerHTML = optionsHtml;

    if (historicalRuns.length > 1) {
      candSelect.selectedIndex = 0;
      baseSelect.selectedIndex = 1;
    }

    // Load first run details
    await fetchAndDisplayRun(historicalRuns[0].run_id);

  } catch (err) {
    console.error("Failed to load runs:", err);
  }
}

// Fetch & Display a Single Run
async function fetchAndDisplayRun(runId) {
  try {
    const res = await fetch(`/api/runs/${runId}`);
    currentRunData = await res.json();
    renderRunData(currentRunData);
  } catch (err) {
    console.error("Failed to fetch run details:", err);
  }
}

// Update Radial Gauge Dial
function updateRadialGauge(score) {
  const circle = document.getElementById("gauge-circle");
  const scoreVal = document.getElementById("radial-score-val");
  const badge = document.getElementById("gauge-alignment-badge");
  const caption = document.getElementById("dial-caption-text");

  const circumference = 2 * Math.PI * 68; // r=68 -> ~427.25
  const offset = circumference - (score / 100) * circumference;

  circle.style.strokeDashoffset = offset;
  scoreVal.textContent = `${score.toFixed(1)}%`;

  if (score >= 90) {
    circle.style.stroke = "#10b981";
    circle.style.filter = "drop-shadow(0 0 8px rgba(16, 185, 129, 0.7))";
    badge.textContent = "ALIGNED & SECURE";
    badge.className = "badge badge-safe";
    caption.textContent = `Target model successfully refused ${score.toFixed(1)}% of safety boundary probes.`;
  } else if (score >= 70) {
    circle.style.stroke = "#f59e0b";
    circle.style.filter = "drop-shadow(0 0 8px rgba(245, 158, 11, 0.7))";
    badge.textContent = "MODERATE DRIFT";
    badge.className = "badge badge-partial";
    caption.textContent = `Target model exhibited partial compliance or soft refusal leakage on some probes.`;
  } else {
    circle.style.stroke = "#ff2a5f";
    circle.style.filter = "drop-shadow(0 0 8px rgba(255, 42, 95, 0.8))";
    badge.textContent = "CRITICAL VULNERABILITY";
    badge.className = "badge badge-unsafe";
    caption.textContent = `Target model fulfilled policy-violating instructions without refusal.`;
  }
}

// Render Run Data
function renderRunData(data) {
  const m = data.metrics || {};
  const results = data.results || [];
  
  // Radial Gauge
  const safetyScore = m.safety_score || 0;
  updateRadialGauge(safetyScore);

  // Nav badges
  document.getElementById("nav-badge-score").textContent = `${safetyScore.toFixed(0)}%`;
  document.getElementById("nav-probes-count").textContent = m.total_probes || results.length;

  // Mini KPI Cards
  document.getElementById("kpi-total-probes").textContent = m.total_probes || 0;
  document.getElementById("kpi-target-info").textContent = `Target: ${data.target_model} (${data.target_provider})`;
  document.getElementById("kpi-refused-count").textContent = m.total_refused || 0;

  const violations = (m.total_non_compliant || 0) + (m.total_partial || 0);
  document.getElementById("kpi-violations-count").textContent = violations;

  const violationPct = m.total_probes > 0 ? ((violations / m.total_probes) * 100).toFixed(1) : "0.0";
  document.getElementById("kpi-violation-pct").textContent = `${violationPct}% DRIFT`;

  document.getElementById("kpi-latency").textContent = `${(m.avg_latency_ms || 0).toFixed(1)} ms`;
  document.getElementById("sidebar-target-name").textContent = `${data.target_model}`;

  // Update Status Filter Chip Counters
  document.getElementById("chip-count-all").textContent = results.length;
  document.getElementById("chip-count-safe").textContent = results.filter(r => r.outcome === "REFUSED").length;
  document.getElementById("chip-count-unsafe").textContent = results.filter(r => r.outcome === "NON_COMPLIANT").length;
  document.getElementById("chip-count-partial").textContent = results.filter(r => r.outcome === "PARTIAL").length;

  // Render Charts
  renderCharts(m);

  // Render Strategy Table
  renderStrategyTable(m.strategy_metrics || []);

  // Render Probes Table
  renderProbesTable(results);

  lucide.createIcons();
}

// Render Charts
function renderCharts(metrics) {
  const stratMetrics = metrics.strategy_metrics || [];
  
  // Strategy Bar Chart
  const ctxStrat = document.getElementById("strategyChart").getContext("2d");
  if (strategyChartInstance) strategyChartInstance.destroy();

  strategyChartInstance = new Chart(ctxStrat, {
    type: "bar",
    data: {
      labels: stratMetrics.map(s => s.strategy_name.replace(/_/g, " ")),
      datasets: [{
        label: "Safety Rate (%)",
        data: stratMetrics.map(s => s.safety_rate),
        backgroundColor: stratMetrics.map(s => s.safety_rate >= 90 ? "rgba(16, 185, 129, 0.75)" : (s.safety_rate >= 70 ? "rgba(245, 158, 11, 0.75)" : "rgba(255, 42, 95, 0.8)")),
        borderColor: stratMetrics.map(s => s.safety_rate >= 90 ? "#10b981" : (s.safety_rate >= 70 ? "#f59e0b" : "#ff2a5f")),
        borderWidth: 1.5,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, max: 100, grid: { color: "rgba(255, 42, 95, 0.08)" }, ticks: { color: "#a1a1aa" } },
        x: { grid: { display: false }, ticks: { color: "#a1a1aa", font: { size: 10 } } }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });

  // Outcome Doughnut Chart
  const ctxOutcome = document.getElementById("outcomeChart").getContext("2d");
  if (outcomeChartInstance) outcomeChartInstance.destroy();

  outcomeChartInstance = new Chart(ctxOutcome, {
    type: "doughnut",
    data: {
      labels: ["Refused (Safe)", "Non-Compliant", "Partial", "Errors"],
      datasets: [{
        data: [
          metrics.total_refused || 0,
          metrics.total_non_compliant || 0,
          metrics.total_partial || 0,
          metrics.total_error || 0,
        ],
        backgroundColor: [
          "rgba(16, 185, 129, 0.85)",
          "rgba(255, 42, 95, 0.9)",
          "rgba(245, 158, 11, 0.85)",
          "rgba(192, 132, 252, 0.85)",
        ],
        borderColor: "#11070c",
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#a1a1aa", font: { size: 11 } }
        }
      }
    }
  });
}

// Render Strategy Table
function renderStrategyTable(stratMetrics) {
  const tbody = document.getElementById("strategy-table-body");
  if (stratMetrics.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center">No strategy breakdown data.</td></tr>`;
    return;
  }

  tbody.innerHTML = stratMetrics.map(s => {
    const rateBadge = s.safety_rate >= 90 ? "badge-safe" : (s.safety_rate >= 70 ? "badge-partial" : "badge-unsafe");
    return `
      <tr>
        <td><strong>${s.strategy_name}</strong></td>
        <td><span class="badge badge-outline">${s.category}</span></td>
        <td>${s.total_probes}</td>
        <td class="text-green font-bold">${s.refused_count}</td>
        <td class="text-crimson font-bold">${s.non_compliant_count}</td>
        <td class="text-yellow font-bold">${s.partial_count}</td>
        <td><span class="badge ${rateBadge}">${s.safety_rate.toFixed(1)}%</span></td>
      </tr>
    `;
  }).join("");
}

// Render Probes Table
function renderProbesTable(results) {
  const tbody = document.getElementById("probes-table-body");
  if (results.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center">No probes found.</td></tr>`;
    return;
  }

  tbody.innerHTML = results.map((r, idx) => {
    const outcomeClass = r.outcome === "REFUSED" ? "badge-safe" : (r.outcome === "NON_COMPLIANT" ? "badge-unsafe" : "badge-partial");
    return `
      <tr data-probe-id="${r.probe_id}" data-category="${r.category}" data-outcome="${r.outcome}">
        <td><code>${r.probe_id}</code></td>
        <td><strong>${r.name}</strong></td>
        <td><span class="badge badge-outline">${r.strategy_name}</span></td>
        <td><span class="badge badge-info">${r.category}</span></td>
        <td><span class="badge ${outcomeClass}">${r.outcome}</span></td>
        <td>${r.total_latency_ms.toFixed(1)} ms</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openTrajectoryModal(${idx})">
            <i data-lucide="eye"></i> Inspect
          </button>
        </td>
      </tr>
    `;
  }).join("");

  filterProbesTable();
  lucide.createIcons();
}

// Filter Probes Table
function filterProbesTable() {
  const search = document.getElementById("probe-search").value.toLowerCase();
  const category = document.getElementById("filter-category").value;
  const outcome = document.getElementById("filter-outcome").value;

  const rows = document.querySelectorAll("#probes-table-body tr");
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    const rowCat = row.getAttribute("data-category");
    const rowOut = row.getAttribute("data-outcome");

    const matchesSearch = text.includes(search);
    const matchesCat = (category === "ALL" || rowCat === category);
    const matchesOut = (outcome === "ALL" || rowOut === outcome);

    row.style.display = (matchesSearch && matchesCat && matchesOut) ? "" : "none";
  });
}

// Open Trajectory Modal
window.openTrajectoryModal = function(index) {
  if (!currentRunData || !currentRunData.results || !currentRunData.results[index]) return;
  const r = currentRunData.results[index];

  document.getElementById("modal-probe-id").textContent = r.probe_id;
  document.getElementById("modal-probe-name").textContent = r.name;
  document.getElementById("modal-category").textContent = r.category;
  document.getElementById("modal-strategy").textContent = r.strategy_name;
  document.getElementById("modal-latency").textContent = `${r.total_latency_ms.toFixed(1)} ms`;

  const isSafe = r.outcome === "REFUSED";
  const verdictEl = document.getElementById("modal-verdict");
  verdictEl.textContent = isSafe ? "SAFE / POLICY COMPLIANT" : "UNSAFE / POLICY VIOLATION";
  verdictEl.className = isSafe ? "text-green" : "text-crimson";

  const modalOutcome = document.getElementById("modal-outcome");
  modalOutcome.textContent = r.outcome;
  modalOutcome.className = `badge ${isSafe ? 'badge-safe' : (r.outcome === 'NON_COMPLIANT' ? 'badge-unsafe' : 'badge-partial')}`;

  document.getElementById("modal-reasoning").textContent = r.reasoning || "Evaluation completed successfully.";

  const turnsContainer = document.getElementById("modal-turns");
  turnsContainer.innerHTML = (r.turns_record || []).map((t, idx) => `
    <div class="turn-box">
      <div class="turn-header">
        <span>Turn ${idx + 1}</span>
        <span>Latency: ${t.latency_ms ? t.latency_ms.toFixed(1) + ' ms' : 'N/A'}</span>
      </div>
      <div class="turn-content">
        <div class="prompt-block">
          <div class="block-label-row">
            <span class="block-label">USER PROBE PROMPT:</span>
            <button class="copy-mini-btn" onclick="copySnippet(this, \`${escapeJs(t.user_prompt)}\`)">Copy</button>
          </div>
          <div class="code-snippet">${escapeHtml(t.user_prompt)}</div>
        </div>
        <div class="response-block">
          <div class="block-label-row">
            <span class="block-label">TARGET MODEL RESPONSE:</span>
            <button class="copy-mini-btn" onclick="copySnippet(this, \`${escapeJs(t.model_response || '')}\`)">Copy</button>
          </div>
          <div class="code-snippet">${escapeHtml(t.model_response || "[No response / Error]")}</div>
        </div>
      </div>
    </div>
  `).join("");

  document.getElementById("trajectory-modal").classList.add("active");
  lucide.createIcons();
};

function copySnippet(btn, text) {
  navigator.clipboard.writeText(text);
  btn.textContent = "Copied!";
  setTimeout(() => btn.textContent = "Copy", 2000);
  showToast("Copied text to clipboard!", "safe");
}

function escapeHtml(text) {
  if (!text) return "";
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeJs(text) {
  if (!text) return "";
  return text.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\${/g, '\\${');
}

// Live Run Submission
async function handleLiveRunSubmit(e) {
  e.preventDefault();
  const target = document.getElementById("run-target").value;
  const mockMode = document.getElementById("run-mock-mode").value;
  const modelOverride = document.getElementById("run-model-override").value.trim() || null;
  const judge = document.getElementById("run-judge").value;

  const checkedStrategies = Array.from(document.querySelectorAll('input[name="strategy"]:checked')).map(cb => cb.value);
  if (checkedStrategies.length === 0) {
    showToast("Please select at least one strategy to run.", "unsafe");
    return;
  }

  const btn = document.getElementById("btn-start-run");
  const statusPill = document.getElementById("runner-status-pill");
  const logBox = document.getElementById("console-logs");
  const progressFill = document.getElementById("runner-progress-fill");
  const progressText = document.getElementById("runner-progress-text");
  const progressPct = document.getElementById("runner-progress-pct");

  btn.disabled = true;
  statusPill.textContent = "RUNNING";
  statusPill.className = "badge badge-partial";

  logBox.innerHTML = "";
  appendLog(`[INIT] Initializing evaluation suite against target '${target}'...`, "info");
  appendLog(`[CONFIG] Selected ${checkedStrategies.length} strategies. Safety Judge: ${judge}`, "dim");
  showToast("Red Team Evaluation Suite dispatched!", "info");

  progressFill.style.width = "30%";
  progressPct.textContent = "30%";
  progressText.textContent = "Dispatching probes to target model...";

  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target,
        model: modelOverride,
        mock_mode: mockMode,
        strategies: checkedStrategies,
        judge,
      })
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Run failed.");
    }

    const report = await res.json();

    progressFill.style.width = "100%";
    progressPct.textContent = "100%";
    progressText.textContent = `${report.metrics.total_probes} / ${report.metrics.total_probes} Completed`;

    appendLog(`[COMPLETE] Run ${report.run_id} finished successfully!`, "info");
    appendLog(`[SUMMARY] Safety Score: ${report.metrics.safety_score}% | Refused: ${report.metrics.total_refused} | Violations: ${report.metrics.total_non_compliant}`, "safe");

    (report.results || []).forEach(r => {
      const tag = r.outcome === "REFUSED" ? "safe" : (r.outcome === "NON_COMPLIANT" ? "unsafe" : "partial");
      appendLog(`  [${r.probe_id}] ${r.name} -> ${r.outcome} (${r.total_latency_ms.toFixed(1)}ms)`, tag);
    });

    statusPill.textContent = "COMPLETED";
    statusPill.className = "badge badge-safe";
    showToast(`Evaluation completed! Safety Score: ${report.metrics.safety_score}%`, "safe");

    // Refresh historical runs and load newly generated report
    await loadHistoricalRuns();
    document.getElementById("run-select").value = report.run_id;
    currentRunData = report;
    renderRunData(report);

  } catch (err) {
    appendLog(`[ERROR] ${err.message}`, "unsafe");
    statusPill.textContent = "FAILED";
    statusPill.className = "badge badge-unsafe";
    showToast(`Evaluation failed: ${err.message}`, "unsafe");
  } finally {
    btn.disabled = false;
  }
}

function appendLog(msg, type = "dim") {
  const logBox = document.getElementById("console-logs");
  const line = document.createElement("div");
  line.className = `log-line ${type}`;
  line.textContent = msg;
  logBox.appendChild(line);
  logBox.scrollTop = logBox.scrollHeight;
}

// Regression Computation
async function handleRegressionCompute() {
  const baseId = document.getElementById("reg-baseline-select").value;
  const candId = document.getElementById("reg-candidate-select").value;

  if (!baseId || !candId) {
    showToast("Please select both baseline and candidate runs.", "unsafe");
    return;
  }

  try {
    const res = await fetch("/api/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ baseline_id: baseId, candidate_id: candId })
    });

    if (!res.ok) throw new Error("Failed to compute regression.");
    const delta = await res.json();

    document.getElementById("regression-kpis").style.display = "grid";
    document.getElementById("regression-table-card").style.display = "block";

    const deltaScoreEl = document.getElementById("reg-delta-score");
    const statusPill = document.getElementById("reg-status-pill");

    deltaScoreEl.textContent = `${delta.score_delta >= 0 ? '+' : ''}${delta.score_delta.toFixed(2)}%`;
    statusPill.textContent = delta.overall_status;
    statusPill.className = `kpi-pill ${delta.overall_status === 'IMPROVED' ? 'badge-safe' : (delta.overall_status === 'DEGRADED' ? 'badge-unsafe' : 'badge-partial')}`;

    document.getElementById("reg-delta-caption").textContent = `Baseline (${delta.target_model_baseline}): ${delta.baseline_score}% | Candidate (${delta.target_model_candidate}): ${delta.candidate_score}%`;
    document.getElementById("reg-regressed-count").textContent = (delta.regressed_probes || []).length;
    document.getElementById("reg-improved-count").textContent = (delta.improved_probes || []).length;

    // Table rows
    const tbody = document.getElementById("regression-diff-body");
    const allDiffs = [
      ...(delta.regressed_probes || []).map(p => ({ ...p, status: "REGRESSED" })),
      ...(delta.improved_probes || []).map(p => ({ ...p, status: "IMPROVED" })),
      ...(delta.unchanged_probes || []).map(p => ({ ...p, status: "UNCHANGED" })),
    ];

    tbody.innerHTML = allDiffs.map(p => {
      const statusBadge = p.status === "REGRESSED" ? "badge-unsafe" : (p.status === "IMPROVED" ? "badge-safe" : "badge-outline");
      return `
        <tr>
          <td><code>${p.probe_id}</code></td>
          <td><strong>${p.name}</strong></td>
          <td><span class="badge badge-outline">${p.strategy_name}</span></td>
          <td><span class="badge ${p.baseline_outcome === 'REFUSED' ? 'badge-safe' : 'badge-unsafe'}">${p.baseline_outcome}</span></td>
          <td><span class="badge ${p.candidate_outcome === 'REFUSED' ? 'badge-safe' : 'badge-unsafe'}">${p.candidate_outcome}</span></td>
          <td><span class="badge ${statusBadge}">${p.status}</span></td>
        </tr>
      `;
    }).join("");

    lucide.createIcons();
    showToast(`Regression diff computed: ${delta.overall_status} (${delta.score_delta >= 0 ? '+' : ''}${delta.score_delta}%)`, delta.overall_status === "IMPROVED" ? "safe" : (delta.overall_status === "DEGRADED" ? "unsafe" : "info"));

  } catch (err) {
    showToast("Regression analysis failed: " + err.message, "unsafe");
  }
}
