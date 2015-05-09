class Buffer:

    """The Buffer class makes an iterable look like a single buffer."""

    def __init__(self, string_iter):
        self.iter = iter(string_iter)
        self.buf = next(self.iter)
        self.start = 0
        self.current = 0

    def ensure(self, n=1):
        """Ensure that a minimum number of characters are available.

        The buffer may be changed by this operation.

        :param int n: The minimum number of characters wanted.
        :return int: The current position in the buffer, or -1 if EOF
            was reached before reading ``n`` characters
        :raise: EOFError if the buffer is empty and the EOF is reached
        """
        buf = self.buf
        current = self.current
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
                    buf += next(self.iter)
                except StopIteration:
                    # If we get StopIteration, we may have some stuff left
                    # in buf, which we need to process first.
                    # Alternatively, we've processed the entire buffer, and we
                    # now have nothing left to process, in which case we
                    # propagate the exception.
                    if buf:
                        self.buf = buf
                        self.current = current
                        return -1
                    else:
                        # We really have reached the end
                        raise EOFError()
            self.buf = buf
            self.current = current
        assert self.buf
        return current

    def get(self):
        """Return the character at the current location."""
        current = self.ensure(1)
        return self.buf[current]

    def advance(self, n=1):
        """Advance the current location."""
        self.current += n

    def next(self):
        """Move to the next character, and return it."""
        self.advance()
        return self.get()

    def extract(self):
        buf = self.buf
        start = self.start
        current = self.current
        if start == 0 and current == len(buf):
            return buf
        else:
            return buf[start:current]

    def matching(self, pat):
        """
        :return: -1 if no match, else known number of characters after match
        """
        current = self.ensure(1)
        result = pat.match(self.buf, current)
        if result:
            self.start = current
            self.current = result.end()
            return len(self.buf) - self.current
        else:
            self.start = current
            return -1

    def match_to_sentinel(self, sentinel):
        """Find the location of a string in the current buffer.

        :return int: the index at which the sentinel was found, or -1 if
            the sentinel was not found."""
        start = self.ensure(len(sentinel))
        buf = self.buf
        if start < 0:
            # EOF and remaining characters < sentinel length
            # -> sentinel can never appear
            self.start = self.current
            self.current = len(buf)
            return -1
        self.start = start
        loc = buf.find(sentinel, start)
        if loc < 0:
            # If sentinel is not found, check whether the last characters
            # of the buffer may be a prefix of the sentinel, and exclude them
            # from the match.
            if buf[-1] in sentinel:
                sentinel = sentinel[:-1]
                while not buf.endswith(sentinel):
                    sentinel = sentinel[:-1]
                self.current = len(buf) - len(sentinel)
            else:
                self.current = len(buf)
            return -1
        else:
            self.current = loc
            return loc - start

    def starts_with(self, s):
        """Test whether the current buffer starts with a string."""
        start = self.ensure(len(s))
        if start < 0 or not self.buf.startswith(s, start):
            return False
        else:
            self.start = start
            self.current = start + len(s)
            return True
