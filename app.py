import os
from functools import wraps
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import db_store
import seed_manager
from services import mandi_service, weather_service, breeding_engine, schemes_service

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "uzhavan-farm-secret-key-2026-auth")

# Initialize seed data
try:
    seed_manager.seed_sample_farm_data()
except Exception as e:
    print(f"Notice on seed check: {e}")

# ==========================================
# AUTHENTICATION HELPERS & MIDDLEWARE
# ==========================================

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db_store.get_user_by_username(user_id)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user_context():
    user = get_current_user()
    if not user:
        # Fallback default object for non-logged in or template safety
        user = {
            "username": "",
            "farmer_name": "Farmer (உழவர்)",
            "farm_name": "Uzhavan Farm",
            "district": "Thanjavur",
            "taluk": "",
            "village": "",
            "language": "ta"
        }
    return dict(current_user=user, settings=user)

# ==========================================
# AUTH ROUTES: LOGIN, SIGNUP, LOGOUT, PROFILE
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))

    districts = mandi_service.ALL_TN_DISTRICTS
    error = None

    if request.method == "POST":
        action = request.form.get("action")
        
        # Quick Demo Login Button
        if action == "demo":
            user = db_store.get_user_by_username("farmer")
            if user:
                _set_user_session(user)
                return redirect(url_for("index"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = db_store.authenticate_user(username, password)
        if user:
            _set_user_session(user)
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        else:
            error = "Invalid username or password. Please try again."

    return render_template("login.html", error=error, districts=districts)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("index"))

    districts = mandi_service.ALL_TN_DISTRICTS
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        farmer_name = request.form.get("farmer_name", "").strip()
        farm_name = request.form.get("farm_name", "").strip()
        district = request.form.get("district", "Thanjavur").strip()
        taluk = request.form.get("taluk", "").strip()
        village = request.form.get("village", "").strip()
        language = request.form.get("language", "ta").strip()

        if not username or not password or not farmer_name:
            error = "Please fill in all required fields (Username, Password, Farmer Name)."
        elif len(password) < 4:
            error = "Password should be at least 4 characters long."
        else:
            user, err = db_store.create_user(
                username=username,
                password=password,
                farmer_name=farmer_name,
                farm_name=farm_name,
                district=district,
                taluk=taluk,
                village=village,
                language=language
            )
            if err:
                error = err
            else:
                _set_user_session(user)
                return redirect(url_for("index"))

    return render_template("signup.html", error=error, districts=districts)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

def _set_user_session(user):
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["farmer_name"] = user.get("farmer_name", "")
    session["farm_name"] = user.get("farm_name", "")
    session["district"] = user.get("district", "Thanjavur")
    session["language"] = user.get("language", "ta")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = get_current_user()
    districts = mandi_service.ALL_TN_DISTRICTS
    msg = None

    if request.method == "POST":
        update_data = {
            "farmer_name": request.form.get("farmer_name", "").strip(),
            "farm_name": request.form.get("farm_name", "").strip(),
            "district": request.form.get("district", "").strip(),
            "taluk": request.form.get("taluk", "").strip(),
            "village": request.form.get("village", "").strip(),
            "language": request.form.get("language", "ta").strip(),
            "data_gov_key": request.form.get("data_gov_key", "").strip()
        }
        pwd = request.form.get("password")
        if pwd and len(pwd.strip()) >= 4:
            update_data["password"] = pwd.strip()

        updated = db_store.update_user_profile(user["username"], update_data)
        if updated:
            _set_user_session(updated)
            user = updated
            msg = "Profile and location preferences updated successfully! Data across the app now reflects your location."

    return render_template("profile.html", user=user, districts=districts, msg=msg)

# ==========================================
# PAGE ROUTES (PROTECTED)
# ==========================================

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/mandi")
@login_required
def mandi():
    districts = mandi_service.ALL_TN_DISTRICTS
    user = get_current_user()
    user_district = user.get("district", "Thanjavur")
    return render_template("mandi.html", districts=districts, user_district=user_district)

@app.route("/crops")
@login_required
def crops():
    return render_template("crops.html")

@app.route("/livestock")
@login_required
def livestock():
    return render_template("livestock.html")

@app.route("/financials")
@login_required
def financials():
    return render_template("financials.html")

@app.route("/advisories")
@login_required
def advisories():
    districts = mandi_service.ALL_TN_DISTRICTS
    user = get_current_user()
    user_district = user.get("district", "Thanjavur")
    return render_template("advisories.html", districts=districts, user_district=user_district)

# Settings alias redirects to profile
@app.route("/settings")
@login_required
def settings_page():
    return redirect(url_for("profile"))

# ==========================================
# REST API ENDPOINTS (SCOPED TO CURRENT USER)
# ==========================================

@app.route("/api/overview")
@login_required
def api_overview():
    user = get_current_user()
    uname = user["username"]
    user_district = user.get("district", "Thanjavur")

    plots = db_store.get_user_items("plots", uname)
    crops = db_store.get_user_items("crops", uname)
    livestock = db_store.get_user_items("livestock", uname)
    breeding_records = db_store.get_user_items("breeding_records", uname)
    financials = db_store.get_user_items("financials", uname)

    total_acres = sum(float(p.get("area_acres", 0)) for p in plots)
    active_crops = [c for c in crops if c.get("status") == "active"]
    
    total_income = sum(float(f.get("amount", 0)) for f in financials if f.get("type") == "income")
    total_expense = sum(float(f.get("amount", 0)) for f in financials if f.get("type") == "expense")
    net_profit = total_income - total_expense

    alerts = breeding_engine.generate_livestock_alerts(livestock, breeding_records)

    # Weather snapshot based on user's selected location!
    weather = weather_service.get_weather_forecast(user_district)

    return jsonify({
        "farmer_name": user.get("farmer_name"),
        "farm_name": user.get("farm_name"),
        "district": user_district,
        "village": user.get("village"),
        "taluk": user.get("taluk"),
        "total_plots": len(plots),
        "total_acres": round(total_acres, 1),
        "active_crops_count": len(active_crops),
        "total_animals": len(livestock),
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_profit": round(net_profit, 2),
        "alerts": alerts[:5],
        "weather_snapshot": {
            "temp": weather["current"]["temp"],
            "condition": weather["current"]["condition"],
            "condition_ta": weather["current"]["condition_ta"],
            "rain_prob": weather["forecast"][0]["rain_prob"] if weather["forecast"] else 0,
            "district": user_district
        }
    })

# --- Location-Centric Mandi Prices ---
@app.route("/api/mandi/prices")
@login_required
def api_mandi_prices():
    user = get_current_user()
    user_district = user.get("district", "Thanjavur")

    # If district is specifically chosen in dropdown, respect that; otherwise default to user's preferred district
    selected_district = request.args.get("district")
    if not selected_district or selected_district == "all":
        district = user_district
        scope = "regional"
    elif selected_district == "user_local":
        district = user_district
        scope = "local"
    elif selected_district == "all_tn":
        district = None
        scope = "all"
    else:
        district = selected_district
        scope = "local"

    search = request.args.get("search", "")
    category = request.args.get("category", "")
    prices = mandi_service.get_mandi_prices_for_user(
        user_district=district, 
        search_term=search, 
        scope=scope, 
        category=category if category else None
    )
    return jsonify(prices)

@app.route("/api/mandi/trend")
@login_required
def api_mandi_trend():
    commodity = request.args.get("commodity", "Paddy (Ponni / பொன்னி)")
    history = mandi_service.get_price_history(commodity, days=15)
    return jsonify(history)

# --- User-Scoped Plots API ---
@app.route("/api/plots", methods=["GET", "POST"])
@login_required
def api_plots():
    user = get_current_user()
    uname = user["username"]

    if request.method == "POST":
        data = request.json or request.form.to_dict()
        data["location"] = f"{user.get('village', '')}, {user.get('district', '')}".strip(", ")
        item = db_store.save_user_item("plots", data, uname)
        return jsonify(item), 201

    return jsonify(db_store.get_user_items("plots", uname))

@app.route("/api/plots/<plot_id>", methods=["DELETE"])
@login_required
def api_delete_plot(plot_id):
    user = get_current_user()
    success = db_store.delete_user_item("plots", plot_id, user["username"])
    return jsonify({"success": success})

# --- User-Scoped Crops API ---
@app.route("/api/crops", methods=["GET", "POST"])
@login_required
def api_crops():
    user = get_current_user()
    uname = user["username"]

    if request.method == "POST":
        data = request.json or request.form.to_dict()
        if not data.get("status"):
            data["status"] = "active"
        if not data.get("stage"):
            data["stage"] = "Sowing / Nursery (விதைப்பு / நாற்றங்கால்)"
        item = db_store.save_user_item("crops", data, uname)
        return jsonify(item), 201
    
    crops = db_store.get_user_items("crops", uname)
    plots = {p["id"]: p.get("name") for p in db_store.get_user_items("plots", uname)}
    for c in crops:
        if c.get("plot_id") in plots:
            c["plot_name"] = plots[c["plot_id"]]
    return jsonify(crops)

@app.route("/api/crops/<crop_id>", methods=["DELETE", "PUT"])
@login_required
def api_modify_crop(crop_id):
    user = get_current_user()
    uname = user["username"]

    if request.method == "DELETE":
        db_store.delete_user_item("crops", crop_id, uname)
        return jsonify({"success": True})
    elif request.method == "PUT":
        data = request.json or {}
        existing = db_store.get_by_id("crops", crop_id)
        if existing and existing.get("user_id", "farmer") == uname:
            existing.update(data)
            db_store.save_user_item("crops", existing, uname)
            return jsonify(existing)
        return jsonify({"error": "Crop not found or unauthorized"}), 404

# --- User-Scoped Livestock API ---
@app.route("/api/livestock", methods=["GET", "POST"])
@login_required
def api_livestock():
    user = get_current_user()
    uname = user["username"]

    if request.method == "POST":
        data = request.json or request.form.to_dict()
        item = db_store.save_user_item("livestock", data, uname)
        return jsonify(item), 201
    
    animals = db_store.get_user_items("livestock", uname)
    breeding_records = db_store.get_user_items("breeding_records", uname)
    sorted_breeding = sorted(breeding_records, key=lambda x: str(x.get("date", "")), reverse=True)
    
    for animal in animals:
        aid = str(animal.get("id"))
        species = (animal.get("species") or "cow").lower()
        active_rec = next((r for r in sorted_breeding if str(r.get("animal_id")) == aid and r.get("status") == "active"), None)
        if active_rec:
            ev_date = active_rec.get("date")
            if species in ["cow", "buffalo", "cattle"]:
                animal["reproduction"] = breeding_engine.calculate_cattle_reproduction(ev_date, is_buffalo=(species == "buffalo"))
            elif species in ["goat", "sheep"]:
                animal["reproduction"] = breeding_engine.calculate_goat_reproduction(ev_date)
            animal["active_breeding_record"] = active_rec

    return jsonify(animals)

@app.route("/api/livestock/<animal_id>", methods=["DELETE"])
@login_required
def api_delete_livestock(animal_id):
    user = get_current_user()
    db_store.delete_user_item("livestock", animal_id, user["username"])
    return jsonify({"success": True})

# --- User-Scoped Breeding Records API ---
@app.route("/api/breeding", methods=["GET", "POST"])
@login_required
def api_breeding():
    user = get_current_user()
    uname = user["username"]

    if request.method == "POST":
        data = request.json or request.form.to_dict()
        if not data.get("status"):
            data["status"] = "active"

        aid = str(data.get("animal_id", "")).strip()
        if aid:
            # Look up animal tag and update animal status to 'pregnant'
            animals = db_store.get_user_items("livestock", uname)
            target_animal = next((a for a in animals if str(a.get("id")) == aid), None)
            if target_animal:
                data["animal_tag"] = target_animal.get("tag_id") or target_animal.get("name") or aid
                if target_animal.get("status") != "pregnant":
                    target_animal["status"] = "pregnant"
                    db_store.save_user_item("livestock", target_animal, uname)

            # Supersede prior active breeding records for this animal so latest takes effect
            existing_recs = db_store.get_user_items("breeding_records", uname)
            for rec in existing_recs:
                if str(rec.get("animal_id")) == aid and rec.get("status") == "active":
                    rec["status"] = "superseded"
                    db_store.save_user_item("breeding_records", rec, uname)

        item = db_store.save_user_item("breeding_records", data, uname)
        return jsonify(item), 201

    recs = db_store.get_user_items("breeding_records", uname)
    recs.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return jsonify(recs)

@app.route("/api/breeding/calculate")
@login_required
def api_breeding_calculate():
    species = request.args.get("species", "cow")
    ev_date = request.args.get("date", date.today().isoformat())
    if species in ["cow", "buffalo"]:
        res = breeding_engine.calculate_cattle_reproduction(ev_date, is_buffalo=(species == "buffalo"))
    else:
        res = breeding_engine.calculate_goat_reproduction(ev_date)
    return jsonify(res)

@app.route("/api/breeding/<record_id>", methods=["DELETE"])
@login_required
def api_delete_breeding(record_id):
    user = get_current_user()
    db_store.delete_user_item("breeding_records", record_id, user["username"])
    return jsonify({"success": True})

# --- User-Scoped Milk Records API ---
@app.route("/api/milk", methods=["GET", "POST"])
@login_required
def api_milk():
    user = get_current_user()
    uname = user["username"]

    if request.method == "POST":
        data = request.json or request.form.to_dict()
        try:
            m = float(data.get("morning_liters", 0))
            e = float(data.get("evening_liters", 0))
            data["total_liters"] = round(m + e, 2)
            rate = float(data.get("rate_per_liter", 38.0))
            data["total_amount"] = round(data["total_liters"] * rate, 2)

            aid = str(data.get("animal_id", "")).strip()
            if aid:
                animals = db_store.get_user_items("livestock", uname)
                target_animal = next((a for a in animals if str(a.get("id")) == aid), None)
                if target_animal:
                    data["animal_tag"] = target_animal.get("tag_id") or target_animal.get("name") or aid
        except Exception:
            pass
        item = db_store.save_user_item("milk_records", data, uname)
        return jsonify(item), 201
    
    logs = db_store.get_user_items("milk_records", uname)
    logs.sort(key=lambda x: x.get("date", ""), reverse=True)
    return jsonify(logs)

@app.route("/api/milk/<log_id>", methods=["DELETE"])
@login_required
def api_delete_milk(log_id):
    user = get_current_user()
    db_store.delete_user_item("milk_records", log_id, user["username"])
    return jsonify({"success": True})

# --- User-Scoped Financials API ---
@app.route("/api/financials", methods=["GET", "POST"])
@login_required
def api_financials():
    user = get_current_user()
    uname = user["username"]

    if request.method == "POST":
        data = request.json or request.form.to_dict()
        if "amount" in data and data["amount"] not in ("", None):
            try:
                data["amount"] = float(data["amount"])
            except (ValueError, TypeError):
                data["amount"] = 0.0
        if "quantity" in data and data["quantity"] not in ("", None):
            try:
                data["quantity"] = float(data["quantity"])
            except (ValueError, TypeError):
                pass
        if "rate_per_unit" in data and data["rate_per_unit"] not in ("", None):
            try:
                data["rate_per_unit"] = float(data["rate_per_unit"])
            except (ValueError, TypeError):
                pass
        item = db_store.save_user_item("financials", data, uname)
        return jsonify(item), 201

    txns = db_store.get_user_items("financials", uname)
    txns.sort(key=lambda x: x.get("date", ""), reverse=True)
    return jsonify(txns)

@app.route("/api/financials/<item_id>", methods=["DELETE"])
@login_required
def api_delete_financial(item_id):
    user = get_current_user()
    db_store.delete_user_item("financials", item_id, user["username"])
    return jsonify({"success": True})

@app.route("/api/financials/stats")
@login_required
def api_financials_stats():
    user = get_current_user()
    uname = user["username"]
    txns = db_store.get_user_items("financials", uname)
    
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

# --- Location-Specific Weather & Advisories API ---
@app.route("/api/weather")
@login_required
def api_weather():
    user = get_current_user()
    district = request.args.get("district")
    if not district or district == "auto":
        district = user.get("district", "Thanjavur")
    data = weather_service.get_weather_forecast(district)
    return jsonify(data)

@app.route("/api/weather/locate")
@login_required
def api_weather_locate():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude required"}), 400
    try:
        data = weather_service.get_weather_by_coords(float(lat), float(lon))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Tamil Nadu Government Schemes & Subsidies API ---
@app.route("/api/schemes")
@login_required
def api_schemes():
    return jsonify(schemes_service.get_all_schemes())

@app.route("/api/schemes/<scheme_id>")
@login_required
def api_scheme_detail(scheme_id):
    scheme = schemes_service.get_scheme_by_id(scheme_id)
    if not scheme:
        return jsonify({"error": "Scheme not found"}), 404
    return jsonify(scheme)

# --- Vaccination Calendar API ---
@app.route("/api/vaccinations")
@login_required
def api_vaccinations():
    return jsonify(breeding_engine.get_vaccination_calendar())

# --- Settings API (Updates User Profile) ---
@app.route("/api/settings", methods=["GET", "POST"])
@login_required
def api_settings():
    user = get_current_user()
    if request.method == "POST":
        data = request.json or request.form.to_dict()
        updated = db_store.update_user_profile(user["username"], data)
        if updated:
            _set_user_session(updated)
            return jsonify(updated)
    return jsonify(user)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
