from minim.tokens import Content


def tokens(string_iter):
    for s in string_iter:
        yield Content(s)


def token_type_generator(string_iter):
    for s in string_iter:
        response = yield Content
        if response is not None:
            # response should either be a token_type (the Content class)
            # or an existing Token.  Currently we always just return a
            # new instance.
            if response.is_token:
                yield Content(s)
            else:
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
        return self.get_token(token)
