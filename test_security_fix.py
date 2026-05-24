import unittest
from unittest.mock import MagicMock, patch
import html
import secrets
import base64
import os
import sys
from datetime import datetime, timezone

# Set up environment variables before importing main
os.environ['SUPABASE_URL'] = 'postgres://test'
os.environ['DISCORD_TOKEN'] = 'test'
os.environ['STATS_USER'] = 'admin'
os.environ['STATS_PASS'] = 'password'

# Mock modules before importing main
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['psycopg2.pool'] = MagicMock()
sys.modules['discord'] = MagicMock()
sys.modules['discord.ext'] = MagicMock()
sys.modules['discord.app_commands'] = MagicMock()

import main

class TestSecurityFixes(unittest.IsolatedAsyncioTestCase):
    def test_check_auth_success(self):
        request = MagicMock()
        auth_str = "admin:password"
        encoded = base64.b64encode(auth_str.encode()).decode()
        request.headers = {'Authorization': f'Basic {encoded}'}

        with patch('secrets.compare_digest', side_effect=secrets.compare_digest) as mock_compare:
            # We need to make sure STATS_USER and STATS_PASS in main match our expectation
            main.STATS_USER = 'admin'
            main.STATS_PASS = 'password'
            self.assertTrue(main.check_auth(request))
            # Verify compare_digest was called (at least twice, once for user, once for pass)
            self.assertTrue(mock_compare.called)

    def test_check_auth_failure(self):
        request = MagicMock()
        auth_str = "admin:wrong"
        encoded = base64.b64encode(auth_str.encode()).decode()
        request.headers = {'Authorization': f'Basic {encoded}'}

        main.STATS_USER = 'admin'
        main.STATS_PASS = 'password'
        self.assertFalse(main.check_auth(request))

    @patch('main.get_all_users')
    @patch('main.get_user_rolls')
    @patch('main.check_auth')
    async def test_handle_stats_escaping(self, mock_auth, mock_rolls, mock_users):
        mock_auth.return_value = True
        mock_users.return_value = [{
            'user_id': 123,
            'username': '<script>alert("xss")</script>',
            'total_rolls': 5,
            'last_roll_time': None,
            'next_roll_time': datetime.now(timezone.utc),
            'notifications_enabled': True
        }]
        mock_rolls.return_value = [{'fruit': '<b>Malicious Fruit</b>'}]

        request = MagicMock()
        response = await main.handle_stats(request)

        self.assertIn('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;', response.text)
        self.assertIn('&lt;b&gt;Malicious Fruit&lt;/b&gt;', response.text)

    @patch('main.get_suspended_users')
    @patch('main.check_auth')
    async def test_handle_suspended_escaping(self, mock_auth, mock_suspended):
        mock_auth.return_value = True
        mock_suspended.return_value = [{
            'user_id': 123,
            'username': '<img src=x onerror=alert(1)>',
            'total_rolls': 5,
            'last_roll_time': None,
            'created_at': None,
            'suspension_reason': '<svg onload=alert(1)>'
        }]

        request = MagicMock()
        response = await main.handle_suspended(request)

        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', response.text)
        self.assertIn('&lt;svg onload=alert(1)&gt;', response.text)

    @patch('main.get_suspended_users')
    @patch('main.check_auth')
    async def test_handle_suspended_error_leakage(self, mock_auth, mock_suspended):
        mock_auth.return_value = True
        mock_suspended.side_effect = Exception("SECRET DATABASE DETAILS EXPOSED")

        request = MagicMock()
        response = await main.handle_suspended(request)

        self.assertEqual(response.status, 500)
        self.assertEqual(response.text, "Internal Server Error")
        self.assertNotIn("SECRET DATABASE DETAILS", response.text)

if __name__ == '__main__':
    unittest.main()
