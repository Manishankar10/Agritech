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
        signup_data = {
            "username": "new_signup_farmer",
            "password": "pass1234",
            "farmer_name": "Rangarajan S (ரங்கராஜன்)",
            "farm_name": "Kongu Naturals",
            "district": "Coimbatore",
            "taluk": "Pollachi",
            "village": "Anamalai",
            "language": "ta"
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

if __name__ == "__main__":
    unittest.main()
