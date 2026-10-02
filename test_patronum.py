"""Tests for patronum — run with: python3 -m pytest test_patronum.py (or python3 test_patronum.py)"""
import unittest
from unittest import mock
import patronum


class TestColour(unittest.TestCase):
    def test_colour_disabled_when_not_tty(self):
        patronum.USE_COLOR = False
        self.assertEqual(patronum.green("x"), "x")
        self.assertEqual(patronum.red("x"), "x")

    def test_colour_enabled(self):
        patronum.USE_COLOR = True
        self.assertIn("38;5;40", patronum.green("x"))
        patronum.USE_COLOR = False


class TestDns(unittest.TestCase):
    def test_valid_domain(self):
        result = patronum.spell_dns("github.com")
        self.assertTrue(result["ok"])
        self.assertGreater(len(result["ipv4"]) + len(result["ipv6"]), 0)

    def test_invalid_domain(self):
        result = patronum.spell_dns("this-domain-should-not-exist-xyz123.invalid")
        self.assertFalse(result["ok"])


class TestPort(unittest.TestCase):
    def test_open_port(self):
        result = patronum.spell_port("github.com", 443)
        self.assertTrue(result["open"])

    def test_closed_port(self):
        result = patronum.spell_port("github.com", 1)  # port 1 unlikely open
        self.assertFalse(result["open"])


class TestPing(unittest.TestCase):
    def test_ping_localhost(self):
        result = patronum.spell_ping("127.0.0.1", count=1)
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
