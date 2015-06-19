import unittest

from minim import iterseq, lex, nslex, tokens


class TokenGeneratorMarkupTests(unittest.TestCase):

    def scan(self, stream, expected_tokens):
        # Add fake sequence to end, to catch additional tokens being
        # emitted after expected. expected[0] is valid to make first
        # test work and output comparison, and expected[1] is error as
        # fallback to ensure final test fails
        expected_tokens.append((tokens.Token(),))
        buf = iterseq.IterableAsSequence(stream)
        scanner = nslex.TokenGenerator.from_token_generator(
            lex.TokenGenerator(buf))
        token_types = iter(scanner)
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
                if expected[0].is_token:
                    self.assertIs(token, expected[0], repr(token.literal))
                else:
                    self.assertIsInstance(
                        token, expected[0], repr(token.literal))
            else:
                token = token_types.send(token_type)
                self.assertIs(token_type, expected[0], repr(token.literal))
            self.assertEqual(token.literal, expected[1])
        self.assertEqual(buf.get(), '')

    def test_start_tag(self):
        xml = '<ttns:tag foo="bar" xmlns:ttns="http://url.example.com/">'
        expected_tokens = [
            (nslex.NamespaceOpen, ''),
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'ttns:tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsToken, '='),
            (tokens.AttributeValueDoubleOpenToken, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleCloseToken, '"'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'xmlns:ttns'),
            (tokens.AttributeEqualsToken, '='),
            (tokens.AttributeValueDoubleOpenToken, '"'),
            (tokens.AttributeValue, 'http://url.example.com/'),
            (tokens.AttributeValueDoubleCloseToken, '"'),
            (tokens.StartTagCloseToken, '>')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag(self):
        xml = '<ns:tag'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.TagName, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_content_only(self):
        xml = "no markup"
        expected_tokens = [
            (tokens.PCData, 'no markup'),
            (tokens.PCData, ''),
            ]
        self.scan([xml], expected_tokens)

    def test_content_markup(self):
        xml = "some content<tag>"
        expected_tokens = [
            (tokens.PCData, 'some content'),
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.StartTagCloseToken, '>')
            ]
        self.scan([xml], expected_tokens)

    def test_markup_content(self):
        xml = "<tag>some content"
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.StartTagCloseToken, '>'),
            (tokens.PCData, 'some content'),
            (tokens.PCData, ''),
            ]
        self.scan([xml], expected_tokens)

    def test_literal_ok(self):
        xml = [
            '<?xml version="1.0"?><some tags="',
            'foo">This <!-- a comment -->is',
            'some </s',
            'ome>text'
            ]
        scanner = nslex.TokenGenerator.from_token_generator(
            lex.TokenGenerator.from_strings(xml))
        token_types = iter(scanner)
        literal = ''
        content = ''
        for token_type in token_types:
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            literal += token.literal
            if token_type.is_content:
                content += token.content
        self.assertEqual(literal, ''.join(xml))
        self.assertEqual(content, 'This issome text')
