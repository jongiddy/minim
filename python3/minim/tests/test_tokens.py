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

    def test_literal_is_decoded_input(self):
        literal = 'hello'
        c = tokens.Content(literal.encode('utf-8'), encoding='utf-8')
        self.assertEqual(c.literal, literal)

    def test_content_is_unicode(self):
        literal = 'hello'
        c = tokens.Content(literal.encode('utf-8'), 'utf-8')
        self.assertEqual(c.content, literal)
