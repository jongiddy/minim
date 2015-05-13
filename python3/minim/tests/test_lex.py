import unittest

from minim import iterseq, lex, tokens


class WhitespaceParserTests(unittest.TestCase):

    def test_parser_matches_space(self):
        s = ' ' * 3 + 'foo'
        buf = iterseq.IterableAsSequence([s])
        parse_whitespace = lex.WhitespaceParserXML10()
        parse_whitespace(buf, tokens.Whitespace)
        parse_whitespace = iter(parse_whitespace)
        self.assertIs(next(parse_whitespace), tokens.Whitespace)
        token = parse_whitespace.send(tokens.Whitespace)
        self.assertEqual(token.literal, ' ' * 3)
        with self.assertRaises(StopIteration) as stop:
            next(parse_whitespace)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)

    def test_parser_empty_on_no_space(self):
        s = 'foo'
        buf = iterseq.IterableAsSequence([s])
        parse_whitespace = lex.WhitespaceParserXML10()
        parse_whitespace(buf, tokens.Whitespace)
        parse_whitespace = iter(parse_whitespace)
        with self.assertRaises(StopIteration) as stop:
            next(parse_whitespace)
        # Test that StopIteration indicates found is False
        self.assertIs(stop.exception.value, False)


class TokenGeneratorMarkupTests(unittest.TestCase):

    def test_parse_open_tag(self):
        xml = '<tag foo="bar">'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenSingleton, '<'),
            (tokens.TagName, 'tag'),
            (tokens.Whitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsSingleton, '='),
            (tokens.AttributeValueDoubleOpenSingleton, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleCloseSingleton, '"'),
            (tokens.StartTagCloseSingleton, '>')
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse_markup(buf)
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])

    def test_parse_empty_tag(self):
        xml = '<tag\tfoo="bar"\n\t/>'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenSingleton, '<'),
            (tokens.TagName, 'tag'),
            (tokens.Whitespace, '\t'),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsSingleton, '='),
            (tokens.AttributeValueDoubleOpenSingleton, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleCloseSingleton, '"'),
            (tokens.Whitespace, '\n\t'),
            (tokens.EmptyTagCloseSingleton, '/>')
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse_markup(buf)
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])
