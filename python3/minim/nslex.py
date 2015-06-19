from minim import lex, tokens


class NamespaceOpen(tokens.Token):

    def __init__(self, namespace, prefix=''):
        super().__init__(literal='')
        self.namespace = namespace
        self.prefix = prefix


class TokenGenerator(lex.YieldBasedTokenGenerator):

    """A generator to add namespace tokens to a basic token generator.

    In order to put the namespace tokens before the tags specifying
    those tokens, this class must read the whole tag, including
    attributes.  It caches the sequence of tags, and then emits any
    NamespaceOpen tokens before the entire sequence.
    """

    def __init__(self, token_generator):
        self.token_generator = token_generator
        self.xmlns_name_limit = 512
        self.xmlns_url_limit = 2048

    @classmethod
    def from_strings(cls, string_iter):
        """Generates tokens from the supplied iterator."""
        return cls(lex.TokenGenerator.from_strings(string_iter))

    def create_generator(self):
        return self.insert_namespace_tokens(self.token_generator)

    def insert_namespace_tokens(self, token_generator):
        cached_tokens = []
        token_iter = iter(token_generator)
        for token_type in token_iter:
            if token_type.is_a(tokens.StartOrEmptyTagOpen):
                cached_tokens = [token_generator.get_token(token_type)]
                token_type = next(token_iter)
                while not token_type.is_a(tokens.StartOrEmptyTagClose):
                    token = token_generator.get_token(token_type)
                    if token_type.is_a(tokens.AttributeName):
                        name = token.literal
                        cached_tokens.append(token)
                        token_type = next(token_iter)
                        while token_type.is_a(tokens.AttributeName):
                            token = token_generator.get_token(token_type)
                            name += token.literal
                            if len(name) > self.xmlns_name_limit:
                                raise RuntimeError('name too long')
                            cached_tokens.append(token)
                            token_type = next(token_iter)
                        if name.startswith('xmlns'):
                            while token_type.is_a(tokens.MarkupWhitespace):
                                cached_tokens.append(
                                    token_generator.get_token(token_type))
                                token_type = next(token_iter)
                            if token_type.is_a(tokens.BadlyFormedEndOfStream):
                                break
                            assert token_type.is_a(
                                tokens.AttributeEquals), token_type
                            cached_tokens.append(
                                token_generator.get_token(token_type))
                            token_type = next(token_iter)
                            while token_type.is_a(tokens.MarkupWhitespace):
                                cached_tokens.append(
                                    token_generator.get_token(token_type))
                                token_type = next(token_iter)
                            if token_type.is_a(tokens.BadlyFormedEndOfStream):
                                break
                            assert token_type.is_a(
                                tokens.AttributeValueOpen), token_type
                            cached_tokens.append(
                                token_generator.get_token(token_type))
                            token_type = next(token_iter)
                            value = ''
                            while token_type.is_a(tokens.AttributeValue):
                                token = token_generator.get_token(token_type)
                                value += token.literal
                                if len(value) > self.xmlns_url_limit:
                                    raise RuntimeError('URL too long')
                                cached_tokens.append(token)
                                token_type = next(token_iter)
                            if token_type.is_a(tokens.BadlyFormedEndOfStream):
                                break
                            assert token_type.is_a(
                                tokens.AttributeValueClose), token_type
                            cached_tokens.append(
                                token_generator.get_token(token_type))
                            if name == 'xmlns':
                                prefix = ''
                            else:
                                assert name[5] == ':', name
                                prefix = name[6:]
                            namespace = value
                            result = yield NamespaceOpen
                            if result is not None:
                                yield NamespaceOpen(namespace, prefix)
                            token_type = next(token_iter)
                    else:
                        cached_tokens.append(token)
                        token_type = next(token_iter)
                yield from cached_tokens
            # Standard way to pass tokens through:
            result = yield token_type
            if result is not None:
                yield token_iter.send(result)
