/**
 * Main Client Application JS for Uzhavan Desk
 */

// Global state
window.UzhavanApp = {
  charts: {}
};

// Toast notification helper
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  
  const toastId = "toast_" + Date.now();
  const bgClass = type === "danger" ? "bg-danger" : type === "warning" ? "bg-warning text-dark" : "bg-success";
  
  const html = `
    <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 mb-2 shadow" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body font-weight-bold">
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>
  `;
  container.insertAdjacentHTML("beforeend", html);
  const el = document.getElementById(toastId);
  const toast = new bootstrap.Toast(el, { delay: 4000 });
  toast.show();
  el.addEventListener("hidden.bs.toast", () => el.remove());
}

// ----------------------------------------------------
// Dashboard Overview Loader
// ----------------------------------------------------
async function loadDashboardOverview() {
  const kpiPlots = document.getElementById("kpiPlots");
  if (!kpiPlots) return;

  try {
    const res = await fetch("/api/overview");
    const data = await res.json();

    document.getElementById("kpiPlots").innerText = `${data.total_plots} (${data.total_acres} ac)`;
    document.getElementById("kpiCrops").innerText = data.active_crops_count;
    document.getElementById("kpiLivestock").innerText = data.total_animals;
    document.getElementById("kpiRevenue").innerText = `₹${data.total_income.toLocaleString("en-IN")}`;
    document.getElementById("kpiExpenses").innerText = `₹${data.total_expense.toLocaleString("en-IN")}`;
    
    const profitEl = document.getElementById("kpiNetProfit");
    profitEl.innerText = `₹${data.net_profit.toLocaleString("en-IN")}`;
    if (data.net_profit >= 0) {
      profitEl.classList.add("text-success");
      profitEl.classList.remove("text-danger");
    } else {
      profitEl.classList.add("text-danger");
      profitEl.classList.remove("text-success");
    }

    // Weather snapshot in dashboard
    if (data.weather_snapshot) {
      const snap = data.weather_snapshot;
      const condText = currentLang === "ta" ? snap.condition_ta : snap.condition;
      const wEl = document.getElementById("dashWeatherText");
      if (wEl) {
        wEl.innerHTML = `<strong>${snap.district}</strong>: ${snap.temp}°C, ${condText} | Rain: ${snap.rain_prob}%`;
      }
    }

    // Render alerts
    renderDashboardAlerts(data.alerts);

  } catch (err) {
    console.error("Dashboard overview load error:", err);
  }
}

function renderDashboardAlerts(alerts) {
  const container = document.getElementById("dashAlertsContainer");
  if (!container) return;

  if (!alerts || alerts.length === 0) {
    container.innerHTML = `
      <div class="alert alert-light border text-muted d-flex align-items-center">
        <i class="bi bi-check-circle-fill text-success fs-4 me-2"></i>
        <span data-i18n="no_alerts">${t("no_alerts")}</span>
      </div>
    `;
    return;
  }

  let html = "";
  alerts.forEach(a => {
    const title = currentLang === "ta" ? (a.title_ta || a.title) : a.title;
    const msg = currentLang === "ta" ? (a.message_ta || a.message) : a.message;
    const badgeColor = a.urgency === "danger" ? "bg-danger" : a.urgency === "warning" ? "bg-warning text-dark" : "bg-info text-dark";

    html += `
      <div class="alert-card ${a.urgency}">
        <div class="d-flex justify-content-between align-items-start mb-1">
          <strong class="text-dark">${title}</strong>
          <span class="badge ${badgeColor}">${a.days_left > 0 ? a.days_left + "d left" : "Today!"}</span>
        </div>
        <div class="small text-secondary">${msg}</div>
      </div>
    `;
  });
  container.innerHTML = html;
}

// ----------------------------------------------------
// Mandi Prices Loader & Filter
// ----------------------------------------------------
async function loadMandiPrices() {
  const tableBody = document.getElementById("mandiTableBody");
  if (!tableBody) return;

  const district = document.getElementById("mandiDistrictSelect")?.value || "";
  const search = document.getElementById("mandiSearchInput")?.value || "";

  tableBody.innerHTML = `<tr><td colspan="9" class="text-center py-4"><div class="spinner-border text-success" role="status"></div></td></tr>`;

  try {
    const res = await fetch(`/api/mandi/prices?district=${encodeURIComponent(district)}&search=${encodeURIComponent(search)}`);
    const prices = await res.json();

    if (!prices || prices.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="9" class="text-center py-4 text-muted">No commodity records found for the selected filter.</td></tr>`;
      return;
    }

    let rows = "";
    prices.forEach((p, idx) => {
      const commName = currentLang === "ta" ? (p.commodity_ta || p.commodity) : p.commodity;
      const changeClass = p.price_change_pct >= 0 ? "price-up" : "price-down";
      const changeSign = p.price_change_pct >= 0 ? "+" : "";

      rows += `
        <tr>
          <td>
            <strong>${commName}</strong>
            ${p.is_local ? `<span class="badge bg-success-subtle text-success border ms-1"><i class="bi bi-geo-alt-fill"></i> Local</span>` : ""}
            <div class="small text-muted">${p.variety}</div>
          </td>
          <td>${p.market}</td>
          <td>
            <span class="badge ${p.is_local ? 'bg-success text-white' : 'bg-light text-dark border'}">${p.district}</span>
          </td>
          <td>
            <span class="badge bg-success-subtle text-success border font-monospace fw-bold px-2 py-1">${p.rate_per_kg_str || '-'}</span>
          </td>
          <td class="tabular-nums">₹${p.min_price.toLocaleString("en-IN")}</td>
          <td class="tabular-nums">₹${p.max_price.toLocaleString("en-IN")}</td>
          <td><span class="price-pill tabular-nums">₹${p.modal_price.toLocaleString("en-IN")}</span> <span class="small text-muted">${p.unit}</span></td>
          <td>
            <span class="${changeClass} fw-bold tabular-nums">
              ${changeSign}${p.price_change_pct}%
            </span>
          </td>
          <td>
            <button class="btn btn-sm btn-outline-success" onclick="viewPriceTrend('${p.commodity}')" title="View 15-day trend">
              <i class="bi bi-graph-up"></i>
            </button>
          </td>
        </tr>
      `;
    });
    tableBody.innerHTML = rows;

  } catch (err) {
    console.error("Mandi prices load error:", err);
  }
}

async function viewPriceTrend(commodityName) {
  const chartCanvas = document.getElementById("mandiTrendChart");
  if (!chartCanvas) return;

  const modalEl = document.getElementById("trendModal");
  const modal = new bootstrap.Modal(modalEl);
  document.getElementById("trendModalTitle").innerText = `${commodityName} - 15 Day Price Trend`;
  modal.show();

  try {
    const res = await fetch(`/api/mandi/trend?commodity=${encodeURIComponent(commodityName)}`);
    const history = await res.json();

    const labels = history.map(h => h.date);
    const dataPoints = history.map(h => h.price);

    if (window.UzhavanApp.charts["trend"]) {
      window.UzhavanApp.charts["trend"].destroy();
    }

    const ctx = chartCanvas.getContext("2d");
    window.UzhavanApp.charts["trend"] = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Modal Price (₹)",
          data: dataPoints,
          borderColor: "#15803d",
          backgroundColor: "rgba(21, 128, 61, 0.1)",
          fill: true,
          tension: 0.3,
          pointRadius: 4,
          pointBackgroundColor: "#15803d"
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: false,
            ticks: {
              callback: val => "₹" + val
            }
          }
        }
      }
    });

  } catch (err) {
    console.error("Trend load error:", err);
  }
}

// ----------------------------------------------------
// Crops & Plots Management
// ----------------------------------------------------
async function loadCropsAndPlots() {
  const cropsContainer = document.getElementById("cropsContainer");
  const plotsContainer = document.getElementById("plotsContainer");
  if (!cropsContainer && !plotsContainer) return;

  try {
    const [cropsRes, plotsRes] = await Promise.all([
      fetch("/api/crops"),
      fetch("/api/plots")
    ]);
    const crops = await cropsRes.json();
    const plots = await plotsRes.json();

    // Populate plot dropdown in planting modal
    const plotSelect = document.getElementById("cropPlotId");
    if (plotSelect) {
      plotSelect.innerHTML = `<option value="">-- Select Plot --</option>` + 
        plots.map(p => `<option value="${p.id}">${p.name} (${p.area_acres} ac)</option>`).join("");
    }

    // Render plots
    if (plotsContainer) {
      if (plots.length === 0) {
        plotsContainer.innerHTML = `<p class="text-muted small">No farmland plots registered yet.</p>`;
      } else {
        let pHtml = "";
        plots.forEach(p => {
          pHtml += `
            <div class="col-md-6 mb-3">
              <div class="card card-custom p-3 h-100">
                <div class="d-flex justify-content-between align-items-start">
                  <h6 class="fw-bold mb-1">${p.name}</h6>
                  <button class="btn btn-sm btn-link text-danger p-0" onclick="deletePlot('${p.id}')">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
                <div class="small text-secondary mb-2">Survey No: ${p.survey_no || "N/A"}</div>
                <div class="row g-2 mt-auto">
                  <div class="col-6"><span class="badge bg-success-subtle text-success border">${p.area_acres} Acres</span></div>
                  <div class="col-6 text-end small text-muted">${p.soil_type}</div>
                </div>
              </div>
            </div>
          `;
        });
        plotsContainer.innerHTML = pHtml;
      }
    }

    // Render crops
    if (cropsContainer) {
      if (crops.length === 0) {
        cropsContainer.innerHTML = `<div class="col-12 text-center py-4 text-muted">No crops currently planted. Click "Plant New Crop" to add one!</div>`;
      } else {
        let cHtml = "";
        crops.forEach(c => {
          cHtml += `
            <div class="col-md-6 mb-4">
              <div class="card card-custom p-3 h-100 border-start border-4 border-success">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <h5 class="fw-bold mb-0 text-success">${c.crop_name}</h5>
                    <span class="small text-muted">${c.variety} | ${c.season}</span>
                  </div>
                  <span class="badge bg-success">${c.status}</span>
                </div>
                <hr class="my-2">
                <div class="small text-secondary mb-2">
                  <i class="bi bi-geo-alt"></i> <strong>Plot:</strong> ${c.plot_name || "Plot"} (${c.area_cultivated_acres || "All"} ac)
                </div>
                <div class="small mb-1">
                  <strong>Stage:</strong> <span class="badge bg-warning-subtle text-dark">${c.stage}</span>
                </div>
                <div class="small text-muted mb-2">
                  <i class="bi bi-calendar-event"></i> Sown: ${c.sowing_date} | Harvest: ${c.expected_harvest || "TBD"}
                </div>
                ${c.notes ? `<div class="small bg-light p-2 rounded text-muted mb-3">${c.notes}</div>` : ""}
                <div class="d-flex gap-2 mt-auto">
                  <button class="btn btn-sm btn-outline-success" onclick="advanceCropStage('${c.id}', '${c.stage}')">
                    <i class="bi bi-arrow-up-circle"></i> Next Stage
                  </button>
                  <button class="btn btn-sm btn-outline-danger ms-auto" onclick="deleteCrop('${c.id}')">
                    <i class="bi bi-trash"></i>
                  </button>
                </div>
              </div>
            </div>
          `;
        });
        cropsContainer.innerHTML = cHtml;
      }
    }

  } catch (err) {
    console.error("Crops load error:", err);
  }
}

async function deletePlot(plotId) {
  if (!confirm(t("confirm_delete"))) return;
  await fetch(`/api/plots/${plotId}`, { method: "DELETE" });
  showToast("Plot deleted successfully");
  loadCropsAndPlots();
}

async function deleteCrop(cropId) {
  if (!confirm(t("confirm_delete"))) return;
  await fetch(`/api/crops/${cropId}`, { method: "DELETE" });
  showToast("Crop record deleted");
  loadCropsAndPlots();
}

async function advanceCropStage(cropId, currentStage) {
  const stages = [
    "Sowing / Nursery (விதைப்பு / நாற்றங்கால்)",
    "Transplanting (நடவு)",
    "Tillering & Vegetative (தூர்கட்டும் பருவம்)",
    "Flowering & Panicle (பூக்கும் / கதிர் பருவம்)",
    "Maturity & Harvest (முதிர்ச்சி & அறுவடை)",
    "Harvested (அறுவடை முடிந்தது)"
  ];
  let nextIdx = stages.findIndex(s => s.toLowerCase().includes(currentStage.split(" ")[0].toLowerCase())) + 1;
  if (nextIdx >= stages.length) nextIdx = stages.length - 1;
  const newStage = stages[nextIdx];

  await fetch(`/api/crops/${cropId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stage: newStage, status: nextIdx === stages.length - 1 ? "harvested" : "active" })
  });
  showToast(`Stage advanced to: ${newStage}`);
  loadCropsAndPlots();
}

// ----------------------------------------------------
// Livestock & Breeding Management
// ----------------------------------------------------
async function loadLivestock() {
  const container = document.getElementById("livestockGrid");
  if (!container) return;

  try {
    const res = await fetch("/api/livestock");
    const animals = await res.json();

    // Populate animal selector in breeding modal & milk modal
    const animalSelectBreeding = document.getElementById("breedingAnimalId");
    const animalSelectMilk = document.getElementById("milkAnimalId");
    if (animalSelectBreeding) {
      animalSelectBreeding.innerHTML = `<option value="">-- Select Animal --</option>` +
        animals.map(a => `<option value="${a.id}" data-species="${a.species}">${a.tag_id} (${a.breed})</option>`).join("");
    }
    if (animalSelectMilk) {
      const milch = animals.filter(a => a.species === "cow" || a.species === "buffalo");
      animalSelectMilk.innerHTML = `<option value="">-- Select Cow / Buffalo --</option>` +
        milch.map(a => `<option value="${a.id}">${a.tag_id} - ${a.name || ""}</option>`).join("");
    }

    if (animals.length === 0) {
      container.innerHTML = `<div class="col-12 text-center py-4 text-muted">No livestock registered yet.</div>`;
      return;
    }

    let html = "";
    animals.forEach(a => {
      const speciesBadge = a.species === "cow" ? "badge-cow" : a.species === "goat" ? "badge-goat" : "badge bg-secondary";
      const rep = a.reproduction || null;

      html += `
        <div class="col-md-6 mb-4">
          <div class="card card-custom p-3 h-100">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <span class="${speciesBadge} me-2 text-uppercase font-weight-bold">${a.species}</span>
                <h5 class="d-inline fw-bold text-dark">${a.tag_id}</h5>
                <div class="small text-muted mt-1">${a.breed} | Age: ${a.age_years || "?"} yrs</div>
              </div>
              <button class="btn btn-sm btn-link text-danger p-0" onclick="deleteLivestock('${a.id}')">
                <i class="bi bi-trash"></i>
              </button>
            </div>
            
            <hr class="my-2">

            ${rep ? `
              <div class="bg-light p-2 rounded mb-2">
                <div class="d-flex justify-content-between small fw-bold mb-1">
                  <span>${currentLang === "ta" ? rep.stage_ta : rep.stage}</span>
                  <span class="text-success">${rep.progress_percentage}%</span>
                </div>
                <div class="progress progress-gestation mb-2">
                  <div class="progress-bar bg-success" style="width: ${rep.progress_percentage}%"></div>
                </div>
                <div class="row g-1 small text-muted">
                  <div class="col-6"><strong>In-Calf:</strong> ${rep.days_pregnant} days</div>
                  <div class="col-6 text-end"><strong>Due in:</strong> ${rep.days_remaining} days</div>
                  <div class="col-12 mt-1">
                    <i class="bi bi-calendar-check text-primary"></i> <strong>Expected Due:</strong> ${rep.expected_calving_date || rep.expected_kidding_date}
                  </div>
                  ${rep.pd_check_date ? `<div class="col-12"><i class="bi bi-activity text-warning"></i> <strong>PD Check:</strong> ${rep.pd_check_date}</div>` : ""}
                  ${rep.dry_off_date ? `<div class="col-12"><i class="bi bi-droplet-half text-danger"></i> <strong>Dry-off:</strong> ${rep.dry_off_date}</div>` : ""}
                </div>
              </div>
            ` : `
              <div class="small text-muted py-2">
                Status: <span class="badge bg-secondary">${a.status || "Healthy"}</span>
              </div>
            `}

            <div class="d-flex gap-2 mt-auto pt-2">
              <button class="btn btn-sm btn-outline-success" onclick="openBreedingModal('${a.id}')">
                <i class="bi bi-heart-pulse"></i> Record Breeding
              </button>
              ${a.species === "cow" ? `
                <button class="btn btn-sm btn-outline-primary" onclick="openMilkModal('${a.id}')">
                  <i class="bi bi-droplet"></i> Log Milk
                </button>
              ` : ""}
            </div>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;

  } catch (err) {
    console.error("Livestock load error:", err);
  }
}

async function deleteLivestock(animalId) {
  if (!confirm(t("confirm_delete"))) return;
  await fetch(`/api/livestock/${animalId}`, { method: "DELETE" });
  showToast("Livestock removed");
  loadLivestock();
}

function openBreedingModal(animalId) {
  const sel = document.getElementById("breedingAnimalId");
  if (sel) sel.value = animalId;
  const modal = new bootstrap.Modal(document.getElementById("breedingModal"));
  modal.show();
}

function openMilkModal(animalId) {
  const sel = document.getElementById("milkAnimalId");
  if (sel) sel.value = animalId;
  const modal = new bootstrap.Modal(document.getElementById("milkModal"));
  modal.show();
}

// ----------------------------------------------------
// Financials Management
// ----------------------------------------------------
async function loadFinancials() {
  const tableBody = document.getElementById("txnsTableBody");
  if (!tableBody) return;

  try {
    const [statsRes, txnsRes] = await Promise.all([
      fetch("/api/financials/stats"),
      fetch("/api/financials")
    ]);
    const stats = await statsRes.json();
    const txns = await txnsRes.json();

    document.getElementById("finIncome").innerText = `₹${stats.total_income.toLocaleString("en-IN")}`;
    document.getElementById("finExpense").innerText = `₹${stats.total_expense.toLocaleString("en-IN")}`;
    
    const netEl = document.getElementById("finNetProfit");
    netEl.innerText = `₹${stats.net_profit.toLocaleString("en-IN")}`;
    netEl.className = stats.net_profit >= 0 ? "kpi-value text-success" : "kpi-value text-danger";
    
    document.getElementById("finRoi").innerText = `${stats.roi_percentage}%`;

    // Render Doughnut Chart of Expenses
    renderExpenseChart(stats.expenses_by_category);

    // Render transactions table
    if (txns.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No transactions recorded yet.</td></tr>`;
      return;
    }

    let rows = "";
    txns.forEach(t => {
      const isExp = t.type === "expense";
      const typeBadge = isExp ? `<span class="badge bg-danger-subtle text-danger">Expense</span>` : `<span class="badge bg-success-subtle text-success">Income</span>`;
      const amtSign = isExp ? "-" : "+";
      const amtClass = isExp ? "text-danger" : "text-success";

      rows += `
        <tr>
          <td>${t.date}</td>
          <td>${typeBadge}</td>
          <td><strong>${t.category}</strong></td>
          <td class="text-secondary small">${t.desc || t.notes || "-"}</td>
          <td class="fw-bold ${amtClass}">${amtSign}₹${parseFloat(t.amount).toLocaleString("en-IN")}</td>
          <td>
            <button class="btn btn-sm btn-link text-danger p-0" onclick="deleteTxn('${t.id}')">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    });
    tableBody.innerHTML = rows;

  } catch (err) {
    console.error("Financials load error:", err);
  }
}

function renderExpenseChart(expensesByCategory) {
  const canvas = document.getElementById("expenseChart");
  if (!canvas) return;

  const labels = Object.keys(expensesByCategory);
  const data = Object.values(expensesByCategory);

  if (window.UzhavanApp.charts["expense"]) {
    window.UzhavanApp.charts["expense"].destroy();
  }

  const ctx = canvas.getContext("2d");
  window.UzhavanApp.charts["expense"] = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: [
          "#15803d", "#0284c7", "#d97706", "#dc2626",
          "#8b5cf6", "#ec4899", "#14b8a6", "#64748b"
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom" }
      }
    }
  });
}

async function deleteTxn(id) {
  if (!confirm(t("confirm_delete"))) return;
  await fetch(`/api/financials/${id}`, { method: "DELETE" });
  showToast("Transaction removed");
  loadFinancials();
}

// ----------------------------------------------------
// Global Form Submit Handlers
// ----------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  // Plot Form
  const plotForm = document.getElementById("plotForm");
  if (plotForm) {
    plotForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(plotForm);
      const data = Object.fromEntries(fd.entries());
      await fetch("/api/plots", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      plotForm.reset();
      bootstrap.Modal.getInstance(document.getElementById("plotModal")).hide();
      showToast("Plot registered successfully");
      loadCropsAndPlots();
    });
  }

  // Crop Form
  const cropForm = document.getElementById("cropForm");
  if (cropForm) {
    cropForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(cropForm);
      const data = Object.fromEntries(fd.entries());
      await fetch("/api/crops", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      cropForm.reset();
      bootstrap.Modal.getInstance(document.getElementById("cropModal")).hide();
      showToast("New planting logged successfully");
      loadCropsAndPlots();
    });
  }

  // Livestock Form
  const animalForm = document.getElementById("animalForm");
  if (animalForm) {
    animalForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(animalForm);
      const data = Object.fromEntries(fd.entries());
      await fetch("/api/livestock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      animalForm.reset();
      bootstrap.Modal.getInstance(document.getElementById("animalModal")).hide();
      showToast("Animal registered successfully");
      loadLivestock();
    });
  }

  // Breeding Form
  const breedingForm = document.getElementById("breedingForm");
  if (breedingForm) {
    breedingForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(breedingForm);
      const data = Object.fromEntries(fd.entries());
      await fetch("/api/breeding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      breedingForm.reset();
      bootstrap.Modal.getInstance(document.getElementById("breedingModal")).hide();
      showToast("Breeding event recorded! Milestones calculated.");
      loadLivestock();
    });
  }

  // Milk Form
  const milkForm = document.getElementById("milkForm");
  if (milkForm) {
    milkForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(milkForm);
      const data = Object.fromEntries(fd.entries());
      await fetch("/api/milk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      milkForm.reset();
      bootstrap.Modal.getInstance(document.getElementById("milkModal")).hide();
      showToast("Daily milk log saved!");
    });
  }

  // Financial Transaction Form
  const finForm = document.getElementById("txnForm");
  if (finForm) {
    finForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(finForm);
      const data = Object.fromEntries(fd.entries());
      await fetch("/api/financials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      finForm.reset();
      bootstrap.Modal.getInstance(document.getElementById("txnModal")).hide();
      showToast("Transaction saved successfully");
      loadFinancials();
    });
  }

  // Settings Form
  const settingsForm = document.getElementById("settingsForm");
  if (settingsForm) {
    settingsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(settingsForm);
      const data = Object.fromEntries(fd.entries());
      await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      showToast("Settings updated successfully!");
    });
  }
});
