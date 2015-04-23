import unittest
from minim import tokens


class TestContent(unittest.TestCase):

    def test_literal_is_same_as_input(self):
        literal = 'hello'
        c = tokens.Content(literal)
        self.assertEqual(c.literal, literal)

    def test_content_is_same_as_input(self):
        literal = 'hello'
        c = tokens.Content(literal)
        self.assertEqual(c.content, literal)
