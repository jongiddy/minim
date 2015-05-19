import unittest

from minim import iterseq, lex, tokens


class NameParserTests(unittest.TestCase):

    def test_parser_matches_name(self):
        s = 'foo '
        buf = iterseq.IterableAsSequence([s])
        parse_name = lex.NameParser()
        parse_name(buf, tokens.TagName)
        parse_name = iter(parse_name)
        self.assertIs(next(parse_name), tokens.TagName)
        token = parse_name.send(tokens.TagName)
        self.assertEqual(token.literal, 'foo')
        with self.assertRaises(StopIteration) as stop:
            next(parse_name)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)

    def test_parser_matches_name_eof(self):
        s = 'foo'
        buf = iterseq.IterableAsSequence([s])
        parse_name = lex.NameParser()
        parse_name(buf, tokens.TagName)
        parse_name = iter(parse_name)
        self.assertIs(next(parse_name), tokens.TagName)
        token = parse_name.send(tokens.TagName)
        self.assertEqual(token.literal, 'foo')
        self.assertIs(token.is_initial, True)
        self.assertIs(token.is_final, False)
        self.assertIs(next(parse_name), tokens.TagName)
        token = parse_name.send(tokens.TagName)
        self.assertEqual(token.literal, '')
        self.assertIs(token.is_initial, False)
        self.assertIs(token.is_final, True)
        with self.assertRaises(StopIteration) as stop:
            next(parse_name)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)

    def test_parser_fails_with_dot(self):
        s = '.foo'
        buf = iterseq.IterableAsSequence([s])
        parse_name = lex.NameParser()
        parse_name(buf, tokens.TagName)
        parse_name = iter(parse_name)
        with self.assertRaises(StopIteration) as stop:
            next(parse_name)
        # Test that StopIteration indicates found is False
        self.assertIs(stop.exception.value, False)

    def test_parser_ok_with_nonfirst_on_next_start(self):
        # valid name, but invalid first char on buffer boundary
        s = ['foo', '-bar>']
        buf = iterseq.IterableAsSequence(s)
        parse_name = lex.NameParser()
        parse_name(buf, tokens.TagName)
        parse_name = iter(parse_name)
        self.assertIs(next(parse_name), tokens.TagName)
        token = parse_name.send(tokens.TagName)
        self.assertEqual(token.literal, 'foo')
        self.assertIs(token.is_initial, True)
        self.assertIs(token.is_final, False)
        self.assertIs(next(parse_name), tokens.TagName)
        token = parse_name.send(tokens.TagName)
        self.assertEqual(token.literal, '-bar')
        self.assertIs(token.is_initial, False)
        self.assertIs(token.is_final, True)
        self.assertEqual(buf.get(), '>')


class WhitespaceParserTests(unittest.TestCase):

    def test_parser_matches_space(self):
        s = ' ' * 3 + 'foo'
        buf = iterseq.IterableAsSequence([s])
        parse_whitespace = lex.WhitespaceParserXML10()
        parse_whitespace(buf, tokens.MarkupWhitespace)
        parse_whitespace = iter(parse_whitespace)
        self.assertIs(next(parse_whitespace), tokens.MarkupWhitespace)
        token = parse_whitespace.send(tokens.MarkupWhitespace)
        self.assertEqual(token.literal, ' ' * 3)
        with self.assertRaises(StopIteration) as stop:
            next(parse_whitespace)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)

    def test_parser_matches_space_eof(self):
        s = ' ' * 3
        buf = iterseq.IterableAsSequence([s])
        parse_whitespace = lex.WhitespaceParserXML10()
        parse_whitespace(buf, tokens.MarkupWhitespace)
        parse_whitespace = iter(parse_whitespace)
        self.assertIs(next(parse_whitespace), tokens.MarkupWhitespace)
        token = parse_whitespace.send(tokens.MarkupWhitespace)
        self.assertEqual(token.literal, ' ' * 3)
        self.assertIs(token.is_initial, True)
        self.assertIs(token.is_final, False)
        self.assertIs(next(parse_whitespace), tokens.MarkupWhitespace)
        token = parse_whitespace.send(tokens.MarkupWhitespace)
        self.assertEqual(token.literal, '')
        self.assertIs(token.is_initial, False)
        self.assertIs(token.is_final, True)
        with self.assertRaises(StopIteration) as stop:
            next(parse_whitespace)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)

    def test_parser_empty_on_no_space(self):
        s = 'foo'
        buf = iterseq.IterableAsSequence([s])
        parse_whitespace = lex.WhitespaceParserXML10()
        parse_whitespace(buf, tokens.MarkupWhitespace)
        parse_whitespace = iter(parse_whitespace)
        with self.assertRaises(StopIteration) as stop:
            next(parse_whitespace)
        # Test that StopIteration indicates found is False
        self.assertIs(stop.exception.value, False)
        self.assertEqual(buf.get(), 'f')


class SentinelParserTests(unittest.TestCase):

    def test_parser_matches_sentinel_at_start(self):
        s = '?>fix'
        buf = iterseq.IterableAsSequence([s])
        parse_sentinel = lex.SentinelParser()
        parse_sentinel(buf, tokens.Content, '?>')
        parse_sentinel = iter(parse_sentinel)
        with self.assertRaises(StopIteration):
            next(parse_sentinel)
        self.assertEqual(buf.extract(), '')
        self.assertEqual(buf.get(), '?')

    def test_parser_matches_sentinel_after_start(self):
        s = 'more?>fix'
        buf = iterseq.IterableAsSequence([s])
        parse_sentinel = lex.SentinelParser()
        parse_sentinel(buf, tokens.Content, '?>')
        parse_sentinel = iter(parse_sentinel)
        self.assertIs(next(parse_sentinel), tokens.Content)
        token = parse_sentinel.send(tokens.Content)
        self.assertEqual(token.literal, 'more')
        with self.assertRaises(StopIteration):
            next(parse_sentinel)
        self.assertEqual(buf.extract(), '')
        self.assertEqual(buf.get(), '?')

    def test_parser_fails_on_empty_string(self):
        s = ''
        buf = iterseq.IterableAsSequence([s])
        parse_sentinel = lex.SentinelParser()
        parse_sentinel(buf, tokens.Content, '?>')
        parse_sentinel = iter(parse_sentinel)
        with self.assertRaises(StopIteration):
            x = next(parse_sentinel)
            print(x)
            if not x.is_token:
                x = parse_sentinel.send(x)
            print(x.literal)
        self.assertEqual(buf.extract(), '')
        self.assertEqual(buf.get(), '')

    def test_parser_fails_on_no_sentinel(self):
        s = 'morefix'
        buf = iterseq.IterableAsSequence([s])
        parse_sentinel = lex.SentinelParser()
        parse_sentinel(buf, tokens.Content, '?>')
        parse_sentinel = iter(parse_sentinel)
        self.assertIs(next(parse_sentinel), tokens.Content)
        token = parse_sentinel.send(tokens.Content)
        self.assertEqual(token.literal, 'morefix')
        self.assertIs(next(parse_sentinel), tokens.Content)
        token = parse_sentinel.send(tokens.Content)
        self.assertEqual(token.literal, '')
        self.assertIs(token.is_final, True)
        with self.assertRaises(StopIteration):
            next(parse_sentinel)
        self.assertEqual(buf.extract(), '')
        self.assertEqual(buf.get(), '')


class TokenGeneratorMarkupTests(unittest.TestCase):

    def test_parse_open_tag(self):
        xml = '<tag foo="bar">'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenSingleton, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
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

    def test_parse_end_tag(self):
        xml = '</ns:tag>'
        expected_tokens = [
            (tokens.EndTagOpenSingleton, '</'),
            (tokens.TagName, 'ns:tag'),
            (tokens.EndTagCloseSingleton, '>')
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
            (tokens.MarkupWhitespace, '\t'),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsSingleton, '='),
            (tokens.AttributeValueDoubleOpenSingleton, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleCloseSingleton, '"'),
            (tokens.MarkupWhitespace, '\n\t'),
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

    def test_parse_comment(self):
        xml = "<!-- Lot's of text, including technically invalid -- -->"
        expected_tokens = [
            (tokens.CommentOpenSingleton, '<!--'),
            (tokens.CommentData,
                " Lot's of text, including technically invalid -- "),
            (tokens.CommentCloseSingleton, '-->')
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])

    def test_parse_empty_comment(self):
        xml = "<!---->"
        expected_tokens = [
            (tokens.CommentOpenSingleton, '<!--'),
            (tokens.CommentCloseSingleton, '-->')
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])

    def test_parse_invalid_comment(self):
        # As non-well-formed markup, this is interpreted as content, but
        # has attribute ``is_well_formed`` set to False for the < character
        xml = '<-- hello -->'
        expected_tokens = [
            (tokens.BadlyFormedLessThanSingleton, '<', False),
            (tokens.PCData, '-- hello -->', True)
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])
            self.assertIs(token_type.is_well_formed, expected[2])

    def test_parse_processing_instruction(self):
        xml = "<?xml foo bar?>"
        expected_tokens = [
            (tokens.ProcessingInstructionOpenSingleton, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.ProcessingInstructionData, 'foo bar'),
            (tokens.ProcessingInstructionCloseSingleton, '?>')
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])

    def test_parse_empty_processing_instruction(self):
        xml = "<?xml?>"
        expected_tokens = [
            (tokens.ProcessingInstructionOpenSingleton, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.ProcessingInstructionCloseSingleton, '?>')
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])

    @unittest.skip('should pass when content is handled')
    def test_parse_invalid_processing_instruction(self):
        xml = '<??>'
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        not_well_formed = False
        s = ''
        for token_type in token_types:
            if not token_type.is_well_formed:
                not_well_formed = True
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            if token_type.is_content:
                s += token.content
            self.assertIs(not_well_formed, True)
            self.assertEqual(s, xml)

    def test_parse_content_only(self):
        xml = "no markup"
        expected_tokens = [
            (tokens.PCData, 'no markup'),
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])

    def test_parse_content_markup(self):
        xml = "some content<tag>"
        expected_tokens = [
            (tokens.PCData, 'some content'),
            (tokens.StartOrEmptyTagOpenSingleton, '<'),
            (tokens.TagName, 'tag'),
            (tokens.StartTagCloseSingleton, '>')
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])

    def test_parse_markup_content(self):
        xml = "<tag>some content"
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenSingleton, '<'),
            (tokens.TagName, 'tag'),
            (tokens.StartTagCloseSingleton, '>'),
            (tokens.PCData, 'some content'),
            ]
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
            else:
                token = token_types.send(token_type)
            self.assertEqual(token_type, expected[0])
            self.assertEqual(token.literal, expected[1])
