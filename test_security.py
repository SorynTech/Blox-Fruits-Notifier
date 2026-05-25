import html
import secrets
import unittest
from unittest.mock import MagicMock

class TestSecurity(unittest.TestCase):
    def test_xss_escaping(self):
        unsafe = "<script>alert('xss')</script>"
        escaped = html.escape(unsafe)
        self.assertIn("&lt;script&gt;", escaped)
        self.assertNotIn("<script>", escaped)

    def test_compare_digest(self):
        self.assertTrue(secrets.compare_digest("admin", "admin"))
        self.assertFalse(secrets.compare_digest("admin", "wrong"))

if __name__ == "__main__":
    unittest.main()
