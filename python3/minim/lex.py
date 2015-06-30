"""Lexical scanning of XML-like languages.

This file contains several classes that implement the generator interface.
These could be implemented as proper generators, but they get called
frequently, and calling new generators allocates memory.  Each call of
the generator function allocates a new generator.  The classes here
are effectively restartable generators. Calling __call__ and __iter__
resets them after a StopIteration.

Due to the token protocol, which interleave next() calls with optional
send() calls, this also allows us to separate these two calls (in a
real generator, they are all in the same function).  The price to pay is
the need to operate a state machine.
"""
import abc
from collections.abc import Iterable, Iterator
import re

from minim import iterseq, tokens


# Pre-allocated return values
_stop_iteration = StopIteration()
_stop_iteration_found = StopIteration(True)
_stop_iteration_not_found = StopIteration(False)


class SentinelParser(Iterator):

    """A non-allocating iterator for a sentinel.

    On end of the iteration, the buffer will point either to the start
    of the sentinel, or to the end of the stream.
    """

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
        return super().__iter__()

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
            if self.buf.get():
                # the next character must be the start of the sentinel
                self.stopped = _stop_iteration_found
            else:
                # reached the end of the stream
                self.stopped = _stop_iteration_not_found
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


class LiteralResponder(Iterator):

    """A non-allocating iterator for a literal value."""

    def __call__(self, token_type, literal):
        self.token_type = token_type
        self.literal = literal
        return self

    def __next__(self):
        if self.literal is None:
            raise _stop_iteration
        yield self.token_type

    def send(self, val):
        if self.literal is None:
            raise _stop_iteration
        if val.is_token:
            val.set(literal=self.buf.literal)
        else:
            assert val is self.token_type, val
            val = self.token_type(literal=self.literal)
        return val


class PatternParser(Iterator):

    """A non-allocating iterator for a regex pattern."""

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
        return super().__iter__()

    def __next__(self):
        if self.stopped is not None:
            raise self.stopped
        if self.found:
            self.is_initial = False
        matched = self.buf.matching(self.pat)
        if matched == 0:
            if self.found:
                self.stopped = _stop_iteration_found
            else:
                self.stopped = _stop_iteration_not_found
            if not self.is_initial and not self.is_final:
                self.is_final = True
                return self.token_type
            else:
                raise self.stopped
        else:
            self.found = True
            if matched < 0:
                self.is_final = True
                self.stopped = _stop_iteration_found
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


class WhitespaceParser(PatternParser):

    pattern = re.compile(r'[ \t\r\n]+')

    def __init__(self):
        super().__init__(self.pattern)


class NmTokenParser(PatternParser):

    """Parse an XML NmToken.

    XML defines an NmToken, which is a sequence of alphanumeric
    characters plus underscore (_), colon (:), dot (.), and dash (-).
    XML also defines a Name, which is an NmToken where the initial
    character is not a number, dot, or dash.  This parser matches
    NmTokens.  A helper function is provided to check whether the
    initial character is valid for a name. This should always be called
    on the initial string first when parsing a name.
    """
    name_initial_pattern = re.compile(r':|[^\W\d]')
    nm_token_pattern = re.compile(r'[\w:.-]+')

    def __init__(self):
        super().__init__(self.nm_token_pattern)

    def matches_initial(self, s):
        """Return whether the start of the string looks like a name."""
        return bool(self.name_initial_pattern.match(s))


class GeneratesTokens(Iterable, metaclass=abc.ABCMeta):

    """An iterable that yields token types, and provides a method to
    obtain the token matching the token type."""

    @abc.abstractmethod
    def next(self):
        """Return the current token type in the input stream.

        This may return either a token type or a token.  In either case,
        the returned object can be interrogated for properties to
        determine whether it is of interest to the caller.

        If the caller needs the token, they call ``get_token`` to obtain
        a token.  In some caes, this just returns the same instance.
        """

    @abc.abstractmethod
    def token_type_to_token(self, token_type, token):
        """Convert a token type to a token.

        This method does the work of turning a token type into a token.
        The supplied token parameter is a type of token that can be
        filled in instead of allocating a new token."""

    def get_token(self, token_type, token=None):
        """Return the current token in the input stream.

        If the token type is of interest to the processor, calling this
        method will return an actual token, which can be processed
        further.

        If the optional ``token`` parameter is not provided, this will
        usually allocate a new token.

        If the optional ``token`` parameter is provided, this function
        **may** choose to use the provided (subclass of) ``Token`` as
        the returned token.  This allows the opportunity for the system
        to avoid allocating memory for the token.

        Note that this method is not required to use the provided token,
        so the return value must be used for subsequent processing of
        the current token.

        :param token_type: A Token Type returned from the iterator
        :param token: An optional Token that can be set
        :return: The current token in the input stream
        :rtype: minim.tokens.Token
        """
        if token_type.is_token:
            # The iterator is permitted to return a token for next()
            # rather than a token_type.  In this case, just return the
            # token again.
            return token_type
        else:
            return self.token_type_to_token(token_type, token)


class SendBasedTokenGenerator(GeneratesTokens):

    """An iterable that yields token types, and responds to send()
    with the token matching the token type."""

    def __init__(self):
        self.generator = None

    def __iter__(self):
        self.generator = self.create_generator()
        return self.generator

    @abc.abstractmethod
    def create_generator(self):
        pass

    def next(self):
        return next(self.generator)

    def token_type_to_token(self, token_type, token):
        if token is None:
            return self.generator.send(token_type)
        else:
            return self.generator.send(token)


class BufferBasedTokenGenerator(GeneratesTokens):

    """An iterable that yields token types, and uses buffer state to
    return the token matching the token type.

    This can only handle the case where a token type is instantiated by
    calling the token type with a saved buffer.
    """

    def __init__(self):
        self.current_parser = None
        self.generator = None

    def __iter__(self):
        self.generator = self.create_generator()
        return self.generator

    @abc.abstractmethod
    def create_generator(self):
        pass

    def next(self):
        return next(self.generator)

    def token_type_to_token(self, token_type, token):
        if token is None:
            return self.current_parser.send(token_type)
        else:
            return self.current_parser.send(token)


class TokenGenerator(BufferBasedTokenGenerator):

    def __init__(self, buf):
        super().__init__()
        self.buf = buf
        self.generator = None
        self.name_parser = NmTokenParser()
        self.space_parser = WhitespaceParser()
        self.sentinel_parser = SentinelParser()

    def parse_name(self, buf, token_type):
        self.current_parser = self.name_parser
        return self.name_parser(buf, token_type)

    def parse_space(self, buf, token_type):
        self.current_parser = self.space_parser
        return self.space_parser(buf, token_type)

    def parse_until(self, buf, token_type, sentinel):
        self.current_parser = self.sentinel_parser
        return self.sentinel_parser(buf, token_type, sentinel)

    @classmethod
    def from_strings(cls, string_iter):
        """Generates tokens from the supplied iterator."""
        return cls(iterseq.IterableAsSequence(string_iter))

    def create_generator(self):
        return self.parse(self.buf)

    def parse(self, buf):
        # Whitespace before initial non-ws is not considered to be content
        yield from self.parse_space(buf, tokens.MarkupWhitespace)
        yield from self.parse_until(
            buf, tokens.PCData, '<')
        while buf.get() == '<':
            ch = buf.next()
            if ch == '/':
                ch = buf.next()
                if self.name_parser.matches_initial(ch):
                    yield tokens.EndTagOpenToken
                    yield from self.parse_name(buf, tokens.TagName)
                    yield from self.parse_space(buf, tokens.MarkupWhitespace)
                    ch = buf.get()
                    if not ch:
                        yield tokens.BadlyFormedEndOfStream()
                        return
                    elif ch != '>':
                        raise RuntimeError('extra data in close tag')
                    yield tokens.EndTagCloseToken
                    buf.advance()
                else:
                    yield tokens.BadlyFormedLessThanToken
                    yield tokens.PCData(literal='/')
            elif ch == '?':
                ch = buf.next()
                if self.name_parser.matches_initial(ch):
                    yield tokens.ProcessingInstructionOpenToken
                    yield from self.parse_name(
                        buf, tokens.ProcessingInstructionTarget)
                    ws_found = yield from self.parse_space(
                        buf, tokens.MarkupWhitespace)
                    if ws_found:
                        found = yield from self.parse_until(
                            buf, tokens.ProcessingInstructionData, '?>')
                        if buf.starts_with('?>'):
                            # `starts_with` is redundant, since `found`
                            # indicates whether the sentinel was found.
                            # `starts_with` consumes the characters
                            assert found, found
                        else:
                            # must be EOS
                            assert not found, found
                            yield tokens.BadlyFormedEndOfStream()
                            return
                    else:
                        if not buf.get():
                            yield tokens.BadlyFormedEndOfStream()
                            return
                        if not buf.starts_with('?>'):
                            raise RuntimeError(
                                'Expected ?>, got %r' % buf.get())
                    yield tokens.ProcessingInstructionCloseToken
                else:
                    yield tokens.BadlyFormedLessThanToken
                    yield tokens.PCData(literal='?')
            elif ch == '!':
                ch = buf.next()
                if ch == '-':
                    ch = buf.next()
                    if ch == '-':
                        yield tokens.CommentOpenToken
                        buf.advance()
                        yield from self.parse_until(
                            buf, tokens.CommentData, '-->')
                        if not buf.starts_with('-->'):
                            yield tokens.BadlyFormedEndOfStream()
                            return
                        yield tokens.CommentCloseToken
                    else:
                        # < does not appear to be well-formed markup - emit a
                        # literal <
                        yield tokens.BadlyFormedLessThanToken
                        yield tokens.PCData(literal='!-')
                elif ch == '[':
                    buf.advance()
                    if buf.starts_with('CDATA['):
                        yield tokens.CDataOpenToken
                        found = yield from self.parse_until(
                            buf, tokens.CData, ']]>')
                        if not buf.starts_with(']]>'):
                            assert not found, found
                            assert not buf.get(), buf.get()
                            yield tokens.BadlyFormedEndOfStream()
                            return
                        yield tokens.CDataCloseToken
                    else:
                        # declaration
                        raise NotImplementedError(
                            'Declarations not implemented')
                else:
                    yield tokens.BadlyFormedLessThanToken
                    yield tokens.PCData(literal='!')
            elif self.name_parser.matches_initial(ch):
                yield tokens.StartOrEmptyTagOpenToken
                if not (yield from self.parse_name(buf, tokens.TagName)):
                    raise RuntimeError('Expected tag name')
                ws_found = yield from self.parse_space(
                    buf, tokens.MarkupWhitespace)
                ch = buf.get()
                while ch not in ('', '>', '/'):
                    if not ws_found:
                        raise RuntimeError(
                            'Expected whitespace, >, or />, found %r' % ch)
                    if not self.name_parser.matches_initial(ch):
                        raise RuntimeError('Expected attribute name')
                    yield from self.parse_name(buf, tokens.AttributeName)
                    yield from self.parse_space(buf, tokens.MarkupWhitespace)
                    ch = buf.get()
                    if ch == '=':
                        yield tokens.AttributeEqualsToken
                        buf.advance()
                        yield from self.parse_space(
                            buf, tokens.MarkupWhitespace)
                        ch = buf.get()
                        if not ch:
                            yield tokens.BadlyFormedEndOfStream()
                            return
                        if ch in ('"', "'"):
                            if ch == '"':
                                yield tokens.AttributeValueDoubleOpenToken
                            else:
                                yield tokens.AttributeValueSingleOpenToken
                            buf.advance()
                            yield from self.parse_until(
                                buf, tokens.AttributeValue, ch)
                            if not buf.starts_with(ch):
                                yield tokens.BadlyFormedEndOfStream()
                                return
                            if ch == '"':
                                yield tokens.AttributeValueDoubleCloseToken
                            else:
                                yield tokens.AttributeValueSingleCloseToken
                        else:
                            # HTML fallback - need a parser to read un-quoted
                            # attribute
                            raise RuntimeError()
                        ws_found = yield from self.parse_space(
                            buf, tokens.MarkupWhitespace)
                        ch = buf.get()
                if not ch:
                    yield tokens.BadlyFormedEndOfStream()
                    return
                elif ch == '>':
                    yield tokens.StartTagCloseToken
                    buf.advance()
                else:
                    assert ch == '/'
                    ch = buf.next()
                    if not ch:
                        yield tokens.BadlyFormedEndOfStream('/')
                        return
                    elif ch != '>':
                        raise RuntimeError('Expected />')
                    yield tokens.EmptyTagCloseToken
                    buf.advance()
            else:
                # < does not appear to be well-formed markup - treat it
                # as a content character
                yield tokens.BadlyFormedLessThanToken
            yield from self.parse_space(buf, tokens.WhitespaceContent)
            yield from self.parse_until(buf, tokens.PCData, '<')
