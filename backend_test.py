#!/usr/bin/env python3
import requests
import unittest
import time
import json
from urllib.parse import urlparse

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://8f2f7923-a357-4b44-8d8a-478e20f6baf4.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class URLShortenerTests(unittest.TestCase):
    """Test cases for URL Shortener API"""

    def setUp(self):
        """Setup for each test"""
        self.valid_url = "example.com"
        self.valid_url_with_protocol = "https://example.com"
        self.invalid_url = "not_a_valid_url"
        self.non_existent_short_code = "nonexistent123"
        self.created_short_codes = []  # Track created short codes for cleanup

    def test_01_shorten_valid_url_without_protocol(self):
        """Test shortening a valid URL without protocol"""
        print("\n=== Testing URL shortening with valid URL (no protocol) ===")
        response = requests.post(
            f"{API_URL}/shorten", 
            json={"original_url": self.valid_url}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("id", data)
        self.assertIn("original_url", data)
        self.assertIn("short_code", data)
        self.assertIn("short_url", data)
        self.assertIn("created_at", data)
        self.assertIn("click_count", data)
        
        # Verify URL was normalized with https://
        self.assertEqual(data["original_url"], f"https://{self.valid_url}")
        
        # Verify short_code length
        self.assertEqual(len(data["short_code"]), 6)
        
        # Save short code for later tests
        self.created_short_codes.append(data["short_code"])
        
        print(f"Successfully created short URL with code: {data['short_code']}")
        return data["short_code"]

    def test_02_shorten_valid_url_with_protocol(self):
        """Test shortening a valid URL with protocol"""
        print("\n=== Testing URL shortening with valid URL (with protocol) ===")
        response = requests.post(
            f"{API_URL}/shorten", 
            json={"original_url": self.valid_url_with_protocol}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify URL was not modified
        self.assertEqual(data["original_url"], self.valid_url_with_protocol)
        
        # Save short code for later tests
        self.created_short_codes.append(data["short_code"])
        
        print(f"Successfully created short URL with code: {data['short_code']}")
        return data["short_code"]

    def test_03_shorten_invalid_url(self):
        """Test shortening an invalid URL"""
        print("\n=== Testing URL shortening with invalid URL ===")
        response = requests.post(
            f"{API_URL}/shorten", 
            json={"original_url": self.invalid_url}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        # Should return 400 Bad Request
        self.assertEqual(response.status_code, 400)
        
        # Verify error message
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "Invalid URL format")
        
        print("Successfully rejected invalid URL")

    def test_04_verify_unique_short_codes(self):
        """Test that multiple shortening requests generate unique codes"""
        print("\n=== Testing unique short code generation ===")
        
        # Create multiple short URLs
        codes = set()
        for i in range(3):
            response = requests.post(
                f"{API_URL}/shorten", 
                json={"original_url": f"test{i}.example.com"}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            codes.add(data["short_code"])
            self.created_short_codes.append(data["short_code"])
        
        # Verify all codes are unique
        self.assertEqual(len(codes), 3)
        print(f"Successfully verified unique short codes: {codes}")

    def test_05_redirect_valid_short_code(self):
        """Test redirection with a valid short code"""
        print("\n=== Testing URL redirection with valid short code ===")
        
        # First create a short URL
        short_code = self.test_01_shorten_valid_url_without_protocol()
        
        # Test redirection (don't follow redirects)
        response = requests.get(
            f"{BACKEND_URL}/{short_code}",
            allow_redirects=False
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        # Should return 302 Found (redirect)
        self.assertEqual(response.status_code, 302)
        
        # Verify redirect location
        self.assertIn("location", response.headers)
        self.assertEqual(response.headers["location"], f"https://{self.valid_url}")
        
        print(f"Successfully verified redirection for short code: {short_code}")

    def test_06_redirect_invalid_short_code(self):
        """Test redirection with an invalid short code"""
        print("\n=== Testing URL redirection with invalid short code ===")
        
        response = requests.get(
            f"{BACKEND_URL}/{self.non_existent_short_code}",
            allow_redirects=False
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        # Should return 404 Not Found
        self.assertEqual(response.status_code, 404)
        
        # Verify error message
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "Short URL not found")
        
        print("Successfully rejected invalid short code")

    def test_07_verify_click_counting(self):
        """Test that clicks are counted correctly"""
        print("\n=== Testing click counting ===")
        
        # First create a short URL
        short_code = self.test_02_shorten_valid_url_with_protocol()
        
        # Get initial stats
        response = requests.get(f"{API_URL}/stats/{short_code}")
        self.assertEqual(response.status_code, 200)
        initial_stats = response.json()
        initial_clicks = initial_stats["total_clicks"]
        
        print(f"Initial click count: {initial_clicks}")
        
        # Simulate multiple clicks
        num_clicks = 3
        for i in range(num_clicks):
            click_response = requests.get(
                f"{BACKEND_URL}/{short_code}",
                allow_redirects=False
            )
            self.assertEqual(click_response.status_code, 302)
            # Small delay to ensure clicks are registered
            time.sleep(0.1)
        
        # Get updated stats
        response = requests.get(f"{API_URL}/stats/{short_code}")
        self.assertEqual(response.status_code, 200)
        updated_stats = response.json()
        updated_clicks = updated_stats["total_clicks"]
        
        print(f"Updated click count: {updated_clicks}")
        
        # Verify click count increased by the expected amount
        self.assertEqual(updated_clicks, initial_clicks + num_clicks)
        
        print(f"Successfully verified click counting for short code: {short_code}")

    def test_08_stats_valid_short_code(self):
        """Test getting stats for a valid short code"""
        print("\n=== Testing stats with valid short code ===")
        
        # First create a short URL
        short_code = self.test_01_shorten_valid_url_without_protocol()
        
        # Simulate a click
        click_response = requests.get(
            f"{BACKEND_URL}/{short_code}",
            allow_redirects=False
        )
        self.assertEqual(click_response.status_code, 302)
        
        # Get stats
        response = requests.get(f"{API_URL}/stats/{short_code}")
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("short_code", data)
        self.assertIn("original_url", data)
        self.assertIn("total_clicks", data)
        self.assertIn("daily_clicks", data)
        self.assertIn("created_at", data)
        
        # Verify data
        self.assertEqual(data["short_code"], short_code)
        self.assertEqual(data["original_url"], f"https://{self.valid_url}")
        self.assertGreaterEqual(data["total_clicks"], 1)
        
        # Verify daily clicks
        self.assertIsInstance(data["daily_clicks"], dict)
        self.assertGreaterEqual(len(data["daily_clicks"]), 1)
        
        print(f"Successfully retrieved stats for short code: {short_code}")

    def test_09_stats_invalid_short_code(self):
        """Test getting stats for an invalid short code"""
        print("\n=== Testing stats with invalid short code ===")
        
        response = requests.get(f"{API_URL}/stats/{self.non_existent_short_code}")
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        # Should return 404 Not Found
        self.assertEqual(response.status_code, 404)
        
        # Verify error message
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "Short URL not found")
        
        print("Successfully rejected invalid short code for stats")

    def test_10_verify_daily_click_aggregation(self):
        """Test that clicks are aggregated by day correctly"""
        print("\n=== Testing daily click aggregation ===")
        
        # First create a short URL
        short_code = self.test_02_shorten_valid_url_with_protocol()
        
        # Simulate multiple clicks
        num_clicks = 5
        for i in range(num_clicks):
            click_response = requests.get(
                f"{BACKEND_URL}/{short_code}",
                allow_redirects=False
            )
            self.assertEqual(click_response.status_code, 302)
            # Small delay to ensure clicks are registered
            time.sleep(0.1)
        
        # Get stats
        response = requests.get(f"{API_URL}/stats/{short_code}")
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        
        # Verify daily clicks
        daily_clicks = stats["daily_clicks"]
        print(f"Daily clicks: {daily_clicks}")
        
        # Get today's date in YYYY-MM-DD format
        import datetime
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        
        # Verify today's clicks
        self.assertIn(today, daily_clicks)
        self.assertGreaterEqual(daily_clicks[today], num_clicks)
        
        # Verify total clicks matches sum of daily clicks
        total_from_daily = sum(daily_clicks.values())
        self.assertEqual(stats["total_clicks"], total_from_daily)
        
        print(f"Successfully verified daily click aggregation for short code: {short_code}")

if __name__ == "__main__":
    unittest.main(verbosity=2)