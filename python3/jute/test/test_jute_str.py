import unittest

from jute import Interface, Dynamic


class StringLike(Interface):

    def __str__(self):
        """Return string representation."""


class StringTestMixin:

    def get_test_object(self):
        return object()

    def test_str(self):
        string_like = self.get_test_object()
        self.assertEqual(str(string_like), 'foo')

    def test_getattr(self):
        string_like = self.get_test_object()
        self.assertEqual(getattr(string_like, '__str__')(), 'foo')

    def test_attribute(self):
        string_like = self.get_test_object()
        self.assertEqual(string_like.__str__(), 'foo')


class FooString(StringLike.Provider):

    def __str__(self):
        return 'foo'


class StrInstanceTests(StringTestMixin, unittest.TestCase):

    def get_test_object(self):
        return FooString()


class NextInterfaceTests(StringTestMixin, unittest.TestCase):

    def get_test_object(self):
        return StringLike(FooString())


class FooStringProxy(Dynamic.Provider):

    def provides_interface(self, interface):
        if issubclass(StringLike, interface):
            return True
        return False

    def __str__(self):
        return 'foo'


class StrDynamicInterfaceTests(StringTestMixin, unittest.TestCase):

    def get_test_object(self):
        return FooStringProxy()


class GeneratedStr(StringLike.Provider):

    """A class that generates the __str__ method dynamically."""

    def __getattr__(self, name):
        if name == '__str__':
            def f():
                return 'foo'
            return f


class GeneratedStrTestMixin(StringTestMixin):

    """Test __str__ for a provider that generates __str__.

    Using a dynamically generated __str__ method fails, no matter how
    __str__ is accessed.  To minimise surprise, the interface should
    behave the same way as a normal instance.

    Note, that getting the attribute succeeds otherwise.
    """

    def test_getattr(self):
        string_like = self.get_test_object()
        self.assertNotEqual(getattr(string_like, '__str__')(), 'foo')

    def test_attribute(self):
        string_like = self.get_test_object()
        self.assertNotEqual(string_like.__str__(), 'foo')

    def test_str(self):
        string_like = self.get_test_object()
        self.assertNotEqual(str(string_like), 'foo')


class GeneratedStrInstanceTests(GeneratedStrTestMixin, unittest.TestCase):

    def get_test_object(self):
        return GeneratedStr()


class GeneratedStrInterfaceTests(GeneratedStrTestMixin, unittest.TestCase):

    def get_test_object(self):
        return StringLike(GeneratedStr())
