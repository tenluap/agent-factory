import unittest

from src.greet import greet


class GreetTests(unittest.TestCase):
    def test_blank_names(self):
        self.assertEqual(greet(""), "Hello, stranger!")
        self.assertEqual(greet("  "), "Hello, stranger!")

    def test_greets_by_name(self):
        self.assertEqual(greet("world"), "Hello, world!")


if __name__ == "__main__":
    unittest.main()
