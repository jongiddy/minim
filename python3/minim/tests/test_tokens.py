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

    def test_pcdata_class_is_a_content(self):
        token_type = tokens.PCData
        self.assertTrue(token_type.is_a(tokens.Content))

    def test_pcdata_token_is_a_content(self):
        token_type = tokens.PCData(literal='foo')
        self.assertTrue(token_type.is_a(tokens.Content))

    def test_token_is_not_a_content(self):
        token_type = tokens.Token
        self.assertFalse(token_type.is_a(tokens.Content))

    def test_markup_class_is_not_a_content(self):
        token_type = tokens.StartTagClose
        self.assertFalse(token_type.is_a(tokens.Content))

    def test_markup_token_is_not_a_content(self):
        token_type = tokens.StartTagCloseToken
        self.assertFalse(token_type.is_a(tokens.Content))
