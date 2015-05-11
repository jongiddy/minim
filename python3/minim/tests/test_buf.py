import unittest

from minim import buf


class BufferInitTest(unittest.TestCase):

    def test_list_is_ok(self):
        buf.Buffer(['Hello, ', 'World!'])

    def test_empty_is_ok(self):
        b = buf.Buffer([])
        with self.assertRaises(StopIteration):
            b.next()


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
