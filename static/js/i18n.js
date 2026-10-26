/**
 * Bilingual Internationalization Dictionary: English & Tamil (தமிழ்)
 * Designed for Tamil Nadu Agriculture & Livestock Farmers
 */

const I18N = {
  en: {
    app_title: "Uzhavan Desk",
    app_subtitle: "TN Agri & Livestock Farm Manager",
    nav_dashboard: "Dashboard",
    nav_mandi: "Live Mandi Prices",
    nav_crops: "Crops & Planting",
    nav_livestock: "Livestock & Breeding",
    nav_financials: "Farm Financials",
    nav_advisory: "Weather & Schemes",
    nav_settings: "Settings",

    // Dashboard
    welcome_farmer: "Welcome, Farmer!",
    overview_title: "Farm Overview & Analytics",
    kpi_plots: "Farmland Plots",
    kpi_acres: "Acres",
    kpi_crops: "Active Crops",
    kpi_livestock: "Total Livestock",
    kpi_revenue: "Total Revenue",
    kpi_expense: "Total Expenses",
    kpi_net_profit: "Net Farm Profit",

    quick_actions: "Quick Farm Actions",
    action_log_expense: "Record Expense",
    action_log_income: "Record Income",
    action_log_milk: "Log Daily Milk",
    action_add_breeding: "New Breeding / AI",
    action_add_crop: "New Planting",

    urgent_alerts: "Important Farm & Breeding Alerts",
    no_alerts: "No urgent alerts today. Everything is running smoothly!",
    weather_widget_title: "Local Weather & Agro-Advisory",
    rain_probability: "Rain Probability",

    // Mandi
    mandi_title: "Tamil Nadu APMC Regulated Markets & Uzhavar Sandhai Prices",
    mandi_subtitle: "Real-time wholesale commodity prices across all 38 Tamil Nadu districts",
    select_district: "Select District",
    all_districts: "All Tamil Nadu Districts",
    search_commodity_placeholder: "Search commodity (e.g. Paddy, Turmeric, Banana, Tomato...)",
    col_commodity: "Commodity & Variety",
    col_market: "Market / APMC",
    col_district: "District",
    col_min_price: "Min Price",
    col_max_price: "Max Price",
    col_modal_price: "Modal Rate",
    col_change: "24h Trend",
    price_trend_title: "Commodity Price Trend (15 Days)",

    // Crops
    crops_title: "Crop Planting & Growth Stage Management",
    plots_title: "Farmland Registered Plots",
    add_plot_btn: "Add New Plot",
    add_crop_btn: "Plant New Crop",
    sowing_date: "Sowing Date",
    expected_harvest: "Expected Harvest",
    crop_stage: "Current Growth Stage",
    mark_harvested: "Mark as Harvested",
    progress: "Progress",

    // Livestock
    livestock_title: "Livestock Registry & Reproductive Health",
    add_animal_btn: "Register Animal",
    breeding_calc_title: "Reproduction & Gestation Calculator",
    species: "Species",
    cow_cattle: "Cow / Cattle (மாடு)",
    buffalo: "Buffalo (எருமை)",
    goat: "Goat (வெள்ளாடு)",
    sheep: "Sheep (செம்மறியாடு)",
    tag_id: "Tag ID / Name",
    breed: "Breed",
    gestation_progress: "Gestation Progress",
    days_pregnant: "Days In-Calf",
    expected_calving: "Expected Calving",
    expected_kidding: "Expected Kidding",
    pd_check: "Pregnancy Check (PD)",
    dry_date: "Dry-off Date",
    milk_log_title: "Daily Milk Yield & Revenue Logger",
    morning_liters: "Morning (Liters)",
    evening_liters: "Evening (Liters)",
    fat_snf: "Fat & SNF %",
    rate_per_liter: "Rate / Liter (₹)",
    total_liters: "Total Liters",
    vaccination_title: "Veterinary Vaccination Calendar (TN)",

    // Financials
    fin_title: "Farm Accounting & P&L Statement",
    add_txn_btn: "Record Transaction",
    type_expense: "Expense",
    type_income: "Income",
    category: "Category",
    amount: "Amount (₹)",
    date: "Date",
    roi_label: "Return on Investment (ROI)",
    breakdown_expenses: "Expense Breakdown by Category",
    recent_txns: "Recent Farm Transactions",
    crop_pnl_title: "Crop-Wise Profitability & Cost of Cultivation",
    crop_pnl_subtitle: "Track direct cultivation expenses, harvest sales returns, and net margins per crop",
    linked_crop: "Linked Crop / Cultivation",
    add_cost_btn: "+ Add Cost",
    add_sale_btn: "+ Add Return",
    crop_ledger_btn: "Ledger",
    general_overhead: "General Farm Overhead / Unallocated",

    // Advisory
    advisory_title: "Weather Forecast & Agricultural Advisory",
    schemes_title: "Tamil Nadu Government Agricultural Schemes & Subsidies",
    helplines_title: "Emergency Agri & Veterinary Helplines",
    use_current_location: "Use Current Location",
    scheme_view_details: "View Details & How to Apply",
    col_per_kg: "₹ / Kg Breakdown",

    // Common
    save_btn: "Save Record",
    cancel_btn: "Cancel",
    delete_btn: "Delete",
    confirm_delete: "Are you sure you want to delete this record?",
    offline_notice: "You are currently offline. Running on Local JSON store mode."
  },

  ta: {
    app_title: "உழவன் மேலாளர்",
    app_subtitle: "தமிழ்நாடு விவசாய & கால்நடை மேலாண்மை",
    nav_dashboard: "முகப்பு",
    nav_mandi: "சந்தை நிலவரம்",
    nav_crops: "பயிர் சாகுபடி",
    nav_livestock: "கால்நடை & சினை",
    nav_financials: "வரவு செலவு",
    nav_advisory: "வானிலை & திட்டங்கள்",
    nav_settings: "அமைப்புகள்",

    // Dashboard
    welcome_farmer: "வணக்கம், உழவரே!",
    overview_title: "பண்ணை மேலோட்டம் & புள்ளிவிவரங்கள்",
    kpi_plots: "நிலப்பரப்புகள்",
    kpi_acres: "ஏக்கர்",
    kpi_crops: "செயலில் உள்ள பயிர்கள்",
    kpi_livestock: "கால்நடைகள் எண்ணிக்கை",
    kpi_revenue: "மொத்த வரவு",
    kpi_expense: "மொத்த செலவு",
    kpi_net_profit: "நிகர பண்ணை லாபம்",

    quick_actions: "விரைவுப் பதிவுகள்",
    action_log_expense: "செலவு பதிவு",
    action_log_income: "வரவு பதிவு",
    action_log_milk: "பால் கறவை பதிவு",
    action_add_breeding: "சினை ஊசி / இணைசேர்க்கை",
    action_add_crop: "புதிய பயிர் விதைப்பு",

    urgent_alerts: "முக்கிய சினை & பண்ணை எச்சரிக்கைகள்",
    no_alerts: "இன்று அவசர எச்சரிக்கைகள் ஏதுமில்லை. பண்ணைப் பணிகள் சீராக உள்ளன!",
    weather_widget_title: "பகுதி வானிலை & விவசாய வழிகாட்டல்",
    rain_probability: "மழை வாய்ப்பு",

    // Mandi
    mandi_title: "தமிழ்நாடு ஒழுங்குமுறை விற்பனைக்கூடம் & உழவர் சந்தை விலைகள்",
    mandi_subtitle: "38 மாவட்டங்களின் நேரடி மொத்த விற்பனை விலை நிலவரம்",
    select_district: "மாவட்டத்தைத் தேர்ந்தெடுக்கவும்",
    all_districts: "அனைத்து தமிழ்நாடு மாவட்டங்கள்",
    search_commodity_placeholder: "பயிரை தேடுக (எ.கா: நெல், மஞ்சள், வாழை, தக்காளி, தேங்காய்...)",
    col_commodity: "பயிர் & ரகம்",
    col_market: "சந்தை / விற்பனைக்கூடம்",
    col_district: "மாவட்டம்",
    col_min_price: "குறைந்த விலை",
    col_max_price: "அதிகபட்ச விலை",
    col_modal_price: "நடைமுறை விலை (Modal)",
    col_change: "24 மணி மாற்ற விகிதம்",
    price_trend_title: "பயிர் விலை வரைபடம் (கடந்த 15 நாட்கள்)",

    // Crops
    crops_title: "பயிர் சாகுபடி மற்றும் வளர்ச்சிப் பருவ கண்காணிப்பு",
    plots_title: "பதிவு செய்யப்பட்ட நிலங்கள்",
    add_plot_btn: "புதிய நிலப்பரப்பு சேர்க்க",
    add_crop_btn: "புதிய பயிர் நடவு",
    sowing_date: "விதைத்த நாள்",
    expected_harvest: "எதிர்பார்க்கப்படும் அறுவடை",
    crop_stage: "தற்போதைய வளர்ச்சிப் பருவம்",
    mark_harvested: "அறுவடை முடிந்தது என குறிக்க",
    progress: "வளர்ச்சி நிலை",

    // Livestock
    livestock_title: "கால்நடைப் பதிவேடு & சினை மேலாண்மை",
    add_animal_btn: "கால்நடை சேர்க்க",
    breeding_calc_title: "சினை & ஈற்று நாள் கணக்கீட்டுக் கருவி",
    species: "இனம்",
    cow_cattle: "பசு / மாடு",
    buffalo: "எருமை",
    goat: "வெள்ளாடு",
    sheep: "செம்மறியாடு",
    tag_id: "அடையாள எண் / பெயர்",
    breed: "ஜாதி / இனம்",
    gestation_progress: "சினை முதிர்ச்சி",
    days_pregnant: "சினை நாட்கள்",
    expected_calving: "கன்று ஈனும் நாள்",
    expected_kidding: "குட்டி ஈனும் நாள்",
    pd_check: "சினை பரிசோதனை (PD)",
    dry_date: "கறவை நிறுத்தம்",
    milk_log_title: "தினசரி பால் கறவை & வருமானப் பதிவேடு",
    morning_liters: "காலை (லிட்டர்)",
    evening_liters: "மாலை (லிட்டர்)",
    fat_snf: "கொழுப்பு & கொழுப்பற்ற சத்து %",
    rate_per_liter: "லிட்டர் விலை (₹)",
    total_liters: "மொத்த லிட்டர்",
    vaccination_title: "கால்நடை தடுப்பூசி அட்டவணை (தமிழ்நாடு)",

    // Financials
    fin_title: "பண்ணை வரவு செலவு & லாப நஷ்ட அறிக்கை",
    add_txn_btn: "பணப் பரிவர்த்தனை பதிவு",
    type_expense: "செலவு",
    type_income: "வரவு",
    category: "வகை",
    amount: "தொகை (₹)",
    date: "தேதி",
    roi_label: "முதலீட்டின் மீதான லாபம் (ROI)",
    breakdown_expenses: "செலவு வகைப்பாடு",
    recent_txns: "சமீபத்திய வரவு செலவுகள்",
    crop_pnl_title: "பயிர்வாரி லாப நட்ட கணக்கு & சாகுபடி செலவு",
    crop_pnl_subtitle: "பயிர்களின் நேரடி சாகுபடி செலவு, அறுவடை வரவு மற்றும் நிகர லாப விவரங்கள்",
    linked_crop: "இணைக்கப்பட்ட பயிர்",
    add_cost_btn: "+ செலவு",
    add_sale_btn: "+ வரவு",
    crop_ledger_btn: "கணக்கு விவரம்",
    general_overhead: "பண்ணை பொது நிர்வாக செலவுகள்",

    // Advisory
    advisory_title: "வானிலை முன்னறிவிப்பு & வேளாண் வழிகாட்டல்கள்",
    schemes_title: "தமிழ்நாடு அரசு விவசாய மானியங்கள் & திட்டங்கள்",
    helplines_title: "அவசர விவசாய & கால்நடை உதவி எண்கள்",
    use_current_location: "தற்போதைய இருப்பிடம்",
    scheme_view_details: "முழு விவரங்கள் & விண்ணப்பிக்க",
    col_per_kg: "கிலோ விலை (₹)",

    // Common
    save_btn: "சேமிக்க",
    cancel_btn: "ரத்து செய்",
    delete_btn: "நீக்கு",
    confirm_delete: "இப்பதிவை நிச்சயமாக நீக்க விரும்புகிறீர்களா?",
    offline_notice: "இணைய தொடர்பு இல்லை. உள்ளூர் கணினியில் (JSON) இயங்குகிறது."
  }
};

let currentLang = localStorage.getItem("uzhavan_lang") || "en";

function t(key) {
  if (I18N[currentLang] && I18N[currentLang][key]) {
    return I18N[currentLang][key];
  }
  if (I18N["en"] && I18N["en"][key]) {
    return I18N["en"][key];
  }
  return key;
}

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("uzhavan_lang", lang);
  applyTranslations();

  fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ language: lang })
  }).catch(() => {});

  const profileBadge = document.getElementById("profileLangBadge");
  if (profileBadge) {
    profileBadge.innerHTML = lang === "en" ? "🇬🇧 English &rarr; தமிழ்" : "🇮🇳 தமிழ் &rarr; English";
  }

  const btn = document.getElementById("langToggleBtn");
  if (btn) {
    btn.innerHTML = lang === "en" ? "🇮🇳 தமிழ்" : "🇬🇧 English";
  }
}

function toggleLanguage() {
  const nextLang = currentLang === "en" ? "ta" : "en";
  setLanguage(nextLang);
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);
  const icon = document.getElementById("themeIcon");
  if (icon) {
    icon.className = newTheme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
  }
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    const trans = t(key);
    if (trans) {
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        if (el.getAttribute("placeholder")) {
          el.setAttribute("placeholder", trans);
        }
      } else {
        el.innerText = trans;
      }
    }
  });

  window.dispatchEvent(new CustomEvent("languageChanged", { detail: { lang: currentLang } }));
}

document.addEventListener("DOMContentLoaded", () => {
  // Apply saved theme
  const savedTheme = localStorage.getItem("theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  const icon = document.getElementById("themeIcon");
  if (icon) {
    icon.className = savedTheme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
  }

  // Apply default language: English
  const initialLang = localStorage.getItem("uzhavan_lang") || "en";
  setLanguage(initialLang);
});
