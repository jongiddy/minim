import unittest

from jute import Interface, Dynamic


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
        """Incomplete implementations are caught (during debugging)."""
        class Bar(FooBar.Provider):
            # doesn't implement foo

            def bar():
                pass

        obj = Bar()
        if __debug__:
            with self.assertRaises(NotImplementedError):
                FooBar(obj)
        else:
            foobar = FooBar(obj)
            with self.assertRaises(AttributeError):
                foobar.foo

    def test_incomplete_implementation_validate_true(self):
        """Incomplete implementations are caught (during debugging)."""
        class Bar(FooBar.Provider):
            # doesn't implement foo

            def bar():
                pass

        obj = Bar()
        with self.assertRaises(NotImplementedError):
            FooBar(obj, validate=True)

    def test_incomplete_implementation_validate_false(self):
        """Incomplete implementations are caught (during debugging)."""
        class Bar(FooBar.Provider):
            # doesn't implement foo

            def bar():
                pass

        obj = Bar()
        foobar = FooBar(obj, validate=False)
        with self.assertRaises(AttributeError):
            foobar.foo

    def test_upcast_fails(self):
        # XXX this should probably give the same error as above
        obj = FooBarBaz()
        foo = Foo(obj)
        with self.assertRaises(TypeError):
            FooBar(foo)

    def test_duck_fails(self):
        """Duck-typed object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails."""
        obj = FooBarBaz()
        with self.assertRaises(TypeError):
            FooBaz(obj)

    def test_wrapped_duck_fails(self):
        """Duck-typed wrapped object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails."""
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
            with self.assertRaises(NotImplementedError):
                FooBar(obj)
        else:
            foobar = FooBar(obj)
            with self.assertRaises(AttributeError):
                foobar.foo

    def test_upcast_fails(self):
        # XXX this should probably give the same error as above
        obj = FooBarProxy()
        foo = Foo(obj)
        with self.assertRaises(TypeError):
            FooBar(foo)

    def test_duck_fails(self):
        """Duck-typed object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails."""
        obj = FooBarProxy()
        with self.assertRaises(TypeError):
            FooBaz(obj)

    def test_wrapped_duck_fails(self):
        """Duck-typed wrapped object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails."""
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


iterable = range(5)


class Iterable(Interface):

    def __iter__(self):
        """Interface for an iterable."""


class Count5(Iterable.Provider):

    def __iter__(self):
        return iter(iterable)


class IteratorProxy(Dynamic.Provider):

    def provides_interface(self, interface):
        if issubclass(Iterable, interface):
            return True
        return False

    def __iter__(self):
        return iter(iterable)


class SpecialMethodTests(unittest.TestCase):

    def test_for_instance(self):
        expected = list(iterable)
        result = []
        cnt = Count5()
        for val in cnt:
            result.append(val)
        self.assertEqual(result, expected)

    def test_for_interface(self):
        expected = list(iterable)
        result = []
        cnt = Iterable(Count5())
        for val in cnt:
            result.append(val)
        self.assertEqual(result, expected)

    def test_getattr(self):
        cnt = Iterable(Count5())
        iterator = getattr(cnt, '__iter__')()
        self.assertEqual(next(iterator), 0)

    def test_iter(self):
        cnt = Iterable(Count5())
        iterator = iter(cnt)
        self.assertEqual(next(iterator), 0)

    def test_attribute(self):
        cnt = Iterable(Count5())
        iterator = cnt.__iter__()
        self.assertEqual(next(iterator), 0)


class DynamicSpecialMethodTests(unittest.TestCase):

    def test_for_instance(self):
        expected = list(iterable)
        result = []
        cnt = IteratorProxy()
        for val in cnt:
            result.append(val)
        self.assertEqual(result, expected)

    def test_for_interface(self):
        expected = list(iterable)
        result = []
        cnt = Iterable(IteratorProxy())
        for val in cnt:
            result.append(val)
        self.assertEqual(result, expected)

    def test_getattr(self):
        cnt = Iterable(IteratorProxy())
        iterator = getattr(cnt, '__iter__')()
        self.assertEqual(next(iterator), 0)

    def test_iter(self):
        cnt = Iterable(IteratorProxy())
        iterator = iter(cnt)
        self.assertEqual(next(iterator), 0)

    def test_attribute(self):
        cnt = Iterable(IteratorProxy())
        iterator = cnt.__iter__()
        self.assertEqual(next(iterator), 0)
