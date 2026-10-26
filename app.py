import os
from functools import wraps
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_from_directory
import db_store
import seed_manager
from services import mandi_service, weather_service, breeding_engine, schemes_service

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "uzhavan-farm-secret-key-2026-auth")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
                               "favicon.ico", mimetype="image/vnd.microsoft.icon")

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

@app.route("/api/plots/<plot_id>", methods=["DELETE", "PUT"])
@login_required
def api_modify_plot(plot_id):
    user = get_current_user()
    uname = user["username"]
    if request.method == "DELETE":
        success = db_store.delete_user_item("plots", plot_id, uname)
        return jsonify({"success": success})
    elif request.method == "PUT":
        data = request.json or {}
        existing = db_store.get_by_id("plots", plot_id)
        if existing and existing.get("user_id", "farmer") == uname:
            existing.update(data)
            existing["id"] = plot_id
            db_store.save_user_item("plots", existing, uname)
            return jsonify(existing)
        return jsonify({"error": "Plot not found or unauthorized"}), 404

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
    plots = {str(p["id"]): p.get("name") for p in db_store.get_user_items("plots", uname)}
    txns = db_store.get_user_items("financials", uname)

    for c in crops:
        cid = str(c.get("id", ""))
        if c.get("plot_id") and str(c.get("plot_id")) in plots:
            c["plot_name"] = plots[str(c["plot_id"])]

        # Collect transactions strictly assigned to this crop
        crop_txns = [t for t in txns if str(t.get("crop_id") or "").strip() == cid]

        total_exp = sum(float(t.get("amount", 0)) for t in crop_txns if t.get("type") == "expense")
        total_inc = sum(float(t.get("amount", 0)) for t in crop_txns if t.get("type") == "income")
        net = total_inc - total_exp

        c["total_expense"] = round(total_exp, 2)
        c["total_income"] = round(total_inc, 2)
        c["net_profit"] = round(net, 2)
        c["roi_percentage"] = round((net / total_exp * 100), 1) if total_exp > 0 else 0.0
        c["expense_count"] = len([t for t in crop_txns if t.get("type") == "expense"])
        c["income_count"] = len([t for t in crop_txns if t.get("type") == "income"])
        c["transactions_count"] = len(crop_txns)

    return jsonify(crops)

@app.route("/api/crops/<crop_id>/financials")
@login_required
def api_crop_financials(crop_id):
    user = get_current_user()
    uname = user["username"]
    crops = db_store.get_user_items("crops", uname)
    target_crop = next((c for c in crops if str(c.get("id")) == str(crop_id)), None)
    if not target_crop:
        return jsonify({"error": "Crop not found"}), 404

    plots = {str(p["id"]): p.get("name") for p in db_store.get_user_items("plots", uname)}
    target_crop["plot_name"] = plots.get(str(target_crop.get("plot_id")), "Plot")

    txns = db_store.get_user_items("financials", uname)
    cid = str(target_crop.get("id"))

    matching = []
    cat_expenses = {}
    for t in txns:
        if str(t.get("crop_id") or "").strip() == cid:
            t["crop_name"] = target_crop.get("crop_name")
            t["plot_name"] = target_crop.get("plot_name")
            matching.append(t)
            if t.get("type") == "expense":
                cat = t.get("category", "General Expense")
                cat_expenses[cat] = cat_expenses.get(cat, 0.0) + float(t.get("amount", 0))

    matching.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    total_exp = sum(float(t.get("amount", 0)) for t in matching if t.get("type") == "expense")
    total_inc = sum(float(t.get("amount", 0)) for t in matching if t.get("type") == "income")
    net = total_inc - total_exp

    return jsonify({
        "crop": target_crop,
        "transactions": matching,
        "total_expense": round(total_exp, 2),
        "total_income": round(total_inc, 2),
        "net_profit": round(net, 2),
        "roi_percentage": round((net / total_exp * 100), 1) if total_exp > 0 else 0.0,
        "expenses_by_category": {k: round(v, 2) for k, v in cat_expenses.items()}
    })

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
            existing["id"] = crop_id
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

@app.route("/api/livestock/<animal_id>", methods=["DELETE", "PUT"])
@login_required
def api_modify_livestock(animal_id):
    user = get_current_user()
    uname = user["username"]
    if request.method == "DELETE":
        db_store.delete_user_item("livestock", animal_id, uname)
        return jsonify({"success": True})
    elif request.method == "PUT":
        data = request.json or {}
        existing = db_store.get_by_id("livestock", animal_id)
        if existing and existing.get("user_id", "farmer") == uname:
            existing.update(data)
            existing["id"] = animal_id
            db_store.save_user_item("livestock", existing, uname)
            return jsonify(existing)
        return jsonify({"error": "Animal not found or unauthorized"}), 404

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

@app.route("/api/breeding/<record_id>", methods=["DELETE", "PUT"])
@login_required
def api_modify_breeding(record_id):
    user = get_current_user()
    uname = user["username"]
    if request.method == "DELETE":
        db_store.delete_user_item("breeding_records", record_id, uname)
        return jsonify({"success": True})
    elif request.method == "PUT":
        data = request.json or {}
        existing = db_store.get_by_id("breeding_records", record_id)
        if existing and existing.get("user_id", "farmer") == uname:
            existing.update(data)
            existing["id"] = record_id
            aid = str(existing.get("animal_id", "")).strip()
            if aid:
                animals = db_store.get_user_items("livestock", uname)
                target_animal = next((a for a in animals if str(a.get("id")) == aid), None)
                if target_animal:
                    existing["animal_tag"] = target_animal.get("tag_id") or target_animal.get("name") or aid
            db_store.save_user_item("breeding_records", existing, uname)
            return jsonify(existing)
        return jsonify({"error": "Breeding record not found or unauthorized"}), 404

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

@app.route("/api/milk/<log_id>", methods=["DELETE", "PUT"])
@login_required
def api_modify_milk(log_id):
    user = get_current_user()
    uname = user["username"]
    if request.method == "DELETE":
        db_store.delete_user_item("milk_records", log_id, uname)
        return jsonify({"success": True})
    elif request.method == "PUT":
        data = request.json or {}
        existing = db_store.get_by_id("milk_records", log_id)
        if existing and existing.get("user_id", "farmer") == uname:
            existing.update(data)
            existing["id"] = log_id
            try:
                m = float(existing.get("morning_liters", 0))
                e = float(existing.get("evening_liters", 0))
                existing["total_liters"] = round(m + e, 2)
                rate = float(existing.get("rate_per_liter", 38.0))
                existing["total_amount"] = round(existing["total_liters"] * rate, 2)
                aid = str(existing.get("animal_id", "")).strip()
                if aid:
                    animals = db_store.get_user_items("livestock", uname)
                    target_animal = next((a for a in animals if str(a.get("id")) == aid), None)
                    if target_animal:
                        existing["animal_tag"] = target_animal.get("tag_id") or target_animal.get("name") or aid
            except Exception:
                pass
            db_store.save_user_item("milk_records", existing, uname)
            return jsonify(existing)
        return jsonify({"error": "Milk log not found or unauthorized"}), 404

def _clean_financial_data(data):
    float_fields = [
        "amount", "quantity", "rate_per_unit", "deduction_per_ton_kg",
        "deduction_flat_kg", "net_quantity", "harvest_charges",
        "transport_charges", "other_charges", "total_expenses", "gross_amount"
    ]
    for field in float_fields:
        if field in data and data[field] not in ("", None):
            try:
                data[field] = float(data[field])
            except (ValueError, TypeError):
                if field == "amount":
                    data[field] = 0.0

# --- User-Scoped Financials API ---
@app.route("/api/financials", methods=["GET", "POST"])
@login_required
def api_financials():
    user = get_current_user()
    uname = user["username"]

    if request.method == "POST":
        data = request.json or request.form.to_dict()
        _clean_financial_data(data)
        
        cid = str(data.get("crop_id") or "").strip()
        if cid:
            crops = db_store.get_user_items("crops", uname)
            target_crop = next((c for c in crops if str(c.get("id")) == cid), None)
            if target_crop:
                data["crop_id"] = cid
                data["crop_name"] = target_crop.get("crop_name")
                if not data.get("plot_id") and target_crop.get("plot_id"):
                    data["plot_id"] = target_crop.get("plot_id")
        else:
            data["crop_id"] = ""

        item = db_store.save_user_item("financials", data, uname)
        return jsonify(item), 201

    txns = db_store.get_user_items("financials", uname)
    crops_map = {str(c["id"]): c for c in db_store.get_user_items("crops", uname)}
    plots_map = {str(p["id"]): p.get("name") for p in db_store.get_user_items("plots", uname)}

    for t in txns:
        cid = str(t.get("crop_id") or "").strip()
        pid = str(t.get("plot_id") or "").strip()
        if cid and cid in crops_map:
            t["crop_name"] = crops_map[cid].get("crop_name")
            if not t.get("plot_name"):
                c_pid = str(crops_map[cid].get("plot_id") or "")
                t["plot_name"] = plots_map.get(c_pid) or crops_map[cid].get("plot_name")
        elif pid and pid in plots_map:
            t["plot_name"] = plots_map[pid]

    txns.sort(key=lambda x: str(x.get("date", "")), reverse=True)
    return jsonify(txns)

@app.route("/api/financials/<item_id>", methods=["DELETE", "PUT"])
@login_required
def api_modify_financial(item_id):
    user = get_current_user()
    uname = user["username"]
    if request.method == "DELETE":
        db_store.delete_user_item("financials", item_id, uname)
        return jsonify({"success": True})
    elif request.method == "PUT":
        data = request.json or {}
        existing = db_store.get_by_id("financials", item_id)
        if existing and existing.get("user_id", "farmer") == uname:
            existing.update(data)
            existing["id"] = item_id
            _clean_financial_data(existing)
            cid = str(existing.get("crop_id") or "").strip()
            if cid:
                crops = db_store.get_user_items("crops", uname)
                target_crop = next((c for c in crops if str(c.get("id")) == cid), None)
                if target_crop:
                    existing["crop_id"] = cid
                    existing["crop_name"] = target_crop.get("crop_name")
                    if not existing.get("plot_id") and target_crop.get("plot_id"):
                        existing["plot_id"] = target_crop.get("plot_id")
            else:
                existing["crop_id"] = ""
            db_store.save_user_item("financials", existing, uname)
            return jsonify(existing)
        return jsonify({"error": "Transaction not found or unauthorized"}), 404

@app.route("/api/financials/stats")
@login_required
def api_financials_stats():
    user = get_current_user()
    uname = user["username"]
    txns = db_store.get_user_items("financials", uname)
    crops = db_store.get_user_items("crops", uname)
    plots_map = {str(p["id"]): p.get("name") for p in db_store.get_user_items("plots", uname)}
    
    cat_expenses = {}
    cat_income = {}
    total_exp = 0.0
    total_inc = 0.0

    # Build crop mapping for fast lookup
    crop_stats = {}
    for c in crops:
        cid = str(c.get("id"))
        p_name = plots_map.get(str(c.get("plot_id")), c.get("plot_name") or "Plot")
        crop_stats[cid] = {
            "id": cid,
            "crop_name": c.get("crop_name"),
            "variety": c.get("variety"),
            "season": c.get("season"),
            "stage": c.get("stage"),
            "status": c.get("status", "active"),
            "plot_id": c.get("plot_id"),
            "plot_name": p_name,
            "area_acres": c.get("area_cultivated_acres", 0),
            "sowing_date": c.get("sowing_date", ""),
            "total_expense": 0.0,
            "total_income": 0.0,
            "net_profit": 0.0,
            "roi_percentage": 0.0,
            "expense_count": 0,
            "income_count": 0,
            "expenses_by_category": {}
        }

    general_exp = 0.0
    general_inc = 0.0

    for t in txns:
        amt = float(t.get("amount", 0))
        cat = t.get("category", "General")
        is_exp = t.get("type") == "expense"
        
        if is_exp:
            total_exp += amt
            cat_expenses[cat] = cat_expenses.get(cat, 0.0) + amt
        else:
            total_inc += amt
            cat_income[cat] = cat_income.get(cat, 0.0) + amt

        # Allocate strictly to linked crop, or general farm overhead if unallocated
        cid = str(t.get("crop_id") or "").strip()
        if cid and cid in crop_stats:
            cs = crop_stats[cid]
            if is_exp:
                cs["total_expense"] += amt
                cs["expense_count"] += 1
                cs["expenses_by_category"][cat] = cs["expenses_by_category"].get(cat, 0.0) + amt
            else:
                cs["total_income"] += amt
                cs["income_count"] += 1
        else:
            if is_exp:
                general_exp += amt
            else:
                general_inc += amt

    # Calculate net profit and ROI for each crop
    crop_summary = []
    for cid, cs in crop_stats.items():
        cs["total_expense"] = round(cs["total_expense"], 2)
        cs["total_income"] = round(cs["total_income"], 2)
        net = cs["total_income"] - cs["total_expense"]
        cs["net_profit"] = round(net, 2)
        cs["roi_percentage"] = round((net / cs["total_expense"] * 100), 1) if cs["total_expense"] > 0 else 0.0
        cs["expenses_by_category"] = {k: round(v, 2) for k, v in cs["expenses_by_category"].items()}
        crop_summary.append(cs)

    # Sort crops by active first, then sowing_date desc
    crop_summary.sort(key=lambda x: (0 if x["status"] == "active" else 1, str(x.get("sowing_date", ""))), reverse=False)

    net = total_inc - total_exp
    roi = round((net / total_exp * 100), 1) if total_exp > 0 else 0.0

    return jsonify({
        "total_income": round(total_inc, 2),
        "total_expense": round(total_exp, 2),
        "net_profit": round(net, 2),
        "roi_percentage": roi,
        "expenses_by_category": {k: round(v, 2) for k, v in cat_expenses.items()},
        "income_by_category": {k: round(v, 2) for k, v in cat_income.items()},
        "crop_summary": crop_summary,
        "general_summary": {
            "total_expense": round(general_exp, 2),
            "total_income": round(general_inc, 2),
            "net_profit": round(general_inc - general_exp, 2)
        }
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
