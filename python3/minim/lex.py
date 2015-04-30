from minim.tokens import Content, Token


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
                yield response(s)
