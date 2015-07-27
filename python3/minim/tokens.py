
class EmptyTextHolderException(Exception):

    pass


class UndefinedValue:
    pass


Undefined = UndefinedValue()


class TextHolder:

    def __init__(
            self, encoded=Undefined, encoding=None, content=Undefined,
            is_initial=True, is_final=True):
        self.set(encoded, encoding, content, is_initial, is_final)

    def set(self, encoded=Undefined, encoding=None, content=Undefined,
            is_initial=True, is_final=True):
        self.encoded = encoded
        self.encoding = encoding
        self._content = content
        # If data is emitted in multiple sections, we mark the initial
        # and final blocks
        self.is_initial = is_initial
        self.is_final = is_final

    def literal(self):
        if self.encoded is Undefined:
            raise EmptyTextHolderException()
        if self.encoding is not None:
            self.encoded = self.encoded.decode(self.encoding)
            self.encoding = None
        return self.encoded

    def literal_bytes(self, encoding):
        """Return the literal bytes from the source.

        :param string encoding: Character encoding for returned literal.
        """
        if encoding == self.encoding:
            bytes = self.encoded
        else:
            bytes = self.literal().encode(encoding)
        return bytes

    def content(self):
        if self._content is Undefined:
            self._content = self.make_content()
        return self._content

    def make_content(self):
        return self.literal()


class Token:

    def __init__(self, text=None):
        self.is_token = True
        self.text = text

    def clone(self, text):
        if text is self.text:
            return self
        else:
            return self.__class__(text)

    @classmethod
    def is_a(cls, token):
        """Does this token match the token type.

        :param class token: the class for the desired token.
        """
        return issubclass(cls, token)


class WellFormed:
    pass


class Content(Token):
    pass


class CData(WellFormed, Content):
    pass


class PCData(WellFormed, Content):
    pass


class WhitespaceContent(PCData):

    """Whitespace that occurs after markup and before any non-space content.

    Separating this into a separate token allows higher-level parsers to
    quickly identify all-whitespace gaps between markup without having
    to scan content.
    """


# Non well-formed content is used to recover from invalid markup, which
# can be interpreted as badly-formatted content.  For example, any '<'
# which doesn't subsequently scan as valid markup is emitted as a
# literal '<' embedded in the content.
BadlyFormedAmpersandToken = Content(TextHolder(encoded='&', content='&'))
BadlyFormedLessThanToken = Content(TextHolder(encoded='<', content='<'))


class Markup(Token):
    pass


class MarkupStructure(WellFormed, Markup):
    pass


class MarkupName(WellFormed, Markup):
    pass


class MarkupData(WellFormed, Markup):
    pass


class MarkupWhitespace(MarkupStructure):
    pass


class TagName(MarkupName):
    pass


class AttributeName(MarkupName):
    pass


class AttributeValue(MarkupData):
    pass


class ProcessingInstructionTarget(MarkupName):
    pass


class ProcessingInstructionData(MarkupData):
    pass


class CommentData(MarkupData):
    pass


class StartOrEmptyTagOpen(MarkupStructure):

    def refine(self, close_tag_token):
        """Change an ambiguous tag into a specific tag."""
        if isinstance(close_tag_token, StartOrEmptyTagClose):
            tag_open_class = close_tag_token.get_tag_open_class()
            return tag_open_class(self.text)
        else:
            # e.g. BadlyFormedEOF
            return self


class StartTagOpen(StartOrEmptyTagOpen):

    def refine(self, close_tag_token):
        return self


class EmptyTagOpen(StartOrEmptyTagOpen):

    def refine(self, close_tag_token):
        return self


class EndTagOpen(MarkupStructure):
    pass


class AttributeEquals(MarkupStructure):
    pass


class AttributeValueOpen(MarkupStructure):
    pass


class AttributeValueDoubleOpen(AttributeValueOpen):
    pass


class AttributeValueSingleOpen(AttributeValueOpen):
    pass


class AttributeValueClose(MarkupStructure):
    pass


class AttributeValueDoubleClose(AttributeValueClose):
    pass


class AttributeValueSingleClose(AttributeValueClose):
    pass


class StartOrEmptyTagClose(MarkupStructure):

    def get_tag_open_class(self):
        raise NotImplementedError()


class StartTagClose(StartOrEmptyTagClose):

    def get_tag_open_class(self):
        return StartTagOpen


class EmptyTagClose(StartOrEmptyTagClose):

    def get_tag_open_class(self):
        return EmptyTagOpen


class EndTagClose(MarkupStructure):
    pass


class ProcessingInstructionOpen(MarkupStructure):
    pass


class ProcessingInstructionClose(MarkupStructure):
    pass


class CommentOpen(MarkupStructure):
    pass


class CommentClose(MarkupStructure):
    pass


class CDataOpen(MarkupStructure):
    pass


class CDataClose(MarkupStructure):
    pass


class BadlyFormedEndOfStream(Markup):

    """Class to represent markup that is not terminated properly."""
