"""Fixed benchmark acceptance cases; implementation must preserve these."""

import unittest

from src.greet import greet


class AcceptanceTests(unittest.TestCase):
    def test_default_is_unchanged(self):
        self.assertEqual(greet("Ada"), "Hello, Ada!")

    def test_uppercase_greeting(self):
        self.assertEqual(greet("Ada", uppercase=True), "HELLO, ADA!")

    def test_empty_name(self):
        self.assertEqual(greet("", uppercase=True), "HELLO, !")
