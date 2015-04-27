
class Singleton:
    pass


Undefined = Singleton()


class Token:

    is_token = False      # Is this a token_type (class) or a token (instance)
    is_content = False    # Is this content
    is_markup = False     # or is it markup

    def __init__(self):
        self.is_token = True


class Content(Token):

    is_content = True

    def __init__(self, literal):
        self._literal = literal
        self._content = Undefined

    @property
    def literal(self, encoding=None):
        if encoding is None:
            return self._literal
        else:
            return self._literal.encode(encoding)

    @property
    def content(self):
        content = self._content
        if content is Undefined:
            content = self._literal
        return content


class Markup(Token):

    is_markup = True
