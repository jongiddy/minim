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
        scanner = nslex.TokenGenerator(lex.TokenGenerator(buf))
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
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ttns:tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleClose, '"'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'xmlns:ttns'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'http://url.example.com/'),
            (tokens.AttributeValueDoubleClose, '"'),
            (tokens.StartTagClose, '>')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag(self):
        xml = '<ns:tag'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ns:tag'),
            (tokens.TagName, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space(self):
        xml = '<ns:tag '
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ns:tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.MarkupWhitespace, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr(self):
        xml = '<ns:tag xmlns:ns'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ns:tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'xmlns:ns'),
            (tokens.AttributeName, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr_equals(self):
        xml = '<ns:tag xmlns:ns='
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ns:tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'xmlns:ns'),
            (tokens.AttributeEquals, '='),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr_equals_quote(self):
        xml = '<ns:tag xmlns:ns="'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ns:tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'xmlns:ns'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr_equals_quote_value(self):
        xml = '<ns:tag xmlns:ns="http://url.example.com/'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ns:tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'xmlns:ns'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'http://url.example.com/'),
            (tokens.AttributeValue, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attribute(self):
        xml = '<ns:tag xmlns:ns="http://url.example.com/"'
        expected_tokens = [
            (nslex.NamespaceOpen, ''),
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ns:tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'xmlns:ns'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'http://url.example.com/'),
            (tokens.AttributeValueDoubleClose, '"'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_empty_tag_space_attribute_slash(self):
        xml = '<ns:tag xmlns:ns="http://url.example.com/" /'
        expected_tokens = [
            (nslex.NamespaceOpen, ''),
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ns:tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'xmlns:ns'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'http://url.example.com/'),
            (tokens.AttributeValueDoubleClose, '"'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.BadlyFormedEndOfStream, '/')
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
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.StartTagClose, '>')
            ]
        self.scan([xml], expected_tokens)

    def test_markup_content(self):
        xml = "<tag>some content"
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.StartTagClose, '>'),
            (tokens.PCData, 'some content'),
            (tokens.PCData, ''),
            ]
        self.scan([xml], expected_tokens)

    def test_literal_ok(self):
        xml = [
            '<?xml version="1.0"?><tns:some tags="',
            'foo" xmlns:tns="http://url.exam',
            'ple.com/">This <!-- a comment -->is',
            'some </s',
            'ome>text'
            ]
        scanner = nslex.TokenGenerator.from_strings(xml)
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

    def test_namespace_values(self):
        xml = ['<tag xmlns:foo="bar">']
        scanner = nslex.TokenGenerator.from_strings(xml)
        token_types = iter(scanner)
        token_type = next(token_types)
        self.assertTrue(token_type.is_a(nslex.NamespaceOpen))
        token = scanner.get_token(token_type)
        self.assertEqual(token.prefix, 'foo')
        self.assertEqual(token.namespace, 'bar')

    def test_namespace_values_split_name(self):
        xml = ['<tag xmlns:fo', 'o="bar">']
        scanner = nslex.TokenGenerator.from_strings(xml)
        token_types = iter(scanner)
        token_type = next(token_types)
        self.assertTrue(token_type.is_a(nslex.NamespaceOpen))
        token = scanner.get_token(token_type)
        self.assertEqual(token.prefix, 'foo')
        self.assertEqual(token.namespace, 'bar')

    def test_namespace_values_split_url(self):
        xml = ['<tag xmlns:foo="b', 'ar">']
        scanner = nslex.TokenGenerator.from_strings(xml)
        token_types = iter(scanner)
        token_type = next(token_types)
        self.assertTrue(token_type.is_a(nslex.NamespaceOpen))
        token = scanner.get_token(token_type)
        self.assertEqual(token.prefix, 'foo')
        self.assertEqual(token.namespace, 'bar')
