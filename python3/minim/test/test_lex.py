import unittest

from minim import iterseq, lex, tokens


class NmTokenParserTests(unittest.TestCase):

    def test_parser_matches_initial(self):
        s = 'foo '
        buf = iterseq.IterableAsSequence([s])
        parse_name = lex.NmTokenParser()
        parse_name(buf, tokens.TagName())
        parse_name = iter(parse_name)
        self.assertIsInstance(next(parse_name), tokens.TagName)
        text = parse_name.send(tokens.TextHolder())
        self.assertEqual(text.literal(), 'foo')
        with self.assertRaises(StopIteration) as stop:
            next(parse_name)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)

    def test_parser_matches_initial_eof(self):
        s = 'foo'
        buf = iterseq.IterableAsSequence([s])
        parse_name = lex.NmTokenParser()
        parse_name(buf, tokens.TagName())
        parse_name = iter(parse_name)
        self.assertIsInstance(next(parse_name), tokens.TagName)
        text = parse_name.send(tokens.TextHolder())
        self.assertEqual(text.literal(), 'foo')
        self.assertIs(text.is_initial, True)
        self.assertIs(text.is_final, False)
        self.assertIsInstance(next(parse_name), tokens.TagName)
        text = parse_name.send(tokens.TextHolder())
        self.assertEqual(text.literal(), '')
        self.assertIs(text.is_initial, False)
        self.assertIs(text.is_final, True)
        with self.assertRaises(StopIteration) as stop:
            next(parse_name)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)

    def test_parser_ok_with_nonfirst_on_next_start(self):
        # valid name, but invalid first char on buffer boundary
        s = ['foo', '-bar>']
        buf = iterseq.IterableAsSequence(s)
        parse_name = lex.NmTokenParser()
        parse_name(buf, tokens.TagName())
        parse_name = iter(parse_name)
        self.assertIsInstance(next(parse_name), tokens.TagName)
        text = parse_name.send(tokens.TextHolder())
        self.assertEqual(text.literal(), 'foo')
        self.assertIs(text.is_initial, True)
        self.assertIs(text.is_final, False)
        self.assertIsInstance(next(parse_name), tokens.TagName)
        text = parse_name.send(tokens.TextHolder())
        self.assertEqual(text.literal(), '-bar')
        self.assertIs(text.is_initial, False)
        self.assertIs(text.is_final, True)
        self.assertEqual(buf.get(), '>')

    def test_letters_are_names(self):
        parse_name = lex.NmTokenParser()
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        self.assertIs(parse_name.matches_initial(chars), True)
        for char in chars:
            self.assertIs(parse_name.matches_initial(char), True, repr(char))

    def test_spaces_are_not_names(self):
        parse_name = lex.NmTokenParser()
        chars = ' \t\n\f\v'
        self.assertIs(parse_name.matches_initial(chars), False)
        for char in chars:
            self.assertIs(parse_name.matches_initial(char), False, repr(char))

    def test_symbols_are_not_names(self):
        parse_name = lex.NmTokenParser()
        chars = '!"£$%^&*()-+=~#@<>&?,.'
        self.assertIs(parse_name.matches_initial(chars), False)
        for char in chars:
            self.assertIs(parse_name.matches_initial(char), False, repr(char))

    def test_some_symbols_are_names(self):
        parse_name = lex.NmTokenParser()
        chars = '_:'
        self.assertIs(parse_name.matches_initial(chars), True)
        for char in chars:
            self.assertIs(parse_name.matches_initial(char), True, repr(char))

    def test_numbers_are_not_names(self):
        parse_name = lex.NmTokenParser()
        chars = '0123456789'
        self.assertIs(parse_name.matches_initial(chars), False)
        for char in chars:
            self.assertIs(parse_name.matches_initial(char), False, repr(char))


class WhitespaceParserTests(unittest.TestCase):

    def test_parser_matches_space(self):
        s = ' ' * 3 + 'foo'
        buf = iterseq.IterableAsSequence([s])
        parse_whitespace = lex.WhitespaceParser()
        parse_whitespace(buf, tokens.MarkupWhitespace())
        parse_whitespace = iter(parse_whitespace)
        self.assertIsInstance(next(parse_whitespace), tokens.MarkupWhitespace)
        text = parse_whitespace.send(tokens.TextHolder())
        self.assertEqual(text.literal(), ' ' * 3)
        with self.assertRaises(StopIteration) as stop:
            next(parse_whitespace)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)

    def test_parser_matches_space_eof(self):
        s = ' ' * 3
        buf = iterseq.IterableAsSequence([s])
        parse_whitespace = lex.WhitespaceParser()
        parse_whitespace(buf, tokens.MarkupWhitespace())
        parse_whitespace = iter(parse_whitespace)
        self.assertIsInstance(next(parse_whitespace), tokens.MarkupWhitespace)
        text = parse_whitespace.send(tokens.TextHolder())
        self.assertEqual(text.literal(), ' ' * 3)
        self.assertIs(text.is_initial, True)
        self.assertIs(text.is_final, False)
        self.assertIsInstance(next(parse_whitespace), tokens.MarkupWhitespace)
        text = parse_whitespace.send(tokens.TextHolder())
        self.assertEqual(text.literal(), '')
        self.assertIs(text.is_initial, False)
        self.assertIs(text.is_final, True)
        with self.assertRaises(StopIteration) as stop:
            next(parse_whitespace)
        # Test that StopIteration indicates found is True
        self.assertIs(stop.exception.value, True)

    def test_parser_empty_on_no_space(self):
        s = 'foo'
        buf = iterseq.IterableAsSequence([s])
        parse_whitespace = lex.WhitespaceParser()
        parse_whitespace(buf, tokens.MarkupWhitespace())
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
        parse_sentinel(buf, tokens.Content(), '?>')
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
        parse_sentinel(buf, tokens.Content(), '?>')
        parse_sentinel = iter(parse_sentinel)
        self.assertIsInstance(next(parse_sentinel), tokens.Content)
        text = parse_sentinel.send(tokens.TextHolder())
        self.assertEqual(text.literal(), 'more')
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
        parse_sentinel(buf, tokens.Content(), '?>')
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
        parse_sentinel(buf, tokens.Content(), '?>')
        parse_sentinel = iter(parse_sentinel)
        self.assertIsInstance(next(parse_sentinel), tokens.Content)
        text = parse_sentinel.send(tokens.TextHolder())
        self.assertEqual(text.literal(), 'morefix')
        self.assertIsInstance(next(parse_sentinel), tokens.Content)
        text = parse_sentinel.send(tokens.TextHolder())
        self.assertEqual(text.literal(), '')
        self.assertIs(text.is_final, True)
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
        parse_sentinel(buf, tokens.Content(), '?>')
        parse_sentinel = iter(parse_sentinel)
        self.assertIsInstance(next(parse_sentinel), tokens.Content)
        text = parse_sentinel.send(tokens.TextHolder())
        self.assertEqual(text.literal(), 'morefix')
        self.assertIsInstance(next(parse_sentinel), tokens.Content)
        text = parse_sentinel.send(tokens.TextHolder())
        self.assertEqual(text.literal(), '?')
        self.assertIs(text.is_final, True)
        with self.assertRaises(StopIteration) as stop:
            next(parse_sentinel)
        # Test that StopIteration indicates found is False
        self.assertIs(stop.exception.value, False)
        self.assertEqual(buf.extract(), '')
        self.assertEqual(buf.get(), '')


class TokenScannerMarkupTests(unittest.TestCase):

    def scan(self, stream, expected_tokens):
        # Add fake sequence to end, to catch additional tokens being
        # emitted after expected. expected[0] is valid to make first
        # test work and output comparison, and expected[1] is error as
        # fallback to ensure final test fails
        # print(self.id())
        expected_tokens.append((tokens.Token(),))
        buf = iterseq.IterableAsSequence(stream)
        scanner = lex.TokenScanner(buf)
        token_stream = iter(scanner)
        for token, expected in zip(token_stream, expected_tokens):
            text = scanner.get_text(token)
            # print(token, repr(text.literal()), text.is_final)
            literal = text.literal()
            while not text.is_final:
                text = scanner.get_text(next(token_stream))
                literal += text.literal()
                self.assertIsInstance(token, expected[0], repr(literal))
            self.assertEqual(literal, expected[1])
        self.assertEqual(buf.get(), '')
        # print()

    def test_start_tag(self):
        xml = '<tag foo="bar">'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleClose, '"'),
            (tokens.StartTagClose, '>')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag(self):
        xml = '<tag'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space(self):
        xml = '<tag '
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr(self):
        xml = '<tag foo'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr_equals(self):
        xml = '<tag foo='
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEquals, '='),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr_equals_quote(self):
        xml = '<tag foo="'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attr_equals_quote_value(self):
        xml = '<tag foo="bar'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_start_tag_space_attribute(self):
        xml = '<tag foo="bar"'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleClose, '"'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_empty_tag_space_attribute_slash(self):
        xml = '<tag foo="bar" /'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleClose, '"'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.BadlyFormedEndOfStream, '/')
            ]
        self.scan([xml], expected_tokens)

    def test_end_tag(self):
        xml = '</ns:tag>'
        expected_tokens = [
            (tokens.EndTagOpen, '</'),
            (tokens.TagName, 'ns:tag'),
            (tokens.EndTagClose, '>')
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
            (tokens.EndTagOpen, '</'),
            (tokens.TagName, 'foo'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_empty_tag(self):
        xml = '<tag\tfoo="bar"\n\t/>'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, '\t'),
            (tokens.AttributeName, 'foo'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'bar'),
            (tokens.AttributeValueDoubleClose, '"'),
            (tokens.MarkupWhitespace, '\n\t'),
            (tokens.EmptyTagClose, '/>')
            ]
        self.scan([xml], expected_tokens)

    def test_cdata(self):
        xml = "<![CDATA[Some <non-markup> text & [] symbols]]>"
        expected_tokens = [
            (tokens.CDataOpen, '<![CDATA['),
            (tokens.CData, 'Some <non-markup> text & [] symbols'),
            (tokens.CDataClose, ']]>')
            ]
        self.scan([xml], expected_tokens)

    def test_empty_cdata(self):
        xml = "<![CDATA[]]>"
        expected_tokens = [
            (tokens.CDataOpen, '<![CDATA['),
            (tokens.CDataClose, ']]>')
            ]
        self.scan([xml], expected_tokens)

    def test_short_cdata(self):
        xml = "<![CDATA[Some <non-markup> text & []"
        expected_tokens = [
            (tokens.CDataOpen, '<![CDATA['),
            (tokens.CData, 'Some <non-markup> text & []'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_comment(self):
        xml = "<!-- Lot's of text, including technically invalid -- -->"
        expected_tokens = [
            (tokens.CommentOpen, '<!--'),
            (tokens.CommentData,
                " Lot's of text, including technically invalid -- "),
            (tokens.CommentClose, '-->')
            ]
        self.scan([xml], expected_tokens)

    def test_empty_comment(self):
        xml = "<!---->"
        expected_tokens = [
            (tokens.CommentOpen, '<!--'),
            (tokens.CommentClose, '-->')
            ]
        self.scan([xml], expected_tokens)

    def test_short_comment(self):
        xml = "<!--"
        expected_tokens = [
            (tokens.CommentOpen, '<!--'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_comment_data(self):
        xml = "<!-- comment "
        expected_tokens = [
            (tokens.CommentOpen, '<!--'),
            (tokens.CommentData, ' comment '),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_invalid_comment(self):
        # As non-well-formed markup, this is interpreted as content, but
        # has attribute ``is_well_formed`` set to False for the < character
        xml = '<-- hello -->'
        expected_tokens = [
            (tokens.Content, '<', False),
            (tokens.PCData, '-- hello -->', True),
            ]
        buf = iterseq.IterableAsSequence([xml])
        token_stream = lex.TokenScanner(buf)
        for token, expected in zip(token_stream, expected_tokens):
            text = token_stream.get_text(token)
            self.assertIsInstance(token, expected[0])
            self.assertEqual(text.literal(), expected[1])
            self.assertIs(isinstance(token, tokens.WellFormed), expected[2])

    def test_processing_instruction(self):
        xml = "<?xml foo bar?>"
        expected_tokens = [
            (tokens.ProcessingInstructionOpen, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.ProcessingInstructionData, 'foo bar'),
            (tokens.ProcessingInstructionClose, '?>')
            ]
        self.scan([xml], expected_tokens)

    def test_empty_processing_instruction(self):
        xml = "<?xml?>"
        expected_tokens = [
            (tokens.ProcessingInstructionOpen, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.ProcessingInstructionClose, '?>')
            ]
        self.scan([xml], expected_tokens)

    def test_short_processing_instruction(self):
        xml = "<?"
        expected_tokens = [
            (tokens.Content, '<'),
            (tokens.PCData, '?'),
            ]
        self.scan([xml], expected_tokens)

    def test_short_processing_instruction_name(self):
        xml = "<?xml"
        expected_tokens = [
            (tokens.ProcessingInstructionOpen, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    @unittest.skip('TODO - emit error token, and return to content mode')
    def test_short_processing_instruction_name_quest(self):
        xml = "<?xml?"
        expected_tokens = [
            (tokens.ProcessingInstructionOpen, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            ]
        self.scan([xml], expected_tokens)

    def test_short_processing_instruction_name_data(self):
        xml = "<?xml vers"
        expected_tokens = [
            (tokens.ProcessingInstructionOpen, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.ProcessingInstructionData, 'vers'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_short_processing_instruction_name_data_quest(self):
        xml = "<?xml vers?"
        expected_tokens = [
            (tokens.ProcessingInstructionOpen, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.ProcessingInstructionData, 'vers?'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    @unittest.skip('TODO - emit error token, and return to content mode')
    def test_invalid_processing_instruction_name_symbol(self):
        xml = "<?xml!?>"
        expected_tokens = [
            (tokens.ProcessingInstructionOpen, '<?'),
            (tokens.ProcessingInstructionTarget, 'xml'),
            (tokens.BadlyFormedEndOfStream, '')
            ]
        self.scan([xml], expected_tokens)

    def test_invalid_processing_instruction(self):
        xml = '<??>'
        buf = iterseq.IterableAsSequence([xml])
        scanner = lex.TokenScanner(buf)
        token_stream = iter(scanner)
        well_formed = True
        s = ''
        for token in token_stream:
            if not isinstance(token, tokens.WellFormed):
                well_formed = False
            if isinstance(token, tokens.Content):
                text = scanner.get_text(token)
                s += text.content()
        self.assertFalse(well_formed)
        self.assertEqual(s, xml)

    def test_markupish_content(self):
        xml = "?>"
        expected_tokens = [
            (tokens.PCData, '?>'),
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

    def test_literal_ok(self):
        xml = [
            '<?xml version="1.0"?><some tags="',
            'foo">This <!-- a comment -->is',
            'some </s',
            'ome>text'
            ]
        buf = iterseq.IterableAsSequence(xml)
        scanner = lex.TokenScanner(buf)
        literal = ''
        content = ''
        for token in scanner:
            text = scanner.get_text(token)
            literal += text.literal()
            if isinstance(token, tokens.Content):
                content += text.content()
        self.assertEqual(literal, ''.join(xml))
        self.assertEqual(content, 'This issome text')

    def test_attribute_colon(self):
        xml = '<tag na:me="value">'
        expected_tokens = [
            (tokens.StartOrEmptyTagOpen, '<'),
            (tokens.TagName, 'tag'),
            (tokens.MarkupWhitespace, ' '),
            (tokens.AttributeName, 'na:me'),
            (tokens.AttributeEquals, '='),
            (tokens.AttributeValueDoubleOpen, '"'),
            (tokens.AttributeValue, 'value'),
            (tokens.AttributeValueClose, '"'),
            (tokens.StartTagClose, '>'),
            ]
        self.scan([xml], expected_tokens)

    def test_attribute_no_space_error(self):
        xml = '<tag foo="value"bar="value">'
        with self.assertRaises(RuntimeError):
            expected_tokens = [
                (tokens.StartOrEmptyTagOpen, '<'),
                (tokens.TagName, 'tag'),
                (tokens.MarkupWhitespace, ' '),
                (tokens.AttributeName, 'foo'),
                (tokens.AttributeEquals, '='),
                (tokens.AttributeValueDoubleOpen, '"'),
                (tokens.AttributeValue, 'value'),
                (tokens.AttributeValueClose, '"'),
                (tokens.AttributeName, 'bar'),
                ]
            self.scan([xml], expected_tokens)


class TestRead(unittest.TestCase):

    def test_content_tokens_1(self):
        """README example 1"""
        string_iter = ['Hello, ', 'World!']
        result = []
        token_stream = lex.TokenScanner.from_strings(string_iter)
        for token in token_stream:
            if isinstance(token, tokens.Content):
                text = token_stream.get_text(token)
                result.append(text.content())
        self.assertEqual(''.join(string_iter), ''.join(result))

    def test_content_tokens_2(self):
        """README example 2"""
        string_iter = ['Hello, ', 'World!']
        result = []
        holder = tokens.TextHolder()
        token_stream = lex.TokenScanner.from_strings(string_iter)
        for token in token_stream:
            if isinstance(token, tokens.Content):
                text = token_stream.get_text(token, holder)
                result.append(text.content())
        self.assertEqual(''.join(string_iter), ''.join(result))
