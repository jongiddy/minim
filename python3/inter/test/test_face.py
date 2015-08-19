import unittest

import inter


class InterfaceTests(unittest.TestCase):

    def test_basic(self):
        # In debug mode, an interface only has attributes defined in interface
        # In optimized mode, the interface is not checked.
        class IFooBar(inter.face):
            bar = 0

            def foo(self):
                """A function."""

        class FooBarBaz(IFooBar.Provider):

            bar = 1

            def foo(self):
                self.bar = 2

            def baz(self):
                self.bar = 3

        obj = FooBarBaz()
        foobar = IFooBar(obj)
        self.assertEqual(foobar.bar, 1)
        foobar.foo()
        self.assertEqual(foobar.bar, 2)
        with self.assertRaises(AttributeError):
            foobar.baz()
        self.assertEqual(foobar.bar, 2)

    def test_inherit(self):
        class IFoo(inter.face):

            def foo(self):
                """A function."""

        class IFooBar(IFoo):
            bar = 0

        class FooBarBaz(IFooBar.Provider):

            bar = 1

            def foo(self):
                self.y = 2

            def baz(self):
                self.y = 3

        obj = FooBarBaz()
        foo = IFoo(obj)
        foo.foo()
        self.assertEqual(obj.y, 2)
        with self.assertRaises(AttributeError):
            foo.baz()
        self.assertEqual(obj.y, 2)

    def test_incomplete_implementation_fails(self):
        class IFooBar(inter.face):
            bar = 0

            def foo(self):
                """A function."""

        class Bar(IFooBar.Provider):
            # doesn't implement foo

            bar = 1

        obj = Bar()
        with self.assertRaises(TypeError):
            IFooBar(obj)

    def test_iterator_ok(self):
        class Iterator(inter.face):

            def __iter__(self):
                pass

            def __next__(self):
                pass

        class XIterator(Iterator.Provider):

            def __init__(self):
                self.x = [1, 2, 3]

            def __iter__(self):
                return self

            def __next__(self):
                if self.x:
                    return self.x.pop(0)
                else:
                    raise StopIteration()

        xiter = XIterator()
        result = []
        for i in Iterator(xiter):
            result.append(i)
        self.assertEqual(result, [1, 2, 3])
