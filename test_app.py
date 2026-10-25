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

    def test_pages_load_successfully(self):
        """Verifies all user-facing web pages return HTTP 200."""
        routes = ["/", "/mandi", "/crops", "/livestock", "/financials", "/advisories", "/settings"]
        for r in routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f"Route {r} failed with status {resp.status_code}")

    def test_overview_api(self):
        """Verifies /api/overview returns complete KPIs and alert summaries."""
        resp = self.client.get("/api/overview")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("total_plots", data)
        self.assertIn("total_acres", data)
        self.assertIn("active_crops_count", data)
        self.assertIn("total_animals", data)
        self.assertIn("total_income", data)
        self.assertIn("total_expense", data)
        self.assertIn("net_profit", data)
        self.assertIn("alerts", data)

    def test_mandi_api(self):
        """Verifies Mandi pricing and trend endpoints."""
        # Prices list
        resp = self.client.get("/api/mandi/prices?district=Thanjavur")
        self.assertEqual(resp.status_code, 200)
        prices = json.loads(resp.data)
        self.assertIsInstance(prices, list)
        self.assertTrue(len(prices) > 0)
        first = prices[0]
        self.assertIn("commodity", first)
        self.assertIn("modal_price", first)

        # Trend history
        trend_resp = self.client.get("/api/mandi/trend?commodity=Paddy (Ponni)")
        self.assertEqual(trend_resp.status_code, 200)
        history = json.loads(trend_resp.data)
        self.assertTrue(len(history) >= 15)

    def test_cattle_reproduction_engine(self):
        """Verifies biological calculation milestones for cows."""
        today = date.today()
        insemination_dt = today - timedelta(days=100)
        result = breeding_engine.calculate_cattle_reproduction(insemination_dt, is_buffalo=False)
        
        self.assertEqual(result["gestation_days_total"], 283)
        self.assertEqual(result["days_pregnant"], 100)
        self.assertEqual(result["days_remaining"], 183)
        
        expected_calving = insemination_dt + timedelta(days=283)
        self.assertEqual(result["expected_calving_date"], expected_calving.isoformat())
        
        expected_dry = expected_calving - timedelta(days=60)
        self.assertEqual(result["dry_off_date"], expected_dry.isoformat())

    def test_goat_reproduction_engine(self):
        """Verifies biological calculation milestones for goats."""
        today = date.today()
        mating_dt = today - timedelta(days=50)
        result = breeding_engine.calculate_goat_reproduction(mating_dt)
        
        self.assertEqual(result["gestation_days_total"], 150)
        self.assertEqual(result["days_pregnant"], 50)
        self.assertEqual(result["days_remaining"], 100)
        
        expected_kidding = mating_dt + timedelta(days=150)
        self.assertEqual(result["expected_kidding_date"], expected_kidding.isoformat())

    def test_financial_stats_api(self):
        """Verifies financials stats calculation endpoint."""
        resp = self.client.get("/api/financials/stats")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("total_income", data)
        self.assertIn("total_expense", data)
        self.assertIn("net_profit", data)
        self.assertIn("roi_percentage", data)
        self.assertIn("expenses_by_category", data)

    def test_db_store_crud(self):
        """Verifies CRUD operations on data store."""
        test_item = {
            "id": "test_plot_unit_1",
            "name": "Unit Test Field",
            "area_acres": 1.5,
            "soil_type": "Red Loam",
            "water_source": "Well"
        }
        # Save
        saved = db_store.save_item("plots", test_item)
        self.assertEqual(saved["id"], "test_plot_unit_1")

        # Read
        fetched = db_store.get_by_id("plots", "test_plot_unit_1")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["name"], "Unit Test Field")

        # Delete
        db_store.delete_item("plots", "test_plot_unit_1")
        deleted = db_store.get_by_id("plots", "test_plot_unit_1")
        self.assertIsNone(deleted)

    def test_weather_service(self):
        """Verifies weather service returns structured forecasts."""
        data = weather_service.get_weather_forecast("Coimbatore")
        self.assertIn("district", data)
        self.assertIn("current", data)
        self.assertIn("forecast", data)
        self.assertIn("advisories", data)
        self.assertTrue(len(data["forecast"]) > 0)

if __name__ == "__main__":
    unittest.main()
