
class Singleton:
    pass


Undefined = Singleton()


class Token:

    is_token = False       # Is this a token_type (class) or a token (instance)
    is_content = False     # Is this content
    is_markup = False      # or is it markup
    is_control = False     # small number of non-markup, non-content tokens
    # If markup is not valid, we treat it as content, but set
    # is_well_formed to False
    is_well_formed = True  # Is this content well-formed
    # Markup sub-classes
    is_structure = False   # Is this markup structural (<, etc.)
    is_name = False        # Is this markup a name?
    is_data = False        # Is this markup data?
    # If data is emitted in multiple sections, we mark the initial and
    # final blocks
    is_initial = True      # Is this an initial section?
    is_final = True        # Is this a final section?

    def __init__(
            self, literal=None, encoding=None, is_initial=True, is_final=True):
        self.is_token = True
        self._literal = literal
        self._encoding = encoding
        self.is_initial = is_initial
        self.is_final = is_final

    def set(self, **kw):
        self._literal = kw.get('literal')
        self._encoding = kw.get('encoding')
        self.is_initial = kw.get('is_initial', True)
        self.is_final = kw.get('is_final', True)

    @property
    def literal(self):
        if self._encoding is not None:
            self._literal = self._literal.decode(self._encoding)
            self._encoding = None
        return self._literal

    def literal_bytes(self, encoding):
        """Return the literal bytes from the source.

        :param string encoding: Character encoding for returned literal.
        """
        if encoding == self._encoding:
            bytes = self._literal
        else:
            bytes = self.literal.encode(encoding)
        return bytes


class Content(Token):

    is_content = True

    def __init__(self, literal=None, encoding=None, content=Undefined, **kw):
        super().__init__(literal, encoding, **kw)
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

        :param string encoding: Character encoding for returned literal.
        """
        return cls.literal.encode(encoding)


class MarkupWhitespace(Markup):
    is_structure = True


class StartOrEmptyTagOpenToken(SingletonMarkup):
    literal = '<'


class EndTagOpenToken(SingletonMarkup):
    literal = '</'


class TagName(Markup):
    is_name = True


class AttributeName(Markup):
    is_name = True


class AttributeEqualsToken(SingletonMarkup):
    literal = '='


class AttributeValueOpen(SingletonMarkup):
    pass


class AttributeValueDoubleOpenToken(AttributeValueOpen):
    literal = '"'


class AttributeValueSingleOpenToken(AttributeValueOpen):
    literal = "'"


class AttributeValue(Markup):
    is_data = True


class AttributeValueClose(SingletonMarkup):
    pass


class AttributeValueDoubleCloseToken(AttributeValueClose):
    literal = '"'


class AttributeValueSingleCloseToken(AttributeValueClose):
    literal = "'"


class StartTagCloseToken(SingletonMarkup):
    literal = '>'


class EmptyTagCloseToken(SingletonMarkup):
    literal = '/>'


class EndTagCloseToken(SingletonMarkup):
    literal = '>'


class ProcessingInstructionOpenToken(SingletonMarkup):
    literal = '<?'


class ProcessingInstructionTarget(Markup):
    is_name = True


class ProcessingInstructionData(Markup):
    is_data = True


class ProcessingInstructionCloseToken(SingletonMarkup):
    literal = '?>'


class CommentOpenToken(SingletonMarkup):
    literal = '<!--'


class CommentData(Markup):
    is_data = True


class CommentCloseToken(SingletonMarkup):
    literal = '-->'


class CDataOpenToken(SingletonMarkup):
    literal = '<[CDATA['


class CData(Content):
    pass


class CDataCloseToken(SingletonMarkup):
    literal = ']]>'


class WhitespaceContent(Content):

    """Whitespace that occurs after markup and before any non-space content.

    Separating this into a separate token allows higher-level parsers to
    quickly identify all-whitespace gaps between markup without having
    to scan content.
    """


class PCData(Content):
    pass


class SingletonContent(PCData):

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

        :param string encoding: Character encoding for returned literal.
        """
        return cls.literal.encode(encoding)


class BadlyFormedLessThanToken(SingletonContent):
    is_well_formed = False
    literal = '<'
    content = '<'


class SingletonControl(Token):

    is_token = True
    is_control = True

    def __init__(self, *args):
        raise NotImplementedError('cannot instantiate SingletonControl class')

    def set(self, **kw):
        raise ImmutableTokenException('Immutable token cannot be modified')

    @classmethod
    def emit(cls):
        yield cls

    @classmethod
    def literal_bytes(cls, encoding):
        """Return the literal bytes from the source.

        :param string encoding: Character encoding for returned literal.
        """
        return cls.literal.encode(encoding)


class BadlyFormedEndOfStreamToken(SingletonControl):
    is_well_formed = False
    literal = ''
    content = ''
