import unittest
import asyncio
import os
import base64
import html
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Mock environment variables BEFORE importing main.py
os.environ['SUPABASE_URL'] = 'postgresql://user:pass@localhost:5432/db'
os.environ['DISCORD_TOKEN'] = 'fake_token'
os.environ['STATS_USER'] = 'admin'
os.environ['STATS_PASS'] = 'secret'

import main

class TestSecurityFixes(unittest.TestCase):
    def setUp(self):
        # Reset stats for testing
        main.stats['bot_start_time'] = datetime.now(timezone.utc)
        main.stats['total_rolls'] = 0
        main.stats['active_users'] = 0
        main.stats['guilds_count'] = 0

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_xss_mitigation_in_handle_stats(self):
        malicious_username = "<script>alert('XSS_USER')</script>"
        malicious_fruit = "<img src=x onerror=alert('XSS_FRUIT')>"

        mock_user = {
            'user_id': 123,
            'username': malicious_username,
            'total_rolls': 5,
            'last_roll_time': datetime.now(timezone.utc),
            'next_roll_time': datetime.now(timezone.utc),
            'notifications_enabled': True
        }

        mock_roll = {'fruit': malicious_fruit}

        with patch('main.get_all_users', return_value=[mock_user]), \
             patch('main.get_user_rolls', return_value=[mock_roll]), \
             patch('main.get_rarity_distribution', return_value={}), \
             patch('main.check_auth', return_value=True):

            request = MagicMock()
            response = self.loop.run_until_complete(main.handle_stats(request))

            self.assertNotIn(malicious_username, response.text, "XSS Vulnerability still exists: Malicious username rendered unescaped")
            self.assertIn(html.escape(malicious_username), response.text, "Mitigation failed: Malicious username not properly escaped")

            self.assertNotIn(malicious_fruit, response.text, "XSS Vulnerability still exists: Malicious fruit name rendered unescaped")
            self.assertIn(html.escape(malicious_fruit), response.text, "Mitigation failed: Malicious fruit name not properly escaped")

    def test_xss_mitigation_in_handle_suspended(self):
        malicious_username = "<script>alert('XSS_SUSPENDED_USER')</script>"
        malicious_reason = "<svg onload=alert('XSS_REASON')>"

        mock_suspended_user = {
            'user_id': 123,
            'username': malicious_username,
            'total_rolls': 0,
            'last_roll_time': None,
            'created_at': None,
            'suspension_reason': malicious_reason
        }

        with patch('main.get_suspended_users', return_value=[mock_suspended_user]), \
             patch('main.check_auth', return_value=True):

            request = MagicMock()
            response = self.loop.run_until_complete(main.handle_suspended(request))

            self.assertNotIn(malicious_username, response.text, "XSS Vulnerability still exists: Malicious username rendered unescaped in suspended")
            self.assertIn(html.escape(malicious_username), response.text, "Mitigation failed: Malicious username not properly escaped in suspended")

            self.assertNotIn(malicious_reason, response.text, "XSS Vulnerability still exists: Malicious reason rendered unescaped in suspended")
            self.assertIn(html.escape(malicious_reason), response.text, "Mitigation failed: Malicious reason not properly escaped in suspended")

    def test_info_leakage_mitigation_in_handle_suspended(self):
        with patch('main.get_suspended_users', side_effect=Exception("Sensitive DB Error")):
            with patch('main.check_auth', return_value=True):
                request = MagicMock()
                response = self.loop.run_until_complete(main.handle_suspended(request))

                self.assertEqual(response.status, 500)
                self.assertEqual(response.text, "Internal Server Error")
                self.assertNotIn("Sensitive DB Error", response.text, "Information leakage still exists")

    def test_auth_still_works(self):
        request = MagicMock()
        auth_str = base64.b64encode(b"admin:secret").decode('utf-8')
        request.headers = {'Authorization': f'Basic {auth_str}'}
        self.assertTrue(main.check_auth(request), "Authentication failed after update")

        request.headers = {'Authorization': f'Basic {base64.b64encode(b"admin:wrong").decode("utf-8")}'}
        self.assertFalse(main.check_auth(request), "Authentication should have failed with wrong password")

if __name__ == '__main__':
    unittest.main()
