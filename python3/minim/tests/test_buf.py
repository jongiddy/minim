import tempfile
import unittest

from minim import buf


class BufferInitTest(unittest.TestCase):

    def test_list_is_ok(self):
        b = buf.Buffer(['Hello, ', 'World!'])
        self.assertEqual(b.get(), 'H')

    def test_empty_is_ok(self):
        b = buf.Buffer([])
        with self.assertRaises(StopIteration):
            b.next()

    def test_bytes_are_ok(self):
        b = buf.Buffer([b'Hello', b'World!'])
        self.assertEqual(b.get(), b'H'[0])

    def test_non_iterable_fails(self):
        with self.assertRaises(TypeError):
            buf.Buffer(5)

    def test_file_is_ok(self):
        with tempfile.TemporaryFile('w+t') as f:
            f.write('Hello, World!\n')
            f.seek(0)
            b = buf.Buffer(f)
            self.assertEqual(b.get(), 'H')


class BufferTest(unittest.TestCase):

    def setUp(self):
        self.s = ['Hello, ', 'World!']
        self.buf = buf.Buffer(['Hello, ', 'World!'])

    def test_pop(self):
        s = self.buf.get()
        try:
            while True:
                s += self.buf.next()
        except EOFError:
            self.assertEqual(s, ''.join(self.s))
        else:
            self.fail('No EOFError')
