from minim import lex, tokens


class NamespaceOpen(tokens.Token):

    def __init__(self, namespace, prefix=''):
        self.namespace = namespace
        self.prefix = prefix

    def literal(self):
        return ''


class GeneratesNamespaceTokens(lex.GeneratesTokens):
    pass


class TokenGenerator(GeneratesNamespaceTokens):

    """A generator to add namespace tokens to a basic token generator.

    In order to put the namespace tokens before the tags specifying
    those tokens, this class must read the whole tag, including
    attributes.  It caches the sequence of tags, and then emits any
    NamespaceOpen tokens before the entire sequence.
    """

    def __init__(self, token_iter):
        self.token_iter = token_iter
        self.xmlns_name_limit = 512
        self.xmlns_url_limit = 2048

    @classmethod
    def from_token_generator(cls, token_generator):
        assert isinstance(token_generator, lex.GeneratesTokens)
        return cls(iter(token_generator))

    def __iter__(self):
        token_iter = self.token_iter
        cached_tokens = []
        for token_type in token_iter:
            if token_type.is_a(tokens.StartOrEmptyTagOpen):
                cached_tokens = [token_iter.get_token(token_type)]
                token_type = next(token_iter)
                while not token_type.is_a(tokens.StartOrEmptyTagClose):
                    if token_type.is_a(tokens.AttributeName):
                        token = token_iter.get_token(token_type)
                        name = token.literal
                        cached_tokens.append(token)
                        token_type = next(token_iter)
                        while token_type.is_a(tokens.AttributeName):
                            token = token_iter.get_token(token_type)
                            name += token.literal
                            if len(name) > self.xmlns_name_limit:
                                raise RuntimeError('name too long')
                            cached_tokens.append(token)
                            token_type = next(token_iter)
                        if name.startswith('xmlns'):
                            while token_type.is_a(tokens.MarkupWhitespace):
                                token = token_iter.get_token(token_type)
                                cached_tokens.append(token)
                                token_type = next(token_iter)
                            assert token_type.is_a(
                                tokens.AttributeEquals), token_type
                            cached_tokens.append(token)
                            token_type = next(token_iter)
                            while token_type.is_a(tokens.MarkupWhitespace):
                                token = token_iter.get_token(token_type)
                                cached_tokens.append(token)
                                token_type = next(token_iter)
                            assert token_type.is_a(
                                tokens.AttributeValueOpen), token_type
                            cached_tokens.append(token)
                            token_type = next(token_iter)
                            value = ''
                            while token_type.is_a(tokens.AttributeValue):
                                token = token_iter.get_token(token_type)
                                value += token.literal
                                if len(value) > self.xmlns_url_limit:
                                    raise RuntimeError('URL too long')
                                cached_tokens.append(token)
                                token_type = next(token_iter)
                            assert token_type.is_a(
                                tokens.AttributeValueClose), token_type
                            cached_tokens.append(token)
                            token_type = next(token_iter)
                        if name == 'xmlns':
                            prefix = ''
                        else:
                            assert name[5] == ':', name
                            prefix = name[6:]
                        namespace = value
                        result = yield NamespaceOpen
                        if result is not None:
                            yield NamespaceOpen(namespace, prefix)
                    else:
                        cached_tokens.append(token)
                        token_type = next(token_iter)
                yield from cached_tokens
            # Standard way to pass tokens through:
            result = yield token_type
            if result is not None:
                yield token_iter.send(result)
