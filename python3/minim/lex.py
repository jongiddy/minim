import re

from minim import tokens


def token_type_generator(string_iter):
    for s in string_iter:
        response = yield tokens.Content
        if response is not None:
            # response should either be a token_type (the Content class)
            # or an existing Token.
            if response.is_token:
                # response is a token: set contents of this token and
                # return
                assert isinstance(response, tokens.Token)
                response.set(literal=s)
                yield response
            else:
                assert issubclass(response, tokens.Token)
                # response is a token_type, instantiate it and set contents
                yield response(s)


class SentinelParser:

    """A non-allocating iterator for a sentinel."""

    # Pre-allocated return value
    stop_iteration = StopIteration()

    def __call__(self, buf, token_type, sentinel):
        self.buf = buf
        self.token_type = token_type
        self.sentinel = sentinel
        return self

    def __iter__(self):
        self.stopped = None
        self.first = True
        self.needs_final = False
        self.is_initial = True
        self.is_final = False
        return self

    def __next__(self):
        if self.stopped is not None:
            raise self.stopped
        if self.needs_final:
            self.is_initial = False
        loc = self.buf.match_to_sentinel(self.sentinel)
        if loc < 0:
            # sentinel or EOF found, but need to handle content first
            self.is_final = True
            self.needs_final = False
        elif loc == 0:
            # sentinel or EOF found at start of string
            self.stopped = self.stop_iteration
            if self.needs_final:
                self.is_final = True
                self.needs_final = False
            else:
                raise self.stopped
        else:
            # content to emit, but sentinel not found
            self.is_final = False
            self.needs_final = True
        return self.token_type

    def send(self, val):
        if val.is_token:
            val.set(
                literal=self.buf.extract(), is_initial=self.is_initial,
                is_final=self.is_final)
        else:
            assert val is self.token_type, val
            val = self.token_type(
                literal=self.buf.extract(), is_initial=self.is_initial,
                is_final=self.is_final)
        return val


class LiteralResponder:

    """A non-allocating iterator for a literal value."""

    # Pre-allocated return value
    stop_iteration = StopIteration()

    def __call__(self, token_type, literal):
        self.token_type = token_type
        self.literal = literal
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self.literal is None:
            raise self.stop_iteration
        yield self.token_type

    def send(self, val):
        if self.literal is None:
            raise self.stop_iteration
        if val.is_token:
            val.set(literal=self.buf.literal)
        else:
            assert val is self.token_type, val
            val = self.token_type(literal=self.literal)
        return val


class PatternParser:

    """A non-allocating iterator for a regex pattern."""

    # Pre-allocated return values
    stop_iteration_found = StopIteration(True)
    stop_iteration_not_found = StopIteration(False)

    def __init__(self, pat):
        self.pat = pat

    def __call__(self, buf, token_type):
        self.buf = buf
        self.token_type = token_type
        return self

    def __iter__(self):
        self.stopped = None
        self.found = False
        self.is_initial = True
        self.is_final = False
        return self

    def __next__(self):
        if self.stopped is not None:
            raise self.stopped
        if self.found:
            self.is_initial = False
        matched = self.buf.matching(self.pat)
        if matched == 0:
            if self.found:
                self.stopped = self.stop_iteration_found
            else:
                self.stopped = self.stop_iteration_not_found
            if not self.is_initial and not self.is_final:
                self.is_final = True
                return self.token_type
            else:
                raise self.stopped
        else:
            self.found = True
            if matched < 0:
                self.is_final = True
                self.stopped = self.stop_iteration_found
            return self.token_type

    def send(self, val):
        if val.is_token:
            val.set(
                literal=self.buf.extract(), is_initial=self.is_initial,
                is_final=self.is_final)
        else:
            assert val is self.token_type, val
            val = self.token_type(
                literal=self.buf.extract(), is_initial=self.is_initial,
                is_final=self.is_final)
        return val


class WhitespaceParserXML10(PatternParser):

    pattern = re.compile(r'[ \t\r\n]+')

    def __init__(self):
        super().__init__(self.pattern)


class NameParser(PatternParser):

    allowed = r'\w:.-'
    invalid_initial = re.compile(r'[\d.-]')
    pattern = re.compile('[{}]+'.format(allowed))

    def __init__(self):
        super().__init__(self.pattern)

    def __next__(self):
        if (not self.found and
                self.buf.matching(self.invalid_initial, extract=False)):
            # initial character might match pattern, but is disallowed
            # as initial name character, so exit here.
            self.stopped = self.stop_iteration_not_found
            raise self.stopped
        return super().__next__()

    def matches_name(self, s):
        """Return whether the start of the string looks like a name."""
        return (
            not self.invalid_initial.match(s) and
            bool(self.pattern.match(s[:1])))


class TokenGenerator:

    def __init__(self, buf):
        self.buf = buf
        self.parse_name = NameParser()
        self.parse_whitespace = WhitespaceParserXML10()
        self.parse_to_sentinel = SentinelParser()

    def parse(self):
        try:
            yield from self.parse_markup(self.buf)
        except EOFError:
            # If an uncaught EOFError reaches here, emit a token to
            # inform the caller that the EOF was unexpected.
            yield tokens.BadlyFormedEndOfStreamSingleton

    def parse_markup(self, buf):
        # MarkupWhitespace before initial non-ws is not considered to be content
        yield from self.parse_whitespace(buf, tokens.MarkupWhitespace)
        yield from self.parse_to_sentinel(buf, tokens.PCData, '<')
        while buf.get() == '<':
            ch = buf.next()
            if ch == '/':
                ch = buf.next()
                if self.parse_name.matches_name(ch):
                    yield tokens.EndTagOpenSingleton
                    yield from self.parse_name(buf, tokens.TagName)
                    yield from self.parse_whitespace(buf, tokens.MarkupWhitespace)
                    ch = buf.get()
                    if ch != '>':
                        raise RuntimeError('extra data in close tag')
                    yield tokens.EndTagCloseSingleton
                    buf.advance()
                else:
                    yield tokens.BadlyFormedLessThanSingleton
                    yield tokens.PCData(literal='/')
            elif ch == '?':
                ch = buf.next()
                if self.parse_name.matches_name(ch):
                    yield tokens.ProcessingInstructionOpenSingleton
                    yield from self.parse_name(
                        buf, tokens.ProcessingInstructionTarget)
                    ws_after_name = yield from self.parse_whitespace(
                        buf, tokens.MarkupWhitespace)
                    if not buf.starts_with('?>'):
                        if not ws_after_name:
                            raise RuntimeError('Expected ?>')
                        yield from self.parse_to_sentinel(
                            buf, tokens.ProcessingInstructionData, '?>')
                        if not buf.starts_with('?>'):
                            raise EOFError()
                    yield tokens.ProcessingInstructionCloseSingleton
                else:
                    yield tokens.BadlyFormedLessThanSingleton
                    print(3)
                    yield tokens.PCData(literal='?')
            elif ch == '!':
                ch = buf.next()
                if ch == '-':
                    ch = buf.next()
                    if ch == '-':
                        yield tokens.CommentOpenSingleton
                        buf.advance()
                        yield from self.parse_to_sentinel(
                            buf, tokens.CommentData, '-->')
                        if not buf.starts_with('-->'):
                            raise EOFError()
                        yield tokens.CommentCloseSingleton
                    else:
                        # < does not appear to be well-formed markup - emit a
                        # literal <
                        yield tokens.BadlyFormedLessThanSingleton
                        yield tokens.PCData(literal='!-')
                elif ch == '[':
                    if buf.starts_with('CDATA['):
                        yield tokens.CDataOpenSingleton
                        yield from self.parse_to_sentinel(buf, tokens.CData, ']]>')
                        if not buf.starts_with(']]>'):
                            raise EOFError()
                        yield tokens.CDataCloseSingleton
                    else:
                        # declaration
                        ...
                else:
                    # < does not appear to be well-formed markup - emit a literal <
                    yield tokens.BadlyFormedLessThanSingleton
                    yield tokens.PCData(literal='!')
            elif self.parse_name.matches_name(ch):
                yield tokens.StartOrEmptyTagOpenSingleton
                if not (yield from self.parse_name(buf, tokens.TagName)):
                    raise RuntimeError('Expected tag name')
                ws_found = yield from self.parse_whitespace(buf, tokens.MarkupWhitespace)
                ch = buf.get()
                while ch not in ('>', '/'):
                    if not ws_found:
                        raise RuntimeError(
                            'Expected whitespace, >, or />, found %r' % ch)
                    if not (yield from self.parse_name(buf, tokens.AttributeName)):
                        raise RuntimeError('Expected attribute name')
                    yield from self.parse_whitespace(buf, tokens.MarkupWhitespace)
                    ch = buf.get()
                    if ch == '=':
                        yield tokens.AttributeEqualsSingleton
                        buf.advance()
                        yield from self.parse_whitespace(buf, tokens.MarkupWhitespace)
                        ch = buf.get()
                        if ch in ('"', "'"):
                            if ch == '"':
                                yield tokens.AttributeValueDoubleOpenSingleton
                            else:
                                yield tokens.AttributeValueSingleOpenSingleton
                            buf.advance()
                            yield from self.parse_to_sentinel(
                                buf, tokens.AttributeValue, ch)
                            if not buf.starts_with(ch):
                                raise EOFError()
                            if ch == '"':
                                yield tokens.AttributeValueDoubleCloseSingleton
                            else:
                                yield tokens.AttributeValueSingleCloseSingleton
                        else:
                            # HTML fallback - need a parser to read un-quoted
                            # attribute
                            raise RuntimeError()
                        ws_found = yield from self.parse_whitespace(
                            buf, tokens.MarkupWhitespace)
                        ch = buf.get()
                if ch == '>':
                    yield tokens.StartTagCloseSingleton
                else:
                    assert ch == '/'
                    ch = buf.next()
                    if ch != '>':
                        raise RuntimeError('Expected />')
                    yield tokens.EmptyTagCloseSingleton
                buf.advance()
            else:
                # < does not appear to be well-formed markup - emit a literal <
                yield tokens.BadlyFormedLessThanSingleton
            yield from self.parse_whitespace(buf, tokens.WhitespaceContent)
            yield from self.parse_to_sentinel(buf, tokens.PCData, '<')
