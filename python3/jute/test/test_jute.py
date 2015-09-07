import unittest

from jute import Interface, Dynamic, InterfaceConformanceError


# Simple interface hierarchy for testing


class Foo(Interface):
    foo = 99


class FooBar(Foo):

    def bar(self):
        """The bar method."""


class FooBaz(Foo):

    def baz(self):
        """The baz method."""


class FooBarBaz(FooBar.Provider):

    """FooBar provider class.

    A class which implements FooBar, and looks like FooBaz, but does
    not implement FooBaz.
    """

    foo = 1

    def bar(self):
        self.foo = 2

    def baz(self):
        self.foo = 3


class FooBarProxy(Dynamic.Provider):

    def provides_interface(self, interface):
        if issubclass(FooBar, interface):
            return True
        return False

    _foo = 1

    def bar(self):
        self._foo = 2

    def baz(self):
        self._foo = 3

    def __getattr__(self, name):
        if name == 'foo':
            return self._foo
        return super().__getattr__(name)


class InterfaceProviderTests(unittest.TestCase):

    def test_provide(self):
        # An interface only has attributes defined in interface (and in
        # sub-interfaces).

        obj = FooBarBaz()
        foobar = FooBar(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        with self.assertRaises(AttributeError):
            foobar.baz()
        self.assertEqual(obj.foo, 2)

    def test_inherit(self):
        obj = FooBarBaz()
        foobar = FooBar(obj)
        foo = Foo(foobar)
        self.assertEqual(foo.foo, 1)
        with self.assertRaises(AttributeError):
            foo.bar()
        self.assertEqual(obj.foo, 1)

    def test_incomplete_implementation_validate_none(self):
        """Incomplete implementations are caught (during debugging).

        If an object claims to provide an interface, but doesn't,
        conversion to the interface will raise an
        InterfaceConformanceError in non-optimised code.

        In optimised code, the relatively expensive verification is
        removed and claims to implement an interface are always
        accepted. Accessing a non-interface attribute will still lead to
        an AttributeError, but this may occur later, when it is more
        difficult to diagnose where the invalid object came from.
        """
        class Bar(FooBar.Provider):
            # doesn't implement foo

            def bar():
                pass

        obj = Bar()
        if __debug__:
            with self.assertRaises(InterfaceConformanceError):
                FooBar(obj)
        else:
            foobar = FooBar(obj)
            with self.assertRaises(AttributeError):
                foobar.foo

    def test_incomplete_implementation_validate_true(self):
        """validate is True -> always raise InterfaceConformanceError."""
        class Bar(FooBar.Provider):
            # doesn't implement foo

            def bar():
                pass

        obj = Bar()
        with self.assertRaises(InterfaceConformanceError):
            FooBar(obj, validate=True)

    def test_incomplete_implementation_validate_false(self):
        """validate is False -> always raise late AttributeError."""
        class Bar(FooBar.Provider):
            # doesn't implement foo

            def bar():
                pass

        obj = Bar()
        foobar = FooBar(obj, validate=False)
        with self.assertRaises(AttributeError):
            foobar.foo

    def test_upcast_fails(self):
        obj = FooBarBaz()
        foo = Foo(obj)
        with self.assertRaises(TypeError):
            FooBar(foo)

    def test_duck_fails(self):
        """Duck-typed object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails with a
        TypeError."""
        obj = FooBarBaz()
        with self.assertRaises(TypeError):
            FooBaz(obj)

    def test_wrapped_duck_fails(self):
        """Duck-typed wrapped object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails with a
        TypeError."""
        obj = FooBarBaz()
        foobar = FooBar(obj)
        with self.assertRaises(TypeError):
            FooBaz(foobar)

    def test_subclass_provider_provides_interface(self):
        class FooBarBazSub(FooBarBaz, FooBaz.Provider):
            pass
        obj = FooBarBazSub()
        foobar = FooBar(obj)
        foobaz = FooBaz(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        foobaz.baz()
        self.assertEqual(obj.foo, 3)

    def test_provider_subclass_provides_interface(self):
        class FooBarBazSub(FooBaz.Provider, FooBarBaz):
            pass
        obj = FooBarBazSub()
        foobar = FooBar(obj)
        foobaz = FooBaz(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        foobaz.baz()
        self.assertEqual(obj.foo, 3)


class DynamicProviderTests(unittest.TestCase):

    def test_provide(self):
        # An interface only has attributes defined in interface (and in
        # sub-interfaces).

        obj = FooBarProxy()
        foobar = FooBar(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        with self.assertRaises(AttributeError):
            foobar.baz()
        self.assertEqual(obj.foo, 2)

    def test_inherit(self):
        obj = FooBarProxy()
        foobar = FooBar(obj)
        foo = Foo(foobar)
        self.assertEqual(foo.foo, 1)
        with self.assertRaises(AttributeError):
            foo.bar()
        self.assertEqual(obj.foo, 1)

    def test_incomplete_implementation_validate_none(self):
        """Incomplete implementations are caught (during debugging)."""
        class BarProxy(Dynamic.Provider):
            # doesn't implement foo

            def provides_interface(self, interface):
                if issubclass(FooBar, interface):
                    return True
                return False

            def bar():
                pass

        obj = BarProxy()
        if __debug__:
            with self.assertRaises(InterfaceConformanceError):
                FooBar(obj)
        else:
            foobar = FooBar(obj)
            with self.assertRaises(AttributeError):
                foobar.foo

    def test_upcast_fails(self):
        obj = FooBarProxy()
        foo = Foo(obj)
        with self.assertRaises(TypeError):
            FooBar(foo)

    def test_duck_fails(self):
        """Duck-typed object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails with a
        TypeError."""
        obj = FooBarProxy()
        with self.assertRaises(TypeError):
            FooBaz(obj)

    def test_wrapped_duck_fails(self):
        """Duck-typed wrapped object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails with a
        TypeError."""
        obj = FooBarProxy()
        foobar = FooBar(obj)
        with self.assertRaises(TypeError):
            FooBaz(foobar)

    def test_subclass_provides_interface(self):
        class FooBarBazSub(FooBarProxy):

            def provides_interface(self, interface):
                if (
                    issubclass(FooBar, interface) or
                    issubclass(FooBaz, interface)
                ):
                    return True
                return False

        obj = FooBarBazSub()
        foobar = FooBar(obj)
        foobaz = FooBaz(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        foobaz.baz()
        self.assertEqual(obj.foo, 3)


count_to_5 = range(5)


class Iterable(Interface):

    def __iter__(self):
        """Interface for an iterable."""


class CountTo5(Iterable.Provider):

    def __iter__(self):
        return iter(count_to_5)


class SpecialMethodTests(unittest.TestCase):

    def test_for_instance(self):
        expected = list(count_to_5)
        result = []
        cnt = CountTo5()
        for val in cnt:
            result.append(val)
        self.assertEqual(result, expected)

    def test_for_interface(self):
        expected = list(count_to_5)
        result = []
        cnt = Iterable(CountTo5())
        for val in cnt:
            result.append(val)
        self.assertEqual(result, expected)

    def test_getattr(self):
        cnt = Iterable(CountTo5())
        iterator = getattr(cnt, '__iter__')()
        self.assertEqual(next(iterator), 0)

    def test_iter(self):
        cnt = Iterable(CountTo5())
        iterator = iter(cnt)
        self.assertEqual(next(iterator), 0)

    def test_attribute(self):
        cnt = Iterable(CountTo5())
        iterator = cnt.__iter__()
        self.assertEqual(next(iterator), 0)


class IterableProxy(Dynamic.Provider):

    def provides_interface(self, interface):
        if issubclass(Iterable, interface):
            return True
        return False

    def __iter__(self):
        return iter(count_to_5)


class DynamicSpecialMethodTests(unittest.TestCase):

    def test_for_instance(self):
        expected = list(count_to_5)
        result = []
        cnt = IterableProxy()
        for val in cnt:
            result.append(val)
        self.assertEqual(result, expected)

    def test_for_interface(self):
        expected = list(count_to_5)
        result = []
        cnt = Iterable(IterableProxy())
        for val in cnt:
            result.append(val)
        self.assertEqual(result, expected)

    def test_getattr(self):
        cnt = Iterable(IterableProxy())
        iterator = getattr(cnt, '__iter__')()
        self.assertEqual(next(iterator), 0)

    def test_iter(self):
        cnt = Iterable(IterableProxy())
        iterator = iter(cnt)
        self.assertEqual(next(iterator), 0)

    def test_attribute(self):
        cnt = Iterable(IterableProxy())
        iterator = cnt.__iter__()
        self.assertEqual(next(iterator), 0)


class GeneratedIterCount5(Iterable.Provider):

    def __getattr__(self, name):
        if name == '__iter__':
            def f():
                return iter(count_to_5)
            return f


class IterSpecialMethodTests(unittest.TestCase):

    """Test __iter__ for a provider that generates __iter__.

    Using a dynamicaly generated __iter__ method fails when using `for`
    on an object.  To minimise surprise, the interface should behave the
    same way.
    """

    def test_iter_for_instance(self):
        cnt = GeneratedIterCount5()
        with self.assertRaises(TypeError):
            iter(cnt)

    def test_iter_for_interface(self):
        cnt = Iterable(GeneratedIterCount5())
        with self.assertRaises(TypeError):
            iter(cnt)

    def test_getattr_for_instance(self):
        cnt = GeneratedIterCount5()
        iterator = getattr(cnt, '__iter__')()
        self.assertEqual(next(iterator), 0)

    def test_getattr_for_interface(self):
        cnt = Iterable(GeneratedIterCount5())
        iterator = getattr(cnt, '__iter__')()
        self.assertEqual(next(iterator), 0)

    def test_attribute_for_instance(self):
        cnt = GeneratedIterCount5()
        iterator = cnt.__iter__()
        self.assertEqual(next(iterator), 0)

    def test_attribute_for_interface(self):
        cnt = Iterable(GeneratedIterCount5())
        iterator = cnt.__iter__()
        self.assertEqual(next(iterator), 0)
