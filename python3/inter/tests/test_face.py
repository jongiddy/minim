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
        if __debug__:
            with self.assertRaises(AttributeError):
                foobar.baz()
            self.assertEqual(foobar.bar, 2)
        else:
            foobar.baz()
            self.assertEqual(foobar.bar, 3)

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
        if __debug__:
            with self.assertRaises(AttributeError):
                foo.baz()
            self.assertEqual(obj.y, 2)
        else:
            foo.baz()
            self.assertEqual(obj.y, 3)

    def test_incomplete_implementation_fails(self):
        class IFooBar(inter.face):
            bar = 0

            def foo(self):
                """A function."""

        class Bar(IFooBar.Provider):
            # doesn't implement foo

            bar = 1

        obj = Bar()
        if __debug__:
            with self.assertRaises(AttributeError):
                IFooBar(obj)
        else:
            IFooBar(obj)
