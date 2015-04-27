import unittest
import minim.lex


class TestLex(unittest.TestCase):

    def test_content_tokens_1(self):
        """README example 1"""
        string_iter = ['Hello, ', 'World!']
        result = []
        for token in minim.lex.tokens(string_iter):
            if token.is_content:
                result.append(token.content)
        self.assertEqual(''.join(string_iter), ''.join(result))

    def test_content_tokens_2(self):
        """README example 2"""
        string_iter = ['Hello, ', 'World!']
        result = []
        token_types = minim.lex.token_types(string_iter)
        for token_type in token_types:
            if token_type.is_content:
                token = token_types.get_token(token_type)
                result.append(token.content)

    def test_content_tokens_3(self):
        """README example 3"""
        string_iter = ['Hello, ', 'World!']
        result = []
        content_token = minim.tokens.Content()
        token_types = minim.lex.token_types(string_iter)
        for token_type in token_types:
            if token_type.is_content:
                token = token_types.set_token(content_token)
                result.append(token.content)

