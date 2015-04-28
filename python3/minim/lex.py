from minim.tokens import Content, Token


def tokens(string_iter):
    for s in string_iter:
        yield Content(s)


def token_type_generator(string_iter):
    for s in string_iter:
        response = yield Content
        if response is not None:
            # response should either be a token_type (the Content class)
            # or an existing Token.
            if response.is_token:
                # response is a token: set contents of this token and
                # return
                assert isinstance(response, Token)
                response.set(literal=s)
                yield response
            else:
                assert issubclass(response, Token)
                # response is a token_type, instantiate it and set contents
                yield Content(s)


class token_types:

    def __init__(self, string_iter):
        self.generator = token_type_generator(string_iter)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.generator)

    def get_token(self, token_type):
        return self.generator.send(token_type)

    def set_token(self, token):
        # This works as long as we don't really care what is being sent
        # to the generator
        return self.generator.send(token)
