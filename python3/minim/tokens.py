
class ImmutableTokenException(Exception):

    pass


class Singleton:
    pass


Undefined = Singleton()


class Token:

    is_token = False       # Is this a token_type (class) or a token (instance)
    is_content = False     # Is this content
    is_markup = False      # or is it markup
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
            self, literal='', encoding=None, is_initial=True, is_final=True):
        self.is_token = True
        self._literal = literal
        self._encoding = encoding
        self.is_initial = is_initial
        self.is_final = is_final

    @classmethod
    def is_a(cls, token_type):
        """Does this token match the token type.

        :param class token_type: the class for the desired token.
        """
        # XXX - won't work for submitted tokens (2nd arg to get_token)
        return issubclass(cls, token_type)

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

    def __init__(self, literal='', encoding=None, content=Undefined, **kw):
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


class CData(Content):
    pass


class PCData(Content):
    pass


class WhitespaceContent(Content):

    """Whitespace that occurs after markup and before any non-space content.

    Separating this into a separate token allows higher-level parsers to
    quickly identify all-whitespace gaps between markup without having
    to scan content.
    """


class BadlyFormedContent(Content):

    """A token that always has the same representation.

    In this case, the class can represent the token.

    BadlyFormedContent is used to recover from invalid markup, which can
    be interpreted as badly-formatted content.  For example, any '<'
    which doesn't subsequently scan as valid markup is emitted as a
    literal '<' embedded in the content.
    """

    is_well_formed = False

    def set(self, **kw):
        raise ImmutableTokenException('Immutable token cannot be modified')


BadlyFormedAmpersandToken = BadlyFormedContent(literal='&', content='&')
BadlyFormedLessThanToken = BadlyFormedContent(literal='<', content='<')


class Markup(Token):

    is_markup = True


class MarkupWhitespace(Markup):
    is_structure = True


class TagName(Markup):
    is_name = True


class AttributeName(Markup):
    is_name = True


class AttributeValue(Markup):
    is_data = True


class ProcessingInstructionTarget(Markup):
    is_name = True


class ProcessingInstructionData(Markup):
    is_data = True


class CommentData(Markup):
    is_data = True


class SingletonMarkup(Markup):

    """A token that always has the same representation."""

    is_structure = True

    def set(self, **kw):
        raise ImmutableTokenException('Immutable token cannot be modified')


class StartOrEmptyTagOpen(SingletonMarkup):
    literal = '<'

StartOrEmptyTagOpenToken = StartOrEmptyTagOpen()


class EndTagOpen(SingletonMarkup):
    literal = '</'

EndTagOpenToken = EndTagOpen()


class AttributeEquals(SingletonMarkup):
    literal = '='

AttributeEqualsToken = AttributeEquals()


class AttributeValueOpen(SingletonMarkup):
    pass


class AttributeValueDoubleOpen(AttributeValueOpen):
    literal = '"'

AttributeValueDoubleOpenToken = AttributeValueDoubleOpen()


class AttributeValueSingleOpen(AttributeValueOpen):
    literal = "'"

AttributeValueSingleOpenToken = AttributeValueSingleOpen()


class AttributeValueClose(SingletonMarkup):
    pass


class AttributeValueDoubleClose(AttributeValueClose):
    literal = '"'

AttributeValueDoubleCloseToken = AttributeValueDoubleClose()


class AttributeValueSingleClose(AttributeValueClose):
    literal = "'"

AttributeValueSingleCloseToken = AttributeValueSingleClose()


class StartOrEmptyTagClose(SingletonMarkup):
    pass


class StartTagClose(StartOrEmptyTagClose):
    literal = '>'

StartTagCloseToken = StartTagClose()


class EmptyTagClose(StartOrEmptyTagClose):
    literal = '/>'

EmptyTagCloseToken = EmptyTagClose()


class EndTagClose(SingletonMarkup):
    literal = '>'

EndTagCloseToken = EndTagClose()


class ProcessingInstructionOpen(SingletonMarkup):
    literal = '<?'

ProcessingInstructionOpenToken = ProcessingInstructionOpen()


class ProcessingInstructionClose(SingletonMarkup):
    literal = '?>'

ProcessingInstructionCloseToken = ProcessingInstructionClose()


class CommentOpen(SingletonMarkup):
    literal = '<!--'

CommentOpenToken = CommentOpen()


class CommentClose(SingletonMarkup):
    literal = '-->'

CommentCloseToken = CommentClose()


class CDataOpen(SingletonMarkup):
    literal = '<![CDATA['

CDataOpenToken = CDataOpen()


class CDataClose(SingletonMarkup):
    literal = ']]>'

CDataCloseToken = CDataClose()


class BadlyFormedEndOfStream(Markup):

    """Class to represent markup that is not terminated properly."""
    is_well_formed = False
