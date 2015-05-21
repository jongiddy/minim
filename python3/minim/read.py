from minim.lex import token_type_generator


def TokenReader(string_iter):
    reader = Reader(string_iter)
    for token_type in reader:
        yield reader.get_token(token_type)


class Reader:

    """Create an iterator that returns a sequence of token types.

    A token type is a pre-allocated object that can be interrogated to
    determine the type of the current token in the input stream.  If the
    token is of interest to the token processor, it can then retrieve
    an actual token, but this may involve memory allocation operations
    (to create the token and also to slice the value out of the input
    stream).
    """

    def __init__(self, string_iter):
        self.generator = token_type_generator(string_iter)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.generator)

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
            if token is None:
                return self.generator.send(token_type)
            else:
                return self.generator.send(token)
