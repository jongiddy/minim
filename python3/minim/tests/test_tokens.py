import unittest
from minim import tokens


class TestContent(unittest.TestCase):

    def test_literal_is_same_as_input(self):
        literal = 'hello'
        c = tokens.TextHolder(literal)
        self.assertEqual(c.literal(), literal)

    def test_content_is_same_as_input(self):
        literal = 'hello'
        c = tokens.TextHolder(literal)
        self.assertEqual(c.content(), literal)

    def test_literal_is_decoded_input(self):
        literal = 'hello'
        c = tokens.TextHolder(literal.encode('utf-8'), encoding='utf-8')
        self.assertEqual(c.literal(), literal)

    def test_content_is_unicode(self):
        literal = 'hel€o'
        c = tokens.TextHolder(literal.encode('utf-8'), 'utf-8')
        self.assertEqual(c.content(), literal)

    def test_pcdata_token_is_a_content(self):
        token = tokens.PCData(tokens.TextHolder(encoded='foo'))
        self.assertTrue(token.is_a(tokens.Content))

    def test_token_is_not_a_content(self):
        token = tokens.Token
        self.assertFalse(token.is_a(tokens.Content))

    def test_markup_token_is_not_a_content(self):
        token = tokens.StartTagClose()
        self.assertFalse(token.is_a(tokens.Content))

    def test_clone_token(self):
        th = tokens.TextHolder('foo')
        t = tokens.Content()
        c = t.clone(th)
        self.assertIsInstance(c, tokens.Content)
        self.assertIs(t.text, None)
        self.assertIs(c.text, th)
