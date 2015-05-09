
class Singleton:
    pass


Undefined = Singleton()


class Token:

    is_token = False      # Is this a token_type (class) or a token (instance)
    is_content = False    # Is this content
    is_markup = False     # or is it markup

    def __init__(self, literal=None, encoding=None):
        self.is_token = True
        self._literal = literal
        self._encoding = encoding

    def set(self, **kw):
        self._literal = kw.get('literal')
        self._encoding = kw.get('encoding')

    @property
    def literal(self):
        if self._encoding is not None:
            self._literal = self._literal.decode(self._encoding)
            self._encoding = None
        return self._literal

    def literal_bytes(self, encoding):
        """Return the literal bytes from the source.

        :param string encoding: Character encoding for returned
            literal."""
        if encoding == self._encoding:
            bytes = self._literal
        else:
            bytes = self.literal.encode(encoding)
        return bytes


class Content(Token):

    is_content = True

    def __init__(self, literal=None, encoding=None, content=Undefined):
        super().__init__(literal, encoding)
        self._content = content

    def set(self, **kw):
        super().set(**kw)
        self._content = kw.get('content', Undefined)

    @property
    def content(self):
        content = self._content
        if content is Undefined:
            content = self.literal
        return content


class Markup(Token):

    is_markup = True


class ImmutableTokenException(Exception):

    pass


class SingletonMarkup(Markup):

    """A token that always has the same representation.

    In this case, the class can represent the token."""

    is_token = True

    def __init__(self, *args):
        raise NotImplementedError('cannot instantiate SingletonMarkup class')

    def set(self, **kw):
        raise ImmutableTokenException('Immutable token cannot be modified')

    @classmethod
    def emit(cls):
        yield cls

    @classmethod
    def literal_bytes(cls, encoding):
        """Return the literal bytes from the source.

        :param string encoding: Character encoding for returned
            literal."""
        return cls.literal.encode(encoding)


class EndTagOpenSingleton(SingletonMarkup):
    literal = '</'


class EndTagCloseSingleton(SingletonMarkup):
    literal = '>'


class ProcessingInstructionOpenSingleton(SingletonMarkup):
    literal = '<?'


class ProcessingInstructionCloseSingleton(SingletonMarkup):
    literal = '?>'
