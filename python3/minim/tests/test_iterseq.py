import re
import tempfile
import unittest

from minim import iterseq


class IterableAsSequenceInitTest(unittest.TestCase):

    def test_list_is_ok(self):
        buf = iterseq.IterableAsSequence(['Hello, ', 'World!'])
        self.assertEqual(buf.get(), 'H')

    def test_empty_is_ok(self):
        buf = iterseq.IterableAsSequence([])
        with self.assertRaises(StopIteration):
            buf.next()

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