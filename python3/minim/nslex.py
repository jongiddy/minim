from minim import lex, tokens

empty_text = tokens.TextHolder('')


class NamespaceIdentifier(tokens.WellFormed, tokens.Token):
    pass


class NamespacePrefix(NamespaceIdentifier):
    pass


class NamespaceDefault(NamespaceIdentifier):
    pass


class NamespaceUri(tokens.WellFormed, tokens.Token):
    pass


_NamespacePrefixToken = NamespacePrefix()
_NamespaceDefaultTextToken = NamespaceDefault(tokens.TextHolder(''))
_NamespaceUriToken = NamespaceUri()


class NamespaceTokenScanner(lex.SendBasedTokenScanner):

    """A generator to add namespace tokens to a basic token generator.

    In order to put the namespace tokens before the tags specifying
    those tokens, this class must read the whole tag, including
    attributes.  It caches the sequence of tags, and then emits any
    NamespaceOpen tokens before the entire sequence.
    """

    def __init__(self, token_generator):
        super().__init__()
        self.token_generator = token_generator
        self.xmlns_name_limit = 512
        self.xmlns_url_limit = 2048

    @classmethod
    def from_strings(cls, string_iter):
        """Generates tokens from the supplied iterator."""
        return cls(lex.TokenScanner.from_strings(string_iter))

    def create_generator(self):
        return self.insert_namespace_tokens(self.token_generator)

    def insert_namespace_tokens(self, token_stream):
        cached_tokens = []
        for token in token_stream:
            if isinstance(token, tokens.StartOrEmptyTagOpen):
                cached_tokens = [token.clone(token_stream.get_text(token))]
                token = token_stream.next()
                while not isinstance(token, tokens.StartOrEmptyTagClose):
                    if isinstance(token, tokens.AttributeName):
                        text = token_stream.get_text(token)
                        name = text.literal()
                        cached_tokens.append(token.clone(text))
                        token = token_stream.next()
                        while isinstance(token, tokens.AttributeName):
                            text = token_stream.get_text(token)
                            name += text.literal()
                            if len(name) > self.xmlns_name_limit:
                                raise RuntimeError('name too long')
                            cached_tokens.append(token.clone(text))
                            token = token_stream.next()
                        if name.startswith('xmlns'):
                            while isinstance(token, tokens.MarkupWhitespace):
                                cached_tokens.append(
                                    token.clone(token_stream.get_text(token)))
                                token = token_stream.next()
                            if isinstance(
                                    token, tokens.BadlyFormedEndOfStream):
                                break
                            assert isinstance(
                                token, tokens.AttributeEquals), token
                            cached_tokens.append(
                                token.clone(token_stream.get_text(token)))
                            token = token_stream.next()
                            while isinstance(token, tokens.MarkupWhitespace):
                                cached_tokens.append(
                                    token.clone(token_stream.get_text(token)))
                                token = token_stream.next()
                            if isinstance(
                                    token, tokens.BadlyFormedEndOfStream):
                                break
                            assert isinstance(
                                token, tokens.AttributeValueOpen), token
                            cached_tokens.append(
                                token.clone(token_stream.get_text(token)))
                            token = token_stream.next()
                            value = ''
                            while isinstance(token, tokens.AttributeValue):
                                text = token_stream.get_text(token)
                                value += text.literal()
                                if len(value) > self.xmlns_url_limit:
                                    raise RuntimeError('URL too long')
                                cached_tokens.append(token.clone(text))
                                token = token_stream.next()
                            if isinstance(
                                    token, tokens.BadlyFormedEndOfStream):
                                break
                            assert isinstance(
                                token, tokens.AttributeValueClose), token
                            cached_tokens.append(
                                token.clone(token_stream.get_text(token)))
                            if name == 'xmlns':
                                yield _NamespaceDefaultTextToken
                            else:
                                assert name[5] == ':', name
                                text = yield _NamespacePrefixToken
                                if text is not None:
                                    prefix = name[6:]
                                    text.set('', content=prefix)
                                    yield text
                            namespace = value
                            text = yield _NamespaceUriToken
                            if text is not None:
                                text.set('', content=namespace)
                                yield text
                            token = token_stream.next()
                    else:
                        cached_tokens.append(
                            token.clone(token_stream.get_text(token)))
                        token = token_stream.next()
                yield from cached_tokens
            # Standard way to pass tokens through:
            text = yield token
            if text is not None:
                yield token_stream.get_text(token, text)
