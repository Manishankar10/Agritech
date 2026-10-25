import os
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for
import db_store
import seed_manager
from services import mandi_service, weather_service, breeding_engine

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "uzhavan-farm-secret-key-2026")

# Initialize seed data if database is empty
try:
    seed_manager.seed_sample_farm_data()
except Exception as e:
    print(f"Notice on seed data check: {e}")

# Context processor to inject user settings into all templates
@app.context_processor
def inject_settings():
    settings = db_store.get_settings()
    return dict(settings=settings)

# ==========================================
# PAGE ROUTES
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mandi")
def mandi():
    districts = mandi_service.ALL_TN_DISTRICTS
    return render_template("mandi.html", districts=districts)

@app.route("/crops")
def crops():
    return render_template("crops.html")

@app.route("/livestock")
def livestock():
    return render_template("livestock.html")

@app.route("/financials")
def financials():
    return render_template("financials.html")

@app.route("/advisories")
def advisories():
    districts = mandi_service.ALL_TN_DISTRICTS
    return render_template("advisories.html", districts=districts)

@app.route("/settings")
def settings_page():
    districts = mandi_service.ALL_TN_DISTRICTS
    return render_template("settings.html", districts=districts)

# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.route("/api/overview")
def api_overview():
    """Returns dashboard summary stats, financial totals, and urgent alerts."""
    plots = db_store.get_all("plots")
    crops = db_store.get_all("crops")
    livestock = db_store.get_all("livestock")
    breeding_records = db_store.get_all("breeding_records")
    financials = db_store.get_all("financials")
    settings = db_store.get_settings()

    total_acres = sum(float(p.get("area_acres", 0)) for p in plots)
    active_crops = [c for c in crops if c.get("status") == "active"]
    
    total_income = sum(float(f.get("amount", 0)) for f in financials if f.get("type") == "income")
    total_expense = sum(float(f.get("amount", 0)) for f in financials if f.get("type") == "expense")
    net_profit = total_income - total_expense

    alerts = breeding_engine.generate_livestock_alerts(livestock, breeding_records)

    # Weather quick snapshot
    district = settings.get("district", "Thanjavur")
    weather = weather_service.get_weather_forecast(district)

    return jsonify({
        "total_plots": len(plots),
        "total_acres": round(total_acres, 1),
        "active_crops_count": len(active_crops),
        "total_animals": len(livestock),
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_profit": round(net_profit, 2),
        "alerts": alerts[:5], # top 5 alerts
        "weather_snapshot": {
            "temp": weather["current"]["temp"],
            "condition": weather["current"]["condition"],
            "condition_ta": weather["current"]["condition_ta"],
            "rain_prob": weather["forecast"][0]["rain_prob"] if weather["forecast"] else 0,
            "district": district
        }
    })

# --- Mandi API ---
@app.route("/api/mandi/prices")
def api_mandi_prices():
    district = request.args.get("district", "")
    search = request.args.get("search", "")
    settings = db_store.get_settings()
    api_key = settings.get("data_gov_key") or os.environ.get("DATA_GOV_IN_API_KEY")

    prices = mandi_service.get_mandi_prices(district=district, search_term=search, api_key=api_key)
    return jsonify(prices)

@app.route("/api/mandi/trend")
def api_mandi_trend():
    commodity = request.args.get("commodity", "Paddy (Ponni)")
    history = mandi_service.get_price_history(commodity, days=15)
    return jsonify(history)

# --- Plots API ---
@app.route("/api/plots", methods=["GET", "POST"])
def api_plots():
    if request.method == "POST":
        data = request.json or request.form.to_dict()
        item = db_store.save_item("plots", data)
        return jsonify(item), 201
    return jsonify(db_store.get_all("plots"))

@app.route("/api/plots/<plot_id>", methods=["DELETE"])
def api_delete_plot(plot_id):
    db_store.delete_item("plots", plot_id)
    return jsonify({"success": True})

# --- Crops API ---
@app.route("/api/crops", methods=["GET", "POST"])
def api_crops():
    if request.method == "POST":
        data = request.json or request.form.to_dict()
        if not data.get("status"):
            data["status"] = "active"
        item = db_store.save_item("crops", data)
        return jsonify(item), 201
    
    crops = db_store.get_all("crops")
    plots = {p["id"]: p.get("name") for p in db_store.get_all("plots")}
    for c in crops:
        if c.get("plot_id") in plots:
            c["plot_name"] = plots[c["plot_id"]]
    return jsonify(crops)

@app.route("/api/crops/<crop_id>", methods=["DELETE", "PUT"])
def api_modify_crop(crop_id):
    if request.method == "DELETE":
        db_store.delete_item("crops", crop_id)
        return jsonify({"success": True})
    elif request.method == "PUT":
        data = request.json or {}
        existing = db_store.get_by_id("crops", crop_id)
        if existing:
            existing.update(data)
            db_store.save_item("crops", existing)
            return jsonify(existing)
        return jsonify({"error": "Crop not found"}), 404

# --- Livestock API ---
@app.route("/api/livestock", methods=["GET", "POST"])
def api_livestock():
    if request.method == "POST":
        data = request.json or request.form.to_dict()
        item = db_store.save_item("livestock", data)
        return jsonify(item), 201
    
    animals = db_store.get_all("livestock")
    breeding_records = db_store.get_all("breeding_records")
    
    # Enrich animal with active breeding info & gestation progress
    for animal in animals:
        aid = str(animal.get("id"))
        species = (animal.get("species") or "cow").lower()
        active_rec = next((r for r in breeding_records if str(r.get("animal_id")) == aid and r.get("status") == "active"), None)
        if active_rec:
            ev_date = active_rec.get("date")
            if species in ["cow", "buffalo", "cattle"]:
                animal["reproduction"] = breeding_engine.calculate_cattle_reproduction(ev_date, is_buffalo=(species == "buffalo"))
            elif species in ["goat", "sheep"]:
                animal["reproduction"] = breeding_engine.calculate_goat_reproduction(ev_date)
            animal["active_breeding_record"] = active_rec

    return jsonify(animals)

@app.route("/api/livestock/<animal_id>", methods=["DELETE"])
def api_delete_livestock(animal_id):
    db_store.delete_item("livestock", animal_id)
    return jsonify({"success": True})

# --- Breeding Records API ---
@app.route("/api/breeding", methods=["GET", "POST"])
def api_breeding():
    if request.method == "POST":
        data = request.json or request.form.to_dict()
        if not data.get("status"):
            data["status"] = "active"
        item = db_store.save_item("breeding_records", data)
        return jsonify(item), 201
    return jsonify(db_store.get_all("breeding_records"))

@app.route("/api/breeding/calculate")
def api_breeding_calculate():
    """Dynamic reproduction calculator for previewing dates."""
    species = request.args.get("species", "cow")
    ev_date = request.args.get("date", date.today().isoformat())
    if species in ["cow", "buffalo"]:
        res = breeding_engine.calculate_cattle_reproduction(ev_date, is_buffalo=(species == "buffalo"))
    else:
        res = breeding_engine.calculate_goat_reproduction(ev_date)
    return jsonify(res)

@app.route("/api/breeding/<record_id>", methods=["DELETE"])
def api_delete_breeding(record_id):
    db_store.delete_item("breeding_records", record_id)
    return jsonify({"success": True})

# --- Milk Records API ---
@app.route("/api/milk", methods=["GET", "POST"])
def api_milk():
    if request.method == "POST":
        data = request.json or request.form.to_dict()
        try:
            m = float(data.get("morning_liters", 0))
            e = float(data.get("evening_liters", 0))
            data["total_liters"] = round(m + e, 2)
            rate = float(data.get("rate_per_liter", 38.0))
            data["total_amount"] = round(data["total_liters"] * rate, 2)
        except Exception:
            pass
        item = db_store.save_item("milk_records", data)
        return jsonify(item), 201
    
    logs = db_store.get_all("milk_records")
    logs.sort(key=lambda x: x.get("date", ""), reverse=True)
    return jsonify(logs)

@app.route("/api/milk/<log_id>", methods=["DELETE"])
def api_delete_milk(log_id):
    db_store.delete_item("milk_records", log_id)
    return jsonify({"success": True})

# --- Financials API ---
@app.route("/api/financials", methods=["GET", "POST"])
def api_financials():
    if request.method == "POST":
        data = request.json or request.form.to_dict()
        if "amount" in data:
            data["amount"] = float(data["amount"])
        item = db_store.save_item("financials", data)
        return jsonify(item), 201

    txns = db_store.get_all("financials")
    txns.sort(key=lambda x: x.get("date", ""), reverse=True)
    return jsonify(txns)

@app.route("/api/financials/<item_id>", methods=["DELETE"])
def api_delete_financial(item_id):
    db_store.delete_item("financials", item_id)
    return jsonify({"success": True})

@app.route("/api/financials/stats")
def api_financials_stats():
    txns = db_store.get_all("financials")
    
    cat_expenses = {}
    cat_income = {}
    total_exp = 0.0
    total_inc = 0.0

    for t in txns:
        amt = float(t.get("amount", 0))
        cat = t.get("category", "General")
        if t.get("type") == "expense":
            total_exp += amt
            cat_expenses[cat] = cat_expenses.get(cat, 0.0) + amt
        else:
            total_inc += amt
            cat_income[cat] = cat_income.get(cat, 0.0) + amt

    net = total_inc - total_exp
    roi = round((net / total_exp * 100), 1) if total_exp > 0 else 0.0

    return jsonify({
        "total_income": round(total_inc, 2),
        "total_expense": round(total_exp, 2),
        "net_profit": round(net, 2),
        "roi_percentage": roi,
        "expenses_by_category": {k: round(v, 2) for k, v in cat_expenses.items()},
        "income_by_category": {k: round(v, 2) for k, v in cat_income.items()}
    })

# --- Weather API ---
@app.route("/api/weather")
def api_weather():
    district = request.args.get("district")
    if not district:
        settings = db_store.get_settings()
        district = settings.get("district", "Thanjavur")
    data = weather_service.get_weather_forecast(district)
    return jsonify(data)

# --- Vaccination Calendar API ---
@app.route("/api/vaccinations")
def api_vaccinations():
    return jsonify(breeding_engine.get_vaccination_calendar())

# --- Settings API ---
@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "POST":
        data = request.json or request.form.to_dict()
        updated = db_store.update_settings(data)
        return jsonify(updated)
    return jsonify(db_store.get_settings())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
