# 🌱 Uzhavan Desk (உழவன் மேலாளர்)
### Tamil Nadu Agriculture & Livestock Farm Management Platform

A specialized, bilingual (Tamil & English) agricultural management application built specifically for farmers in Tamil Nadu, India. Tracks crop lifecycles, farm expenses and returns (P&L), cattle and goat reproduction cycles, live APMC Mandi commodity rates, weather agro-advisories, and government subsidies.

Hosted on **Render** with a **Dual Data Store Engine (MongoDB Atlas Cloud + Local JSON Fallback)** for zero-downtime and offline resilience.

---

## 🌟 Key Features

### 1. 📈 Live Mandi & Market Prices (சந்தை நிலவரம்)
- Covers all **38 Tamil Nadu districts** (Thanjavur, Madurai, Coimbatore, Erode, Salem, Dindigul, Tiruppur, etc.).
- Real-time wholesale prices for Paddy (Ponni, CR-1009, Seeraga Samba), Turmeric (Erode, Salem), Coconut (Pollachi), Tomato, Small Onion (Shallots), Banana (Poovan, Nendran, Red Banana), Cotton, Groundnut, etc.
- Min, Max, and Modal Price per Quintal / Kg.
- Interactive **15-day price trend charts** with Chart.js.

### 2. 🐄 Livestock & Breeding Engine (கால்நடை & சினை மேலாண்மை)
- **Cattle Management (மாடுகள்)**:
  - Supports Kangayam, Umblachery, Bargur, Pulikulam, Jersey Cross, HF Cross, Murrah Buffalo.
  - Heat detection watch (~21 days alert window).
  - Insemination (AI / Natural service) tracker.
  - Automatic **Pregnancy Diagnosis (PD) check alert at 60–90 days**.
  - **283-day gestation countdown** with visual progress bar.
  - **Dry period alert at 60 days before calving** (stop milking for mammary rest).
  - Expected Calving Date countdown and preparation checklist.
- **Goats & Sheep (ஆடுகள் மேலாண்மை)**:
  - Supports Kanni Aadu, Kodi Aadu, Salem Black, Mecheri, Tellicherry.
  - **150-day (~5 months) gestation calculator** & expected kidding date.
  - Weaning reminder at 60–90 days.
- **Daily Milk Production & Revenue Logger**:
  - Morning / Evening yields (Liters), Fat %, SNF, and Aavin/society payout calculations.
- **Veterinary Vaccination Calendar**:
  - FMD (Foot and Mouth Disease / கோமாரி நோய்) bi-annual alerts.
  - Deworming (குடற்புழு நீக்கம்) quarterly schedule.
  - Anthrax, Black Quarter (BQ), and Enterotoxemia (ET) schedules.

### 3. 🌾 Crop Lifecycle & Planting Manager (பயிர் சாகுபடி)
- **Farmland Plot Registry**: Acreage, soil types (வண்டல் மண், செம்மண், கரிசல் மண்), and irrigation sources.
- **Season Templates**: Kuruvai (குறுவை), Samba/Thaladi (சம்பா/தாளடி), and Navarai (நவரை).
- **Growth Stage Progression**: Sowing $\rightarrow$ Transplanting $\rightarrow$ Tillering $\rightarrow$ Flowering $\rightarrow$ Harvest.
- Fertilizer and irrigation reminders.

### 4. 💰 Farm Accounting & P&L Statement (வரவு செலவு கணக்கு)
- Categorized expense logging (Seeds, Fertilizer, Pesticide, Tractor, Labor, Feed, Vet, Diesel, Transport).
- Income logging (Produce sales, Milk cooperative payments, Livestock sales).
- Dynamic **Net Farm Profit / Loss** calculation.
- **Return on Investment (ROI %)** on farm expenditures.
- Interactive category breakdown doughnut chart.

### 5. ⛅ Weather & Agro-Advisories (வானிலை & வழிகாட்டல்)
- Live Open-Meteo weather data for all 38 districts of Tamil Nadu (Temperature, Humidity, Wind speed, Rain probability, 7-day outlook).
- Rule-based agro-advisories (e.g. rain warnings to postpone pesticide spraying and urea dressing; high-wind warnings to prop banana trees).
- Tamil Nadu Government Subsidies Directory (PM-KISAN, Micro-Irrigation 100% subsidy, Free Agri Power, Crop Insurance PMFBY).
- Emergency Helplines (Kisan Call Centre 1800-180-1551, Mobile Veterinary Ambulance 1962).

### 6. 🌐 Bilingual & Mobile PWA (தமிழ் / English)
- Instant toggle between **Tamil (தமிழ்)** and **English**.
- Mobile-first bottom tab bar.
- Progressive Web App (PWA) ready — installable directly on Android smartphones via "Add to Home Screen".

---

## 🛠️ Architecture & Dual Storage Engine

```
TN-Agri-Dashboard/
├── app.py                     # Flask web server & REST API
├── db_store.py                # Dual MongoDB Atlas + Local JSON persistence engine
├── seed_manager.py            # Sample farm data initialization for TN
├── services/
│   ├── mandi_service.py       # Live Mandi rates & 15-day trend generator
│   ├── weather_service.py     # Open-Meteo weather & agro-advisory engine
│   └── breeding_engine.py     # Veterinary gestation & reproduction calculations
├── static/
│   ├── css/style.css          # Farmer-friendly lush theme & mobile navigation
│   ├── js/
│   │   ├── app.js             # AJAX reactivity, chart rendering & modals
│   │   ├── i18n.js            # English & Tamil translation dictionary
│   │   └── sw.js              # PWA service worker for offline support
│   └── manifest.json          # PWA manifest
├── templates/                 # Jinja2 responsive templates
│   ├── base.html
│   ├── index.html
│   ├── mandi.html
│   ├── crops.html
│   ├── livestock.html
│   ├── financials.html
│   ├── advisories.html
│   └── settings.html
├── requirements.txt
├── Procfile
├── render.yaml
└── README.md
```

### How the Dual Storage Engine Works:
- **With MongoDB Atlas**: Provide `MONGO_URI` environment variable. The app automatically connects to Atlas (`uzhavan_db`) and synchronizes all collections (`plots`, `crops`, `livestock`, `breeding_records`, `milk_records`, `financials`, `settings`).
- **Offline / Local JSON Fallback**: If `MONGO_URI` is not set or network drops, data is automatically loaded from and atomically saved to `local_data/*.json` files. Zero data loss!

---

## 🚀 Local Quickstart

1. **Clone or Navigate to the directory**:
   ```bash
   cd c:\Users\admin\Desktop\TN-Agri-Dashboard
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python app.py
   ```

4. **Open in Browser**:
   Navigate to `http://localhost:5000`

---

## ☁️ Deployment on Render

This application is ready to deploy directly on **Render Free Tier**:

1. Push this repository to GitHub or GitLab.
2. In the Render Dashboard, click **New + $\rightarrow$ Web Service**.
3. Connect your repository.
4. Configure the settings:
   - **Environment:** `Python`
   - **Region:** `Singapore` (closest to Tamil Nadu)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers=2 --threads=2 --timeout=120`
5. Under **Environment Variables**, add:
   - `MONGO_URI`: `mongodb+srv://<username>:<password>@cluster0.mongodb.net/uzhavan_db?retryWrites=true&w=majority`
   - `SECRET_KEY`: Any random string (e.g. `uzhavan-secret-2026`)
   - `DATA_GOV_IN_API_KEY`: *(Optional)* Your free API key from data.gov.in
6. Click **Create Web Service**. Your app is now live!
