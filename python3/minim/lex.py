import re
import warnings

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

    """A non-allocating iterator for a sentinel.

    When this iterator ends, the buffer will contain the sentinel.
    That is, calling buf.extract() will return the sentinel, and
    subsequent matches will start from after the sentinel.
    """

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
        if self.buf.starts_with(self.sentinel) and not self.needs_final:
            self.stopped = self.stop_iteration
            raise self.stopped
        if self.needs_final:
            self.is_initial = False
        loc = self.buf.match_to_sentinel(self.sentinel)
        if loc < 0:
            self.needs_final = True
        else:
            self.is_final = True
            self.needs_final = False
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
        remain = self.buf.matching(self.pat)
        if remain < 0:
            if self.found:
                self.stopped = self.stop_iteration_found
            else:
                self.stopped = self.stop_iteration_not_found
            if not self.is_final:
                self.is_final = True
                return self.token_type
            else:
                raise self.stopped
        else:
            self.found = True
            if remain > 0:
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

    # Simple pattern, with most commonly expected non-name characters.
    # Lots of values would pass this filter, despite not being valid
    # names, e.g.: 123, -123, .343
    pattern = re.compile(r'[^ \t\r\n<>/?!=]+')

    def __init__(self):
        super().__init__(self.pattern)


class TokenGenerator:

    def __init__(self, buf):
        self.buf = buf
        self.parse_name = NameParser()
        self.parse_whitespace = WhitespaceParserXML10()
        self.parse_to_sentinel = SentinelParser()

    def parse_markup(self, buf):
        assert buf.get() == '<'
        ch = buf.next()
        if ch == '/':
            yield tokens.EndTagOpenSingleton
            buf.advance()
            if not (yield from self.parse_name(buf, tokens.TagName)):
                raise RuntimeError('Expected name')
            yield from self.parse_whitespace(buf, tokens.Whitespace)
            ch = buf.next()
            if ch != '>':
                raise RuntimeError('extra data in close tag')
            yield tokens.EndTagCloseSingleton
            buf.advance()
        elif ch == '?':
            yield tokens.ProcessingInstructionOpenSingleton
            if not (yield from self.parse_name(
                    buf, tokens.ProcessingInstructionTarget)):
                raise RuntimeError('Expected name')
            ws_after_name = yield from self.parse_whitespace(
                buf, tokens.Whitespace)
            if not buf.starts_with('?>'):
                if not ws_after_name:
                    raise RuntimeError('Expected ?>')
                yield from self.parse_to_sentinel(
                    buf, tokens.ProcessingInstructionData, '?>')
            assert buf.extract() == '?>'
            yield tokens.ProcessingInstructionCloseSingleton
        elif ch == '!':
            ch = buf.next()
            if ch == '-':
                ch = buf.next()
                if ch == '-':
                    yield tokens.CommentOpenSingleton
                    buf.advance()
                    yield from self.parse_to_sentinel(
                        buf, tokens.CommentData, '-->')
                    assert buf.extract() == '-->'
                    yield tokens.CommentCloseSingleton
                else:
                    yield tokens.LiteralLessThanContent
                    yield tokens.LiteralExclamationMarkDash
            elif ch == '[':
                if buf.starts_with('CDATA['):
                    yield tokens.CDataOpenSingleton
                    yield from self.parse_to_sentinel(buf, tokens.CData, ']]>')
                    assert buf.extract() == ']]>'
                    yield tokens.CDataCloseSingleton
                else:
                    # declaration
                    ...
            else:
                yield tokens.LiteralLessThanContent
                yield tokens.LiteralExclamationMark
        else:
            yield tokens.StartOrEmptyTagOpenSingleton
            if not (yield from self.parse_name(buf, tokens.TagName)):
                raise RuntimeError('Expected tag name')
            ws_found = yield from self.parse_whitespace(buf, tokens.Whitespace)
            ch = buf.get()
            while ch not in ('>', '/'):
                if not ws_found:
                    raise RuntimeError('Expected whitespace, >, or />')
                if not (yield from self.parse_name(buf, tokens.AttributeName)):
                    raise RuntimeError('Expected attribute name')
                yield from self.parse_whitespace(buf, tokens.Whitespace)
                ch = buf.get()
                if ch == '=':
                    yield tokens.AttributeEqualsSingleton
                    buf.advance()
                    yield from self.parse_whitespace(buf, tokens.Whitespace)
                    ch = buf.get()
                    if ch in ('"', "'"):
                        if ch == '"':
                            yield tokens.AttributeValueDoubleOpenSingleton
                        else:
                            yield tokens.AttributeValueSingleOpenSingleton
                        yield from self.parse_to_sentinel(
                            buf, tokens.AttributeValue, ch)
                        if ch == '"':
                            yield tokens.AttributeValueDoubleCloseSingleton
                        else:
                            yield tokens.AttributeValueSingleCloseSingleton
                    else:
                        # HTML fallback - need a parser to read un-quoted
                        # attribute
                        raise RuntimeError()
                    ws_found = yield from self.parse_whitespace(
                        buf, tokens.Whitespace)
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
