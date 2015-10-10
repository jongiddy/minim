import unittest

from jute import Interface, Dynamic


class Iterable(Interface):

    def __iter__(self):
        """Interface for an iterable."""


class Iterator(Iterable):

    def __next__(self):
        """Interface for an iterator."""


class IterTestMixin:

    def get_test_object(self):
        return object()

    def test_next(self):
        iterator = self.get_test_object()
        self.assertEqual(next(iterator), 0)

    def test_getattr(self):
        iterator = self.get_test_object()
        self.assertEqual(getattr(iterator, '__next__')(), 0)

    def test_attribute(self):
        iterator = self.get_test_object()
        self.assertEqual(iterator.__next__(), 0)


class LotsOfZeros(Iterator.Provider):

    def __iter__(self):
        return self

    def __next__(self):
        return 0


class NextInstanceTests(IterTestMixin, unittest.TestCase):

    def get_test_object(self):
        return LotsOfZeros()


class NextInterfaceTests(IterTestMixin, unittest.TestCase):

    def get_test_object(self):
        return Iterator(LotsOfZeros())


class IteratorProxy(Dynamic.Provider):

    def __init__(self, wrapped_iterator):
        self.wrapped = wrapped_iterator

    def provides_interface(self, interface):
        return interface.implemented_by(Iterator)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.wrapped)


class NextDynamicInstanceTests(IterTestMixin, unittest.TestCase):

    def get_test_object(self):
        return IteratorProxy(LotsOfZeros())


class NextDynamicInterfaceTests(IterTestMixin, unittest.TestCase):

    def get_test_object(self):
        return Iterator(IteratorProxy(LotsOfZeros()))


class GeneratedNext(Iterator.Provider):

    """A class that generates the __next__ method dynamically."""

    def __getattr__(self, name):
        if name == '__next__':
            def f():
                return 0
            return f

    def __iter__(self):
        return self


class GeneratedNextTestMixin(IterTestMixin):

    """Test __next__ for a provider that generates __next__.

    Using a dynamically generated __next__ method fails when using `next`
    or `for` on an object.  To minimise surprise, the interface should
    behave the same way as a normal instance.

    Note, that getting the attribute succeeds otherwise.
    """

    def test_next(self):
        iterator = self.get_test_object()
        with self.assertRaises(TypeError):
            next(iterator)


class GeneratedNextInstanceTests(GeneratedNextTestMixin, unittest.TestCase):

    def get_test_object(self):
        return GeneratedNext()


class GeneratedNextInterfaceTests(GeneratedNextTestMixin, unittest.TestCase):

    def get_test_object(self):
        return Iterator(GeneratedNext())
