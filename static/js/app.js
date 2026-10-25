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
    window.UzhavanApp.crops = crops || [];
    window.UzhavanApp.plots = plots || [];

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
                  <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-link text-primary p-0" title="Edit Plot" onclick="editPlot('${p.id}')">
                      <i class="bi bi-pencil-square"></i>
                    </button>
                    <button class="btn btn-sm btn-link text-danger p-0" title="Delete Plot" onclick="deletePlot('${p.id}')">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
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
                <div class="d-flex gap-2 mt-auto flex-wrap align-items-center">
                  <button class="btn btn-sm btn-outline-success" onclick="advanceCropStage('${c.id}', '${c.stage}')">
                    <i class="bi bi-arrow-up-circle"></i> Next Stage
                  </button>
                  <button class="btn btn-sm btn-outline-primary" onclick="editCrop('${c.id}')">
                    <i class="bi bi-pencil-square"></i> Edit
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

function editPlot(plotId) {
  const plot = (window.UzhavanApp.plots || []).find(p => String(p.id) === String(plotId));
  if (!plot) return;

  const form = document.getElementById("plotForm");
  if (!form) return;

  form.dataset.editId = plotId;
  const nameInp = document.getElementById("plotName") || form.querySelector("input[name='name']");
  const areaInp = document.getElementById("plotArea") || form.querySelector("input[name='area_acres']");
  const survInp = document.getElementById("plotSurvey") || form.querySelector("input[name='survey_no']");
  const soilInp = document.getElementById("plotSoil") || form.querySelector("select[name='soil_type']");
  const waterInp = document.getElementById("plotWater") || form.querySelector("input[name='water_source']");

  if (nameInp) nameInp.value = plot.name || "";
  if (areaInp) areaInp.value = plot.area_acres || "";
  if (survInp) survInp.value = plot.survey_no || "";
  if (soilInp) soilInp.value = plot.soil_type || "";
  if (waterInp) waterInp.value = plot.water_source || "";

  const titleEl = document.getElementById("plotModalTitle");
  if (titleEl) titleEl.innerText = "Edit Farmland Plot (நிலத்தை திருத்து)";
  const submitBtn = document.getElementById("plotSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Update Plot';

  const modalEl = document.getElementById("plotModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl) || (bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalEl) : new bootstrap.Modal(modalEl));
    modal.show();
  }
}

function resetPlotModal() {
  const form = document.getElementById("plotForm");
  if (!form) return;
  form.reset();
  delete form.dataset.editId;
  const titleEl = document.getElementById("plotModalTitle");
  if (titleEl) titleEl.innerText = "Register Farmland Plot";
  const submitBtn = document.getElementById("plotSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerText = "Save Plot";
}

function editCrop(cropId) {
  const crop = (window.UzhavanApp.crops || []).find(c => String(c.id) === String(cropId));
  if (!crop) return;

  const form = document.getElementById("cropForm");
  if (!form) return;

  form.dataset.editId = cropId;
  const plotSel = document.getElementById("cropPlotId");
  const nameInp = document.getElementById("cropName") || form.querySelector("input[name='crop_name']");
  const varInp = document.getElementById("cropVariety") || form.querySelector("input[name='variety']");
  const seasonSel = document.getElementById("cropSeason") || form.querySelector("select[name='season']");
  const sowInp = document.getElementById("cropSowingDate") || form.querySelector("input[name='sowing_date']");
  const harvInp = document.getElementById("cropHarvestDate") || form.querySelector("input[name='expected_harvest']");
  const areaInp = document.getElementById("cropArea") || form.querySelector("input[name='area_cultivated_acres']");
  const stageSel = document.getElementById("cropStageSelect") || form.querySelector("select[name='stage']");
  const statusSel = document.getElementById("cropStatusSelect") || form.querySelector("select[name='status']");
  const notesInp = document.getElementById("cropNotes") || form.querySelector("textarea[name='notes']");

  if (plotSel) plotSel.value = crop.plot_id || "";
  if (nameInp) nameInp.value = crop.crop_name || "";
  if (varInp) varInp.value = crop.variety || "";
  if (seasonSel) seasonSel.value = crop.season || "";
  if (sowInp) sowInp.value = crop.sowing_date || "";
  if (harvInp) harvInp.value = crop.expected_harvest || "";
  if (areaInp) areaInp.value = crop.area_cultivated_acres || "";
  if (stageSel && crop.stage) stageSel.value = crop.stage;
  if (statusSel && crop.status) statusSel.value = crop.status;
  if (notesInp) notesInp.value = crop.notes || "";

  const titleEl = document.getElementById("cropModalTitle");
  if (titleEl) titleEl.innerText = "Edit Crop Planting (பயிரை திருத்து)";
  const submitBtn = document.getElementById("cropSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Update Crop';

  const modalEl = document.getElementById("cropModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl) || (bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalEl) : new bootstrap.Modal(modalEl));
    modal.show();
  }
}

function resetCropModal() {
  const form = document.getElementById("cropForm");
  if (!form) return;
  form.reset();
  delete form.dataset.editId;
  const titleEl = document.getElementById("cropModalTitle");
  if (titleEl) titleEl.innerText = "Plant New Crop";
  const submitBtn = document.getElementById("cropSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerText = "Save Planting";
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
    window.UzhavanApp.animals = animals || [];

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

    // Also populate breeding history table if on livestock page
    if (typeof loadBreedingRecords === "function") {
      loadBreedingRecords();
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
              <div class="d-flex gap-2">
                <button class="btn btn-sm btn-link text-primary p-0" title="Edit Animal" onclick="editLivestock('${a.id}')">
                  <i class="bi bi-pencil-square"></i>
                </button>
                <button class="btn btn-sm btn-link text-danger p-0" title="Delete Animal" onclick="deleteLivestock('${a.id}')">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
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
                ${a.active_breeding_record ? `
                  <div class="mt-2 pt-1 border-top d-flex justify-content-between align-items-center">
                    <span class="small text-muted"><i class="bi bi-heart me-1 text-danger"></i>AI/Mated: ${a.active_breeding_record.date}</span>
                    <button class="btn btn-sm btn-link text-primary p-0" title="Edit Active Breeding Event" onclick="editBreeding('${a.active_breeding_record.id}')">
                      <i class="bi bi-pencil-square me-1"></i>Edit AI/Breed
                    </button>
                  </div>
                ` : ""}
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

function editLivestock(animalId) {
  const animal = (window.UzhavanApp.animals || []).find(a => String(a.id) === String(animalId));
  if (!animal) return;

  const form = document.getElementById("animalForm");
  if (!form) return;

  form.dataset.editId = animalId;
  const spSel = document.getElementById("animalSpecies") || form.querySelector("select[name='species']");
  const genSel = document.getElementById("animalGender") || form.querySelector("select[name='gender']");
  const tagInp = document.getElementById("animalTagId") || form.querySelector("input[name='tag_id']");
  const brdInp = document.getElementById("animalBreed") || form.querySelector("input[name='breed']");
  const ageInp = document.getElementById("animalAge") || form.querySelector("input[name='age_years']");
  const lacInp = document.getElementById("animalLactation") || form.querySelector("input[name='lactation_number']");
  const stSel = document.getElementById("animalStatus") || form.querySelector("select[name='status']");
  const ntsInp = document.getElementById("animalNotes") || form.querySelector("input[name='notes']");

  if (spSel) spSel.value = animal.species || "cow";
  if (genSel) genSel.value = animal.gender || "female";
  if (tagInp) tagInp.value = animal.tag_id || "";
  if (brdInp) brdInp.value = animal.breed || "";
  if (ageInp) ageInp.value = animal.age_years || "";
  if (lacInp) lacInp.value = animal.lactation_number || "";
  if (stSel) stSel.value = animal.status || "healthy";
  if (ntsInp) ntsInp.value = animal.notes || "";

  const titleEl = document.getElementById("animalModalTitle");
  if (titleEl) titleEl.innerText = "Edit Livestock (கால்நடையை திருத்து)";
  const submitBtn = document.getElementById("animalSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Update Animal';

  const modalEl = document.getElementById("animalModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl) || (bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalEl) : new bootstrap.Modal(modalEl));
    modal.show();
  }
}

function resetAnimalModal() {
  const form = document.getElementById("animalForm");
  if (!form) return;
  form.reset();
  delete form.dataset.editId;
  const titleEl = document.getElementById("animalModalTitle");
  if (titleEl) titleEl.innerText = "Register Animal";
  const submitBtn = document.getElementById("animalSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerText = "Register Animal";
}

async function loadBreedingRecords() {
  const tbody = document.getElementById("breedingTableBody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/breeding");
    const recs = await res.json();
    window.UzhavanApp.breedingRecords = recs || [];

    if (!recs || recs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-3 text-muted">No breeding records logged yet.</td></tr>`;
      return;
    }

    let rows = "";
    recs.forEach(r => {
      const typeLabel = r.event_type === "insemination" ? "AI (செயற்கை முறை)" : "Natural Mating (இயற்கை)";
      const statusBadge = r.status === "active" ? `<span class="badge bg-warning text-dark">Active Gestation</span>` :
        r.status === "calved" ? `<span class="badge bg-success">Calved / Eennadhu</span>` :
        r.status === "failed" ? `<span class="badge bg-danger">Failed / Repeat</span>` :
        `<span class="badge bg-secondary">${r.status || 'Past'}</span>`;

      rows += `
        <tr>
          <td class="text-nowrap">${r.date}</td>
          <td><strong>${r.animal_tag || r.animal_id}</strong></td>
          <td>${typeLabel}</td>
          <td>${r.semen_bull_info || "-"}</td>
          <td>${r.technician || "-"}</td>
          <td>${statusBadge}</td>
          <td class="text-nowrap">
            <button class="btn btn-sm btn-link text-primary p-0 me-2" title="Edit Breeding Event" onclick="editBreeding('${r.id}')">
              <i class="bi bi-pencil-square"></i>
            </button>
            <button class="btn btn-sm btn-link text-danger p-0" title="Delete Record" onclick="deleteBreeding('${r.id}')">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = rows;
  } catch (err) {
    console.error("Breeding records load error:", err);
  }
}

async function editBreeding(recId) {
  if (!recId) return;
  let rec = (window.UzhavanApp.breedingRecords || []).find(r => String(r.id) === String(recId));
  if (!rec) {
    try {
      const res = await fetch("/api/breeding");
      const list = await res.json();
      window.UzhavanApp.breedingRecords = list;
      rec = list.find(r => String(r.id) === String(recId));
    } catch (e) {}
  }
  if (!rec) return;

  await populateQuickLogDropdowns();
  const form = document.getElementById("breedingForm");
  if (!form) return;

  form.dataset.editId = recId;
  const anSel = document.getElementById("breedingAnimalId");
  const evSel = document.getElementById("breedingEventType") || form.querySelector("select[name='event_type']");
  const dtInp = document.getElementById("breedingDate") || form.querySelector("input[name='date']");
  const blInp = document.getElementById("breedingBullInfo") || form.querySelector("input[name='semen_bull_info']");
  const tcInp = document.getElementById("breedingTechnician") || form.querySelector("input[name='technician']");
  const stSel = document.getElementById("breedingStatus") || form.querySelector("select[name='status']");
  const ntsInp = document.getElementById("breedingNotes") || form.querySelector("input[name='notes']");

  if (anSel) anSel.value = rec.animal_id || "";
  if (evSel) evSel.value = rec.event_type || "insemination";
  if (dtInp) dtInp.value = rec.date || "";
  if (blInp) blInp.value = rec.semen_bull_info || "";
  if (tcInp) tcInp.value = rec.technician || "";
  if (stSel) stSel.value = rec.status || "active";
  if (ntsInp) ntsInp.value = rec.notes || "";

  const titleEl = document.getElementById("breedingModalTitle");
  if (titleEl) titleEl.innerText = "Edit Breeding Event (சினைப்பதிவை திருத்து)";
  const submitBtn = document.getElementById("breedingSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Update Record';

  const modalEl = document.getElementById("breedingModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl) || (bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalEl) : new bootstrap.Modal(modalEl));
    modal.show();
  }
}

function resetBreedingModal() {
  const form = document.getElementById("breedingForm");
  if (!form) return;
  form.reset();
  delete form.dataset.editId;
  const titleEl = document.getElementById("breedingModalTitle");
  if (titleEl) titleEl.innerText = "Record Insemination / Mating";
  const submitBtn = document.getElementById("breedingSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerText = "Record Milestones";
}

async function deleteBreeding(recId) {
  if (!confirm(t("confirm_delete"))) return;
  await fetch(`/api/breeding/${recId}`, { method: "DELETE" });
  showToast("Breeding record deleted");
  if (typeof loadLivestock === "function") loadLivestock();
  if (typeof loadBreedingRecords === "function") loadBreedingRecords();
}

async function loadMilkLogs() {
  const tbody = document.getElementById("milkLogsTableBody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/milk");
    const logs = await res.json();
    window.UzhavanApp.milkLogs = logs || [];

    if (!logs || logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-3 text-muted">No milk logs recorded yet.</td></tr>`;
      return;
    }

    let rows = "";
    logs.slice(0, 10).forEach(l => {
      rows += `
        <tr>
          <td>${l.date}</td>
          <td><strong>${l.animal_tag || l.animal_id}</strong></td>
          <td>${l.total_liters} L <span class="text-muted small">(${l.morning_liters}M / ${l.evening_liters}E)</span></td>
          <td>${l.fat_pct || "-"}% / ${l.snf_pct || "-"}%</td>
          <td class="text-success fw-bold">₹${parseFloat(l.total_amount || 0).toLocaleString("en-IN")}</td>
          <td class="text-nowrap">
            <button class="btn btn-sm btn-link text-primary p-0 me-2" title="Edit Milk Log" onclick="editMilkLog('${l.id}')">
              <i class="bi bi-pencil-square"></i>
            </button>
            <button class="btn btn-sm btn-link text-danger p-0" title="Delete Milk Log" onclick="deleteMilkLog('${l.id}')">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = rows;
  } catch (err) {
    console.error("Milk logs load error:", err);
  }
}

async function editMilkLog(logId) {
  if (!logId) return;
  let log = (window.UzhavanApp.milkLogs || []).find(l => String(l.id) === String(logId));
  if (!log) {
    try {
      const res = await fetch("/api/milk");
      const list = await res.json();
      window.UzhavanApp.milkLogs = list;
      log = list.find(l => String(l.id) === String(logId));
    } catch (e) {}
  }
  if (!log) return;

  await populateQuickLogDropdowns();
  const form = document.getElementById("milkForm");
  if (!form) return;

  form.dataset.editId = logId;
  const anSel = document.getElementById("milkAnimalId");
  const dtInp = document.getElementById("milkDate") || form.querySelector("input[name='date']");
  const mrnInp = document.getElementById("milkMorning") || form.querySelector("input[name='morning_liters']");
  const evnInp = document.getElementById("milkEvening") || form.querySelector("input[name='evening_liters']");
  const fatInp = document.getElementById("milkFat") || form.querySelector("input[name='fat_pct']");
  const snfInp = document.getElementById("milkSnf") || form.querySelector("input[name='snf_pct']");
  const rtInp = document.getElementById("milkRate") || form.querySelector("input[name='rate_per_liter']");
  const byrInp = document.getElementById("milkBuyer") || form.querySelector("input[name='buyer']");

  if (anSel) anSel.value = log.animal_id || "";
  if (dtInp) dtInp.value = log.date || "";
  if (mrnInp) mrnInp.value = log.morning_liters || "";
  if (evnInp) evnInp.value = log.evening_liters || "";
  if (fatInp) fatInp.value = log.fat_pct || "";
  if (snfInp) snfInp.value = log.snf_pct || "";
  if (rtInp) rtInp.value = log.rate_per_liter || "";
  if (byrInp) byrInp.value = log.buyer || "";

  const titleEl = document.getElementById("milkModalTitle");
  if (titleEl) titleEl.innerText = "Edit Daily Milk Yield (பால் பதிவை திருத்து)";
  const submitBtn = document.getElementById("milkSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Update Milk Log';

  const modalEl = document.getElementById("milkModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl) || (bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalEl) : new bootstrap.Modal(modalEl));
    modal.show();
  }
}

function resetMilkModal() {
  const form = document.getElementById("milkForm");
  if (!form) return;
  form.reset();
  delete form.dataset.editId;
  const titleEl = document.getElementById("milkModalTitle");
  if (titleEl) titleEl.innerText = "Log Daily Milk Yield";
  const submitBtn = document.getElementById("milkSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerText = "Save Milk Log";
}

async function deleteMilkLog(logId) {
  if (!confirm(t("confirm_delete"))) return;
  await fetch(`/api/milk/${logId}`, { method: "DELETE" });
  showToast("Milk log removed");
  if (typeof loadMilkLogs === "function") loadMilkLogs();
}

async function deleteLivestock(animalId) {
  if (!confirm(t("confirm_delete"))) return;
  await fetch(`/api/livestock/${animalId}`, { method: "DELETE" });
  showToast("Livestock removed");
  loadLivestock();
}

async function openBreedingModal(animalId) {
  resetBreedingModal();
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
  resetMilkModal();
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
    { value: "Crop Sale (பயிர் விற்பனை)", label: "Crop Sale - General" },
    { value: "Tapioca / Kuchchi Kilangu (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)", label: "Tapioca / Kuchchi Kilangu" },
    { value: "Paddy Harvest Sale (நெல் அறுவடை விற்பனை)", label: "Paddy Harvest" },
    { value: "Coconut & Copra Sale (தேங்காய் & கொப்பரை விற்பனை)", label: "Coconut & Copra" },
    { value: "Sugarcane Mill Supply (கரும்பு ஆலை சப்ளை)", label: "Sugarcane Mill Supply" },
    { value: "Turmeric Harvest Sale (மஞ்சள் விளைச்சல் விற்பனை)", label: "Turmeric Harvest" },
    { value: "Banana Harvest Sale (வாழைத் தார் விற்பனை)", label: "Banana Harvest" },
    { value: "Vegetables / Onion Sale (காய்கறி / வெங்காயம் விற்பனை)", label: "Vegetables & Onion" },
    { value: "Milk Sale (பால் விற்பனை)", label: "Milk Sale (Dairy)" },
    { value: "Livestock Sale (கால்நடை / ஆடு மாடு விற்பனை)", label: "Livestock Sale" },
    { value: "Govt Subsidy / DBT (அரசு மானியம்)", label: "Govt Subsidy / DBT" },
    { value: "Other Farm Income (இதர விவசாய வரவு)", label: "Other Farm Income" }
  ],
  expense: [
    { value: "Fertilizer & Manure (உரம் & எரு)", label: "Fertilizer & Manure" },
    { value: "Labor & Coolie (கூலி & கூலியாட்கள்)", label: "Labor & Wages" },
    { value: "Seeds & Saplings (விதை & நாற்று)", label: "Seeds & Saplings" },
    { value: "Tractor & Machinery Rental (டிராக்டர் / இயந்திர வாடகை)", label: "Machinery & Tractor Rental" },
    { value: "Diesel & Fuel (டீசல் & எரிபொருள்)", label: "Diesel & Fuel" },
    { value: "Pesticides & Crop Protection (பூச்சிக்கொல்லி & மருந்து)", label: "Pesticides & Protection" },
    { value: "Electricity & Irrigation (மின்சாரம் & பாசனம்)", label: "Electricity & Irrigation" },
    { value: "Cattle Feed & Fodder (தீவனம் & புல்)", label: "Cattle Feed & Fodder" },
    { value: "Veterinary & Medicine (கால்நடை மருத்துவம்)", label: "Veterinary & Health" },
    { value: "Transport & Freight (சரக்கு வண்டி வாடகை)", label: "Transport & Freight" },
    { value: "Equipment Maintenance (கருவிகள் பழுதுபார்ப்பு)", label: "Maintenance & Repairs" },
    { value: "Other Farm Expense (இதர விவசாய செலவு)", label: "Other Farm Expense" }
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

  const produceTitle = document.querySelector("#cropTradeSection .small.fw-bold.text-dark");
  if (produceTitle) {
    if (type === "expense") {
      produceTitle.innerHTML = `<i class="bi bi-box-seam text-danger me-1"></i> Input & Quantity Details`;
    } else {
      produceTitle.innerHTML = `<i class="bi bi-basket2-fill text-success me-1"></i> Produce & Quantity Details`;
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
    commInput.value = "Tapioca / Kuchchi Kilangu (மரவள்ளி)";
    if (unitSelect) unitSelect.value = "Tons";
  } else if (val.includes("paddy")) {
    commInput.value = "Paddy / Rice (நெல்)";
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
  const previewBox = document.getElementById("txnCalcPreview");
  const netQtyInput = document.getElementById("txnNetQuantity");
  const netUnitLabel = document.getElementById("txnNetUnitLabel");

  const dedPerTonInput = document.getElementById("txnDeductionPerTon");
  const dedFlatInput = document.getElementById("txnDeductionFlat");
  const harvestInput = document.getElementById("txnHarvestCharges");
  const transportInput = document.getElementById("txnTransportCharges");
  const otherChargesInput = document.getElementById("txnOtherCharges");

  if (!qtyInput || !rateInput || !unitSelect) return;

  const unit = unitSelect.value || "Unit";
  const unitDisplay = unit.replace(/\s*\(.*\)/, '').trim();
  if (rateLabel) {
    rateLabel.innerText = `Rate / Price per ${unitDisplay.replace(/s$/, '')} (₹)`;
  }
  if (netUnitLabel) {
    netUnitLabel.innerText = unitDisplay;
  }

  const grossQty = parseFloat(qtyInput.value);
  const rate = parseFloat(rateInput.value);

  const dedPerTon = parseFloat(dedPerTonInput ? dedPerTonInput.value : 0) || 0;
  const dedFlatKg = parseFloat(dedFlatInput ? dedFlatInput.value : 0) || 0;
  const harvestCharge = parseFloat(harvestInput ? harvestInput.value : 0) || 0;
  const transportCharge = parseFloat(transportInput ? transportInput.value : 0) || 0;
  const otherCharge = parseFloat(otherChargesInput ? otherChargesInput.value : 0) || 0;
  const totalCharges = harvestCharge + transportCharge + otherCharge;

  if (!isNaN(grossQty) && grossQty > 0) {
    let totalDeductKg = 0;
    if (unitDisplay.toLowerCase().includes("ton")) {
      totalDeductKg = (grossQty * dedPerTon) + dedFlatKg;
    } else if (unitDisplay.toLowerCase().includes("quintal")) {
      totalDeductKg = (grossQty * (dedPerTon / 10.0)) + dedFlatKg;
    } else {
      totalDeductKg = dedFlatKg;
    }

    let deductInUnit = 0;
    if (unitDisplay.toLowerCase().includes("ton")) {
      deductInUnit = totalDeductKg / 1000.0;
    } else if (unitDisplay.toLowerCase().includes("quintal")) {
      deductInUnit = totalDeductKg / 100.0;
    } else if (unitDisplay.toLowerCase() === "kg") {
      deductInUnit = totalDeductKg;
    }

    let netQty = Math.max(0, grossQty - deductInUnit);
    netQty = Math.round(netQty * 1000) / 1000;

    if (netQtyInput) {
      netQtyInput.value = netQty.toFixed(3);
    }

    if (!isNaN(rate) && rate > 0) {
      const grossProduceVal = Math.round((netQty * rate) * 100) / 100;
      const netPayout = Math.max(0, Math.round((grossProduceVal - totalCharges) * 100) / 100);

      if (amtInput) {
        amtInput.value = netPayout.toFixed(2);
      }

      if (previewBox) {
        previewBox.className = "border rounded p-2 mb-2 bg-success-subtle border-success-subtle small font-monospace";
        
        let deductionText = totalDeductKg > 0
          ? `<span class="text-danger fw-bold">-${totalDeductKg.toFixed(1)} kg (-${deductInUnit.toFixed(3)} ${unitDisplay})</span>`
          : `<span class="text-muted">0 kg</span>`;

        let chargesText = totalCharges > 0
          ? `<span class="text-danger fw-bold">-₹${totalCharges.toLocaleString("en-IN")}</span>`
          : `<span class="text-muted">₹0</span>`;

        previewBox.innerHTML = `
          <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-1">
            <div>
              <span class="text-muted">Gross:</span> <strong>${grossQty} ${unitDisplay}</strong>
              <span class="text-muted mx-1">&bull;</span>
              <span class="text-muted">Sand/Tare:</span> ${deductionText}
              <span class="text-muted mx-1">&bull;</span>
              <span class="text-muted">Net Wt:</span> <span class="text-success fw-bold">${netQty} ${unitDisplay}</span>
            </div>
            <div class="text-md-end">
              <span class="text-muted">Produce:</span> <strong>₹${grossProduceVal.toLocaleString("en-IN")}</strong>
              <span class="text-muted mx-1">&bull;</span>
              <span class="text-muted">Charges:</span> ${chargesText}
              <span class="text-muted mx-1">&bull;</span>
              <span class="text-success fw-bold">Net Payout: ₹${netPayout.toLocaleString("en-IN")}</span>
            </div>
          </div>
        `;
      }
    } else {
      if (previewBox) {
        previewBox.className = "border rounded p-2 mb-2 bg-white text-muted small font-monospace";
        previewBox.innerHTML = `<i class="bi bi-calculator me-1 text-primary"></i> Gross ${grossQty} ${unitDisplay} (Net ${netQty} ${unitDisplay}). Enter Rate to calculate total.`;
      }
    }
  } else {
    if (netQtyInput) netQtyInput.value = "";
    if (previewBox) {
      previewBox.className = "border rounded p-2 mb-2 bg-white text-muted small font-monospace";
      previewBox.innerHTML = `<i class="bi bi-calculator me-1 text-primary"></i> Enter Quantity & Rate to auto-calculate settlement`;
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
    window.UzhavanApp.txns = txns || [];

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
        let weightStr = `<strong>${t.quantity} ${u}</strong>`;
        if (t.deduction_per_ton_kg) {
          weightStr += ` <span class="text-danger small font-monospace">(-${t.deduction_per_ton_kg}kg/T sand)</span>`;
        }
        if (t.net_quantity && t.net_quantity !== t.quantity) {
          weightStr += ` &rarr; <span class="text-success fw-bold font-monospace">Net ${t.net_quantity} ${u}</span>`;
        }
        produceDetails += `<div class="badge bg-light text-dark border mb-1 tabular-nums"><i class="bi bi-calculator me-1 text-primary"></i>${weightStr} &times; ₹${parseFloat(t.rate_per_unit).toLocaleString("en-IN")}/${u.replace(/\s*\(.*\)/, '').replace(/s\b/, '')}</div>`;
      }
      if (t.harvest_charges || t.transport_charges || t.other_charges || (t.total_expenses && parseFloat(t.total_expenses) > 0)) {
        const totalExp = t.total_expenses || ((parseFloat(t.harvest_charges||0) + parseFloat(t.transport_charges||0) + parseFloat(t.other_charges||0)));
        if (totalExp > 0) {
          produceDetails += `<div class="small text-danger mb-1 font-monospace"><i class="bi bi-dash-circle me-1"></i>Charges Paid: -₹${parseFloat(totalExp).toLocaleString("en-IN")}</div>`;
        }
      }
      if (t.buyer) {
        produceDetails += `<div class="small text-muted"><i class="bi bi-building me-1 text-secondary"></i><strong>Party:</strong> ${t.buyer}</div>`;
      }
      if (t.slip_no) {
        produceDetails += `<div class="small text-muted"><i class="bi bi-receipt me-1 text-secondary"></i><strong>Slip:</strong> ${t.slip_no}</div>`;
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
          <td class="text-nowrap">
            <button class="btn btn-sm btn-link text-primary p-0 me-2" title="Edit Transaction" onclick="editTxn('${t.id}')">
              <i class="bi bi-pencil-square"></i>
            </button>
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

async function editTxn(txnId) {
  if (!txnId) return;
  let txn = (window.UzhavanApp.txns || []).find(t => String(t.id) === String(txnId));
  if (!txn) {
    try {
      const res = await fetch("/api/financials");
      const list = await res.json();
      window.UzhavanApp.txns = list;
      txn = list.find(t => String(t.id) === String(txnId));
    } catch (e) {}
  }
  if (!txn) return;

  const form = document.getElementById("txnForm");
  if (!form) return;

  form.dataset.editId = txnId;

  // Set type radio
  const typeIncome = document.getElementById("txnTypeIncome");
  const typeExpense = document.getElementById("txnTypeExpense");
  if (txn.type === "expense") {
    if (typeExpense) typeExpense.checked = true;
    if (typeof onTxnTypeChange === "function") onTxnTypeChange("expense");
  } else {
    if (typeIncome) typeIncome.checked = true;
    if (typeof onTxnTypeChange === "function") onTxnTypeChange("income");
  }

  // Populate category
  const catSel = document.getElementById("txnCategorySelect");
  if (catSel && txn.category) {
    let found = false;
    for (let i = 0; i < catSel.options.length; i++) {
      if (catSel.options[i].value === txn.category) {
        found = true;
        break;
      }
    }
    if (!found) {
      const opt = document.createElement("option");
      opt.value = txn.category;
      opt.text = txn.category;
      catSel.appendChild(opt);
    }
    catSel.value = txn.category;
    if (typeof onTxnCategorySelectChange === "function") onTxnCategorySelectChange();
  }

  const dtInp = document.getElementById("txnDate");
  const comInp = document.getElementById("txnCommodity");
  const qtyInp = document.getElementById("txnQuantity");
  const untSel = document.getElementById("txnUnit");
  const rtInp = document.getElementById("txnRate");
  const dedPerTonInp = document.getElementById("txnDeductionPerTon");
  const dedFlatInp = document.getElementById("txnDeductionFlat");
  const hrvInp = document.getElementById("txnHarvestCharges");
  const trnInp = document.getElementById("txnTransportCharges");
  const othInp = document.getElementById("txnOtherCharges");
  const byrInp = document.getElementById("txnBuyer") || form.querySelector("input[name='buyer']");
  const slpInp = document.getElementById("txnSlipNo") || form.querySelector("input[name='slip_no']");
  const amtInp = document.getElementById("txnAmount");
  const dscInp = document.getElementById("txnDesc");

  if (dtInp) dtInp.value = txn.date || "";
  if (comInp) comInp.value = txn.commodity || "";
  if (qtyInp) qtyInp.value = txn.quantity || "";
  if (untSel) untSel.value = txn.unit || "Tons";
  if (rtInp) rtInp.value = txn.rate_per_unit || "";
  if (dedPerTonInp) dedPerTonInp.value = txn.deduction_per_ton_kg || "";
  if (dedFlatInp) dedFlatInp.value = txn.deduction_flat_kg || "";
  if (hrvInp) hrvInp.value = txn.harvest_charges || "";
  if (trnInp) trnInp.value = txn.transport_charges || "";
  if (othInp) othInp.value = txn.other_charges || "";
  if (byrInp) byrInp.value = txn.buyer || "";
  if (slpInp) slpInp.value = txn.slip_no || "";
  if (amtInp) amtInp.value = txn.amount || "";
  if (dscInp) dscInp.value = txn.desc || txn.notes || "";

  if (typeof calculateTxnTotal === "function") calculateTxnTotal();

  const titleEl = document.getElementById("txnModalTitle");
  if (titleEl) titleEl.innerText = "Edit Transaction";
  const submitBtn = document.getElementById("txnSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Update Transaction';

  const modalEl = document.getElementById("txnModal");
  if (modalEl) {
    const modal = bootstrap.Modal.getInstance(modalEl) || (bootstrap.Modal.getOrCreateInstance ? bootstrap.Modal.getOrCreateInstance(modalEl) : new bootstrap.Modal(modalEl));
    modal.show();
  }
}

function resetTxnModal() {
  const form = document.getElementById("txnForm");
  if (!form) return;
  form.reset();
  delete form.dataset.editId;
  const incRadio = document.getElementById("txnTypeIncome");
  if (incRadio) {
    incRadio.checked = true;
    if (typeof onTxnTypeChange === "function") onTxnTypeChange("income");
  }
  const calcPreview = document.getElementById("txnCalcPreview");
  if (calcPreview) {
    calcPreview.className = "border rounded p-2 mb-2 bg-white text-muted small font-monospace";
    calcPreview.innerHTML = '<i class="bi bi-calculator me-1 text-primary"></i> Enter Quantity & Rate to auto-calculate settlement';
  }
  const today = new Date().toISOString().split("T")[0];
  const dtInp = document.getElementById("txnDate");
  if (dtInp) dtInp.value = today;

  const netQtyInp = document.getElementById("txnNetQuantity");
  if (netQtyInp) netQtyInp.value = "";

  const titleEl = document.getElementById("txnModalTitle");
  if (titleEl) titleEl.innerText = "Record Transaction";
  const submitBtn = document.getElementById("txnSubmitBtn") || form.querySelector("button[type='submit']");
  if (submitBtn) submitBtn.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i> Save Transaction';
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
        const editId = plotForm.dataset.editId;
        const url = editId ? `/api/plots/${editId}` : "/api/plots";
        const method = editId ? "PUT" : "POST";
        const res = await fetch(url, {
          method: method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          resetPlotModal();
          safeCloseModal("plotModal");
          showToast(editId ? "Plot updated successfully!" : "Plot registered successfully!", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadCropsAndPlots === "function") loadCropsAndPlots();
          populateQuickLogDropdowns();
        } else {
          showToast("Failed to save plot", "danger");
        }
      } catch (err) {
        console.error("Plot save error:", err);
        showToast("Error saving plot", "danger");
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

        const editId = cropForm.dataset.editId;
        const url = editId ? `/api/crops/${editId}` : "/api/crops";
        const method = editId ? "PUT" : "POST";
        const res = await fetch(url, {
          method: method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          resetCropModal();
          safeCloseModal("cropModal");
          showToast(editId ? "Planting updated successfully!" : "New planting logged successfully!", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadCropsAndPlots === "function") loadCropsAndPlots();
          populateQuickLogDropdowns();
        } else {
          showToast("Failed to save planting", "danger");
        }
      } catch (err) {
        console.error("Crop save error:", err);
        showToast("Error saving planting", "danger");
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
        const editId = animalForm.dataset.editId;
        const url = editId ? `/api/livestock/${editId}` : "/api/livestock";
        const method = editId ? "PUT" : "POST";
        const res = await fetch(url, {
          method: method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          resetAnimalModal();
          safeCloseModal("animalModal");
          showToast(editId ? "Animal updated successfully!" : "Animal registered successfully!", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadLivestock === "function") loadLivestock();
          populateQuickLogDropdowns();
        } else {
          showToast("Failed to save animal", "danger");
        }
      } catch (err) {
        console.error("Animal save error:", err);
        showToast("Error saving animal", "danger");
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

        const editId = breedingForm.dataset.editId;
        const url = editId ? `/api/breeding/${editId}` : "/api/breeding";
        const method = editId ? "PUT" : "POST";
        const res = await fetch(url, {
          method: method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          resetBreedingModal();
          safeCloseModal("breedingModal");
          showToast(editId ? "Breeding record updated successfully!" : "Breeding event recorded! Gestation countdown started.", "success");
          if (typeof loadDashboardOverview === "function") loadDashboardOverview();
          if (typeof loadLivestock === "function") loadLivestock();
          if (typeof loadBreedingRecords === "function") loadBreedingRecords();
          populateQuickLogDropdowns();
        } else {
          showToast("Failed to save breeding event", "danger");
        }
      } catch (err) {
        console.error("Breeding save error:", err);
        showToast("Error saving breeding event", "danger");
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

        const editId = milkForm.dataset.editId;
        const url = editId ? `/api/milk/${editId}` : "/api/milk";
        const method = editId ? "PUT" : "POST";
        const res = await fetch(url, {
          method: method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          resetMilkModal();
          safeCloseModal("milkModal");
          showToast(editId ? "Daily milk log updated successfully!" : "Daily milk yield recorded successfully!", "success");
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
        const editId = finForm.dataset.editId;
        const url = editId ? `/api/financials/${editId}` : "/api/financials";
        const method = editId ? "PUT" : "POST";
        const res = await fetch(url, {
          method: method,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        });

        if (res.ok) {
          resetTxnModal();
          safeCloseModal("txnModal");
          showToast(editId ? "Transaction updated successfully" : "Financial transaction recorded successfully", "success");
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

  // Reset modals cleanly on dismiss
  const modalResets = {
    "plotModal": typeof resetPlotModal === "function" ? resetPlotModal : null,
    "cropModal": typeof resetCropModal === "function" ? resetCropModal : null,
    "animalModal": typeof resetAnimalModal === "function" ? resetAnimalModal : null,
    "breedingModal": typeof resetBreedingModal === "function" ? resetBreedingModal : null,
    "milkModal": typeof resetMilkModal === "function" ? resetMilkModal : null,
    "txnModal": typeof resetTxnModal === "function" ? resetTxnModal : null
  };

  Object.entries(modalResets).forEach(([modalId, resetFn]) => {
    const el = document.getElementById(modalId);
    if (el) {
      el.addEventListener("hidden.bs.modal", () => {
        if (modalId === "plotModal" && typeof resetPlotModal === "function") resetPlotModal();
        else if (modalId === "cropModal" && typeof resetCropModal === "function") resetCropModal();
        else if (modalId === "animalModal" && typeof resetAnimalModal === "function") resetAnimalModal();
        else if (modalId === "breedingModal" && typeof resetBreedingModal === "function") resetBreedingModal();
        else if (modalId === "milkModal" && typeof resetMilkModal === "function") resetMilkModal();
        else if (modalId === "txnModal" && typeof resetTxnModal === "function") resetTxnModal();
      });
    }
  });

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
