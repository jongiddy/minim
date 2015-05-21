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

    def test_letters_are_names(self):
        parse_name = lex.NameParser()
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        self.assertIs(parse_name.matches_name(chars), True)
        for char in chars:
            self.assertIs(parse_name.matches_name(char), True, repr(char))

    def test_spaces_are_not_names(self):
        parse_name = lex.NameParser()
        chars = ' \t\n\f\v'
        self.assertIs(parse_name.matches_name(chars), False)
        for char in chars:
            self.assertIs(parse_name.matches_name(char), False, repr(char))

    def test_symbols_are_not_names(self):
        parse_name = lex.NameParser()
        chars = ' !"£$%^&*()-+=~#@<>&?,.'
        self.assertIs(parse_name.matches_name(chars), False)
        for char in chars:
            self.assertIs(parse_name.matches_name(char), False, repr(char))

    def test_numbers_are_not_names(self):
        parse_name = lex.NameParser()
        chars = '0123456789'
        self.assertIs(parse_name.matches_name(chars), False)
        for char in chars:
            self.assertIs(parse_name.matches_name(char), False, repr(char))


class WhitespaceParserTests(unittest.TestCase):

    def test_parser_matches_space(self):
        s = ' ' * 3 + 'foo'
        buf = iterseq.IterableAsSequence([s])
        parse_whitespace = lex.WhitespaceParser()
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
        parse_whitespace = lex.WhitespaceParser()
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
        parse_whitespace = lex.WhitespaceParser()
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
        with self.assertRaises(StopIteration) as stop:
            next(parse_sentinel)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)
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
        with self.assertRaises(StopIteration) as stop:
            next(parse_sentinel)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)
        self.assertEqual(buf.extract(), '')
        self.assertEqual(buf.get(), '?')

    def test_parser_fails_on_empty_string(self):
        s = ''
        buf = iterseq.IterableAsSequence([s])
        parse_sentinel = lex.SentinelParser()
        parse_sentinel(buf, tokens.Content, '?>')
        parse_sentinel = iter(parse_sentinel)
        with self.assertRaises(StopIteration) as stop:
            next(parse_sentinel)
        # Test that StopIteration indicates found is False
        self.assertIs(stop.exception.value, False)
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
        with self.assertRaises(StopIteration) as stop:
            next(parse_sentinel)
        # Test that StopIteration indicates found is False
        self.assertIs(stop.exception.value, False)
        self.assertEqual(buf.extract(), '')
        self.assertEqual(buf.get(), '')

    def test_parser_fails_on_partial_sentinel(self):
        s = 'morefix?'
        buf = iterseq.IterableAsSequence([s])
        parse_sentinel = lex.SentinelParser()
        parse_sentinel(buf, tokens.Content, '?>')
        parse_sentinel = iter(parse_sentinel)
        self.assertIs(next(parse_sentinel), tokens.Content)
        token = parse_sentinel.send(tokens.Content)
        self.assertEqual(token.literal, 'morefix')
        self.assertIs(next(parse_sentinel), tokens.Content)
        token = parse_sentinel.send(tokens.Content)
        self.assertEqual(token.literal, '?')
        self.assertIs(token.is_final, True)
        with self.assertRaises(StopIteration) as stop:
            next(parse_sentinel)
        # Test that StopIteration indicates found is False
        self.assertIs(stop.exception.value, False)
        self.assertEqual(buf.extract(), '')
        self.assertEqual(buf.get(), '')


class TokenGeneratorMarkupTests(unittest.TestCase):

    def scan(self, stream, expected_tokens):
        # Add fake sequence to end, to catch additional tokens being
        # emitted after expected. expected[0] is valid to make first
        # test work and output comparison, and expected[1] is error as
        # fallback to ensure final test fails
        expected_tokens.append((tokens.Token(),))
        buf = iterseq.IterableAsSequence(stream)
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
        for token_type, expected in zip(token_types, expected_tokens):
            if token_type.is_token:
                token = token_type
                if expected[0].is_token:
                    self.assertIs(token, expected[0])
                else:
                    self.assertIsInstance(token, expected[0])
            else:
                self.assertIs(token_type, expected[0])
                token = token_types.send(token_type)
            self.assertEqual(token.literal, expected[1])
        self.assertEqual(buf.get(), '')

    def test_start_tag(self):
        xml = '<tag foo="bar">'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsToken, '='),
            (tokens.AttributeValueDoubleOpenToken, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleCloseToken, '"'),
            (tokens.StartTagCloseToken, '>')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag(self):
        xml = '<tag'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.TagName, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space(self):
        xml = '<tag '
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.MarkupWhitespace, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr(self):
        xml = '<tag foo'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeName, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr_equals(self):
        xml = '<tag foo='
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsToken, '='),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr_equals_quote(self):
        xml = '<tag foo="'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsToken, '='),
            (tokens.AttributeValueDoubleOpenToken, '"'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr_equals_quote_value(self):
        xml = '<tag foo="bar'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsToken, '='),
            (tokens.AttributeValueDoubleOpenToken, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValue, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attribute(self):
        xml = '<tag foo="bar"'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsToken, '='),
            (tokens.AttributeValueDoubleOpenToken, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleCloseToken, '"'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_empty_tag_space_attribute_slash(self):
        xml = '<tag foo="bar" /'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsToken, '='),
            (tokens.AttributeValueDoubleOpenToken, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleCloseToken, '"'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.BadlyFormedEndOfStream, '/')
            ]
        self.scan([xml], expected_tokens)

    def test_end_tag(self):
        xml = '</ns:tag>'
        expected_tokens = [
            (tokens.EndTagOpenToken, '</'),
            (tokens.TagName, 'ns:tag'),
            (tokens.EndTagCloseToken, '>')
            ]
        self.scan([xml], expected_tokens)

    def test_short_end_tag(self):
        xml = '</'
        expected_tokens = [
            (tokens.BadlyFormedLessThanToken, '<'),
            (tokens.PCData, '/')
            ]
        self.scan([xml], expected_tokens)

    def test_short_end_tag_name(self):
        xml = '</foo'
        expected_tokens = [
            (tokens.EndTagOpenToken, '</'),
            (tokens.TagName, 'foo'),
            (tokens.TagName, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_empty_tag(self):
        xml = '<tag\tfoo="bar"\n\t/>'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpenToken, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, '\t'),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEqualsToken, '='),
            (tokens.AttributeValueDoubleOpenToken, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleCloseToken, '"'),
            (tokens.MarkupWhitespace, '\n\t'),
            (tokens.EmptyTagCloseToken, '/>')
            ]
        self.scan([xml], expected_tokens)

    def test_comment(self):
        xml = "<!-- Lot's of text, including technically invalid -- -->"
        expected_tokens = [
            (tokens.CommentOpenToken, '<!--'),
            (tokens.CommentData,
                " Lot's of text, including technically invalid -- "),
            (tokens.CommentCloseToken, '-->')
            ]
        self.scan([xml], expected_tokens)

    def test_empty_comment(self):
        xml = "<!---->"
        expected_tokens = [
            (tokens.CommentOpenToken, '<!--'),
            (tokens.CommentCloseToken, '-->')
            ]
        self.scan([xml], expected_tokens)

    def test_short_comment(self):
        xml = "<!--"
        expected_tokens = [
            (tokens.CommentOpenToken, '<!--'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_comment_data(self):
        xml = "<!-- comment "
        expected_tokens = [
            (tokens.CommentOpenToken, '<!--'),
            (tokens.CommentData, ' comment '),
            (tokens.CommentData, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_invalid_comment(self):
        # As non-well-formed markup, this is interpreted as content, but
        # has attribute ``is_well_formed`` set to False for the < character
        xml = '<-- hello -->'
        expected_tokens = [
            (tokens.BadlyFormedLessThanToken, '<', False),
            (tokens.PCData, '-- hello -->', True),
            (tokens.PCData, '', True),
            (tokens.Token(),)
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

    def test_processing_instruction(self):
        xml = "<?xml foo bar?>"
        expected_tokens = [
            (tokens.ProcessingInstructionOpenToken, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.ProcessingInstructionData, 'foo bar'),
            (tokens.ProcessingInstructionCloseToken, '?>')
            ]
        self.scan([xml], expected_tokens)

    def test_empty_processing_instruction(self):
        xml = "<?xml?>"
        expected_tokens = [
            (tokens.ProcessingInstructionOpenToken, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.ProcessingInstructionCloseToken, '?>')
            ]
        self.scan([xml], expected_tokens)

    def test_short_processing_instruction(self):
        xml = "<?"
        expected_tokens = [
            (tokens.BadlyFormedLessThanToken, '<'),
            (tokens.PCData, '?'),
            ]
        self.scan([xml], expected_tokens)

    def test_short_processing_instruction_name(self):
        xml = "<?xml"
        expected_tokens = [
            (tokens.ProcessingInstructionOpenToken, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.ProcessingInstructionTarget, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_processing_instruction_name_quest(self):
        xml = "<?xml?"
        expected_tokens = [
            (tokens.ProcessingInstructionOpenToken, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.BadlyFormedEndOfStream, '?')
            ]
        self.scan([xml], expected_tokens)

    def test_short_processing_instruction_name_data(self):
        xml = "<?xml vers"
        expected_tokens = [
            (tokens.ProcessingInstructionOpenToken, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.ProcessingInstructionData, 'vers'),
            (tokens.ProcessingInstructionData, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    @unittest.skip('TODO - fix bad end of stream handling')
    def test_short_processing_instruction_name_data_quest(self):
        xml = "<?xml vers?"
        expected_tokens = [
            (tokens.ProcessingInstructionOpenToken, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.ProcessingInstructionData, 'vers'),
            (tokens.ProcessingInstructionData, ''),
            (tokens.BadlyFormedEndOfStream, '?')
            ]
        self.scan([xml], expected_tokens)

    @unittest.skip('TODO - emit error token, and return to content mode')
    def test_invalid_processing_instruction_name_symbol(self):
        xml = "<?xml!?>"
        expected_tokens = [
            (tokens.ProcessingInstructionOpenToken, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.ProcessingInstructionTarget, ''),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_invalid_processing_instruction(self):
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

    def test_markupish_content(self):
        xml = "?>"
        expected_tokens = [
            (tokens.PCData, '?>'),
            (tokens.PCData, '')
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
        buf = iterseq.IterableAsSequence(xml)
        scanner = lex.TokenGenerator(buf)
        token_types = scanner.parse()
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
