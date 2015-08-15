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
import re

import inter
from minim import iterseq, tokens


# Pre-allocated return values
_stop_iteration = StopIteration()
_stop_iteration_found = StopIteration(True)
_stop_iteration_not_found = StopIteration(False)

_StartOrEmptyTagOpenTextToken = tokens.StartOrEmptyTagOpen(
    tokens.TextHolder('<'))
_EndTagOpenTextToken = tokens.EndTagOpen(tokens.TextHolder('</'))
_AttributeEqualsTextToken = tokens.AttributeEquals(tokens.TextHolder('='))
_dquote = tokens.TextHolder('"')
_squote = tokens.TextHolder("'")
_AttributeValueDoubleOpenTextToken = tokens.AttributeValueDoubleOpen(_dquote)
_AttributeValueSingleOpenTextToken = tokens.AttributeValueSingleOpen(_squote)
_AttributeValueDoubleCloseTextToken = tokens.AttributeValueDoubleClose(_dquote)
_AttributeValueSingleCloseTextToken = tokens.AttributeValueSingleClose(_squote)
_gt = tokens.TextHolder('>')
_StartTagCloseTextToken = tokens.StartTagClose(_gt)
_EmptyTagCloseTextToken = tokens.EmptyTagClose(tokens.TextHolder('/>'))
_EndTagCloseTextToken = tokens.EndTagClose(_gt)
_ProcessingInstructionOpenTextToken = tokens.ProcessingInstructionOpen(
    tokens.TextHolder('<?'))
_ProcessingInstructionCloseTextToken = tokens.ProcessingInstructionClose(
    tokens.TextHolder('?>'))
_CommentOpenTextToken = tokens.CommentOpen(tokens.TextHolder('<!--'))
_CommentCloseTextToken = tokens.CommentClose(tokens.TextHolder('-->'))
_CDataOpenTextToken = tokens.CDataOpen(tokens.TextHolder('<![CDATA['))
_CDataCloseTextToken = tokens.CDataClose(tokens.TextHolder(']]>'))
_BadlyFormedEndOfStreamEmptyTextToken = tokens.BadlyFormedEndOfStream(
    tokens.TextHolder(''))

_MarkupWhitespaceToken = tokens.MarkupWhitespace()
_TagNameToken = tokens.TagName()
_CDataToken = tokens.CData()
_PCDataToken = tokens.PCData()
_WhitespaceContentToken = tokens.WhitespaceContent()
_ProcessingInstructionTargetToken = tokens.ProcessingInstructionTarget()
_ProcessingInstructionDataToken = tokens.ProcessingInstructionData()
_AttributeNameToken = tokens.AttributeName()
_AttributeValueToken = tokens.AttributeValue()


class SentinelParser:

    """A non-allocating iterator for a sentinel.

    On end of the iteration, the buffer will point either to the start
    of the sentinel, or to the end of the stream.
    """

    def __call__(self, buf, token, sentinel):
        assert isinstance(token, tokens.Token), token
        self.buf = buf
        self.token = token
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
        return self.token

    def send(self, text):
        assert isinstance(text, tokens.TextHolder), text
        text.set(
            encoded=self.buf.extract(), is_initial=self.is_initial,
            is_final=self.is_final)
        return text


class LiteralResponder:

    """A non-allocating iterator for a literal value."""

    def __call__(self, token, literal):
        assert isinstance(token, tokens.Token), token
        self.token = token
        self.literal = literal
        return self

    def __next__(self):
        if self.literal is None:
            raise _stop_iteration
        yield self.token

    def send(self, text):
        if self.literal is None:
            raise _stop_iteration
        assert isinstance(text, tokens.TextHolder), text
        text.set(encoded=self.buf.extract())
        return text


class PatternParser:

    """A non-allocating iterator for a regex pattern."""

    def __init__(self, pat):
        self.pat = pat

    def __call__(self, buf, token):
        assert isinstance(token, tokens.Token), token
        self.buf = buf
        self.token = token
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
                self.stopped = _stop_iteration_found
            else:
                self.stopped = _stop_iteration_not_found
            if not self.is_initial and not self.is_final:
                self.is_final = True
                return self.token
            else:
                raise self.stopped
        else:
            self.found = True
            if matched < 0:
                self.is_final = True
                self.stopped = _stop_iteration_found
            return self.token

    def send(self, text):
        assert isinstance(text, tokens.TextHolder), text
        text.set(
            encoded=self.buf.extract(), is_initial=self.is_initial,
            is_final=self.is_final)
        return text


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


class GeneratesTokens(inter.face):

    """An iterable that yields token types, and provides a method to
    obtain the token matching the token type."""

    def next(self):
        """Return the current token type in the input stream.

        This may return either a token type or a token.  In either case,
        the returned object can be interrogated for properties to
        determine whether it is of interest to the caller.

        If the caller needs the token, they call ``get_token`` to obtain
        a token.  In some caes, this just returns the same instance.
        """

    def token_to_text(self, token, text_holder):
        """Obtain the text for the current token.

        This method does the work of turning a token into text."""


class BaseTokenScanner(GeneratesTokens.Provider):

    def get_text(self, token, text_holder=None):
        """Return the current text in the input stream.

        If the token type is of interest to the processor, calling this
        method will return the actual text, which can be processed
        further.

        If the optional ``text_holder`` parameter is not provided, this
        will usually allocate a new Text instance.

        If the optional ``text_holder`` parameter is provided, this
        function **may** choose to use the provided (subclass of)
        ``TextHolder`` as the returned text.  This allows the
        opportunity for the system to avoid allocating memory for the
        text.

        Note that this method is not required to use the provided text
        holder, so the return value must be used for subsequent
        processing of the text.

        :param token: A Token returned from the iterator
        :param text_holder: An optional TextHolder that can be set
        :return: The current text in the input stream
        :rtype: minim.tokens.TextHolder
        """
        assert isinstance(token, tokens.Token), token
        text = token.text
        if text is None:
            if text_holder is None:
                text_holder = tokens.TextHolder()
            assert isinstance(text_holder, tokens.TextHolder), text_holder
            text = self.token_to_text(token, text_holder)
        return text


class SendBasedTokenScanner(BaseTokenScanner):

    """An iterable that yields token types, and responds to send()
    with the token matching the token type."""

    def __init__(self):
        self.generator = None

    def __iter__(self):
        self.generator = self.create_generator()
        return self.generator

    def create_generator(self):
        pass

    def next(self):
        return next(self.generator)

    def token_to_text(self, token, text_holder):
        return self.generator.send(text_holder)


class BufferBasedTokenScanner(BaseTokenScanner):

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

    def create_generator(self):
        pass

    def next(self):
        return next(self.generator)

    def token_to_text(self, token, text_holder):
        if text_holder is None:
            return self.current_parser.send(token)
        else:
            return self.current_parser.send(text_holder)


class TokenScanner(BufferBasedTokenScanner):

    def __init__(self, buf):
        super().__init__()
        self.buf = buf
        self.generator = None
        self.name_parser = NmTokenParser()
        self.space_parser = WhitespaceParser()
        self.sentinel_parser = SentinelParser()

    def parse_name(self, buf, token):
        self.current_parser = self.name_parser
        return self.name_parser(buf, token)

    def parse_space(self, buf, token):
        self.current_parser = self.space_parser
        return self.space_parser(buf, token)

    def parse_until(self, buf, token, sentinel):
        self.current_parser = self.sentinel_parser
        return self.sentinel_parser(buf, token, sentinel)

    @classmethod
    def from_strings(cls, string_iter):
        """Generates tokens from the supplied iterator."""
        return cls(iterseq.IterableAsSequence(string_iter))

    def create_generator(self):
        return self.parse(self.buf)

    def parse(self, buf):
        # Whitespace before initial non-ws is not considered to be content
        yield from self.parse_space(buf, _MarkupWhitespaceToken)
        yield from self.parse_until(buf, _PCDataToken, '<')
        while buf.get() == '<':
            ch = buf.next()
            if ch == '/':
                ch = buf.next()
                if self.name_parser.matches_initial(ch):
                    yield _EndTagOpenTextToken
                    yield from self.parse_name(buf, _TagNameToken)
                    yield from self.parse_space(buf, _MarkupWhitespaceToken)
                    ch = buf.get()
                    if not ch:
                        yield _BadlyFormedEndOfStreamEmptyTextToken
                        return
                    elif ch != '>':
                        raise RuntimeError('extra data in close tag')
                    yield _EndTagCloseTextToken
                    buf.advance()
                else:
                    yield tokens.BadlyFormedLessThanToken
                    yield tokens.PCData(tokens.TextHolder('/'))
            elif ch == '?':
                ch = buf.next()
                if self.name_parser.matches_initial(ch):
                    yield _ProcessingInstructionOpenTextToken
                    yield from self.parse_name(
                        buf, _ProcessingInstructionTargetToken)
                    ws_found = yield from self.parse_space(
                        buf, _MarkupWhitespaceToken)
                    if ws_found:
                        found = yield from self.parse_until(
                            buf, _ProcessingInstructionDataToken, '?>')
                        if buf.starts_with('?>'):
                            # `starts_with` is redundant, since `found`
                            # indicates whether the sentinel was found.
                            # `starts_with` consumes the characters
                            assert found, found
                        else:
                            # must be EOS
                            assert not found, found
                            yield _BadlyFormedEndOfStreamEmptyTextToken
                            return
                    else:
                        if not buf.get():
                            yield _BadlyFormedEndOfStreamEmptyTextToken
                            return
                        if not buf.starts_with('?>'):
                            raise RuntimeError(
                                'Expected ?>, got %r' % buf.get())
                    yield _ProcessingInstructionCloseTextToken
                else:
                    yield tokens.BadlyFormedLessThanToken
                    yield tokens.PCData(tokens.TextHolder('?'))
            elif ch == '!':
                ch = buf.next()
                if ch == '-':
                    ch = buf.next()
                    if ch == '-':
                        yield _CommentOpenTextToken
                        buf.advance()
                        yield from self.parse_until(
                            buf, tokens.CommentData(), '-->')
                        if not buf.starts_with('-->'):
                            yield _BadlyFormedEndOfStreamEmptyTextToken
                            return
                        yield _CommentCloseTextToken
                    else:
                        # < does not appear to be well-formed markup - emit a
                        # literal <
                        yield tokens.BadlyFormedLessThanToken
                        yield tokens.PCData(tokens.TextHolder('!-'))
                elif ch == '[':
                    buf.advance()
                    if buf.starts_with('CDATA['):
                        yield _CDataOpenTextToken
                        found = yield from self.parse_until(
                            buf, _CDataToken, ']]>')
                        if not buf.starts_with(']]>'):
                            assert not found, found
                            assert not buf.get(), buf.get()
                            yield _BadlyFormedEndOfStreamEmptyTextToken
                            return
                        yield _CDataCloseTextToken
                    else:
                        # declaration
                        raise NotImplementedError(
                            'Declarations not implemented')
                else:
                    yield tokens.BadlyFormedLessThanToken
                    yield tokens.PCData('!')
            elif self.name_parser.matches_initial(ch):
                yield _StartOrEmptyTagOpenTextToken
                if not (yield from self.parse_name(buf, _TagNameToken)):
                    raise RuntimeError('Expected tag name')
                ws_found = yield from self.parse_space(
                    buf, _MarkupWhitespaceToken)
                ch = buf.get()
                while ws_found and self.name_parser.matches_initial(ch):
                    yield from self.parse_name(buf, _AttributeNameToken)
                    yield from self.parse_space(buf, _MarkupWhitespaceToken)
                    ch = buf.get()
                    if ch == '=':
                        yield _AttributeEqualsTextToken
                        buf.advance()
                        yield from self.parse_space(
                            buf, _MarkupWhitespaceToken)
                        ch = buf.get()
                        if not ch:
                            yield _BadlyFormedEndOfStreamEmptyTextToken
                            return
                        if ch in ('"', "'"):
                            if ch == '"':
                                yield _AttributeValueDoubleOpenTextToken
                            else:
                                yield _AttributeValueSingleOpenTextToken
                            buf.advance()
                            yield from self.parse_until(
                                buf, _AttributeValueToken, ch)
                            if not buf.starts_with(ch):
                                yield _BadlyFormedEndOfStreamEmptyTextToken
                                return
                            if ch == '"':
                                yield _AttributeValueDoubleCloseTextToken
                            else:
                                yield _AttributeValueSingleCloseTextToken
                        else:
                            # HTML fallback - need a parser to read un-quoted
                            # attribute
                            raise RuntimeError()
                        ws_found = yield from self.parse_space(
                            buf, _MarkupWhitespaceToken)
                        ch = buf.get()
                if not ch:
                    yield _BadlyFormedEndOfStreamEmptyTextToken
                    return
                elif ch == '>':
                    yield _StartTagCloseTextToken
                    buf.advance()
                elif ch == '/':
                    ch = buf.next()
                    if not ch:
                        yield tokens.BadlyFormedEndOfStream(
                            tokens.TextHolder('/'))
                        return
                    elif ch != '>':
                        raise RuntimeError('Expected />')
                    yield _EmptyTagCloseTextToken
                    buf.advance()
                else:
                    raise RuntimeError(
                        'Expected whitespace, >, or />, found %r' % ch)
            else:
                # < does not appear to be well-formed markup - treat it
                # as a content character
                yield tokens.BadlyFormedLessThanToken
            yield from self.parse_space(buf, _WhitespaceContentToken)
            yield from self.parse_until(buf, _PCDataToken, '<')
