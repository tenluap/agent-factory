import unittest

from src.greet import greet


class GreetTests(unittest.TestCase):
    def test_greets_by_name(self):
        self.assertEqual(greet("world"), "Hello, world!")

    def test_blank_names(self):
        for name in ("", "  ", "\t\n"):
            with self.subTest(name=name):
                self.assertEqual(greet(name), "Hello, stranger!")
        self.assertEqual(greet(" world "), "Hello,  world !")


if __name__ == "__main__":
    unittest.main()
