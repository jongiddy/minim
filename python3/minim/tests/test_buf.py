import unittest

from minim import buf


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
