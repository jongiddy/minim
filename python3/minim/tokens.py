
class Singleton:
    pass


Undefined = Singleton()


class Token:

    is_token = False      # Is this a token_type (class) or a token (instance)
    is_content = False    # Is this content
    is_markup = False     # or is it markup
    is_invalid = False    # Is this content that has not been escaped correctly
    is_structure = False  # Is this markup structural (<, etc.)
    is_name = False       # Is this markup a name?
    is_data = False       # Is this markup data?

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
    is_structure = True

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


class Whitespace(Markup):
    is_structure = True


class StartOrEmptyTagOpenSingleton(SingletonMarkup):
    literal = '<'


class EndTagOpenSingleton(SingletonMarkup):
    literal = '</'


class TagName(Markup):
    is_name = True


class AttributeName(Markup):
    is_name = True


class AttributeEqualsSingleton(SingletonMarkup):
    literal = '='


class AttributeValueOpen(SingletonMarkup):
    pass


class AttributeValueDoubleOpenSingleton(AttributeValueOpen):
    literal = '"'


class AttributeValueSingleOpenSingleton(AttributeValueOpen):
    literal = "'"


class AttributeValue(Markup):
    is_data = True


class AttributeValueClose(SingletonMarkup):
    pass


class AttributeValueDoubleCloseSingleton(AttributeValueClose):
    literal = '"'


class AttributeValueSingleCloseSingleton(AttributeValueClose):
    literal = "'"


class StartTagCloseSingleton(SingletonMarkup):
    literal = '>'


class EmptyTagCloseSingleton(SingletonMarkup):
    literal = '/>'


class EndTagCloseSingleton(SingletonMarkup):
    literal = '>'


class ProcessingInstructionOpenSingleton(SingletonMarkup):
    literal = '<?'


class ProcessingInstructionTarget(Markup):
    is_name = True


class ProcessingInstructionData(Markup):
    is_data = True


class ProcessingInstructionCloseSingleton(SingletonMarkup):
    literal = '?>'


class CommentOpenSingleton(SingletonMarkup):
    literal = '<!--'


class CommentData(Markup):
    is_data = True


class CommentCloseSingleton(SingletonMarkup):
    literal = '-->'


class CDataOpenSingleton(SingletonMarkup):
    literal = '<[CDATA['


class CData(Content):
    pass


class CDataCloseSingleton(SingletonMarkup):
    literal = ']]>'


class LeadingWhitespace(Content):

    """Whitespace that occurs after markup and before any non-space content.

    Separating this into a separate token allows higher-level parsers to
    quickly identify all-whitespace gaps between markup without having
    to scan content.
    """


class PCData(Content):
    pass


class SingletonContent(Content):

    """A token that always has the same representation.

    In this case, the class can represent the token.

    SingletonContent is used to recover from invalid markup, which is
    interpreted as badly-formatted content.  For example, any '<' which
    doesn't subsequently scan as valid markup is emitted as a literal
    '<' embedded in the content (which should have been escaped)."""

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


class LiteralLessThanContentSingleton(SingletonContent):
    is_invalid = True
    literal = '<'


class LiteralExclamationMarkSingleton(SingletonContent):
    literal = '!'


class LiteralExclamationMarkDashSingleton(SingletonContent):
    literal = '!-'


