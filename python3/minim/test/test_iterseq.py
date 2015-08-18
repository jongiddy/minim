import re
import tempfile
import unittest

from minim import iterseq


class IterableAsSequenceInitTest(unittest.TestCase):

    def test_list_is_ok(self):
        buf = iterseq.IterableAsSequence(['Hello, ', 'World!'])
        self.assertEqual(buf.get(), 'H')

    def test_bytes_are_ok(self):
        buf = iterseq.IterableAsSequence([b'Hello', b'World!'])
        self.assertEqual(buf.get(), b'H'[0])

    def test_non_iterable_fails(self):
        with self.assertRaises(TypeError):
            iterseq.IterableAsSequence(5)

    def test_file_is_ok(self):
        with tempfile.TemporaryFile('w+t') as f:
            f.write('Hello, World!\n')
            f.seek(0)
            buf = iterseq.IterableAsSequence(f)
            self.assertEqual(buf.get(), 'H')


class EmptyIterableAsSequenceTest(unittest.TestCase):

    """Test empty iterable in constructor.

    For an empty sequence, the type of the buffer is unknown, so calls
    that normally return an empty character sequence on EOF return None.
    """

    def setUp(self):
        self.buf = iterseq.IterableAsSequence([])

    def test_get(self):
        self.assertIs(self.buf.get(), None)

    def test_matching(self):
        self.assertEqual(self.buf.matching(re.compile('d')), 0)
        self.assertIs(self.buf.extract(), None)

    def test_match_to_sentinel(self):
        self.assertEqual(self.buf.match_to_sentinel('foo'), 0)
        self.assertIs(self.buf.extract(), None)

    def test_starts_with(self):
        self.assertFalse(self.buf.starts_with('foo'))
        self.assertIs(self.buf.extract(), None)


class IterableAsSequenceTest(unittest.TestCase):

    def setUp(self):
        self.s = ['Hello, ', 'World!']
        self.buf = iterseq.IterableAsSequence(self.s)

    def test_pop(self):
        s = self.buf.get()
        ch = self.buf.next()
        while ch:
            s += ch
            ch = self.buf.next()
        self.assertEqual(s, ''.join(self.s))

    def test_matching(self):
        pat = re.compile(r'[A-Za-z]+')
        result = self.buf.matching(pat)
        self.assertLess(result, 0)
        length = -result
        self.assertEqual(self.buf.extract(), self.s[0][:length])
        self.assertEqual(self.buf.get(), ',')

    def test_matching_over_next(self):
        pat = re.compile(r'[A-Za-z ,]+')
        result = self.buf.matching(pat)
        self.assertGreater(result, 0)
        self.assertEqual(self.buf.extract(), self.s[0])
        self.assertEqual(self.buf.get(), self.s[1][:1])
        result = self.buf.matching(pat)
        self.assertLess(result, 0)
        length = -result
        self.assertEqual(self.buf.extract(), self.s[1][:length])
        self.assertEqual(self.buf.get(), '!')

    def test_matching_no_match(self):
        pat = re.compile(r'[ ]+')
        self.assertEqual(self.buf.matching(pat), 0)
        self.assertEqual(self.buf.get(), 'H')

    def test_matching_to_eof(self):
        pat = re.compile(r'[A-Za-z ,!]+')
        self.assertGreater(self.buf.matching(pat), 0)
        self.assertEqual(self.buf.extract(), self.s[0])
        self.assertGreater(self.buf.matching(pat), 0)
        self.assertEqual(self.buf.extract(), self.s[1])
        self.assertEqual(self.buf.matching(pat), 0)

    def test_match_to_sentinel(self):
        result = self.buf.match_to_sentinel(',')
        self.assertLess(result, 0)
        length = -result
        self.assertEqual(self.buf.extract(), self.s[0][:length])
        self.assertEqual(self.buf.get(), ',')

    def test_match_to_sentinel_over_next(self):
        length = self.buf.match_to_sentinel(', W')
        self.assertGreater(length, 0)
        self.assertEqual(self.buf.extract(), self.s[0][:-2])
        self.assertEqual(self.buf.get(), self.s[0][-2:-1])
        result = self.buf.match_to_sentinel(', W')
        self.assertEqual(result, 0)
        self.assertEqual(self.buf.extract(), '')
        self.assertEqual(self.buf.get(), ',')

    def test_match_to_sentinel_after_next(self):
        length = self.buf.match_to_sentinel('!')
        self.assertGreater(length, 0)
        self.assertEqual(self.buf.extract(), self.s[0])
        result = self.buf.match_to_sentinel('!')
        self.assertLess(result, 0)
        length = -result
        self.assertEqual(self.buf.extract(), self.s[1][:length])
        self.assertEqual(self.buf.get(), '!')

    def test_match_to_sentinel_no_match(self):
        length = self.buf.match_to_sentinel('XXX')
        self.assertGreater(length, 0)
        self.assertEqual(self.buf.extract(), self.s[0])
        length = self.buf.match_to_sentinel('XXX')
        self.assertGreater(length, 0)
        self.assertEqual(self.buf.extract(), self.s[1])
        length = self.buf.match_to_sentinel('XXX')
        self.assertEqual(length, 0)
        self.assertEqual(self.buf.extract(), '')
        self.assertEqual(self.buf.get(), '')

    def test_starts_with(self):
        self.assertIs(self.buf.starts_with('He'), True)
        self.assertEqual(self.buf.extract(), 'He')
        self.assertEqual(self.buf.get(), 'l')

    def test_starts_with_over_next(self):
        self.assertIs(self.buf.starts_with('Hello, Worl'), True)
        self.assertEqual(self.buf.extract(), 'Hello, Worl')
        self.assertEqual(self.buf.get(), 'd')

    def test_starts_with_no_match(self):
        self.assertIs(self.buf.starts_with('ABC'), False)
        self.assertEqual(self.buf.get(), 'H')
