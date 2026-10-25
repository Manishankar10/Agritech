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
  await populateQuickLogDropdowns();
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
  await populateQuickLogDropdowns();
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

async function openBreedingModal(animalId) {
  await populateQuickLogDropdowns();
  const sel = document.getElementById("breedingAnimalId");
  if (sel && animalId) sel.value = animalId;
  const modalEl = document.getElementById("breedingModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl) || (bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalEl) : new bootstrap.Modal(modalEl));
    modal.show();
  }
}

async function openMilkModal(animalId) {
  await populateQuickLogDropdowns();
  const sel = document.getElementById("milkAnimalId");
  if (sel && animalId) sel.value = animalId;
  const modalEl = document.getElementById("milkModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl) || (bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalEl) : new bootstrap.Modal(modalEl));
    modal.show();
  }
}

// ----------------------------------------------------
// Financials Management
// ----------------------------------------------------
// Agricultural Trade & Transaction Helpers
// ----------------------------------------------------
const TXN_CATEGORIES = {
  income: [
    { value: "Crop Sale (பயிர் விற்பனை)", label: "Crop Sale (பயிர் விற்பனை - பொதுவானது)" },
    { value: "Tapioca / Kuchchi Kilangu (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)", label: "Tapioca / Kuchchi Kilangu (மரவள்ளிக் கிழங்கு)" },
    { value: "Paddy Harvest Sale (நெல் அறுவடை விற்பனை)", label: "Paddy Harvest Sale (நெல் அறுவடை விற்பனை)" },
    { value: "Coconut & Copra Sale (தேங்காய் & கொப்பரை விற்பனை)", label: "Coconut & Copra Sale (தேங்காய் & கொப்பரை விற்பனை)" },
    { value: "Sugarcane Mill Supply (கரும்பு ஆலை சப்ளை)", label: "Sugarcane Mill Supply (கரும்பு ஆலை சப்ளை)" },
    { value: "Turmeric Harvest Sale (மஞ்சள் விளைச்சல் விற்பனை)", label: "Turmeric Harvest Sale (மஞ்சள் விளைச்சல் விற்பனை)" },
    { value: "Banana Harvest Sale (வாழைத் தார் விற்பனை)", label: "Banana Harvest Sale (வாழைத் தார் விற்பனை)" },
    { value: "Vegetables / Onion Sale (காய்கறி / வெங்காயம் விற்பனை)", label: "Vegetables / Onion Sale (காய்கறி / வெங்காயம் விற்பனை)" },
    { value: "Milk Sale (பால் விற்பனை)", label: "Milk Sale (பால் விற்பனை)" },
    { value: "Livestock Sale (கால்நடை / ஆடு மாடு விற்பனை)", label: "Livestock Sale (கால்நடை / ஆடு மாடு விற்பனை)" },
    { value: "Govt Subsidy / DBT (அரசு மானியம்)", label: "Govt Subsidy / DBT (அரசு மானியம்)" },
    { value: "Other Farm Income (இதர விவசாய வரவு)", label: "Other Farm Income (இதர விவசாய வரவு)" }
  ],
  expense: [
    { value: "Fertilizer & Manure (உரம் & எரு)", label: "Fertilizer & Manure (உரம் & எரு)" },
    { value: "Labor & Coolie (கூலி & கூலியாட்கள்)", label: "Labor & Coolie (கூலி & கூலியாட்கள்)" },
    { value: "Seeds & Saplings (விதை & நாற்று)", label: "Seeds & Saplings (விதை & நாற்று)" },
    { value: "Tractor & Machinery Rental (டிராக்டர் / இயந்திர வாடகை)", label: "Tractor & Machinery Rental (டிராக்டர் / இயந்திர வாடகை)" },
    { value: "Diesel & Fuel (டீசல் & எரிபொருள்)", label: "Diesel & Fuel (டீசல் & எரிபொருள்)" },
    { value: "Pesticides & Crop Protection (பூச்சிக்கொல்லி & மருந்து)", label: "Pesticides & Crop Protection (பூச்சிக்கொல்லி & மருந்து)" },
    { value: "Electricity & Irrigation (மின்சாரம் & பாசனம்)", label: "Electricity & Irrigation (மின்சாரம் & பாசனம்)" },
    { value: "Cattle Feed & Fodder (தீவனம் & புல்)", label: "Cattle Feed & Fodder (தீவனம் & புல்)" },
    { value: "Veterinary & Medicine (கால்நடை மருத்துவம்)", label: "Veterinary & Medicine (கால்நடை மருத்துவம்)" },
    { value: "Transport & Freight (சரக்கு வண்டி வாடகை)", label: "Transport & Freight (சரக்கு வண்டி வாடகை)" },
    { value: "Equipment Maintenance (கருவிகள் பழுதுபார்ப்பு)", label: "Equipment Maintenance (கருவிகள் பழுதுபார்ப்பு)" },
    { value: "Other Farm Expense (இதர விவசாய செலவு)", label: "Other Farm Expense (இதர விவசாய செலவு)" }
  ]
};

function onTxnTypeChange(type) {
  const catSelect = document.getElementById("txnCategorySelect");
  if (catSelect) {
    const cats = TXN_CATEGORIES[type] || TXN_CATEGORIES.income;
    const currentVal = catSelect.value;
    catSelect.innerHTML = cats.map(c => `<option value="${c.value}">${c.label}</option>`).join("");
    if (cats.some(c => c.value === currentVal)) {
      catSelect.value = currentVal;
    }
  }

  // Update produce card title
  const produceTitle = document.querySelector("#cropTradeSection .small.fw-bold.text-dark");
  if (produceTitle) {
    if (type === "expense") {
      produceTitle.innerHTML = `<i class="bi bi-box-seam text-danger me-1"></i> Agricultural Input / Quantity Details (உள்ளீடு & அளவு விவரம்)`;
    } else {
      produceTitle.innerHTML = `<i class="bi bi-basket-fill text-success me-1"></i> Produce & Quantity Details (விளைபொருள் விவரம் & எடை)`;
    }
  }

  calculateTxnTotal();
}

function onTxnCategorySelectChange() {
  const catSelect = document.getElementById("txnCategorySelect");
  const commInput = document.getElementById("txnCommodity");
  const unitSelect = document.getElementById("txnUnit");
  if (!catSelect || !commInput) return;

  const val = (catSelect.value || "").toLowerCase();
  if (val.includes("tapioca") || val.includes("kuchchi")) {
    commInput.value = "Kuchchi Kilangu / Tapioca (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)";
    if (unitSelect) unitSelect.value = "Tons";
  } else if (val.includes("paddy")) {
    commInput.value = "Paddy / Rice (நெல் / பொன்னி / குண்டு நெல்)";
    if (unitSelect) unitSelect.value = "Bags (75kg)";
  } else if (val.includes("coconut") || val.includes("copra")) {
    commInput.value = "De-husked Coconut (மட்டை உரித்த தேங்காய்)";
    if (unitSelect) unitSelect.value = "Tons";
  } else if (val.includes("sugarcane")) {
    commInput.value = "Sugarcane (கரும்பு)";
    if (unitSelect) unitSelect.value = "Tons";
  } else if (val.includes("turmeric")) {
    commInput.value = "Turmeric (மஞ்சள்)";
    if (unitSelect) unitSelect.value = "Quintals";
  } else if (val.includes("milk")) {
    commInput.value = "Cow Milk (பசும்பால்)";
    if (unitSelect) unitSelect.value = "Liters";
  }

  calculateTxnTotal();
}

function calculateTxnTotal() {
  const qtyInput = document.getElementById("txnQuantity");
  const rateInput = document.getElementById("txnRate");
  const unitSelect = document.getElementById("txnUnit");
  const rateLabel = document.getElementById("txnRateLabel");
  const amtInput = document.getElementById("txnAmount");
  const previewBadge = document.getElementById("txnCalcPreview");

  if (!qtyInput || !rateInput || !unitSelect) return;

  const unit = unitSelect.value || "Unit";
  let unitName = unit;
  if (unit === "Tons") unitName = "Ton (₹ / டன் விலை)";
  else if (unit === "Quintals") unitName = "Quintal (₹ / குவிண்டால் விலை)";
  else if (unit === "Bags (75kg)") unitName = "75kg Bag (₹ / மூட்டை விலை)";
  else if (unit === "Bags (50kg)") unitName = "50kg Bag (₹ / மூட்டை விலை)";
  else if (unit === "Kg") unitName = "Kg (₹ / கிலோ விலை)";
  else if (unit === "Pieces") unitName = "Piece / Coconut (₹ / காய் எண்ணிக்கை விலை)";
  else if (unit === "Liters") unitName = "Liter (₹ / லிட்டர் விலை)";
  else if (unit === "Bunches") unitName = "Bunch (₹ / தார் விலை)";

  if (rateLabel) {
    rateLabel.innerText = `Rate / Price per ${unitName}`;
  }

  const qty = parseFloat(qtyInput.value);
  const rate = parseFloat(rateInput.value);

  if (!isNaN(qty) && qty > 0 && !isNaN(rate) && rate > 0) {
    const total = Math.round((qty * rate) * 100) / 100;
    if (amtInput) amtInput.value = total.toFixed(2);

    if (previewBadge) {
      previewBadge.className = "badge bg-success-subtle text-success border border-success-subtle p-2 w-100 text-start font-monospace small";
      previewBadge.innerHTML = `<i class="bi bi-check-circle-fill text-success me-1"></i> ${qty} ${unit} &times; ₹${rate.toLocaleString("en-IN")} = <strong>₹${total.toLocaleString("en-IN")}</strong>`;
    }
  } else {
    if (previewBadge) {
      previewBadge.className = "badge bg-white text-dark border p-2 w-100 text-start font-monospace small";
      previewBadge.innerHTML = `<i class="bi bi-calculator me-1 text-primary"></i> Enter Quantity & Rate to auto-calculate total`;
    }
  }
}

// ----------------------------------------------------
// Financials Loader
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
      const typeBadge = isExp ? `<span class="badge bg-danger-subtle text-danger"><i class="bi bi-dash-circle me-1"></i>Expense</span>` : `<span class="badge bg-success-subtle text-success"><i class="bi bi-plus-circle me-1"></i>Income</span>`;
      const amtSign = isExp ? "-" : "+";
      const amtClass = isExp ? "text-danger" : "text-success";

      let produceDetails = "";
      if (t.quantity && t.rate_per_unit) {
        const u = t.unit || "Units";
        produceDetails += `<div class="badge bg-light text-dark border mb-1 tabular-nums"><i class="bi bi-calculator me-1 text-primary"></i><strong>${t.quantity} ${u}</strong> &times; ₹${parseFloat(t.rate_per_unit).toLocaleString("en-IN")}/${u.replace(/s\b/, '')}</div>`;
      }
      if (t.buyer) {
        produceDetails += `<div class="small text-muted"><i class="bi bi-building me-1 text-secondary"></i><strong>Party/Mill:</strong> ${t.buyer}</div>`;
      }
      if (t.slip_no) {
        produceDetails += `<div class="small text-muted"><i class="bi bi-receipt me-1 text-secondary"></i><strong>Slip/Ref:</strong> ${t.slip_no}</div>`;
      }
      if (t.desc) {
        produceDetails += `<div class="small text-dark mt-1 p-2 bg-light border-start border-3 border-secondary rounded" style="white-space: pre-wrap; font-family: inherit;">${t.desc}</div>`;
      }
      if (!produceDetails) {
        produceDetails = `<span class="text-muted small">${t.notes || "-"}</span>`;
      }

      const commodityBadge = t.commodity ? `<div class="small fw-bold text-success mt-1"><i class="bi bi-basket2-fill me-1"></i>${t.commodity}</div>` : "";

      rows += `
        <tr>
          <td class="text-nowrap">${t.date}</td>
          <td>${typeBadge}</td>
          <td>
            <strong>${t.category}</strong>
            ${commodityBadge}
          </td>
          <td>${produceDetails}</td>
          <td class="fw-bold tabular-nums text-nowrap ${amtClass}">${amtSign}₹${parseFloat(t.amount).toLocaleString("en-IN")}</td>
          <td>
            <button class="btn btn-sm btn-link text-danger p-0" title="Delete" onclick="deleteTxn('${t.id}')">
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
// Modal Dropdowns Populator (Works on Any Page)
// ----------------------------------------------------
async function populateQuickLogDropdowns() {
  const breedingSel = document.getElementById("breedingAnimalId");
  const milkSel = document.getElementById("milkAnimalId");
  const cropPlotSel = document.getElementById("cropPlotId");

  if (breedingSel || milkSel) {
    try {
      const res = await fetch("/api/livestock");
      const animals = await res.json();
      if (Array.isArray(animals)) {
        if (breedingSel) {
          const currentVal = breedingSel.value;
          breedingSel.innerHTML = `<option value="">-- Select Animal (கால்நடை) --</option>` +
            animals.map(a => `<option value="${a.id}">${a.tag_id} - ${a.name || a.breed} (${(a.species || '').toUpperCase()})</option>`).join("");
          if (currentVal) breedingSel.value = currentVal;
        }
        if (milkSel) {
          const currentVal = milkSel.value;
          const milch = animals.filter(a => a.species === "cow" || a.species === "buffalo");
          milkSel.innerHTML = `<option value="">-- Select Cow / Buffalo (கறவை மாடு) --</option>` +
            milch.map(a => `<option value="${a.id}">${a.tag_id} - ${a.name || a.breed}</option>`).join("");
          if (currentVal) milkSel.value = currentVal;
        }
      }
    } catch (err) {
      console.error("Failed to populate animal dropdowns:", err);
    }
  }

  if (cropPlotSel) {
    try {
      const res = await fetch("/api/plots");
      const plots = await res.json();
      if (Array.isArray(plots)) {
        const currentVal = cropPlotSel.value;
        cropPlotSel.innerHTML = `<option value="">-- Select Farmland Plot (நிலம்) --</option>` +
          plots.map(p => `<option value="${p.id}">${p.name} (${p.area_acres} ac)</option>`).join("");
        if (currentVal) cropPlotSel.value = currentVal;
      }
    } catch (err) {
      console.error("Failed to populate plot dropdowns:", err);
    }
  }

  // Populate financial transaction categories if empty
  const catSelect = document.getElementById("txnCategorySelect");
  if (catSelect && catSelect.children.length === 0) {
    onTxnTypeChange("income");
  }

  // Pre-fill any empty date inputs with today's date
  const today = new Date().toISOString().split("T")[0];
  document.querySelectorAll("input[type='date']").forEach(inp => {
    if (!inp.value) inp.value = today;
  });
}

function safeCloseModal(modalId) {
  const modalEl = document.getElementById(modalId);
  if (!modalEl) return;

  try {
    const inst = bootstrap.Modal.getInstance(modalEl) || (bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalEl) : null);
    if (inst) {
      inst.hide();
    }
  } catch (err) {
    console.warn("safeCloseModal notice:", err);
  }

  // Also trigger dismiss button if modal is still active
  const closeBtn = modalEl.querySelector("[data-bs-dismiss='modal']");
  if (closeBtn) closeBtn.click();

  // Clean up any remaining backdrop elements and restore body scrolling
  setTimeout(() => {
    document.querySelectorAll(".modal-backdrop").forEach(b => b.remove());
    document.body.classList.remove("modal-open");
    document.body.style.removeProperty("overflow");
    document.body.style.removeProperty("padding-right");
  }, 250);
}

// ----------------------------------------------------
// Global Form Submit Handlers
// ----------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  populateQuickLogDropdowns();

  // Plot Form
  const plotForm = document.getElementById("plotForm");
  if (plotForm) {
    plotForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = plotForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const fd = new FormData(plotForm);
        const data = Object.fromEntries(fd.entries());
        const res = await fetch("/api/plots", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          plotForm.reset();
          safeCloseModal("plotModal");
          showToast("Plot registered successfully!", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadCropsAndPlots === "function") loadCropsAndPlots();
          populateQuickLogDropdowns();
        } else {
          showToast("Failed to register plot", "danger");
        }
      } catch (err) {
        console.error("Plot save error:", err);
        showToast("Error registering plot", "danger");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  // Crop Form
  const cropForm = document.getElementById("cropForm");
  if (cropForm) {
    cropForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = cropForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const fd = new FormData(cropForm);
        const data = Object.fromEntries(fd.entries());

        if (!data.plot_id) {
          showToast("Please select a farmland plot first", "warning");
          if (submitBtn) submitBtn.disabled = false;
          return;
        }

        const res = await fetch("/api/crops", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          cropForm.reset();
          safeCloseModal("cropModal");
          showToast("New planting logged successfully!", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadCropsAndPlots === "function") loadCropsAndPlots();
          populateQuickLogDropdowns();
        } else {
          showToast("Failed to log planting", "danger");
        }
      } catch (err) {
        console.error("Crop save error:", err);
        showToast("Error logging planting", "danger");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  // Livestock Form
  const animalForm = document.getElementById("animalForm");
  if (animalForm) {
    animalForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = animalForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const fd = new FormData(animalForm);
        const data = Object.fromEntries(fd.entries());
        const res = await fetch("/api/livestock", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          animalForm.reset();
          safeCloseModal("animalModal");
          showToast("Animal registered successfully!", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadLivestock === "function") loadLivestock();
          populateQuickLogDropdowns();
        } else {
          showToast("Failed to register animal", "danger");
        }
      } catch (err) {
        console.error("Animal save error:", err);
        showToast("Error registering animal", "danger");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  // Breeding Form
  const breedingForm = document.getElementById("breedingForm");
  if (breedingForm) {
    breedingForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = breedingForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const fd = new FormData(breedingForm);
        const data = Object.fromEntries(fd.entries());

        if (!data.animal_id) {
          showToast("Please select an animal first", "warning");
          if (submitBtn) submitBtn.disabled = false;
          return;
        }

        const res = await fetch("/api/breeding", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          breedingForm.reset();
          safeCloseModal("breedingModal");
          showToast("Breeding event recorded! Gestation countdown started.", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadLivestock === "function") loadLivestock();
          populateQuickLogDropdowns();
        } else {
          showToast("Failed to record breeding event", "danger");
        }
      } catch (err) {
        console.error("Breeding save error:", err);
        showToast("Error recording breeding event", "danger");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  // Milk Form
  const milkForm = document.getElementById("milkForm");
  if (milkForm) {
    milkForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = milkForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const fd = new FormData(milkForm);
        const data = Object.fromEntries(fd.entries());

        if (!data.animal_id) {
          showToast("Please select a cow or buffalo first", "warning");
          if (submitBtn) submitBtn.disabled = false;
          return;
        }

        const res = await fetch("/api/milk", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          milkForm.reset();
          safeCloseModal("milkModal");
          showToast("Daily milk yield recorded successfully!", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadLivestock === "function") loadLivestock();
          if (typeof loadMilkLogs === "function") loadMilkLogs();
          populateQuickLogDropdowns();
        } else {
          showToast("Failed to save milk log", "danger");
        }
      } catch (err) {
        console.error("Milk save error:", err);
        showToast("Error saving milk record", "danger");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  // Financial Transaction Form
  const finForm = document.getElementById("txnForm");
  if (finForm) {
    // Intercept Enter key inside single-line inputs to avoid accidental premature submit
    finForm.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.target && e.target.tagName === "INPUT") {
        e.preventDefault();
      }
    });

    // Handle multiline description box - prevent submit on Enter / Shift+Enter
    const txnDesc = document.getElementById("txnDesc");
    if (txnDesc) {
      txnDesc.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          // Allow natural newline insertion in textarea, stop form interception
          e.stopPropagation();
        }
      });
    }

    finForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = finForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const fd = new FormData(finForm);
        const data = Object.fromEntries(fd.entries());
        const res = await fetch("/api/financials", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          finForm.reset();
          if (typeof onTxnTypeChange === "function") onTxnTypeChange("income");
          const calcPreview = document.getElementById("txnCalcPreview");
          if (calcPreview) {
            calcPreview.className = "badge bg-white text-dark border p-2 w-100 text-start font-monospace small";
            calcPreview.innerHTML = '<i class="bi bi-calculator me-1 text-primary"></i> Enter Quantity & Rate to auto-calculate total';
          }
          safeCloseModal("txnModal");
          showToast("Financial transaction recorded successfully", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadFinancials === "function") loadFinancials();
        } else {
          showToast("Failed to save transaction", "danger");
        }
      } catch (err) {
        console.error("Financials save error:", err);
        showToast("Error saving transaction", "danger");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  // Settings Form
  const settingsForm = document.getElementById("settingsForm");
  if (settingsForm) {
    settingsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const submitBtn = settingsForm.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;

      try {
        const fd = new FormData(settingsForm);
        const data = Object.fromEntries(fd.entries());
        const res = await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          showToast("Settings updated successfully!", "success");
        } else {
          showToast("Failed to update settings", "danger");
        }
      } catch (err) {
        console.error("Settings save error:", err);
        showToast("Error updating settings", "danger");
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }
});

// Re-populate modal dropdowns anytime a modal begins to open
document.addEventListener("show.bs.modal", () => {
  populateQuickLogDropdowns();
});
