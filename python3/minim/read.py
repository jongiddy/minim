from minim.lex import TokenGenerator


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
        token_generator = TokenGenerator.from_strings(string_iter)
        self.generator = iter(token_generator)
        self.get_token = token_generator.get_token

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.generator)
