class Buffer:

    """The Buffer class makes an iterable look like a single buffer."""

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
                    # Alternatively, we've processed the entire buffer, and we
                    # now have nothing left to process, in which case we
                    # propagate the exception.
                    if buf:
                        self._buf = buf
                        self._current = current
                        return -1
                    else:
                        # We really have reached the end
                        raise EOFError()
            self._buf = buf
            self._current = current
        assert self._buf
        return current

    def get(self):
        """Return the character at the current location."""
        current = self.ensure(1)
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
        :return: -1 if no match, else known number of characters after match
        """
        current = self.ensure(1)
        result = pat.match(self._buf, current)
        if result:
            self._start = current
            self._current = result.end()
            return len(self._buf) - self._current
        else:
            self._start = current
            return -1

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
