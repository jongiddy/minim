class IterableAsSequence:

    """Make an iterable of character sequences look like a single sequence."""

    def __init__(self, string_iter):
        self._iter = iter(string_iter)
        self._buf = None
        self._start = 0
        self._current = 0

    def ensure(self, n=1):
        """Ensure that a minimum number of characters are available.

        The buffer may be changed by this operation.

        :param int n: The minimum number of characters wanted.
        :return int: The current position in the buffer, or -1 if EOF
            was reached before reading ``n`` characters
        :raise: EOFError if the buffer is empty and the EOF is reached
        """
        buf = self._buf
        if buf is None:
            buf = self._buf = next(self._iter)
        current = self._current
        if len(buf) - current < n:
            if current > 0:
                # This may be called before we have reached the end of
                # the current buffer.  So trim the processed data up to
                # ``current``, and start with the small rump.
                buf = buf[current:]
                current = 0
            # Read more data until at least ``n`` bytes are available.
            while len(buf) < n:
                try:
                    buf += next(self._iter)
                except StopIteration:
                    # If we get StopIteration, we may have some stuff left
                    # in buf, which we need to process first.
                    self._buf = buf
                    self._current = current
                    return -1
            self._buf = buf
            self._current = current
        assert self._buf
        return current

    def get(self):
        """Return the character at the current location."""
        current = self.ensure(1)
        if current < 0:
            raise EOFError()
        return self._buf[current]

    def advance(self, n=1):
        """Advance the current location."""
        self._current += n

    def next(self):
        """Move to the next character, and return it."""
        self.advance()
        return self.get()

    def extract(self):
        buf = self._buf
        start = self._start
        current = self._current
        if start == 0 and current == len(buf):
            return buf
        else:
            return buf[start:current]

    def matching(self, pat):
        """
        :return:
            +n there is a match of length n,
                and subsequent call may match more;
            -n there is a match of length n,
                and subsequent call will not match;
            0 there is no match, and ``extract`` will return an empty string.
            For non-zero return, ``extract`` will return the matched string.
        """
        start = self.ensure(1)
        if start < 0:
            # at EOF - we don't raise EOFError, as calling code may need
            # to yield an is_final token
            self._start = self._current
            return 0
        result = pat.match(self._buf, start)
        if result:
            self._start = start
            self._current = current = result.end()
            if current == len(self._buf):
                return current - start
            else:
                return start - current
        else:
            self._start = self._current
            return 0

    def match_to_sentinel(self, sentinel):
        """Find the location of a string in the current buffer.

        :return int: the index at which the sentinel was found, or -1 if
            the sentinel was not found."""
        start = self.ensure(len(sentinel))
        buf = self._buf
        if start < 0:
            # EOF and remaining characters < sentinel length
            # -> sentinel can never appear
            self._start = self._current
            self._current = len(buf)
            return -1
        self._start = start
        loc = buf.find(sentinel, start)
        if loc < 0:
            # If sentinel is not found, check whether the last characters
            # of the buffer may be a prefix of the sentinel, and exclude them
            # from the match.
            if buf[-1] in sentinel:
                sentinel = sentinel[:-1]
                while not buf.endswith(sentinel):
                    sentinel = sentinel[:-1]
                self._current = len(buf) - len(sentinel)
            else:
                self._current = len(buf)
            return -1
        else:
            self._current = loc
            return loc - start

    def starts_with(self, s):
        """Test whether the current buffer starts with a string."""
        start = self.ensure(len(s))
        if start < 0 or not self._buf.startswith(s, start):
            return False
        else:
            self._start = start
            self._current = start + len(s)
            return True
