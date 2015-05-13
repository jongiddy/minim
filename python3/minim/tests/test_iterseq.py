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
        try:
            s = self.buf.get()
            while True:
                s += self.buf.next()
        except EOFError:
            self.assertEqual(s, ''.join(self.s))
        else:
            self.fail('No EOFError')

    def test_matching_to_eof(self):
        pat = re.compile(r'[A-Za-z ,!]+')
        self.assertGreater(self.buf.matching(pat), 0)
        self.assertEqual(self.buf.extract(), self.s[0])
        self.assertGreater(self.buf.matching(pat), 0)
        self.assertEqual(self.buf.extract(), self.s[1])
        self.assertEqual(self.buf.matching(pat), 0)
