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

if __name__ == "__main__":
    unittest.main()

