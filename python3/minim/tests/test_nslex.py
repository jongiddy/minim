import unittest

from minim import iterseq, lex, nslex, tokens


class NamespaceTokenScannerMarkupTests(unittest.TestCase):

    def scan(self, stream, expected_tokens):
        # Add fake sequence to end, to catch additional tokens being
        # emitted after expected. expected[0] is valid to make first
        # test work and output comparison, and expected[1] is error as
        # fallback to ensure final test fails
        expected_tokens.append((tokens.Token(),))
        buf = iterseq.IterableAsSequence(stream)
        scanner = nslex.NamespaceTokenScanner(lex.TokenScanner(buf))
        for token, expected in zip(scanner, expected_tokens):
            text = scanner.get_text(token)
            # print(token, repr(text.content()), text.is_final)
            content = text.content()
            while not text.is_final:
                token = scanner.next()
                text = scanner.get_text(token)
                content += text.content()
                self.assertIsInstance(token, expected[0], repr(content))
            self.assertEqual(content, expected[1])
        self.assertEqual(buf.get(), '')

    def test_start_tag(self):
        xml = '<ttns:tag foo="bar" xmlns:ttns="http://url.example.com/">'
        expected_tokens = [
            (nslex.NamespacePrefix, 'ttns'),
            (nslex.NamespaceUri, 'http://url.example.com/'),
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
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space(self):
        xml = '<ns:tag '
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'ns:tag'),
            (tokens.MarkupWhitespace, ' '),
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
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attribute(self):
        xml = '<ns:tag xmlns:ns="http://url.example.com/"'
        expected_tokens = [
            (nslex.NamespacePrefix, 'ns'),
            (nslex.NamespaceUri, 'http://url.example.com/'),
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
            (nslex.NamespacePrefix, 'ns'),
            (nslex.NamespaceUri, 'http://url.example.com/'),
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
            ]
        self.scan([xml], expected_tokens)

    def test_open_tags_refined(self):
        """Test that scanner refines tag to specify open or empty.

        Since the NamespaceTokenScanner must parse the entire tag before
        emitting any tokens, it has the opportunity to convert an
        ambiguous StartOrEmptyTagOpen to a specific StartTagOpen or
        EmptyTagOpen token.
        """
        xml = "<tag>some content<another />"
        expected_tokens = [
            (tokens.StartTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.StartTagClose, '>'),
            (tokens.PCData, 'some content'),
            (tokens.EmptyTagOpen, '<'),
            (tokens.TagName, 'another'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.EmptyTagClose, '/>'),
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
        scanner = nslex.NamespaceTokenScanner.from_strings(xml)
        token_stream = iter(scanner)
        literal = ''
        content = ''
        for token in token_stream:
            text = scanner.get_text(token)
            literal += text.literal()
            if isinstance(token, tokens.Content):
                content += text.content()
        self.assertEqual(literal, ''.join(xml))
        self.assertEqual(content, 'This issome text')

    def test_default_namespace(self):
        xml = ['<tag xmlns="bar">']
        scanner = nslex.NamespaceTokenScanner.from_strings(xml)
        token_stream = iter(scanner)
        token = next(token_stream)
        self.assertIsInstance(token, nslex.NamespaceDefault, token)
        text = scanner.get_text(token)
        self.assertEqual(text.content(), '')
        token = next(token_stream)
        self.assertIsInstance(token, nslex.NamespaceUri, token)
        text = scanner.get_text(token)
        self.assertEqual(text.content(), 'bar')

    def test_namespace_values(self):
        xml = ['<tag xmlns:foo="bar">']
        scanner = nslex.NamespaceTokenScanner.from_strings(xml)
        token_stream = iter(scanner)
        token = next(token_stream)
        self.assertIsInstance(token, nslex.NamespacePrefix, token)
        text = scanner.get_text(token)
        self.assertEqual(text.content(), 'foo')
        token = next(token_stream)
        self.assertIsInstance(token, nslex.NamespaceUri, token)
        text = scanner.get_text(token)
        self.assertEqual(text.content(), 'bar')

    def test_namespace_values_split_name(self):
        xml = ['<tag xmlns:fo', 'o="bar">']
        scanner = nslex.NamespaceTokenScanner.from_strings(xml)
        token_stream = iter(scanner)
        token = next(token_stream)
        self.assertIsInstance(token, nslex.NamespacePrefix, token)
        text = scanner.get_text(token)
        self.assertEqual(text.content(), 'foo')
        token = next(token_stream)
        self.assertIsInstance(token, nslex.NamespaceUri, token)
        text = scanner.get_text(token)
        self.assertEqual(text.content(), 'bar')

    def test_namespace_values_split_url(self):
        xml = ['<tag xmlns:foo="b', 'ar">']
        scanner = nslex.NamespaceTokenScanner.from_strings(xml)
        token_stream = iter(scanner)
        token = next(token_stream)
        self.assertIsInstance(token, nslex.NamespacePrefix, token)
        text = scanner.get_text(token)
        self.assertEqual(text.content(), 'foo')
        token = next(token_stream)
        self.assertIsInstance(token, nslex.NamespaceUri, token)
        text = scanner.get_text(token)
        self.assertEqual(text.content(), 'bar')
