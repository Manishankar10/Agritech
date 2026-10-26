import unittest
import json
from datetime import date, timedelta
from app import app
import db_store
from services import breeding_engine, mandi_service, weather_service

class TestUzhavanDesk(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_unauthenticated_redirect(self):
        """Verifies unauthenticated visitors are redirected to login."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_login_and_signup_pages_render_correctly(self):
        """Verifies login and signup pages render visible HTML with closed style tags and forms."""
        login_resp = self.client.get("/login?next=https://uzhavan-agritech.onrender.com/")
        self.assertEqual(login_resp.status_code, 200)
        login_html = login_resp.data.decode("utf-8")
        self.assertIn("</style>", login_html)
        self.assertIn("Sign In to Farm Dashboard", login_html)
        self.assertIn("<form", login_html)
        self.assertIn("username", login_html)

        signup_resp = self.client.get("/signup")
        self.assertEqual(signup_resp.status_code, 200)
        signup_html = signup_resp.data.decode("utf-8")
        self.assertIn("</style>", signup_html)
        self.assertIn("Register Farmer Profile", signup_html)
        self.assertIn("<form", signup_html)

    def test_login_and_pages_load(self):
        """Verifies demo login and authenticated page loads."""
        # Perform demo login
        login_resp = self.client.post("/login", data={"action": "demo"}, follow_redirects=True)
        self.assertEqual(login_resp.status_code, 200)

        # Verify pages load
        routes = ["/", "/mandi", "/crops", "/livestock", "/financials", "/advisories", "/profile"]
        for r in routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f"Route {r} failed with status {resp.status_code}")

    def test_signup_with_location_preference(self):
        """Verifies signing up with custom district and village preferences."""
        import uuid
        uname = f"farmer_{uuid.uuid4().hex[:6]}"
        signup_data = {
            "username": uname,
            "password": "pass1234",
            "farmer_name": "Rangarajan S (ரங்கராஜன்)",
            "farm_name": "Kongu Naturals",
            "district": "Coimbatore",
            "taluk": "Pollachi",
            "village": "Anamalai",
            "language": "en"
        }
        resp = self.client.post("/signup", data=signup_data, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify overview returns Coimbatore as district
        overview_resp = self.client.get("/api/overview")
        self.assertEqual(overview_resp.status_code, 200)
        ov = json.loads(overview_resp.data)
        self.assertEqual(ov["district"], "Coimbatore")
        self.assertEqual(ov["farmer_name"], "Rangarajan S (ரங்கராஜன்)")

    def test_location_scoped_mandi_prices(self):
        """Verifies mandi prices default to user district and surrounding regional APMCs."""
        # Ensure user exists
        if not db_store.get_user_by_username("coimbatore_farmer"):
            db_store.create_user("coimbatore_farmer", "pass1234", "Rangarajan", "Kongu Farm", "Coimbatore")

        # Login as Coimbatore farmer
        self.client.post("/login", data={"username": "coimbatore_farmer", "password": "pass1234"}, follow_redirects=True)

        # Default query (regional scope for Coimbatore)
        resp = self.client.get("/api/mandi/prices")
        self.assertEqual(resp.status_code, 200)
        prices = json.loads(resp.data)
        self.assertTrue(len(prices) > 0)
        
        # Verify regional clustering includes Coimbatore / Pollachi / Western zone
        districts_in_result = set(p["district"] for p in prices)
        self.assertTrue("Coimbatore" in districts_in_result or "Tiruppur" in districts_in_result or "Erode" in districts_in_result)

    def test_profile_update_changes_location(self):
        """Verifies changing location in Profile instantly changes active data location."""
        # Login as demo farmer
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)

        # Update profile location to Madurai
        update_data = {
            "farmer_name": "Murugan K",
            "farm_name": "Meenakshi Thottam",
            "district": "Madurai",
            "taluk": "Melur",
            "village": "Alagarkoil",
            "language": "ta",
            "data_gov_key": ""
        }
        resp = self.client.post("/profile", data=update_data, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Verify overview API now reports Madurai
        ov_resp = self.client.get("/api/overview")
        ov = json.loads(ov_resp.data)
        self.assertEqual(ov["district"], "Madurai")
        self.assertEqual(ov["weather_snapshot"]["district"], "Madurai")

    def test_cattle_reproduction_engine(self):
        """Verifies biological calculation milestones for cows."""
        today = date.today()
        insemination_dt = today - timedelta(days=100)
        result = breeding_engine.calculate_cattle_reproduction(insemination_dt, is_buffalo=False)
        
        self.assertEqual(result["gestation_days_total"], 283)
        self.assertEqual(result["days_pregnant"], 100)
        self.assertEqual(result["days_remaining"], 183)

    def test_goat_reproduction_engine(self):
        """Verifies biological calculation milestones for goats."""
        today = date.today()
        mating_dt = today - timedelta(days=50)
        result = breeding_engine.calculate_goat_reproduction(mating_dt)
        
        self.assertEqual(result["gestation_days_total"], 150)
        self.assertEqual(result["days_pregnant"], 50)
        self.assertEqual(result["days_remaining"], 100)

    def test_weather_service(self):
        """Verifies weather service returns structured forecasts."""
        data = weather_service.get_weather_forecast("Madurai")
        self.assertEqual(data["district"], "Madurai")
        self.assertIn("current", data)
        self.assertIn("forecast", data)
        self.assertTrue(len(data["forecast"]) > 0)

    def test_schemes_directory_and_detail(self):
        """Verifies government schemes directory and detailed scheme insights."""
        # Demo login
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)
        
        # Test all schemes endpoint
        resp = self.client.get("/api/schemes")
        self.assertEqual(resp.status_code, 200)
        schemes = json.loads(resp.data)
        self.assertTrue(len(schemes) >= 5)

        scheme_ids = [s["id"] for s in schemes]
        self.assertIn("pmksy_micro_irrigation", scheme_ids)
        self.assertIn("free_agri_electricity", scheme_ids)
        self.assertIn("cattle_shed_fodder_scheme", scheme_ids)

        # Test single scheme detail
        detail_resp = self.client.get("/api/schemes/pmksy_micro_irrigation")
        self.assertEqual(detail_resp.status_code, 200)
        detail = json.loads(detail_resp.data)
        self.assertEqual(detail["id"], "pmksy_micro_irrigation")
        self.assertIn("eligibility", detail)
        self.assertIn("documents_required", detail)
        self.assertIn("how_to_apply", detail)
        self.assertTrue(len(detail["how_to_apply"]) >= 4)
        self.assertTrue(detail["official_portal"].startswith("http"))

    def test_weather_gps_locate(self):
        """Verifies GPS coordinate mapping to nearest Tamil Nadu district."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)
        # Thanjavur coords: 10.7870, 79.1378
        resp = self.client.get("/api/weather/locate?lat=10.7870&lon=79.1378")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["district"], "Thanjavur")
        self.assertTrue(data.get("is_live_gps"))
        self.assertIn("forecast", data)

    def test_coconut_mandi_rates_and_per_kg_breakdown(self):
        """Verifies comprehensive Coconut derivatives and ₹ / kg rate calculation."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)
        resp = self.client.get("/api/mandi/prices?district=all_tn&search=Coconut")
        self.assertEqual(resp.status_code, 200)
        prices = json.loads(resp.data)
        self.assertTrue(len(prices) >= 3)

        # Verify coconut varieties are present
        commodities = [p["commodity"] for p in prices]
        self.assertTrue(any("Milling Copra" in c for c in commodities))
        self.assertTrue(any("Mature Coconut" in c for c in commodities))

        # Verify rate_per_kg_str is populated
        for p in prices:
            self.assertIn("rate_per_kg_str", p)
            self.assertTrue(len(p["rate_per_kg_str"]) > 0)

    def test_quick_log_breeding_record(self):
        """Verifies quick logging an AI/breeding event and updating animal status."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)
        today_str = date.today().isoformat()
        breed_data = {
            "animal_id": "animal_tn02",
            "event_type": "insemination",
            "date": today_str,
            "semen_bull_info": "Kangayam Purebred Bull #402",
            "technician": "Dr. Senthil / VAS"
        }
        resp = self.client.post("/api/breeding", json=breed_data)
        self.assertEqual(resp.status_code, 201)
        created = json.loads(resp.data)
        self.assertEqual(created["animal_id"], "animal_tn02")
        self.assertIn("TN-02-KAMALAM", created.get("animal_tag", ""))

        # Verify livestock endpoint now shows animal_tn02 with active reproduction
        ls_resp = self.client.get("/api/livestock")
        self.assertEqual(ls_resp.status_code, 200)
        animals = json.loads(ls_resp.data)
        kamalam = next((a for a in animals if a["id"] == "animal_tn02"), None)
        self.assertIsNotNone(kamalam)
        self.assertEqual(kamalam.get("status"), "pregnant")
        self.assertIn("reproduction", kamalam)
        self.assertEqual(kamalam["reproduction"]["days_pregnant"], 0)

    def test_quick_log_milk_record(self):
        """Verifies quick logging daily milk yield and financial calculation."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)
        milk_data = {
            "animal_id": "animal_tn01",
            "date": date.today().isoformat(),
            "morning_liters": 8.5,
            "evening_liters": 6.5,
            "rate_per_liter": 40.0,
            "fat_pct": 4.5,
            "snf_pct": 8.8,
            "buyer": "Aavin Co-op"
        }
        resp = self.client.post("/api/milk", json=milk_data)
        self.assertEqual(resp.status_code, 201)
        created = json.loads(resp.data)
        self.assertEqual(created["total_liters"], 15.0)
        self.assertEqual(created["total_amount"], 600.0)
        self.assertIn("TN-01-LAKSHMI", created.get("animal_tag", ""))

    def test_quick_log_financial_transaction(self):
        """Verifies quick logging financial expense and revenue records."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)
        exp_data = {
            "type": "expense",
            "category": "Fertilizer / உரங்கள்",
            "amount": 2500.0,
            "date": date.today().isoformat(),
            "desc": "Neem Coated Urea (2 bags)"
        }
        resp = self.client.post("/api/financials", json=exp_data)
        self.assertEqual(resp.status_code, 201)

        # Verify overview stats reflect new financial record
        ov_resp = self.client.get("/api/overview")
        self.assertEqual(ov_resp.status_code, 200)
        ov = json.loads(ov_resp.data)
        self.assertTrue(ov["total_expense"] >= 2500.0)

    def test_quick_log_crop_planting(self):
        """Verifies quick logging a new crop planting."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)
        crop_data = {
            "plot_id": "plot_delta_01",
            "crop_name": "Groundnut (மணிலா / நிலக்கடலை)",
            "variety": "TMV-7",
            "season": "Samba / Thaladi (சம்பா / தாளடி)",
            "sowing_date": date.today().isoformat(),
            "expected_harvest": (date.today() + timedelta(days=105)).isoformat(),
            "area_cultivated_acres": 1.5
        }
        resp = self.client.post("/api/crops", json=crop_data)
        self.assertEqual(resp.status_code, 201)
        created = json.loads(resp.data)
        self.assertEqual(created["status"], "active")
        self.assertIn("Sowing", created["stage"])

    def test_kuchchi_kilangu_crop_sale_trade_record(self):
        """Verifies structured crop trade entry for Kuchchi Kilangu (Tapioca) with tons, rate, and multiline description."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)
        trade_data = {
            "type": "income",
            "category": "Tapioca / Kuchchi Kilangu (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)",
            "commodity": "Kuchchi Kilangu / Tapioca (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)",
            "quantity": 14.5,
            "unit": "Tons",
            "rate_per_unit": 9200.0,
            "amount": 133400.0,
            "buyer": "Salem Sago Factory / Trader Murugan",
            "slip_no": "Weighbridge Slip #4892 • TN-28-AB-1234",
            "date": date.today().isoformat(),
            "desc": "First harvest from Plot #2.\nStarch point 28 - no deductions.\nPayment settled via NEFT."
        }
        resp = self.client.post("/api/financials", json=trade_data)
        self.assertEqual(resp.status_code, 201)
        created = json.loads(resp.data)
        self.assertEqual(created["commodity"], "Kuchchi Kilangu / Tapioca (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)")
        self.assertEqual(created["quantity"], 14.5)
        self.assertEqual(created["unit"], "Tons")
        self.assertEqual(created["rate_per_unit"], 9200.0)
        self.assertEqual(created["amount"], 133400.0)
        self.assertEqual(created["buyer"], "Salem Sago Factory / Trader Murugan")
        self.assertIn("\n", created["desc"])

        # Verify record is retrieved via GET /api/financials
        get_resp = self.client.get("/api/financials")
        self.assertEqual(get_resp.status_code, 200)
        records = json.loads(get_resp.data)
        target = next((r for r in records if r["id"] == created["id"]), None)
        self.assertIsNotNone(target)
        self.assertEqual(target["slip_no"], "Weighbridge Slip #4892 • TN-28-AB-1234")

        # Verify stats reflect new income
        stats_resp = self.client.get("/api/financials/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats = json.loads(stats_resp.data)
        self.assertTrue(stats["total_income"] >= 133400.0)

    def test_crop_expense_and_profit_tracking(self):
        """Verifies storing expenses and profits against specific active crops, grouping them, and separate overhead additions."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)

        # 1. Create a plot and active crop: Kuchchi Kilangu
        plot_resp = self.client.post("/api/plots", json={
            "name": "New Coconut Plot",
            "area_acres": 1.0,
            "soil_type": "Red Loam",
            "water_source": "Drip Borewell"
        })
        self.assertEqual(plot_resp.status_code, 201)
        plot_id = json.loads(plot_resp.data)["id"]

        crop_resp = self.client.post("/api/crops", json={
            "plot_id": plot_id,
            "crop_name": "Kuchchi",
            "variety": "4",
            "season": "Kuruvai (குறுவை)",
            "sowing_date": "2026-10-25",
            "area_cultivated_acres": 1.0,
            "stage": "Tillering & Vegetative (தூர்கட்டும் பருவம்)",
            "status": "active"
        })
        self.assertEqual(crop_resp.status_code, 201)
        crop_id = json.loads(crop_resp.data)["id"]

        # 2. Record an expense directly against this crop (Fertilizer: 3200)
        exp_resp = self.client.post("/api/financials", json={
            "type": "expense",
            "crop_id": crop_id,
            "category": "Fertilizer & Manure (உரம் & எரு)",
            "amount": 3200.0,
            "date": "2026-10-25",
            "desc": "Basal DAP & Organic compost for Kuchchi"
        })
        self.assertEqual(exp_resp.status_code, 201)
        exp_item = json.loads(exp_resp.data)
        self.assertEqual(exp_item["crop_id"], crop_id)
        self.assertEqual(exp_item["crop_name"], "Kuchchi")

        # 3. Record a separate general overhead expense (Machinery repair: 1500) with NO crop_id
        gen_resp = self.client.post("/api/financials", json={
            "type": "expense",
            "crop_id": "",
            "category": "Equipment Maintenance (கருவிகள் பழுதுபார்ப்பு)",
            "amount": 1500.0,
            "date": "2026-10-25",
            "desc": "Borewell starter panel replacement"
        })
        self.assertEqual(gen_resp.status_code, 201)

        # 4. Record a harvest sales return directly against this crop (Yield return: 18500)
        inc_resp = self.client.post("/api/financials", json={
            "type": "income",
            "crop_id": crop_id,
            "category": "Tapioca / Kuchchi Kilangu (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)",
            "commodity": "Kuchchi",
            "amount": 18500.0,
            "date": "2026-10-26",
            "quantity": 2.0,
            "unit": "Tons",
            "rate_per_unit": 9250.0,
            "desc": "Harvest batch 1 dispatch"
        })
        self.assertEqual(inc_resp.status_code, 201)

        # 5. Verify /api/crops returns enriched crop metrics: total_expense, total_income, net_profit
        crops_resp = self.client.get("/api/crops")
        self.assertEqual(crops_resp.status_code, 200)
        crops_list = json.loads(crops_resp.data)
        kuchchi_crop = next((c for c in crops_list if c["id"] == crop_id), None)
        self.assertIsNotNone(kuchchi_crop)
        self.assertEqual(kuchchi_crop["total_expense"], 3200.0)
        self.assertEqual(kuchchi_crop["total_income"], 18500.0)
        self.assertEqual(kuchchi_crop["net_profit"], 15300.0)
        self.assertEqual(kuchchi_crop["expense_count"], 1)
        self.assertEqual(kuchchi_crop["income_count"], 1)

        # 6. Verify dedicated /api/crops/<crop_id>/financials endpoint returns itemized ledger
        ledger_resp = self.client.get(f"/api/crops/{crop_id}/financials")
        self.assertEqual(ledger_resp.status_code, 200)
        ledger_data = json.loads(ledger_resp.data)
        self.assertEqual(ledger_data["total_expense"], 3200.0)
        self.assertEqual(ledger_data["total_income"], 18500.0)
        self.assertEqual(ledger_data["net_profit"], 15300.0)
        self.assertEqual(len(ledger_data["transactions"]), 2)

        # 7. Verify /api/financials/stats includes crop_summary and general_summary
        stats_resp = self.client.get("/api/financials/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats_data = json.loads(stats_resp.data)
        self.assertIn("crop_summary", stats_data)
        self.assertIn("general_summary", stats_data)
        summary_crop = next((cs for cs in stats_data["crop_summary"] if cs["id"] == crop_id), None)
        self.assertIsNotNone(summary_crop)
        self.assertEqual(summary_crop["net_profit"], 15300.0)
        self.assertTrue(stats_data["general_summary"]["total_expense"] >= 1500.0)

        # 8. Clean up created items
        self.client.delete(f"/api/crops/{crop_id}")
        self.client.delete(f"/api/plots/{plot_id}")
        self.client.delete(f"/api/financials/{exp_item['id']}")
        self.client.delete(f"/api/financials/{json.loads(gen_resp.data)['id']}")
        self.client.delete(f"/api/financials/{json.loads(inc_resp.data)['id']}")

    def test_edit_endpoints_everywhere(self):
        """Verifies edit (PUT) functionality for plots, crops, livestock, breeding, milk, and financial transactions."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)

        # 1. Plot Edit
        plot_post = self.client.post("/api/plots", json={
            "name": "Kallikudi North",
            "area_acres": 2.5,
            "survey_number": "142/3B",
            "soil_type": "Clay Loam",
            "water_source": "Borewell"
        })
        self.assertEqual(plot_post.status_code, 201)
        plot_id = json.loads(plot_post.data)["id"]

        plot_put = self.client.put(f"/api/plots/{plot_id}", json={
            "name": "Kallikudi North - Renovated",
            "area_acres": 3.0,
            "survey_number": "142/3B",
            "soil_type": "Clay Loam",
            "water_source": "Canal + Borewell"
        })
        self.assertEqual(plot_put.status_code, 200)
        updated_plot = json.loads(plot_put.data)
        self.assertEqual(updated_plot["name"], "Kallikudi North - Renovated")
        self.assertEqual(updated_plot["area_acres"], 3.0)
        self.assertEqual(updated_plot["water_source"], "Canal + Borewell")

        # 2. Crop Edit
        crop_post = self.client.post("/api/crops", json={
            "plot_id": plot_id,
            "crop_name": "Tapioca (மரவள்ளிக் கிழங்கு)",
            "variety": "Kunguma Roja",
            "season": "Navarai",
            "sowing_date": date.today().isoformat(),
            "expected_harvest": (date.today() + timedelta(days=280)).isoformat(),
            "area_cultivated_acres": 2.0
        })
        self.assertEqual(crop_post.status_code, 201)
        crop_id = json.loads(crop_post.data)["id"]

        crop_put = self.client.put(f"/api/crops/{crop_id}", json={
            "plot_id": plot_id,
            "crop_name": "Tapioca (மரவள்ளிக் கிழங்கு)",
            "variety": "Kunguma Roja Superior",
            "stage": "Tuber Bulking (கிழங்கு பெருக்கும் பருவம்)",
            "status": "active",
            "area_cultivated_acres": 2.2,
            "notes": "Excellent root development after potassium application"
        })
        self.assertEqual(crop_put.status_code, 200)
        updated_crop = json.loads(crop_put.data)
        self.assertEqual(updated_crop["variety"], "Kunguma Roja Superior")
        self.assertEqual(updated_crop["stage"], "Tuber Bulking (கிழங்கு பெருக்கும் பருவம்)")
        self.assertEqual(updated_crop["area_cultivated_acres"], 2.2)

        # 3. Livestock Edit
        animal_post = self.client.post("/api/livestock", json={
            "species": "cow",
            "gender": "female",
            "tag_id": "TN-99-TEST",
            "breed": "Kangayam",
            "age_years": 4,
            "lactation_number": 2,
            "status": "healthy"
        })
        self.assertEqual(animal_post.status_code, 201)
        animal_id = json.loads(animal_post.data)["id"]

        animal_put = self.client.put(f"/api/livestock/{animal_id}", json={
            "species": "cow",
            "gender": "female",
            "tag_id": "TN-99-TEST",
            "breed": "Pure Kangayam Champion",
            "age_years": 5,
            "lactation_number": 3,
            "status": "healthy",
            "notes": "Winner of district native breed expo"
        })
        self.assertEqual(animal_put.status_code, 200)
        updated_animal = json.loads(animal_put.data)
        self.assertEqual(updated_animal["breed"], "Pure Kangayam Champion")
        self.assertEqual(updated_animal["age_years"], 5)
        self.assertEqual(updated_animal["notes"], "Winner of district native breed expo")

        # 4. Breeding Record Edit
        breed_post = self.client.post("/api/breeding", json={
            "animal_id": animal_id,
            "event_type": "insemination",
            "date": date.today().isoformat(),
            "semen_bull_info": "Bull #101",
            "technician": "VAS Senthil"
        })
        self.assertEqual(breed_post.status_code, 201)
        breed_id = json.loads(breed_post.data)["id"]

        breed_put = self.client.put(f"/api/breeding/{breed_id}", json={
            "animal_id": animal_id,
            "event_type": "insemination",
            "date": date.today().isoformat(),
            "semen_bull_info": "Kangayam Elite Bull #101-A",
            "technician": "Chief VAS Senthil",
            "status": "active",
            "notes": "Verified pregnancy at 60 days via ultrasound"
        })
        self.assertEqual(breed_put.status_code, 200)
        updated_breed = json.loads(breed_put.data)
        self.assertEqual(updated_breed["semen_bull_info"], "Kangayam Elite Bull #101-A")
        self.assertEqual(updated_breed["technician"], "Chief VAS Senthil")
        self.assertEqual(updated_breed["notes"], "Verified pregnancy at 60 days via ultrasound")

        # 5. Milk Log Edit
        milk_post = self.client.post("/api/milk", json={
            "animal_id": animal_id,
            "date": date.today().isoformat(),
            "morning_liters": 6.0,
            "evening_liters": 4.0,
            "rate_per_liter": 42.0,
            "fat_pct": 4.2,
            "snf_pct": 8.6,
            "buyer": "Local Dairy Co-op"
        })
        self.assertEqual(milk_post.status_code, 201)
        milk_id = json.loads(milk_post.data)["id"]

        milk_put = self.client.put(f"/api/milk/{milk_id}", json={
            "animal_id": animal_id,
            "date": date.today().isoformat(),
            "morning_liters": 7.0,
            "evening_liters": 5.0,
            "rate_per_liter": 44.0,
            "fat_pct": 4.5,
            "snf_pct": 8.9,
            "buyer": "Aavin Premium"
        })
        self.assertEqual(milk_put.status_code, 200)
        updated_milk = json.loads(milk_put.data)
        self.assertEqual(updated_milk["morning_liters"], 7.0)
        self.assertEqual(updated_milk["evening_liters"], 5.0)
        self.assertEqual(updated_milk["total_liters"], 12.0)
        self.assertEqual(updated_milk["rate_per_liter"], 44.0)
        self.assertEqual(updated_milk["total_amount"], 528.0)
        self.assertEqual(updated_milk["buyer"], "Aavin Premium")

        # 6. Financial Transaction Edit
        fin_post = self.client.post("/api/financials", json={
            "type": "income",
            "category": "Crop Sale (பயிர் விற்பனை)",
            "amount": 50000.0,
            "date": date.today().isoformat(),
            "notes": "Advance for Paddy"
        })
        self.assertEqual(fin_post.status_code, 201)
        fin_id = json.loads(fin_post.data)["id"]

        fin_put = self.client.put(f"/api/financials/{fin_id}", json={
            "type": "income",
            "category": "Tapioca / Kuchchi Kilangu (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)",
            "commodity": "Kuchchi Kilangu / Tapioca (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)",
            "quantity": 10.0,
            "unit": "Tons",
            "rate_per_unit": 9500.0,
            "amount": 95000.0,
            "buyer": "Salem Modern Sago Mill",
            "slip_no": "WB-9988",
            "date": date.today().isoformat(),
            "desc": "Full settlement after weighment"
        })
        self.assertEqual(fin_put.status_code, 200)
        updated_fin = json.loads(fin_put.data)
        self.assertEqual(updated_fin["quantity"], 10.0)
        self.assertEqual(updated_fin["rate_per_unit"], 9500.0)
        self.assertEqual(updated_fin["amount"], 95000.0)
        self.assertEqual(updated_fin["buyer"], "Salem Modern Sago Mill")
        self.assertEqual(updated_fin["slip_no"], "WB-9988")

    def test_kuchchi_kilangu_sand_deduction_and_charges(self):
        """Verifies recording 15.37 tons with 50kg/ton sand deduction, freight & harvest charges."""
        self.client.post("/login", data={"action": "demo"}, follow_redirects=True)

        gross_qty = 15.370
        rate = 11600.0
        ded_per_ton = 50.0  # kg/ton
        ded_tons = (gross_qty * ded_per_ton) / 1000.0  # 0.7685 Tons
        net_qty = round(gross_qty - ded_tons, 3)  # 14.6015 -> 14.602 Tons
        gross_produce_val = round(net_qty * rate, 2)  # 169383.20

        harvest_charges = 8000.0
        transport_charges = 5000.0
        other_charges = 500.0
        total_charges = harvest_charges + transport_charges + other_charges  # 13500.0
        net_amount = round(gross_produce_val - total_charges, 2)  # 155883.20

        trade_payload = {
            "type": "income",
            "category": "Tapioca / Kuchchi Kilangu (மரவள்ளிக் கிழங்கு / குச்சிக் கிழங்கு)",
            "commodity": "Tapioca / Kuchchi Kilangu (மரவள்ளி)",
            "quantity": gross_qty,
            "unit": "Tons",
            "rate_per_unit": rate,
            "deduction_per_ton_kg": ded_per_ton,
            "deduction_flat_kg": 0.0,
            "net_quantity": net_qty,
            "harvest_charges": harvest_charges,
            "transport_charges": transport_charges,
            "other_charges": other_charges,
            "total_expenses": total_charges,
            "amount": net_amount,
            "buyer": "Salem Sago Factory / Trader Murugan",
            "slip_no": "Weighbridge Slip #4892",
            "date": date.today().isoformat(),
            "desc": "Sand deduction 50kg/T applied at weighbridge. Labour and lorry transport paid directly."
        }

        # Create
        res = self.client.post("/api/financials", json=trade_payload)
        self.assertEqual(res.status_code, 201)
        created = json.loads(res.data)
        self.assertEqual(created["quantity"], 15.370)
        self.assertEqual(created["deduction_per_ton_kg"], 50.0)
        self.assertEqual(created["net_quantity"], net_qty)
        self.assertEqual(created["amount"], net_amount)
        self.assertEqual(created["harvest_charges"], 8000.0)
        self.assertEqual(created["transport_charges"], 5000.0)

        # Update via PUT
        trade_payload["harvest_charges"] = 7500.0
        trade_payload["total_expenses"] = 13000.0
        trade_payload["amount"] = round(gross_produce_val - 13000.0, 2)

        put_res = self.client.put(f"/api/financials/{created['id']}", json=trade_payload)
        self.assertEqual(put_res.status_code, 200)
        updated = json.loads(put_res.data)
        self.assertEqual(updated["harvest_charges"], 7500.0)
        self.assertEqual(updated["total_expenses"], 13000.0)
        self.assertEqual(updated["amount"], round(gross_produce_val - 13000.0, 2))

    def test_multi_user_data_isolation(self):
        """Verifies data isolation across different logged-in users (plots, crops, transactions)."""
        import uuid
        user_a = f"farmer_a_{uuid.uuid4().hex[:4]}"
        user_b = f"farmer_b_{uuid.uuid4().hex[:4]}"

        # 1. Sign up User A
        self.client.post("/signup", data={
            "username": user_a,
            "password": "password123",
            "farmer_name": "Farmer A",
            "farm_name": "Farm A",
            "district": "Salem"
        }, follow_redirects=True)

        # User A adds a plot and transaction
        plot_a_res = self.client.post("/api/plots", json={"name": "Alpha Field", "area_acres": 5.0})
        self.assertEqual(plot_a_res.status_code, 201)

        txn_a_res = self.client.post("/api/financials", json={
            "type": "income",
            "category": "Crop Sale",
            "amount": 25000.0,
            "date": date.today().isoformat()
        })
        self.assertEqual(txn_a_res.status_code, 201)

        # Logout User A
        self.client.get("/logout")

        # 2. Sign up User B
        self.client.post("/signup", data={
            "username": user_b,
            "password": "password123",
            "farmer_name": "Farmer B",
            "farm_name": "Farm B",
            "district": "Erode"
        }, follow_redirects=True)

        # User B adds their own plot and transaction
        plot_b_res = self.client.post("/api/plots", json={"name": "Beta Plantation", "area_acres": 12.0})
        self.assertEqual(plot_b_res.status_code, 201)

        txn_b_res = self.client.post("/api/financials", json={
            "type": "expense",
            "category": "Fertilizer",
            "amount": 6000.0,
            "date": date.today().isoformat()
        })
        self.assertEqual(txn_b_res.status_code, 201)

        # Verify User B sees ONLY User B's plot and transaction
        plots_b = json.loads(self.client.get("/api/plots").data)
        plot_names_b = [p["name"] for p in plots_b]
        self.assertIn("Beta Plantation", plot_names_b)
        self.assertNotIn("Alpha Field", plot_names_b)

        txns_b = json.loads(self.client.get("/api/financials").data)
        self.assertEqual(len(txns_b), 1)
        self.assertEqual(txns_b[0]["amount"], 6000.0)

        # Logout User B, Login as User A
        self.client.get("/logout")
        self.client.post("/login", data={"username": user_a, "password": "password123"}, follow_redirects=True)

        # Verify User A sees ONLY User A's plot and transaction
        plots_a = json.loads(self.client.get("/api/plots").data)
        plot_names_a = [p["name"] for p in plots_a]
        self.assertIn("Alpha Field", plot_names_a)
        self.assertNotIn("Beta Plantation", plot_names_a)

        txns_a = json.loads(self.client.get("/api/financials").data)
        self.assertEqual(len(txns_a), 1)
        self.assertEqual(txns_a[0]["amount"], 25000.0)

if __name__ == "__main__":
    unittest.main()

