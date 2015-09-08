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


class BaseProviderTestsMixin:

    # Change these to the classes to be tested
    HasFooBarBaz = object
    HasBarOnly = object

    def test_provide(self):
        # An interface only has attributes defined in interface (and in
        # sub-interfaces).
        obj = self.HasFooBarBaz()
        foobar = FooBar(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        with self.assertRaises(AttributeError):
            foobar.baz()
        self.assertEqual(obj.foo, 2)

    def test_inherit(self):
        obj = self.HasFooBarBaz()
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
        obj = self.HasBarOnly()
        if __debug__:
            with self.assertRaises(InterfaceConformanceError):
                FooBar(obj)
        else:
            foobar = FooBar(obj)
            with self.assertRaises(AttributeError):
                foobar.foo

    def test_incomplete_implementation_validate_true(self):
        """validate is True -> always raise InterfaceConformanceError."""
        obj = self.HasBarOnly()
        with self.assertRaises(InterfaceConformanceError):
            FooBar(obj, validate=True)

    def test_incomplete_implementation_validate_false(self):
        """validate is False -> always raise late AttributeError."""
        obj = self.HasBarOnly()
        foobar = FooBar(obj, validate=False)
        with self.assertRaises(AttributeError):
            foobar.foo

    def test_upcast_fails(self):
        obj = self.HasFooBarBaz()
        foo = Foo(obj)
        with self.assertRaises(TypeError):
            FooBar(foo)

    def test_duck_fails(self):
        """Duck-typed object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails with a
        TypeError."""
        obj = self.HasFooBarBaz()
        with self.assertRaises(TypeError):
            FooBaz(obj)

    def test_wrapped_duck_fails(self):
        """Duck-typed wrapped object does not match unclaimed interface.

        Although object matches the interface by duck-typing, it does
        not claim to provide the interface, so it fails with a
        TypeError."""
        obj = self.HasFooBarBaz()
        foobar = FooBar(obj)
        with self.assertRaises(TypeError):
            FooBaz(foobar)

    def test_subclass_provider_provides_interface(self):
        class FooBarBazSubclass(self.HasFooBarBaz, FooBaz.Provider):
            pass
        obj = FooBarBazSubclass()
        foobar = FooBar(obj)
        foobaz = FooBaz(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        foobaz.baz()
        self.assertEqual(obj.foo, 3)

    def test_provider_subclass_provides_interface(self):
        class FooBarBazSubclass(FooBaz.Provider, self.HasFooBarBaz):
            pass
        obj = FooBarBazSubclass()
        foobar = FooBar(obj)
        foobaz = FooBaz(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        foobaz.baz()
        self.assertEqual(obj.foo, 3)


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


class IncompleteFooBar(FooBar.Provider):
    # doesn't implement foo

    def bar():
        pass


class InterfaceProviderTests(BaseProviderTestsMixin, unittest.TestCase):

    HasFooBarBaz = FooBarBaz
    HasBarOnly = IncompleteFooBar


class FooBarBazDynamic(Dynamic.Provider):

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


class IncompleteFooBarDynamic(Dynamic.Provider):
    # doesn't implement foo

    def provides_interface(self, interface):
        if issubclass(FooBar, interface):
            return True
        return False

    def bar():
        pass


class DynamicProviderTests(BaseProviderTestsMixin, unittest.TestCase):

    HasFooBarBaz = FooBarBazDynamic
    HasBarOnly = IncompleteFooBarDynamic

    def test_subclass_provides_interface(self):
        class FooBarBazSubclass(self.HasFooBarBaz):

            def provides_interface(self, interface):
                if (
                    issubclass(FooBar, interface) or
                    issubclass(FooBaz, interface)
                ):
                    return True
                return False

        obj = FooBarBazSubclass()
        foobar = FooBar(obj)
        foobaz = FooBaz(obj)
        self.assertEqual(foobar.foo, 1)
        foobar.bar()
        self.assertEqual(obj.foo, 2)
        foobaz.baz()
        self.assertEqual(obj.foo, 3)
