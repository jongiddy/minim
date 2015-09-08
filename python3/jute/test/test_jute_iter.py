import unittest

from jute import Interface, Dynamic


count_to_5 = range(5)


class Iterable(Interface):

    def __iter__(self):
        """Interface for an iterable."""


class IterTestMixin:

    def get_test_object(self):
        return object()

    def test_for(self):
        cnt = self.get_test_object()
        expected = list(count_to_5)
        result = []
        cnt = self.get_test_object()
        for val in cnt:
            result.append(val)
        self.assertEqual(result, expected)

    def test_iter(self):
        cnt = self.get_test_object()
        iterator = iter(cnt)
        self.assertEqual(next(iterator), 0)

    def test_getattr(self):
        cnt = self.get_test_object()
        iterator = getattr(cnt, '__iter__')()
        self.assertEqual(next(iterator), 0)

    def test_attribute(self):
        cnt = self.get_test_object()
        iterator = cnt.__iter__()
        self.assertEqual(next(iterator), 0)


class CountTo5(Iterable.Provider):

    def __iter__(self):
        return iter(count_to_5)


class IterInstanceTests(IterTestMixin, unittest.TestCase):

    def get_test_object(self):
        return CountTo5()


class IterInterfaceTests(IterTestMixin, unittest.TestCase):

    def get_test_object(self):
        return Iterable(CountTo5())


class IterableProxy(Dynamic.Provider):

    def __init__(self, wrapped_iterable):
        self.wrapped = wrapped_iterable

    def provides_interface(self, interface):
        if issubclass(Iterable, interface):
            return True
        return False

    def __iter__(self):
        return iter(self.wrapped)


class IterDynamicInterfaceTests(IterTestMixin, unittest.TestCase):

    def get_test_object(self):
        return IterableProxy(CountTo5())


class GeneratedIter(Iterable.Provider):

    """A class that generates the __iter__ method dynamically."""

    def __getattr__(self, name):
        if name == '__iter__':
            def f():
                return iter(count_to_5)
            return f


class GeneratedIterTestMixin(IterTestMixin):

    """Test __iter__ for a provider that generates __iter__.

    Using a dynamically generated __iter__ method fails when using `iter`
    or `for` on an object.  To minimise surprise, the interface should
    behave the same way as a normal instance.

    Note, that getting the attribute succeeds otherwise.
    """

    def test_for(self):
        cnt = self.get_test_object()
        with self.assertRaises(TypeError):
            for val in cnt:
                pass

    def test_iter(self):
        cnt = self.get_test_object()
        with self.assertRaises(TypeError):
            iter(cnt)


class GeneratedIterInstanceTests(GeneratedIterTestMixin, unittest.TestCase):

    def get_test_object(self):
        return GeneratedIter()


class GeneratedIterInterfaceTests(GeneratedIterTestMixin, unittest.TestCase):

    def get_test_object(self):
        return Iterable(GeneratedIter())
